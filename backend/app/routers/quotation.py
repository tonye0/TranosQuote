"""Quotation endpoints: live BOM preview + Excel/Word export."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import date
import re

from models.db import get_db
from models.schemas import QuotationRequest, QuotationResponse
from services.quotation_engine import build_quotation, QuotationError
from services.excel_generator import generate_bom_excel
from services.docx_generator import generate_spec_docx

router = APIRouter(prefix="/api/quotation", tags=["quotation"])


def _safe_filename(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_\-]+", "_", name).strip("_")
    return name or "Project"


@router.post("/preview", response_model=QuotationResponse)
def preview_quotation(req: QuotationRequest, db: Session = Depends(get_db)):
    """Compute the BOM without generating files - used for live preview in the UI."""
    try:
        return build_quotation(db, req)
    except QuotationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export/excel")
def export_excel(req: QuotationRequest, db: Session = Depends(get_db)):
    try:
        quotation = build_quotation(db, req)
    except QuotationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    content = generate_bom_excel(quotation)
    filename = f"BOM_{_safe_filename(quotation.project_name)}_{date.today().isoformat()}.xlsx"

    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/export/spec")
def export_spec(req: QuotationRequest, db: Session = Depends(get_db)):
    try:
        quotation = build_quotation(db, req)
    except QuotationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    content = generate_spec_docx(quotation, req, db)
    filename = f"TechnicalSpec_{_safe_filename(quotation.project_name)}_{date.today().isoformat()}.docx"

    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
