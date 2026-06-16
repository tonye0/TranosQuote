"""
Core quotation engine.

Given a QuotationRequest, builds a complete, ordered Bill of Materials (BOM):
  - Looks up each selected breaker by ID (scoped to the chosen OEM).
  - Resolves cable size (< 250A) or busbar substitution (>= 250A) per
    requirement #5, using the fixed lookup tables in data/fixed_lookups.py.
  - Appends accessories driven by breaker-size rules (terminal blocks,
    shunt trip coils, motor mechanisms) and by customer template
    (indication lamps, meter, fan, filter, e-stop) - requirement #7.
  - Resolves the panel-level main busbar from total incomer amperage.
"""
from sqlalchemy.orm import Session

from app.models.db import Breaker, Accessory, Customer
from app.models.schemas import QuotationRequest, BOMLine, QuotationResponse, OptionalComponentSelection
from app.data.fixed_lookups import (
    BUSBAR_THRESHOLD_AMPERAGE,
    cable_size_for_amperage,
    outgoing_busbar_for_amperage,
    main_busbar_for_panel_rating,
)


class QuotationError(Exception):
    """Raised for user-facing validation errors (e.g. unknown breaker ID,
    missing customer name, OEM mismatch)."""
    pass


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------
def _find_breaker(db: Session, breaker_id: int, oem: str) -> Breaker:
    breaker = db.query(Breaker).filter(Breaker.id == breaker_id).first()
    if not breaker:
        raise QuotationError(f"Breaker with id={breaker_id} not found. It may have been removed from the catalog.")
    if breaker.oem != oem:
        raise QuotationError(
            f"Breaker '{breaker.part_number}' ({breaker.series}, {breaker.amperage}A) belongs to "
            f"{breaker.oem}, but the quotation is scoped to {oem}. "
            f"Please choose a breaker from the {oem} catalog."
        )
    return breaker


def _find_accessory(db: Session, type_: str, applicability: str, oem: str | None) -> Accessory | None:
    """Find an accessory by type + applicability, preferring an OEM-specific
    match, falling back to an OEM-agnostic (oem=None) entry."""
    if oem:
        acc = (
            db.query(Accessory)
            .filter(Accessory.type == type_, Accessory.applicability == applicability, Accessory.oem == oem)
            .first()
        )
        if acc:
            return acc

    return (
        db.query(Accessory)
        .filter(Accessory.type == type_, Accessory.applicability == applicability, Accessory.oem.is_(None))
        .first()
    )


def _accessory_line(acc: Accessory, quantity: int, sn: int, description_override: str | None = None) -> BOMLine:
    return BOMLine(
        sn=sn,
        description=description_override or acc.description,
        quantity=quantity,
        part_number=acc.part_number,
        unit_price=acc.unit_price,
        total_price=round(acc.unit_price * quantity, 2),
        category="accessory",
    )


# ---------------------------------------------------------------------------
# Breaker + cable/busbar lines (requirement #5)
# ---------------------------------------------------------------------------
def _breaker_and_supply_lines(db: Session, specs, category: str, label_prefix: str, oem: str, sn_start: int, warnings: list[str]):
    """Build BOM lines for a list of BreakerSpec: the breaker itself, plus
    either a cable line (<250A) or a per-breaker outgoing busbar line (>=250A).

    Returns (lines, sn, breaker_rows) where breaker_rows is a list of
    (Breaker, quantity) for downstream accessory rules.
    """
    lines: list[BOMLine] = []
    breaker_rows: list[tuple[Breaker, int]] = []
    sn = sn_start

    for spec in specs:
        breaker = _find_breaker(db, spec.breaker_id, oem)
        breaker_rows.append((breaker, spec.quantity))

        lines.append(BOMLine(
            sn=sn,
            description=(
                f"{label_prefix} MCCB - {breaker.oem} {breaker.series}, "
                f"{breaker.amperage}A, {breaker.rating_kA}kA, 415V 3-Phase, 4-Pole"
            ),
            quantity=spec.quantity,
            part_number=breaker.part_number,
            unit_price=breaker.unit_price,
            total_price=round(breaker.unit_price * spec.quantity, 2),
            category=category,
        ))
        sn += 1

        if breaker.amperage < BUSBAR_THRESHOLD_AMPERAGE:
            cable_size = cable_size_for_amperage(breaker.amperage)
            if cable_size is None:
                warnings.append(
                    f"No cable size is defined for {breaker.amperage}A ({breaker.oem} {breaker.series}, "
                    f"{label_prefix.lower()}). Please confirm cable sizing manually before finalizing."
                )
            else:
                lines.append(BOMLine(
                    sn=sn,
                    description=f"Power Cable - {cable_size}, XLPE/PVC, for {breaker.amperage}A {label_prefix.lower()} (per breaker, 3 runs)",
                    quantity=spec.quantity * 3,  # 3 single-core runs per breaker (3-phase)
                    part_number=f"CBL-{cable_size.replace(' ', '').replace('²', '2').replace('mm', 'MM')}",
                    unit_price=0.0,  # cable priced per meter on-site; placeholder for sales to fill
                    total_price=0.0,
                    category="cable",
                ))
                sn += 1
        else:
            # >=250A: busbar substitution (requirement #5)
            result = outgoing_busbar_for_amperage(breaker.amperage)
            if result is None:
                warnings.append(
                    f"No outgoing busbar size is defined for {breaker.amperage}A ({breaker.oem} {breaker.series}, "
                    f"{label_prefix.lower()}). This exceeds the published busbar table - please confirm sizing with engineering."
                )
            else:
                matched_rating, busbar_desc = result
                note = "" if matched_rating == breaker.amperage else f" (sized for {matched_rating}A - next size up)"
                lines.append(BOMLine(
                    sn=sn,
                    description=f"{busbar_desc} - outgoing busbar for {breaker.amperage}A {label_prefix.lower()}{note}",
                    quantity=spec.quantity,
                    part_number=f"BUSBAR-{busbar_desc.replace(' ', '').upper()}",
                    unit_price=0.0,  # busbar priced per length on-site; placeholder for sales to fill
                    total_price=0.0,
                    category="busbar",
                ))
                sn += 1

    return lines, sn, breaker_rows


