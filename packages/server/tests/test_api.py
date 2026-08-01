import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from beear.api import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["frames"] >= 72
    assert "pd_calibration" in body["features"]
    assert "person_3d" in body["features"]
    assert "studio3d" in body["features"]
    assert body.get("person_models", 0) >= 1
    assert body.get("glb_frames", 0) >= 8


def test_catalog_and_fit():
    r = client.get("/api/catalog")
    assert r.status_code == 200
    payload = r.json()
    frames = payload["frames"]
    assert frames
    assert payload.get("person_models")
    fid = frames[0]["id"]
    r = client.get(f"/api/catalog/{fid}")
    assert r.status_code == 200
    r = client.post(
        "/api/tryon/fit",
        json={"frame_id": fid, "pupil_distance_px": 110, "face_width_px": 200, "pd_mm": 66},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["pd_mm"] == 66


def test_catalog_meta_and_studio3d_route():
    r = client.get("/api/catalog/meta")
    assert r.status_code == 200
    body = r.json()
    assert body["person_count"] >= 1
    assert body["studio_url"] == "/studio3d.html"
    r = client.get("/studio3d.html")
    assert r.status_code == 200
    assert b"studio3d" in r.content.lower() or b"3D" in r.content


def test_landmarks():
    r = client.post(
        "/api/tryon/landmarks",
        json={"left_eye": [0.35, 0.4], "right_eye": [0.65, 0.4], "canvas_w": 640, "canvas_h": 480},
    )
    assert r.status_code == 200
    assert "mid" in r.json()


def test_compare_and_sessions():
    r = client.post(
        "/api/tryon/compare",
        json={"frame_a": "aviator_gold", "frame_b": "wayfarer_black", "pd_mm": 64},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True

    r = client.post("/api/sessions", json={"frame_ids": ["aviator_gold"], "note": "test"})
    assert r.status_code == 200
    sid = r.json()["id"]
    r = client.post(f"/api/sessions/{sid}/wishlist", json={"frame_id": "sport_blue"})
    assert r.status_code == 200
    assert "sport_blue" in r.json()["wishlist"]
    r = client.get(f"/api/sessions/{sid}")
    assert r.status_code == 200


class TestSessionsFull:
    """Comprehensive session CRUD + wishlist tests."""

    def test_create_session_defaults(self):
        r = client.post("/api/sessions", json={})
        assert r.status_code == 200
        body = r.json()
        assert "id" in body
        assert body["frame_ids"] == []
        assert body["wishlist"] == []
        assert body["note"] == ""

    def test_create_session_with_data(self):
        r = client.post("/api/sessions", json={
            "frame_ids": ["aviator_gold", "wayfarer_black"],
            "note": "my try-on session"
        })
        assert r.status_code == 200
        body = r.json()
        assert body["frame_ids"] == ["aviator_gold", "wayfarer_black"]
        assert body["note"] == "my try-on session"

    def test_get_session_not_found(self):
        r = client.get("/api/sessions/nonexistent")
        assert r.status_code == 404

    def test_patch_session_update_note(self):
        r = client.post("/api/sessions", json={"note": "original"})
        sid = r.json()["id"]
        r = client.patch(f"/api/sessions/{sid}", json={"note": "updated"})
        assert r.status_code == 200
        assert r.json()["note"] == "updated"

    def test_patch_session_update_wishlist(self):
        r = client.post("/api/sessions", json={})
        sid = r.json()["id"]
        r = client.patch(f"/api/sessions/{sid}", json={"wishlist": ["sport_blue", "aviator_gold"]})
        assert r.status_code == 200
        assert set(r.json()["wishlist"]) == {"sport_blue", "aviator_gold"}

    def test_patch_session_dedup_wishlist(self):
        r = client.post("/api/sessions", json={})
        sid = r.json()["id"]
        r = client.patch(f"/api/sessions/{sid}", json={"wishlist": ["sport_blue", "sport_blue"]})
        assert r.status_code == 200
        assert r.json()["wishlist"] == ["sport_blue"]

    def test_patch_session_not_found(self):
        r = client.patch("/api/sessions/nonexistent", json={"note": "x"})
        assert r.status_code == 404

    def test_wishlist_add_unknown_frame(self):
        r = client.post("/api/sessions", json={})
        sid = r.json()["id"]
        r = client.post(f"/api/sessions/{sid}/wishlist", json={"frame_id": "no_such_frame"})
        assert r.status_code == 400

    def test_wishlist_add_no_duplicate(self):
        r = client.post("/api/sessions", json={})
        sid = r.json()["id"]
        client.post(f"/api/sessions/{sid}/wishlist", json={"frame_id": "sport_blue"})
        r = client.post(f"/api/sessions/{sid}/wishlist", json={"frame_id": "sport_blue"})
        assert r.status_code == 200
        assert r.json()["wishlist"].count("sport_blue") == 1

    def test_wishlist_remove_existing(self):
        r = client.post("/api/sessions", json={})
        sid = r.json()["id"]
        client.post(f"/api/sessions/{sid}/wishlist", json={"frame_id": "sport_blue"})
        client.post(f"/api/sessions/{sid}/wishlist", json={"frame_id": "aviator_gold"})
        r = client.request("DELETE", f"/api/sessions/{sid}/wishlist", json={"frame_id": "sport_blue"})
        assert r.status_code == 200
        assert "sport_blue" not in r.json()["wishlist"]
        assert "aviator_gold" in r.json()["wishlist"]

    def test_wishlist_remove_nonexistent_frame(self):
        r = client.post("/api/sessions", json={})
        sid = r.json()["id"]
        r = client.request("DELETE", f"/api/sessions/{sid}/wishlist", json={"frame_id": "no_such"})
        assert r.status_code == 200

    def test_wishlist_remove_session_not_found(self):
        r = client.request("DELETE", "/api/sessions/nonexistent/wishlist", json={"frame_id": "sport_blue"})
        assert r.status_code == 404

    def test_delete_session(self):
        r = client.post("/api/sessions", json={"note": "to-delete"})
        sid = r.json()["id"]
        r = client.delete(f"/api/sessions/{sid}")
        assert r.status_code == 200
        assert r.json()["deleted"] is True
        assert r.json()["id"] == sid
        # Verify gone
        r = client.get(f"/api/sessions/{sid}")
        assert r.status_code == 404

    def test_delete_session_not_found(self):
        r = client.delete("/api/sessions/nonexistent")
        assert r.status_code == 404

    def test_list_sessions_empty(self):
        """Sessions are in-memory and shared; just verify structure."""
        r = client.get("/api/sessions")
        assert r.status_code == 200
        body = r.json()
        assert "sessions" in body
        assert isinstance(body["sessions"], list)

    def test_list_sessions_limit(self):
        r = client.get("/api/sessions?limit=3")
        assert r.status_code == 200
        assert len(r.json()["sessions"]) <= 3

    def test_session_has_timestamps(self):
        r = client.post("/api/sessions", json={})
        body = r.json()
        assert "created_at" in body
        assert "updated_at" in body

    def test_updated_at_changes_on_patch(self):
        r = client.post("/api/sessions", json={})
        sid = r.json()["id"]
        old_ts = r.json()["updated_at"]
        r = client.patch(f"/api/sessions/{sid}", json={"note": "bumped"})
        new_ts = r.json()["updated_at"]
        assert new_ts > old_ts


class TestNewCatalogFrames:
    """Verify the 8 new frame SKUs from cycle 17."""

    NEW_FRAME_IDS = [
        "pantos_crystal",
        "oversized_square_tortoise",
        "cat_eye_tortoise_shell",
        "wayfarer_crystal_blush",
        "round_sunset_gradient",
        "aviator_silver_mirror",
        "rectangle_two_tone_blue",
        "oval_pearl_white",
    ]

    def test_new_frames_exist_in_catalog(self):
        r = client.get("/api/catalog")
        frames = r.json()["frames"]
        frame_ids = {f["id"] for f in frames}
        for fid in self.NEW_FRAME_IDS:
            assert fid in frame_ids, f"Missing new frame: {fid}"

    def test_new_frames_have_required_fields(self):
        r = client.get("/api/catalog")
        frames = {f["id"]: f for f in r.json()["frames"]}
        for fid in self.NEW_FRAME_IDS:
            f = frames[fid]
            assert f["name"], f"{fid} missing name"
            assert f["brand"], f"{fid} missing brand"
            assert f["category"], f"{fid} missing category"
            assert f["style"], f"{fid} missing style"
            assert isinstance(f["price_cents"], int) and f["price_cents"] > 0
            assert isinstance(f["fit"]["width_mm"], (int, float))

    def test_new_frames_individually_accessible(self):
        for fid in self.NEW_FRAME_IDS:
            r = client.get(f"/api/catalog/{fid}")
            assert r.status_code == 200, f"Frame {fid} not reachable via API"
            assert r.json()["id"] == fid

    def test_total_frame_count_increased(self):
        r = client.get("/api/catalog")
        frames = r.json()["frames"]
        assert len(frames) >= 80, f"Expected >=80 frames, got {len(frames)}"
