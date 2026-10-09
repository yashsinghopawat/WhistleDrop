"""Moderator side: needs a login token."""


def test_moderator_routes_need_token(client):
    assert client.get("/moderation/reports").status_code == 401
    assert client.get("/moderation/reports/1").status_code == 401
    assert client.get("/moderation/reports/stats").status_code == 401
    assert client.patch("/moderation/reports/1/status", json={"status": "UNDER_REVIEW"}).status_code == 401
    assert client.post("/moderation/reports/1/updates", json={"message": "hi"}).status_code == 401


def test_list_reports(client, moderator_headers, sample_report):
    response = client.get("/moderation/reports", headers=moderator_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_moderator_response_has_no_reporter_info(client, moderator_headers, sample_report):
    body = client.get("/moderation/reports/1", headers=moderator_headers).json()
    for forbidden in ("user", "user_id", "ip", "reporter", "case_code", "case_code_hash"):
        assert forbidden not in body


def test_filter_by_category_and_status(client, moderator_headers, sample_report):
    client.post("/reports", json={"category": "HARASSMENT", "description": "Someone is bullying staff."})

    by_category = client.get("/moderation/reports?category=HARASSMENT", headers=moderator_headers)
    assert len(by_category.json()) == 1
    assert by_category.json()[0]["category"] == "HARASSMENT"

    by_status = client.get("/moderation/reports?status=RESOLVED", headers=moderator_headers)
    assert by_status.json() == []


def test_filter_with_invalid_value(client, moderator_headers):
    response = client.get("/moderation/reports?status=WRONG", headers=moderator_headers)
    assert response.status_code == 422


def test_search_reports(client, moderator_headers, sample_report):
    found = client.get("/moderation/reports?search=server room", headers=moderator_headers)
    assert len(found.json()) == 1
    missing = client.get("/moderation/reports?search=banana", headers=moderator_headers)
    assert missing.json() == []


def test_get_missing_report(client, moderator_headers):
    response = client.get("/moderation/reports/999", headers=moderator_headers)
    assert response.status_code == 404


def test_full_status_flow_visible_to_reporter(client, moderator_headers, sample_report):
    code = sample_report["case_code"]

    r1 = client.patch("/moderation/reports/1/status", headers=moderator_headers,
                      json={"status": "UNDER_REVIEW", "message": "We are looking into it"})
    assert r1.status_code == 200
    assert r1.json()["status"] == "UNDER_REVIEW"

    r2 = client.patch("/moderation/reports/1/status", headers=moderator_headers,
                      json={"status": "RESOLVED", "message": "Door lock fixed"})
    assert r2.status_code == 200

    tracked = client.post("/reports/track", json={"case_code": code}).json()
    assert tracked["status"] == "RESOLVED"
    messages = [u["message"] for u in tracked["updates"]]
    assert messages == ["Report received", "We are looking into it", "Door lock fixed"]


def test_cannot_skip_status(client, moderator_headers, sample_report):
    response = client.patch("/moderation/reports/1/status", headers=moderator_headers,
                            json={"status": "RESOLVED"})
    assert response.status_code == 400


def test_closed_case_cannot_change(client, moderator_headers, sample_report):
    client.patch("/moderation/reports/1/status", headers=moderator_headers, json={"status": "UNDER_REVIEW"})
    client.patch("/moderation/reports/1/status", headers=moderator_headers, json={"status": "DISMISSED"})

    again = client.patch("/moderation/reports/1/status", headers=moderator_headers,
                         json={"status": "UNDER_REVIEW"})
    assert again.status_code == 409

    update = client.post("/moderation/reports/1/updates", headers=moderator_headers,
                         json={"message": "too late"})
    assert update.status_code == 409


def test_invalid_status_value(client, moderator_headers, sample_report):
    response = client.patch("/moderation/reports/1/status", headers=moderator_headers,
                            json={"status": "FINISHED"})
    assert response.status_code == 422


def test_add_update_keeps_status(client, moderator_headers, sample_report):
    response = client.post("/moderation/reports/1/updates", headers=moderator_headers,
                           json={"message": "Can you tell us more?"})
    assert response.status_code == 201
    assert response.json()["status"] == "SUBMITTED"

    tracked = client.post("/reports/track", json={"case_code": sample_report["case_code"]}).json()
    assert tracked["updates"][-1]["message"] == "Can you tell us more?"


def test_add_update_missing_message(client, moderator_headers, sample_report):
    response = client.post("/moderation/reports/1/updates", headers=moderator_headers, json={})
    assert response.status_code == 422


def test_status_change_on_missing_report(client, moderator_headers):
    response = client.patch("/moderation/reports/999/status", headers=moderator_headers,
                            json={"status": "UNDER_REVIEW"})
    assert response.status_code == 404


def test_stats(client, moderator_headers, sample_report):
    body = client.get("/moderation/reports/stats", headers=moderator_headers).json()
    assert body["total"] == 1
    assert body["by_status"] == {"SUBMITTED": 1}
    assert body["by_category"] == {"SECURITY": 1}
