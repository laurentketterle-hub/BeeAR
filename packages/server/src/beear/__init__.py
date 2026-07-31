"""BeeAR — virtual try-on server."""

__version__ = "0.4.56"

# PD calibration wizard (Issue #7)
from .calibration import router as calibration_router
app.include_router(calibration_router)
