"""
Admin endpoints: full CRUD for the breaker and accessory catalogs
(requirements #3 and #7).

These endpoints have no separate authentication layer in this codebase -
in production, mount this router behind whatever auth/role-check middleware
protects the rest of the admin/settings area.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.db import get_db, Breaker, Accessory
from models.schemas import (
    BreakerOut, BreakerCreate, BreakerUpdate,
    AccessoryOut, AccessoryCreate, AccessoryUpdate,
)
from routers.reference import _attach_supply_info

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Breakers
# ---------------------------------------------------------------------------
@router.get("/breakers", response_model=list[BreakerOut])
def admin_list_breakers(db: Session = Depends(get_db)):
    """List the full breaker catalog across all OEMs/series (admin view)."""
    breakers = db.query(Breaker).order_by(Breaker.oem, Breaker.series, Breaker.amperage).all()
    return [_attach_supply_info(b) for b in breakers]


@router.post("/breakers", response_model=BreakerOut, status_code=201)
def admin_create_breaker(payload: BreakerCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(Breaker)
        .filter(
            Breaker.oem == payload.oem,
            Breaker.series == payload.series,
            Breaker.amperage == payload.amperage,
            Breaker.rating_kA == payload.rating_kA,
            Breaker.part_number == payload.part_number,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A breaker with OEM={payload.oem}, series={payload.series}, "
                f"{payload.amperage}A, {payload.rating_kA}kA and part number "
                f"'{payload.part_number}' already exists (id={existing.id})."
            ),
        )

    breaker = Breaker(**payload.model_dump())
    db.add(breaker)
    db.commit()
    db.refresh(breaker)
    return _attach_supply_info(breaker)


@router.put("/breakers/{breaker_id}", response_model=BreakerOut)
def admin_update_breaker(breaker_id: int, payload: BreakerUpdate, db: Session = Depends(get_db)):
    breaker = db.query(Breaker).filter(Breaker.id == breaker_id).first()
    if not breaker:
        raise HTTPException(status_code=404, detail=f"Breaker with id={breaker_id} not found.")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    for field, value in updates.items():
        setattr(breaker, field, value)

    db.commit()
    db.refresh(breaker)
    return _attach_supply_info(breaker)


@router.delete("/breakers/{breaker_id}", status_code=204)
def admin_delete_breaker(breaker_id: int, db: Session = Depends(get_db)):
    breaker = db.query(Breaker).filter(Breaker.id == breaker_id).first()
    if not breaker:
        raise HTTPException(status_code=404, detail=f"Breaker with id={breaker_id} not found.")
    db.delete(breaker)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Accessories
# ---------------------------------------------------------------------------
@router.get("/accessories", response_model=list[AccessoryOut])
def admin_list_accessories(db: Session = Depends(get_db)):
    """List the full accessory catalog across all OEMs/types (admin view)."""
    return db.query(Accessory).order_by(Accessory.oem, Accessory.type, Accessory.applicability).all()


@router.post("/accessories", response_model=AccessoryOut, status_code=201)
def admin_create_accessory(payload: AccessoryCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(Accessory)
        .filter(
            Accessory.oem == payload.oem,
            Accessory.type == payload.type,
            Accessory.applicability == payload.applicability,
            Accessory.part_number == payload.part_number,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"An accessory with OEM={payload.oem}, type={payload.type}, "
                f"applicability={payload.applicability} and part number "
                f"'{payload.part_number}' already exists (id={existing.id})."
            ),
        )

    accessory = Accessory(**payload.model_dump())
    db.add(accessory)
    db.commit()
    db.refresh(accessory)
    return accessory


@router.put("/accessories/{accessory_id}", response_model=AccessoryOut)
def admin_update_accessory(accessory_id: int, payload: AccessoryUpdate, db: Session = Depends(get_db)):
    accessory = db.query(Accessory).filter(Accessory.id == accessory_id).first()
    if not accessory:
        raise HTTPException(status_code=404, detail=f"Accessory with id={accessory_id} not found.")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    for field, value in updates.items():
        setattr(accessory, field, value)

    db.commit()
    db.refresh(accessory)
    return accessory


@router.delete("/accessories/{accessory_id}", status_code=204)
def admin_delete_accessory(accessory_id: int, db: Session = Depends(get_db)):
    accessory = db.query(Accessory).filter(Accessory.id == accessory_id).first()
    if not accessory:
        raise HTTPException(status_code=404, detail=f"Accessory with id={accessory_id} not found.")
    db.delete(accessory)
    db.commit()
    return None
