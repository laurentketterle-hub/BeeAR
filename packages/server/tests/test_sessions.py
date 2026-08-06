"""Tests for sessions + wishlist API (in-memory)."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from beear.api import app

client = TestClient(app)
