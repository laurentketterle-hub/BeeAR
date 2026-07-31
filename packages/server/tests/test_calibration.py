"""Tests for PD calibration wizard (Issue #7)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from bee_ar_server.calibration import (
    compute_calibration, CalibrationInput,
    REFERENCE_PD_MM, REFERENCE_FRAME_WIDTH_MM, REFERENCE_FRAME_HEIGHT_MM
)


def test_proportional_scale_at_reference():
    """At reference PD, scale = 1.0."""
    result = compute_calibration(CalibrationInput(pd_mm=REFERENCE_PD_MM, method="proportional"))
    assert result.scale_factor == 1.0
    assert result.fit_width_mm == REFERENCE_FRAME_WIDTH_MM


def test_proportional_scale_half_pd():
    """Half PD gives scale ~0.5."""
    result = compute_calibration(CalibrationInput(pd_mm=32.0, method="proportional"))
    assert abs(result.scale_factor - 0.5) < 0.01


def test_proportional_scale_double_pd():
    """Double PD gives scale ~2.0."""
    result = compute_calibration(CalibrationInput(pd_mm=128.0, method="proportional"))
    assert abs(result.scale_factor - 2.0) < 0.01


def test_linear_method_reference():
    """Linear method with reference PD gives scale=1."""
    result = compute_calibration(CalibrationInput(pd_mm=REFERENCE_PD_MM, method="linear"))
    assert result.scale_factor == 1.0


def test_linear_method_clamped():
    """Linear method clamps to [0.5, 2.0]."""
    result = compute_calibration(CalibrationInput(pd_mm=200.0, method="linear"))
    assert result.scale_factor == 2.0


def test_pd_validation_rejects_zero():
    """PD=0 should be rejected by Pydantic validation."""
    with pytest.raises(Exception):
        CalibrationInput(pd_mm=0)


def test_pd_validation_rejects_negative():
    """Negative PD should be rejected."""
    with pytest.raises(Exception):
        CalibrationInput(pd_mm=-5.0)


def test_narrow_anchor():
    """PD < 58mm gives narrow anchor."""
    result = compute_calibration(CalibrationInput(pd_mm=50.0))
    assert result.recommended_anchor == "narrow"


def test_standard_anchor():
    """PD between 58-70 gives standard anchor."""
    result = compute_calibration(CalibrationInput(pd_mm=64.0))
    assert result.recommended_anchor == "standard"


def test_wide_anchor():
    """PD > 70mm gives wide anchor."""
    result = compute_calibration(CalibrationInput(pd_mm=75.0))
    assert result.recommended_anchor == "wide"


def test_fit_dimensions_proportional():
    """Fit dimensions scale proportionally."""
    result = compute_calibration(CalibrationInput(pd_mm=32.0, method="proportional"))
    assert result.fit_width_mm == pytest.approx(70.0, rel=0.01)
    assert result.fit_height_mm == pytest.approx(25.0, rel=0.01)
