"""
Seed data for the AC Combiner Panel quotation system.

This module is consumed once by `init_db()` to populate the database on
first run. After that, breakers and accessories are fully manageable via the
admin CRUD endpoints (app/routers/admin.py) - this file is NOT re-read on
every startup once data exists.

To reseed from scratch in development, delete `quotation.db` and restart.
"""

# ---------------------------------------------------------------------------
# Frame size helper
#
# Frame size groups breaker amperages for the purpose of selecting
# compatible accessories (shunt trip coil, motor mechanism - requirement #7:
# "breakers with frame size 100/250/400 can have the same shunt trip coil and
# motor mechanism").
# ---------------------------------------------------------------------------
def amperage_to_frame(amperage: int) -> str:
    if amperage <= 100:
        return "FRAME_100"
    if amperage <= 250:
        return "FRAME_250"
    if amperage <= 400:
        return "FRAME_400"
    return "FRAME_630"


# ---------------------------------------------------------------------------
# BREAKERS (requirement #3 / #6)
#
# Multiple OEMs and multiple series per OEM. The same amperage may appear
# more than once across different series/OEMs with different kA ratings,
# part numbers and prices - this is intentional and required.
# ---------------------------------------------------------------------------
BREAKERS = [
    # ---------------- Schneider - NSX series ----------------
    {"oem": "Schneider", "series": "NSX", "amperage": 100, "rating_kA": 25, "voltage": 415, "part_number": "NSX100F-TM100D", "unit_price": 95.00, "frame_size": amperage_to_frame(100)},
    {"oem": "Schneider", "series": "NSX", "amperage": 100, "rating_kA": 36, "voltage": 415, "part_number": "NSX100N-TM100D", "unit_price": 115.00, "frame_size": amperage_to_frame(100)},
    {"oem": "Schneider", "series": "NSX", "amperage": 160, "rating_kA": 25, "voltage": 415, "part_number": "NSX160F-TM160D", "unit_price": 135.00, "frame_size": amperage_to_frame(160)},
    {"oem": "Schneider", "series": "NSX", "amperage": 160, "rating_kA": 36, "voltage": 415, "part_number": "NSX160N-TM160D", "unit_price": 165.00, "frame_size": amperage_to_frame(160)},
    {"oem": "Schneider", "series": "NSX", "amperage": 250, "rating_kA": 36, "voltage": 415, "part_number": "NSX250N-TM250D", "unit_price": 258.00, "frame_size": amperage_to_frame(250)},
    {"oem": "Schneider", "series": "NSX", "amperage": 250, "rating_kA": 50, "voltage": 415, "part_number": "NSX250H-TM250D", "unit_price": 340.00, "frame_size": amperage_to_frame(250)},
    {"oem": "Schneider", "series": "NSX", "amperage": 400, "rating_kA": 36, "voltage": 415, "part_number": "NSX400N-TM400D", "unit_price": 415.00, "frame_size": amperage_to_frame(400)},
    {"oem": "Schneider", "series": "NSX", "amperage": 400, "rating_kA": 50, "voltage": 415, "part_number": "NSX400H-TM400D", "unit_price": 545.00, "frame_size": amperage_to_frame(400)},
    {"oem": "Schneider", "series": "NSX", "amperage": 630, "rating_kA": 36, "voltage": 415, "part_number": "NSX630N-TM630D", "unit_price": 620.00, "frame_size": amperage_to_frame(630)},
    {"oem": "Schneider", "series": "NSX", "amperage": 630, "rating_kA": 50, "voltage": 415, "part_number": "NSX630H-TM630D", "unit_price": 810.00, "frame_size": amperage_to_frame(630)},

    # ---------------- Schneider - CVS series (lower-cost alternative) ----------------
    {"oem": "Schneider", "series": "CVS", "amperage": 100, "rating_kA": 25, "voltage": 415, "part_number": "CVS100F-TM100D", "unit_price": 78.00, "frame_size": amperage_to_frame(100)},
    {"oem": "Schneider", "series": "CVS", "amperage": 160, "rating_kA": 25, "voltage": 415, "part_number": "CVS160F-TM160D", "unit_price": 112.00, "frame_size": amperage_to_frame(160)},
    {"oem": "Schneider", "series": "CVS", "amperage": 250, "rating_kA": 25, "voltage": 415, "part_number": "CVS250F-TM250D", "unit_price": 198.00, "frame_size": amperage_to_frame(250)},
    {"oem": "Schneider", "series": "CVS", "amperage": 400, "rating_kA": 25, "voltage": 415, "part_number": "CVS400F-TM400D", "unit_price": 320.00, "frame_size": amperage_to_frame(400)},

    # ---------------- Schneider - GoPact series (compact, entry-level) ----------------
    {"oem": "Schneider", "series": "GoPact", "amperage": 63,  "rating_kA": 10, "voltage": 415, "part_number": "GOPACT-MCCB-063-10", "unit_price": 45.00, "frame_size": amperage_to_frame(63)},
    {"oem": "Schneider", "series": "GoPact", "amperage": 100, "rating_kA": 10, "voltage": 415, "part_number": "GOPACT-MCCB-100-10", "unit_price": 65.00, "frame_size": amperage_to_frame(100)},
    {"oem": "Schneider", "series": "GoPact", "amperage": 160, "rating_kA": 10, "voltage": 415, "part_number": "GOPACT-MCCB-160-10", "unit_price": 95.00, "frame_size": amperage_to_frame(160)},
    {"oem": "Schneider", "series": "GoPact", "amperage": 200, "rating_kA": 10, "voltage": 415, "part_number": "GOPACT-MCCB-200-10", "unit_price": 120.00, "frame_size": amperage_to_frame(200)},

    # ---------------- Siemens - 3VA series ----------------
    {"oem": "Siemens", "series": "3VA", "amperage": 100, "rating_kA": 25, "voltage": 415, "part_number": "3VA1110-3ED32-0AA0", "unit_price": 98.00, "frame_size": amperage_to_frame(100)},
    {"oem": "Siemens", "series": "3VA", "amperage": 100, "rating_kA": 36, "voltage": 415, "part_number": "3VA1110-3ED36-0AA0", "unit_price": 118.00, "frame_size": amperage_to_frame(100)},
    {"oem": "Siemens", "series": "3VA", "amperage": 160, "rating_kA": 25, "voltage": 415, "part_number": "3VA1116-3ED32-0AA0", "unit_price": 138.00, "frame_size": amperage_to_frame(160)},
    {"oem": "Siemens", "series": "3VA", "amperage": 160, "rating_kA": 36, "voltage": 415, "part_number": "3VA1116-3ED36-0AA0", "unit_price": 168.00, "frame_size": amperage_to_frame(160)},
    {"oem": "Siemens", "series": "3VA", "amperage": 250, "rating_kA": 36, "voltage": 415, "part_number": "3VA1225-3ED36-0AA0", "unit_price": 262.00, "frame_size": amperage_to_frame(250)},
    {"oem": "Siemens", "series": "3VA", "amperage": 250, "rating_kA": 50, "voltage": 415, "part_number": "3VA1225-3ED56-0AA0", "unit_price": 345.00, "frame_size": amperage_to_frame(250)},
    {"oem": "Siemens", "series": "3VA", "amperage": 400, "rating_kA": 36, "voltage": 415, "part_number": "3VA1240-3ED36-0AA0", "unit_price": 420.00, "frame_size": amperage_to_frame(400)},
    {"oem": "Siemens", "series": "3VA", "amperage": 400, "rating_kA": 50, "voltage": 415, "part_number": "3VA1240-3ED56-0AA0", "unit_price": 550.00, "frame_size": amperage_to_frame(400)},
    {"oem": "Siemens", "series": "3VA", "amperage": 630, "rating_kA": 36, "voltage": 415, "part_number": "3VA1263-3ED36-0AA0", "unit_price": 625.00, "frame_size": amperage_to_frame(630)},

    # ---------------- Siemens - 3VL series ----------------
    {"oem": "Siemens", "series": "3VL", "amperage": 160, "rating_kA": 25, "voltage": 415, "part_number": "3VL1716-1DD36-0AA0", "unit_price": 130.00, "frame_size": amperage_to_frame(160)},
    {"oem": "Siemens", "series": "3VL", "amperage": 250, "rating_kA": 25, "voltage": 415, "part_number": "3VL1725-1DD36-0AA0", "unit_price": 200.00, "frame_size": amperage_to_frame(250)},
    {"oem": "Siemens", "series": "3VL", "amperage": 400, "rating_kA": 25, "voltage": 415, "part_number": "3VL1740-1DD36-0AA0", "unit_price": 325.00, "frame_size": amperage_to_frame(400)},
]


