"""Tests for sessions + wishlist API (in-memory)."""
import pytest
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from beear.api import app
from beear import sessions as sess_mod
client = TestClient(app)