# ---------------------------------------------------------------------------
# Frame / amperage-driven accessories (requirement #7)
# ---------------------------------------------------------------------------
def _frame_linked_accessories(db: Session, breaker_rows, label_prefix: str, oem: str, sn: int, warnings: list[str]):
    """For each incomer/outgoing breaker:
      - terminal block, if amperage <= 200A
    (Shunt trip / motor mechanism are NOT auto-included here; they remain
    selectable for 'Others' and are auto-included for Daystar via
    _daystar_breaker_accessories, since not every breaker needs a shunt trip.)
    """
    lines: list[BOMLine] = []

    for breaker, qty in breaker_rows:
        if breaker.amperage <= 200:
            acc = _find_accessory(db, "terminal_block", "LE_200A", oem=None)
            if acc is None:
                warnings.append(
                    f"No terminal block accessory is configured for breakers <=200A "
                    f"(needed for {label_prefix.lower()} {breaker.amperage}A)."
                )
            else:
                lines.append(_accessory_line(
                    acc, qty, sn,
                    description_override=f"{acc.description} ({label_prefix} {breaker.amperage}A, {breaker.series})"
                ))
                sn += 1

    return lines, sn


def _frame_accessory_for_breakers(db: Session, breaker_rows, acc_type: str, oem: str, label: str, sn: int, warnings: list[str]):
    """Add one `acc_type` (shunt_trip / motor_mechanism) per breaker, sized to
    that breaker's frame and OEM."""
    lines: list[BOMLine] = []

    for breaker, qty in breaker_rows:
        acc = _find_accessory(db, acc_type, breaker.frame_size, oem=oem)
        if acc is None:
            warnings.append(
                f"No {label} is configured for {oem} {breaker.frame_size} "
                f"(needed for {breaker.series} {breaker.amperage}A)."
            )
            continue
        lines.append(_accessory_line(
            acc, qty, sn,
            description_override=f"{acc.description} (for {breaker.series} {breaker.amperage}A)"
        ))
        sn += 1

    return lines, sn


