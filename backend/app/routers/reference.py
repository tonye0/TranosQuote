"""
Reference-data endpoints: customers, OEM-scoped breaker catalog (with
auto-resolved cable size / busbar), and accessory catalog.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import distinct

from app.models.db import get_db, Customer, Breaker, Accessory
from app.models.schemas import CustomerOut, BreakerOut, AccessoryOut, RatingOptionsOut
from app.data.fixed_lookups import (
    BUSBAR_THRESHOLD_AMPERAGE,
    cable_size_for_amperage,
    outgoing_busbar_for_amperage,
)

router = APIRouter(prefix="/api", tags=["reference"])


def _attach_supply_info(breaker: Breaker) -> BreakerOut:
    """Resolve cable size or busbar for a breaker based on its amperage
    (requirements #4 and #5 - fixed, non-editable logic)."""
    out = BreakerOut.model_validate(breaker, from_attributes=True)

    if breaker.amperage < BUSBAR_THRESHOLD_AMPERAGE:
        out.cable_size = cable_size_for_amperage(breaker.amperage)
        out.busbar = None
    else:
        out.cable_size = None
        result = outgoing_busbar_for_amperage(breaker.amperage)
        out.busbar = result[1] if result else None

    return out


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------
@router.get("/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    return [
        CustomerOut(
            id=c.id, name=c.name, description=c.description,
            requires_custom_name=c.requires_custom_name,
        )
        for c in customers
    ]


@router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")
    return CustomerOut(
        id=c.id, name=c.name, description=c.description,
        requires_custom_name=c.requires_custom_name,
    )


# ---------------------------------------------------------------------------
# Breakers - OEM-scoped (requirement #6)
# ---------------------------------------------------------------------------
@router.get("/breakers/options", response_model=RatingOptionsOut)
def breaker_options(
    oem: str = Query(..., description="Schneider or Siemens"),
    db: Session = Depends(get_db),
):
    """Return the distinct series and amperages available for the given OEM,
    used to populate dropdowns. Requires an OEM selection (requirement #6)."""
    base = db.query(Breaker).filter(Breaker.oem == oem)

    series_list = [r[0] for r in base.with_entities(distinct(Breaker.series)).order_by(Breaker.series).all()]
    amps = [r[0] for r in base.with_entities(distinct(Breaker.amperage)).order_by(Breaker.amperage).all()]

    if not series_list:
        raise HTTPException(
            status_code=404,
            detail=f"No breakers found for OEM '{oem}'. The catalog may be empty - check the admin panel.",
        )

    return RatingOptionsOut(series_list=series_list, amperages=amps)


@router.get("/breakers", response_model=list[BreakerOut])
def list_breakers(
    oem: str = Query(..., description="Schneider or Siemens - required"),
    series: str | None = None,
    amperage: int | None = None,
    db: Session = Depends(get_db),
):
    """List breakers for the given OEM, optionally filtered by series and/or
    amperage. Cable size or busbar is resolved automatically for each row."""
    q = db.query(Breaker).filter(Breaker.oem == oem)
    if series is not None:
        q = q.filter(Breaker.series == series)
    if amperage is not None:
        q = q.filter(Breaker.amperage == amperage)

    breakers = q.order_by(Breaker.series, Breaker.amperage, Breaker.rating_kA).all()

    if not breakers:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No breakers found for OEM='{oem}'"
                + (f", series='{series}'" if series else "")
                + (f", amperage={amperage}A" if amperage is not None else "")
                + ". Please choose a different combination, or check the admin panel."
            ),
        )

    return [_attach_supply_info(b) for b in breakers]


@router.get("/breakers/{breaker_id}", response_model=BreakerOut)
def get_breaker(breaker_id: int, db: Session = Depends(get_db)):
    """Look up a single breaker by ID, with cable size / busbar resolved.
    Used by the frontend for real-time preview once a specific breaker is chosen."""
    b = db.query(Breaker).filter(Breaker.id == breaker_id).first()
    if not b:
        raise HTTPException(status_code=404, detail=f"Breaker with id={breaker_id} not found.")
    return _attach_supply_info(b)


# ---------------------------------------------------------------------------
# Accessories
# ---------------------------------------------------------------------------
@router.get("/accessories", response_model=list[AccessoryOut])
def list_accessories(
    type: str | None = None,
    oem: str | None = None,
    customer_scope: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Accessory)
    if type is not None:
        q = q.filter(Accessory.type == type)
    if oem is not None:
        q = q.filter((Accessory.oem == oem) | (Accessory.oem.is_(None)))
    if customer_scope is not None:
        q = q.filter((Accessory.customer_scope == customer_scope) | (Accessory.customer_scope == "all"))
    return q.all()
