"""
Fixed system lookup tables.

These mappings are intentionally HARDCODED and must NOT be exposed through
any admin/CRUD UI (requirements #4 and #5):
  - Amperage -> cable size (preserved from the original implementation)
  - Amperage -> per-breaker outgoing busbar (>=250A)
  - Panel rating -> main busbar (>=250A)

Cable sizing applies for amperages below 250A. From 250A and above, busbar
substitution applies automatically (see services/quotation_engine.py).
"""

# ---------------------------------------------------------------------------
# Amperage -> Cable size (unchanged from original implementation)
# ---------------------------------------------------------------------------
AMPERAGE_TO_CABLE_SIZE = {
    63:  "16 mm²",
    100: "25 mm²",
    125: "35 mm²",
    160: "50 mm²",
    200: "70 mm²",
    250: "95 mm²",
    320: "120 mm²",
    400: "150 mm²",
    630: "2x150 mm²",
}


def cable_size_for_amperage(amperage: int) -> str | None:
    """Return the fixed cable size for a given amperage, or None if undefined.

    Returns None for amperages >= 250 since busbar substitution applies instead
    (caller is expected to check amperage against BUSBAR threshold first).
    """
    return AMPERAGE_TO_CABLE_SIZE.get(amperage)


# ---------------------------------------------------------------------------
# Busbar substitution threshold
# ---------------------------------------------------------------------------
BUSBAR_THRESHOLD_AMPERAGE = 250  # >= this amperage => busbar instead of cable


# ---------------------------------------------------------------------------
# Per-breaker outgoing busbar (busbar run directly off an individual breaker)
# ---------------------------------------------------------------------------
OUTGOING_BUSBAR_BY_AMPERAGE = {
    250:  "20 x 5 Copper Busbar",
    400:  "20 x 10 Copper Busbar",
    630:  "30 x 10 Copper Busbar",
    800:  "40 x 10 Copper Busbar",
    1000: "50 x 10 Copper Busbar",
    1250: "60 x 10 Copper Busbar",
    1600: "2 x 50 x 10 Copper Busbar",
    2000: "2 x 60 x 10 Copper Busbar",
    2500: "3 x 60 x 10 Copper Busbar",
}


# ---------------------------------------------------------------------------
# Main busbar (panel-level, sized to the overall panel/incomer rating)
# ---------------------------------------------------------------------------
MAIN_BUSBAR_BY_PANEL_RATING = {
    250:  "20 x 5 Copper Busbar",
    300:  "20 x 5 Copper Busbar",
    400:  "20 x 10 Copper Busbar",
    630:  "40 x 10 Copper Busbar",
    800:  "50 x 10 Copper Busbar",
    1000: "60 x 10 Copper Busbar",
    1250: "80 x 10 Copper Busbar",
    1600: "100 x 10 Copper Busbar",
    2000: "120 x 10 Copper Busbar",
    2500: "160 x 10 Copper Busbar",
}


def _nearest_at_or_above(table: dict[int, str], rating: int) -> tuple[int, str] | None:
    """Find the smallest key in `table` that is >= `rating`.

    Used so that e.g. a 300A incomer maps cleanly, and amperages that fall
    between published busbar steps still resolve to the next size up rather
    than failing outright.
    """
    candidates = sorted(k for k in table if k >= rating)
    if not candidates:
        return None
    key = candidates[0]
    return key, table[key]


def outgoing_busbar_for_amperage(amperage: int) -> tuple[int, str] | None:
    """Return (matched_rating, busbar_description) for a per-breaker outgoing busbar,
    or None if the amperage exceeds the published table (caller should flag for
    manual engineering review)."""
    if amperage in OUTGOING_BUSBAR_BY_AMPERAGE:
        return amperage, OUTGOING_BUSBAR_BY_AMPERAGE[amperage]
    return _nearest_at_or_above(OUTGOING_BUSBAR_BY_AMPERAGE, amperage)


def main_busbar_for_panel_rating(panel_rating: int) -> tuple[int, str] | None:
    """Return (matched_rating, busbar_description) for the panel's main busbar,
    or None if the rating exceeds the published table."""
    if panel_rating in MAIN_BUSBAR_BY_PANEL_RATING:
        return panel_rating, MAIN_BUSBAR_BY_PANEL_RATING[panel_rating]
    return _nearest_at_or_above(MAIN_BUSBAR_BY_PANEL_RATING, panel_rating)
