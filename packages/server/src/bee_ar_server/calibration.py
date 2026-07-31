"""PD calibration wizard: slider + measure (Issue #7)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/calibration", tags=["calibration"])

REFERENCE_PD_MM = 64.0
REFERENCE_FRAME_WIDTH_MM = 140.0
REFERENCE_FRAME_HEIGHT_MM = 50.0


class CalibrationInput(BaseModel):
    pd_mm: float = Field(..., ge=0.1, le=150.0, description="Interpupillary distance in mm")
    method: str = Field(default="proportional", description="Fit method")


class CalibrationResult(BaseModel):
    pd_mm: float
    scale_factor: float
    fit_width_mm: float
    fit_height_mm: float
    recommended_anchor: str


@router.post("/compute", response_model=CalibrationResult)
def compute_calibration(data: CalibrationInput):
    """Compute AR fit scale from PD measurement."""
    if data.method == "proportional":
        scale = data.pd_mm / REFERENCE_PD_MM
    elif data.method == "linear":
        scale = max(0.5, min(2.0, data.pd_mm / REFERENCE_PD_MM))
    else:
        raise HTTPException(status_code=400, detail=f"Unknown method: {data.method}")

    fit_w = REFERENCE_FRAME_WIDTH_MM * scale
    fit_h = REFERENCE_FRAME_HEIGHT_MM * scale

    if data.pd_mm < 58:
        anchor = "narrow"
    elif data.pd_mm > 70:
        anchor = "wide"
    else:
        anchor = "standard"

    return CalibrationResult(
        pd_mm=data.pd_mm,
        scale_factor=round(scale, 4),
        fit_width_mm=round(fit_w, 2),
        fit_height_mm=round(fit_h, 2),
        recommended_anchor=anchor,
    )


@router.get("/presets")
def list_presets():
    """List common PD presets for quick calibration."""
    return {
        "presets": [
            {"name": "Child (5-10)", "pd_mm": 52.0, "description": "Typical child IPD"},
            {"name": "Teen", "pd_mm": 60.0, "description": "Typical teen IPD"},
            {"name": "Adult Average", "pd_mm": 64.0, "description": "Average adult IPD"},
            {"name": "Adult Wide", "pd_mm": 70.0, "description": "Wide adult IPD"},
        ]
    }