# ---------------------------------------------------------------------------
# Main quotation builder
# ---------------------------------------------------------------------------
def build_quotation(db: Session, req: QuotationRequest) -> QuotationResponse:
    customer = db.query(Customer).filter(Customer.id == req.customer_id).first()
    if not customer:
        raise QuotationError(f"Unknown customer_id '{req.customer_id}'.")

    # --- Customer name resolution (requirement #2) ---
    if customer.requires_custom_name:
        if not req.customer_name or not req.customer_name.strip():
            raise QuotationError(
                f"'{customer.name}' requires a customer name to be entered before generating a quotation."
            )
        resolved_customer_name = req.customer_name.strip()
    else:
        resolved_customer_name = customer.name

    # --- OEM validation (requirement #6) ---
    if req.oem not in ("Schneider", "Siemens"):
        raise QuotationError("An OEM (Schneider or Siemens) must be selected before generating a quotation.")

    bom: list[BOMLine] = []
    warnings: list[str] = []
    sn = 1

    # --- Incomers ---
    incomer_lines, sn, incomer_rows = _breaker_and_supply_lines(
        db, req.incomers, "incomer", "Incomer", req.oem, sn, warnings
    )
    bom.extend(incomer_lines)

    # --- Outgoings ---
    outgoing_lines, sn, outgoing_rows = _breaker_and_supply_lines(
        db, req.outgoings, "outgoing", "Outgoing", req.oem, sn, warnings
    )
    bom.extend(outgoing_lines)

    all_breaker_rows = incomer_rows + outgoing_rows

    # --- Terminal blocks (<=200A, requirement #7) ---
    tb_lines, sn = _frame_linked_accessories(db, incomer_rows, "Incomer", req.oem, sn, warnings)
    bom.extend(tb_lines)
    tb_lines, sn = _frame_linked_accessories(db, outgoing_rows, "Outgoing", req.oem, sn, warnings)
    bom.extend(tb_lines)

    # --- Main busbar (panel-level, sized to total incoming capacity) ---
    total_incomer_amperage = sum(b.amperage * qty for b, qty in incomer_rows)
    main_result = main_busbar_for_panel_rating(total_incomer_amperage) if total_incomer_amperage >= BUSBAR_THRESHOLD_AMPERAGE else None
    if main_result:
        matched_rating, busbar_desc = main_result
        note = "" if matched_rating == total_incomer_amperage else f" (sized for {matched_rating}A - next size up)"
        bom.append(BOMLine(
            sn=sn,
            description=f"{busbar_desc} - main busbar, panel rated {total_incomer_amperage}A{note}",
            quantity=1,
            part_number=f"BUSBAR-MAIN-{busbar_desc.replace(' ', '').upper()}",
            unit_price=0.0,
            total_price=0.0,
            category="busbar",
        ))
        sn += 1
    elif total_incomer_amperage >= BUSBAR_THRESHOLD_AMPERAGE:
        warnings.append(
            f"No main busbar size is defined for a total panel rating of {total_incomer_amperage}A. "
            f"This exceeds the published main busbar table - please confirm sizing with engineering."
        )

    # -----------------------------------------------------------------
    # Customer-template-driven accessories (requirement #7)
    # -----------------------------------------------------------------
    if customer.id == "daystar":
        # Daystar: phase indication lamps (auto), meter/fan/filter (auto, one
        # set per panel), and shunt trip + motor mechanism per incomer breaker
        # (sized to frame/OEM).
        acc = _find_accessory(db, "indication_lamp_phase", "ALL", oem=None)
        if acc is None:
            warnings.append("No phase indication lamp accessory is configured.")
        else:
            bom.append(_accessory_line(acc, 1, sn))
            sn += 1

        for acc_type, label in (("shunt_trip", "shunt trip coil"), ("motor_mechanism", "motor mechanism")):
            lines, sn = _frame_accessory_for_breakers(db, incomer_rows, acc_type, req.oem, label, sn, warnings)
            bom.extend(lines)

        for acc_type in ("meter", "fan", "filter"):
            acc = _find_accessory(db, acc_type, "ALL", oem=None)
            if acc is None:
                warnings.append(f"No '{acc_type}' accessory is configured.")
                continue
            bom.append(_accessory_line(acc, 1, sn))
            sn += 1

    else:
        # Others: everything below is user-selectable.
        opt: OptionalComponentSelection | None = req.optional_components

        if opt is None:
            warnings.append(
                "No optional components were selected for this customer. "
                "Review whether indication lamps, e-stop, meter, fan, filter, "
                "shunt trip or motor mechanism are required."
            )
        else:
            # Indication lamps - Others may choose phase and/or on/off/trip
            if opt.indication_lamp_phase:
                acc = _find_accessory(db, "indication_lamp_phase", "ALL", oem=None)
                if acc is None:
                    warnings.append("No phase indication lamp accessory is configured.")
                else:
                    bom.append(_accessory_line(acc, 1, sn))
                    sn += 1

            if opt.indication_lamp_on_off_trip:
                acc = _find_accessory(db, "indication_lamp_on_off_trip", "ALL", oem=None)
                if acc is None:
                    warnings.append("No On/Off/Trip indication lamp accessory is configured.")
                else:
                    bom.append(_accessory_line(acc, 1, sn))
                    sn += 1

            # Meter / fan / filter / e-stop - quantity-selectable
            for acc_type, enabled, qty in (
                ("meter", opt.meter, opt.meter_qty),
                ("fan", opt.fan, opt.fan_qty),
                ("filter", opt.filter, opt.filter_qty),
                ("e_stop", opt.e_stop, opt.e_stop_qty),
            ):
                if enabled and qty > 0:
                    acc = _find_accessory(db, acc_type, "ALL", oem=None)
                    if acc is None:
                        warnings.append(f"No '{acc_type}' accessory is configured.")
                        continue
                    bom.append(_accessory_line(acc, qty, sn))
                    sn += 1

    # --- General notes ---
    if any(line.category == "cable" for line in bom):
        warnings.append(
            "Cable unit prices are not pre-populated; please confirm cable pricing "
            "with procurement before finalizing the quotation."
        )
    if any(line.category == "busbar" for line in bom):
        warnings.append(
            "Busbar unit prices are not pre-populated; please confirm busbar pricing "
            "(length/fabrication) with procurement before finalizing the quotation."
        )

    grand_total = round(sum(line.total_price for line in bom), 2)

    return QuotationResponse(
        customer_id=customer.id,
        customer_name=resolved_customer_name,
        oem=req.oem,
        project_name=req.project_name or "Untitled Project",
        bom=bom,
        grand_total=grand_total,
        warnings=warnings,
    )
