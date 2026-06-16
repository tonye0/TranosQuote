"""
Database configuration and models using SQLAlchemy + SQLite.

SQLite is used for simplicity / zero-config deployment. Swap DATABASE_URL
for Postgres/MySQL in production - SQLAlchemy handles the rest.

Schema notes (see README "Architecture" section for the full writeup):
  - Breaker now stores OEM, series, and supports multiple entries per
    amperage (different OEM/series combinations each have their own part
    number, price and kA rating).
  - Accessory is a flexible, admin-manageable catalog: each row has a
    `type`, `applicability` (frame/amperage band or "ALL"), OEM,
    customer_scope, part number, description and price. New accessory types
    can be added purely through data (admin CRUD) - no code changes needed.
  - Cable size and busbar lookups are NOT stored in the DB; they are fixed
    system logic in app/data/fixed_lookups.py (per requirements #4 and #5).
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "quotation.db")
DATABASE_URL = f"sqlite:///{os.path.abspath(DB_PATH)}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------
class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, index=True)  # e.g. "daystar", "others"
    name = Column(String, nullable=False)
    description = Column(String, default="")
    # Whether this customer requires a manually-entered customer name
    # (requirement #2 - "Others" prompts for a free-text customer name).
    requires_custom_name = Column(Boolean, nullable=False, default=False)


# ---------------------------------------------------------------------------
# Breakers (requirement #3)
#
# Each row is one OEM/series/amperage/kA/part-number combination. The same
# amperage can legitimately have multiple rows (different series within the
# same OEM, e.g. Schneider NSX160 @ 36kA vs. Schneider CVS160 @ 25kA, or the
# same amperage/kA under different OEMs).
# ---------------------------------------------------------------------------
class Breaker(Base):
    __tablename__ = "breakers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    oem = Column(String, nullable=False, index=True)        # "Schneider" | "Siemens"
    series = Column(String, nullable=False, index=True)     # "NSX", "CVS", "GoPact", "3VA", ...
    amperage = Column(Integer, nullable=False, index=True)
    rating_kA = Column(Integer, nullable=False, index=True)
    voltage = Column(Integer, nullable=False, default=415)

    part_number = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False, default=0.0)

    # Frame size used to group compatible accessories (shunt trip / motor
    # mechanism). Distinct from amperage - several amperages share a frame.
    frame_size = Column(String, nullable=False, index=True)  # "FRAME_100" | "FRAME_250" | "FRAME_400" | "FRAME_630"

    __table_args__ = (
        UniqueConstraint("oem", "series", "amperage", "rating_kA", "part_number", name="uq_breaker_combo"),
    )


# ---------------------------------------------------------------------------
# Accessories (requirement #7)
#
# A flexible catalog. `applicability` encodes the rule that determines when
# this accessory is relevant:
#   - For frame-linked accessories (shunt trip coil, motor mechanism):
#       applicability = "FRAME_100" | "FRAME_250" | "FRAME_400" | "FRAME_630"
#   - For amperage-threshold accessories (terminal blocks):
#       applicability = "LE_200A"  (applies when breaker amperage <= 200A)
#   - For panel-level / customer-scoped accessories (indication lamps,
#     e-stop, meter, fan, filter):
#       applicability = "ALL" or "STANDARD"
#
# `customer_scope` controls which customer templates may select/receive this
# accessory:
#   - "all"     -> available to every customer
#   - "daystar" -> Daystar only
#   - "others"  -> Others only
# ---------------------------------------------------------------------------
class Accessory(Base):
    __tablename__ = "accessories"

    id = Column(Integer, primary_key=True, autoincrement=True)

    type = Column(String, nullable=False, index=True)
    # e.g. "shunt_trip", "motor_mechanism", "terminal_block",
    #      "indication_lamp_phase", "indication_lamp_on_off_trip",
    #      "e_stop", "meter", "fan", "filter"

    applicability = Column(String, nullable=False, index=True, default="ALL")
    oem = Column(String, nullable=True, index=True)  # null = OEM-agnostic accessory
    customer_scope = Column(String, nullable=False, default="all", index=True)

    part_number = Column(String, nullable=False)
    description = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        UniqueConstraint("type", "applicability", "oem", "part_number", name="uq_accessory_combo"),
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables and seed initial data if empty."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(Customer).count() == 0:
            from app.data.components import CUSTOMERS

            for c in CUSTOMERS:
                db.add(Customer(
                    id=c["id"],
                    name=c["name"],
                    description=c["description"],
                    requires_custom_name=c.get("requires_custom_name", False),
                ))
            db.commit()

        if db.query(Breaker).count() == 0:
            from app.data.components import BREAKERS
            for b in BREAKERS:
                db.add(Breaker(**b))
            db.commit()

        if db.query(Accessory).count() == 0:
            from app.data.components import ACCESSORIES
            for a in ACCESSORIES:
                db.add(Accessory(**a))
            db.commit()
    finally:
        db.close()