# ---------------------------------------------------------------------------
# ACCESSORIES (requirement #7)
#
# applicability:
#   - "FRAME_100" / "FRAME_250" / "FRAME_400" / "FRAME_630"  -> shunt trip /
#     motor mechanism, shared across all amperages within that frame
#   - "LE_200A"  -> terminal blocks, included automatically when the
#     associated breaker amperage <= 200A
#   - "ALL"      -> panel-level accessory, not tied to a specific breaker
#
# customer_scope:
#   - "all"      -> any customer
#   - "daystar"  -> Daystar only
#   - "others"   -> Others only
# ---------------------------------------------------------------------------
ACCESSORIES = [
    # ---------------- Emergency stop (panel-level, all customers) ----------------
    {"type": "e_stop", "applicability": "ALL", "oem": None, "customer_scope": "all",
     "part_number": "ACC-ESTOP-001",
     "description": "Emergency Stop Push Button, 22mm, Red Mushroom Head, NC contact",
     "unit_price": 18.00},

    # ---------------- Shunt trip coils (frame-linked, OEM-specific) ----------------
    # Schneider
    {"type": "shunt_trip", "applicability": "FRAME_100", "oem": "Schneider", "customer_scope": "all",
     "part_number": "SCH-SHT-100", "description": "Shunt Trip Coil, 230VAC, for Schneider 100A Frame MCCB", "unit_price": 35.00},
    {"type": "shunt_trip", "applicability": "FRAME_250", "oem": "Schneider", "customer_scope": "all",
     "part_number": "SCH-SHT-250", "description": "Shunt Trip Coil, 230VAC, for Schneider 250A Frame MCCB", "unit_price": 48.00},
    {"type": "shunt_trip", "applicability": "FRAME_400", "oem": "Schneider", "customer_scope": "all",
     "part_number": "SCH-SHT-400", "description": "Shunt Trip Coil, 230VAC, for Schneider 400A Frame MCCB", "unit_price": 62.00},
    {"type": "shunt_trip", "applicability": "FRAME_630", "oem": "Schneider", "customer_scope": "all",
     "part_number": "SCH-SHT-630", "description": "Shunt Trip Coil, 230VAC, for Schneider 630A Frame MCCB", "unit_price": 85.00},
    # Siemens
    {"type": "shunt_trip", "applicability": "FRAME_100", "oem": "Siemens", "customer_scope": "all",
     "part_number": "SIE-SHT-100", "description": "Shunt Trip Coil, 230VAC, for Siemens 100A Frame MCCB", "unit_price": 37.00},
    {"type": "shunt_trip", "applicability": "FRAME_250", "oem": "Siemens", "customer_scope": "all",
     "part_number": "SIE-SHT-250", "description": "Shunt Trip Coil, 230VAC, for Siemens 250A Frame MCCB", "unit_price": 50.00},
    {"type": "shunt_trip", "applicability": "FRAME_400", "oem": "Siemens", "customer_scope": "all",
     "part_number": "SIE-SHT-400", "description": "Shunt Trip Coil, 230VAC, for Siemens 400A Frame MCCB", "unit_price": 64.00},
    {"type": "shunt_trip", "applicability": "FRAME_630", "oem": "Siemens", "customer_scope": "all",
     "part_number": "SIE-SHT-630", "description": "Shunt Trip Coil, 230VAC, for Siemens 630A Frame MCCB", "unit_price": 88.00},

    # ---------------- Motor mechanisms (frame-linked, OEM-specific) ----------------
    # Schneider
    {"type": "motor_mechanism", "applicability": "FRAME_100", "oem": "Schneider", "customer_scope": "all",
     "part_number": "SCH-MOE-100", "description": "Motor Mechanism (Motorised Operator), 230VAC, for Schneider 100A Frame MCCB", "unit_price": 145.00},
    {"type": "motor_mechanism", "applicability": "FRAME_250", "oem": "Schneider", "customer_scope": "all",
     "part_number": "SCH-MOE-250", "description": "Motor Mechanism (Motorised Operator), 230VAC, for Schneider 250A Frame MCCB", "unit_price": 195.00},
    {"type": "motor_mechanism", "applicability": "FRAME_400", "oem": "Schneider", "customer_scope": "all",
     "part_number": "SCH-MOE-400", "description": "Motor Mechanism (Motorised Operator), 230VAC, for Schneider 400A Frame MCCB", "unit_price": 260.00},
    {"type": "motor_mechanism", "applicability": "FRAME_630", "oem": "Schneider", "customer_scope": "all",
     "part_number": "SCH-MOE-630", "description": "Motor Mechanism (Motorised Operator), 230VAC, for Schneider 630A Frame MCCB", "unit_price": 340.00},
    # Siemens
    {"type": "motor_mechanism", "applicability": "FRAME_100", "oem": "Siemens", "customer_scope": "all",
     "part_number": "SIE-MOE-100", "description": "Motor Mechanism (Motorised Operator), 230VAC, for Siemens 100A Frame MCCB", "unit_price": 150.00},
    {"type": "motor_mechanism", "applicability": "FRAME_250", "oem": "Siemens", "customer_scope": "all",
     "part_number": "SIE-MOE-250", "description": "Motor Mechanism (Motorised Operator), 230VAC, for Siemens 250A Frame MCCB", "unit_price": 200.00},
    {"type": "motor_mechanism", "applicability": "FRAME_400", "oem": "Siemens", "customer_scope": "all",
     "part_number": "SIE-MOE-400", "description": "Motor Mechanism (Motorised Operator), 230VAC, for Siemens 400A Frame MCCB", "unit_price": 265.00},
    {"type": "motor_mechanism", "applicability": "FRAME_630", "oem": "Siemens", "customer_scope": "all",
     "part_number": "SIE-MOE-630", "description": "Motor Mechanism (Motorised Operator), 230VAC, for Siemens 630A Frame MCCB", "unit_price": 345.00},

    # ---------------- Terminal blocks (amperage <= 200A, OEM-agnostic) ----------------
    {"type": "terminal_block", "applicability": "LE_200A", "oem": None, "customer_scope": "all",
     "part_number": "ACC-TB-STD", "description": "Terminal Block Set, for MCCB rated 200A and below", "unit_price": 6.50},

    # ---------------- Indication lamps ----------------
    # Daystar: phase indication lamps only
    {"type": "indication_lamp_phase", "applicability": "ALL", "oem": None, "customer_scope": "all",
     "part_number": "ACC-LMP-PHASE-3", "description": "Phase Indication Lamps (R/Y/B), 22mm LED, panel-mounted, set of 3", "unit_price": 24.00},
    # Others: additionally offer On/Off/Trip lamps
    {"type": "indication_lamp_on_off_trip", "applicability": "ALL", "oem": None, "customer_scope": "others",
     "part_number": "ACC-LMP-OOT-3", "description": "On/Off/Trip Indication Lamps, 22mm LED, set of 3", "unit_price": 28.00},

    # ---------------- Meter (Daystar auto-include, Others selectable) ----------------
    {"type": "meter", "applicability": "ALL", "oem": None, "customer_scope": "all",
     "part_number": "ACC-MTR-DIG01", "description": "Digital Multifunction Power Meter (V/A/kW/kWh), LCD display, RS485", "unit_price": 110.00},

    # ---------------- Fan (Daystar auto-include, Others selectable) ----------------
    {"type": "fan", "applicability": "ALL", "oem": None, "customer_scope": "all",
     "part_number": "ACC-FAN-220V", "description": "Panel Cooling Fan, 220VAC, 150 CFM, with louvre", "unit_price": 42.00},

    # ---------------- Filter (Daystar auto-include, Others selectable) ----------------
    {"type": "filter", "applicability": "ALL", "oem": None, "customer_scope": "all",
     "part_number": "ACC-FLT-STD", "description": "Replaceable Intake Air Filter Mesh, fits standard fan louvre", "unit_price": 8.00},
]


# ---------------------------------------------------------------------------
# CUSTOMERS / TEMPLATES (requirement #2)
# ---------------------------------------------------------------------------
CUSTOMERS = [
    {
        "id": "daystar",
        "name": "Daystar",
        "description": "Standard Daystar panel template - phase indication lamps, meter, fan & filter included automatically. Shunt trip / motor mechanism / terminal blocks applied per breaker rules.",
        "requires_custom_name": False,
    },
    {
        "id": "others",
        "name": "Others",
        "description": "Generic customer template - enter the customer's name; all optional accessories are user-selectable.",
        "requires_custom_name": True,
    },
]

# ---------------------------------------------------------------------------
# PANEL-LEVEL CONSTANTS / GENERAL SPEC DEFAULTS
# ---------------------------------------------------------------------------
PANEL_DEFAULTS = {
    "system_voltage": "415V AC, 3-Phase, 50Hz",
    "control_voltage": "230V AC",
    "enclosure_rating": "IP54",
    "enclosure_material": "Mild Steel, powder coated (RAL 7035)",
    "busbar_material": "Tinned Copper",
    "earth_fault_protection": "Included on all incomers",
    "standard_compliance": "IEC 61439-1 / IEC 61439-2",
}
