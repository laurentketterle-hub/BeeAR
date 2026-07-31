"""Tests for sessions + wishlist API endpoints."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from beear.api import app

client = TestClient(app)


class TestSessionsCreate:
    """POST /api/sessions — create sessions with frames and frame_ids."""

    def test_create_with_frame_ids(self):
        r = client.post(
            "/api/sessions",
            json={"frame_ids": ["aviator_gold", "wayfarer_black"], "note": "test"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "id" in body
        assert body["frame_ids"] == ["aviator_gold", "wayfarer_black"]
        assert body["note"] == "test"
        assert "created_at" in body
        assert "frames" in body
        assert body["frames"] == []

    def test_create_with_frames_metadata(self):
        """POST /api/sessions with frames containing sku, name, type, anchor, offset."""
        frames_payload = [
            {"sku": "WF-001", "name": "Wayfarer Black", "type": "glasses", "anchor": "nose", "offset": [0, 0.05, 0]},
            {"sku": "AG-002", "name": "Aviator Gold", "type": "glasses", "anchor": "nose", "offset": [0, 0.02, 0]},
        ]
        r = client.post(
            "/api/sessions",
            json={
                "frame_ids": ["wayfarer_black", "aviator_gold"],
                "frames": frames_payload,
                "note": "with metadata",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert "id" in body
        assert body["frames"] == frames_payload
        assert body["note"] == "with metadata"
        assert body["frame_ids"] == ["wayfarer_black", "aviator_gold"]

    def test_create_minimal(self):
        """POST /api/sessions with no body fields."""
        r = client.post("/api/sessions", json={})
        assert r.status_code == 200
        body = r.json()
        assert "id" in body
        assert body["frame_ids"] == []
        assert body["frames"] == []
        assert body["wishlist"] == []
        assert body["note"] == ""


class TestSessionsGet:
    """GET /api/sessions and GET /api/sessions/{id}."""

    def test_list_sessions(self):
        r = client.get("/api/sessions")
        assert r.status_code == 200
        body = r.json()
        assert "sessions" in body
        assert isinstance(body["sessions"], list)

    def test_get_session_by_id(self):
        # Create a session first
        r = client.post(
            "/api/sessions",
            json={"frame_ids": ["sport_blue"], "note": "get test"},
        )
        sid = r.json()["id"]

        r = client.get(f"/api/sessions/{sid}")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == sid
        assert body["frame_ids"] == ["sport_blue"]
        assert body["note"] == "get test"

    def test_get_nonexistent_session(self):
        r = client.get("/api/sessions/does-not-exist")
        assert r.status_code == 404


class TestSessionsPatch:
    """PATCH /api/sessions/{id}."""

    def test_patch_note(self):
        r = client.post("/api/sessions", json={"note": "before"})
        sid = r.json()["id"]

        r = client.patch(f"/api/sessions/{sid}", json={"note": "after"})
        assert r.status_code == 200
        assert r.json()["note"] == "after"

    def test_patch_wishlist(self):
        r = client.post("/api/sessions", json={})
        sid = r.json()["id"]

        r = client.patch(f"/api/sessions/{sid}", json={"wishlist": ["aviator_gold"]})
        assert r.status_code == 200
        assert "aviator_gold" in r.json()["wishlist"]

    def test_patch_frame_ids(self):
        r = client.post("/api/sessions", json={"frame_ids": ["sport_blue"]})
        sid = r.json()["id"]

        r = client.patch(
            f"/api/sessions/{sid}",
            json={"frame_ids": ["aviator_gold", "wayfarer_black"]},
        )
        assert r.status_code == 200
        assert r.json()["frame_ids"] == ["aviator_gold", "wayfarer_black"]

    def test_patch_nonexistent(self):
        r = client.patch("/api/sessions/nope", json={"note": "nope"})
        assert r.status_code == 404


class TestWishlist:
    """Wishlist: per-session add + global GET."""

    def test_add_wishlist_to_session(self):
        r = client.post("/api/sessions", json={"note": "wishlist test"})
        sid = r.json()["id"]

        r = client.post(
            f"/api/sessions/{sid}/wishlist",
            json={"frame_id": "sport_blue"},
        )
        assert r.status_code == 200
        assert "sport_blue" in r.json()["wishlist"]

    def test_add_wishlist_nonexistent_session(self):
        r = client.post(
            "/api/sessions/nope/wishlist",
            json={"frame_id": "aviator_gold"},
        )
        assert r.status_code == 404

    def test_add_wishlist_unknown_frame(self):
        r = client.post("/api/sessions", json={})
        sid = r.json()["id"]

        r = client.post(
            f"/api/sessions/{sid}/wishlist",
            json={"frame_id": "no_such_frame"},
        )
        assert r.status_code == 400

    def test_add_wishlist_dedup(self):
        """Adding the same frame_id twice should not duplicate."""
        r = client.post("/api/sessions", json={})
        sid = r.json()["id"]

        client.post(f"/api/sessions/{sid}/wishlist", json={"frame_id": "sport_blue"})
        r = client.post(f"/api/sessions/{sid}/wishlist", json={"frame_id": "sport_blue"})
        assert r.status_code == 200
        assert r.json()["wishlist"].count("sport_blue") == 1

    def test_global_wishlist(self):
        """GET /api/wishlist aggregates items from all sessions."""
        # Create two sessions with wishlist items
        r1 = client.post("/api/sessions", json={})
        sid1 = r1.json()["id"]
        client.post(f"/api/sessions/{sid1}/wishlist", json={"frame_id": "aviator_gold"})
        client.post(f"/api/sessions/{sid1}/wishlist", json={"frame_id": "sport_blue"})

        r2 = client.post("/api/sessions", json={})
        sid2 = r2.json()["id"]
        client.post(f"/api/sessions/{sid2}/wishlist", json={"frame_id": "wayfarer_black"})

        r = client.get("/api/wishlist")
        assert r.status_code == 200
        body = r.json()
        assert "wishlist" in body
        assert "count" in body
        assert body["count"] >= 3

        frame_ids = [item["frame_id"] for item in body["wishlist"]]
        assert "aviator_gold" in frame_ids
        assert "sport_blue" in frame_ids
        assert "wayfarer_black" in frame_ids

    def test_global_wishlist_empty(self):
        """Wishlist endpoint returns proper structure even with no dedicated items."""
        # We can't guarantee empty since in-memory shared across tests,
        # but we can verify the response structure.
        r = client.get("/api/wishlist")
        assert r.status_code == 200
        body = r.json()
        assert "wishlist" in body
        assert "count" in body
        assert isinstance(body["wishlist"], list)
        assert body["count"] == len(body["wishlist"])
