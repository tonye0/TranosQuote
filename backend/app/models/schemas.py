"""Pydantic models (request/response schemas) for the API."""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Literal


OEM = Literal["Schneider", "Siemens"]


# ---------------------------------------------------------------------------
# Reference data responses
# ---------------------------------------------------------------------------
class CustomerOut(BaseModel):
    id: str
    name: str
    description: str
    requires_custom_name: bool


class BreakerOut(BaseModel):
    id: int
    oem: str
    series: str
    amperage: int
    rating_kA: int
    voltage: int
    part_number: str
    unit_price: float
    frame_size: str

    # Populated dynamically (not stored) based on amperage:
    # - cable_size: set for amperage < 250A
    # - busbar: set for amperage >= 250A (per-breaker outgoing busbar)
    cable_size: Optional[str] = None
    busbar: Optional[str] = None


class AccessoryOut(BaseModel):
    id: int
    type: str
    applicability: str
    oem: Optional[str] = None
    customer_scope: str
    part_number: str
    description: str
    unit_price: float


class RatingOptionsOut(BaseModel):
    """Distinct values available for a given OEM, used to populate dropdowns."""
    series_list: List[str]
    amperages: List[int]


# ---------------------------------------------------------------------------
# Admin CRUD - Breakers
# ---------------------------------------------------------------------------
class BreakerCreate(BaseModel):
    oem: OEM
    series: str = Field(..., min_length=1, max_length=40)
    amperage: int = Field(..., gt=0, le=6300)
    rating_kA: int = Field(..., gt=0, le=200)
    voltage: int = Field(default=415, gt=0)
    part_number: str = Field(..., min_length=1, max_length=80)
    unit_price: float = Field(..., ge=0)
    frame_size: Literal["FRAME_100", "FRAME_250", "FRAME_400", "FRAME_630", "NS630b...1600"]


class BreakerUpdate(BaseModel):
    oem: Optional[OEM] = None
    series: Optional[str] = Field(default=None, min_length=1, max_length=40)
    amperage: Optional[int] = Field(default=None, gt=0, le=6300)
    rating_kA: Optional[int] = Field(default=None, gt=0, le=200)
    voltage: Optional[int] = Field(default=None, gt=0)
    part_number: Optional[str] = Field(default=None, min_length=1, max_length=80)
    unit_price: Optional[float] = Field(default=None, ge=0)
    frame_size: Optional[Literal["FRAME_100", "FRAME_250", "FRAME_400", "FRAME_630", "NS630b...1600"]] = None


# ---------------------------------------------------------------------------
# Admin CRUD - Accessories
# ---------------------------------------------------------------------------
class AccessoryCreate(BaseModel):
    type: str = Field(..., min_length=1, max_length=60)
    applicability: str = Field(..., min_length=1, max_length=20)
    oem: Optional[OEM] = None
    customer_scope: Literal["all", "daystar", "others"] = "all"
    part_number: str = Field(..., min_length=1, max_length=80)
    description: str = Field(..., min_length=1, max_length=300)
    unit_price: float = Field(..., ge=0)


class AccessoryUpdate(BaseModel):
    type: Optional[str] = Field(default=None, min_length=1, max_length=60)
    applicability: Optional[str] = Field(default=None, min_length=1, max_length=20)
    oem: Optional[OEM] = None
    customer_scope: Optional[Literal["all", "daystar", "others"]] = None
    part_number: Optional[str] = Field(default=None, min_length=1, max_length=80)
    description: Optional[str] = Field(default=None, min_length=1, max_length=300)
    unit_price: Optional[float] = Field(default=None, ge=0)


# ---------------------------------------------------------------------------
# Quotation request
# ---------------------------------------------------------------------------
class BreakerSpec(BaseModel):
    """A single breaker line item the user configures (incomer or outgoing)."""
    quantity: int = Field(..., gt=0, le=200)
    breaker_id: int = Field(..., description="ID of the selected Breaker catalog entry")


class OptionalComponentSelection(BaseModel):
    """For 'Others' customers - explicit selection of optional accessories
    that are not automatically determined by breaker-size rules."""
    indication_lamp_phase: bool = False
    indication_lamp_on_off_trip: bool = False

    meter: bool = False
    meter_qty: int = Field(default=1, ge=0, le=50)

    fan: bool = False
    fan_qty: int = Field(default=1, ge=0, le=50)

    filter: bool = False
    filter_qty: int = Field(default=1, ge=0, le=50)

    e_stop: bool = False
    e_stop_qty: int = Field(default=1, ge=0, le=50)


class QuotationRequest(BaseModel):
    customer_id: str = Field(..., description="e.g. 'daystar' or 'others'")
    customer_name: Optional[str] = Field(
        default=None,
        description="Required (non-empty) when customer_id requires a custom name, e.g. 'others'.",
    )
    oem: OEM = Field(..., description="Schneider or Siemens - selected before configuration begins")
    project_name: Optional[str] = Field(default="Untitled Project")
    incomers: List[BreakerSpec] = Field(..., min_length=1)
    outgoings: List[BreakerSpec] = Field(..., min_length=1)
    optional_components: Optional[OptionalComponentSelection] = None

    @model_validator(mode="after")
    def check_customer_name(self):
        # Validated again server-side against Customer.requires_custom_name
        # in the quotation engine (DB is the source of truth); this just
        # catches the obvious empty-string case early.
        if self.customer_name is not None and not self.customer_name.strip():
            raise ValueError("customer_name cannot be blank if provided.")
        return self


# ---------------------------------------------------------------------------
# BOM / Quotation response
# ---------------------------------------------------------------------------
class BOMLine(BaseModel):
    sn: int
    description: str
    quantity: int
    part_number: str
    unit_price: float
    total_price: float
    category: str  # incomer | outgoing | accessory | cable | busbar


class QuotationResponse(BaseModel):
    customer_id: str
    customer_name: str
    oem: str
    project_name: str
    bom: List[BOMLine]
    grand_total: float
    warnings: List[str] = []
