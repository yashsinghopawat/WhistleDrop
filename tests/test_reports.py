"""Public side: submitting and tracking reports without an account."""


def track(client, case_code):
    return client.post("/reports/track", json={"case_code": case_code})


def test_submit_report_without_account(client):
    response = client.post("/reports", json={
        "category": "CORRUPTION",
        "description": "A manager is taking money for approving vendor contracts.",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["case_code"].startswith("WD-")
    assert body["status"] == "SUBMITTED"


def test_case_codes_are_unique_and_long(client):
    codes = set()
    for _ in range(5):
        response = client.post("/reports", json={
            "category": "OTHER",
            "description": "Just another report for the test.",
        })
        codes.add(response.json()["case_code"])
    assert len(codes) == 5
    assert all(len(code) == 19 for code in codes)


def test_submit_invalid_category(client):
    response = client.post("/reports", json={"category": "FOOD", "description": "long enough text here"})
    assert response.status_code == 422


def test_submit_missing_description(client):
    response = client.post("/reports", json={"category": "SECURITY"})
    assert response.status_code == 422


def test_submit_short_description(client):
    response = client.post("/reports", json={"category": "SECURITY", "description": "short"})
    assert response.status_code == 422


def test_submit_invalid_evidence_url(client):
    response = client.post("/reports", json={
        "category": "SECURITY",
        "description": "This description is long enough.",
        "evidence_url": "not a url",
    })
    assert response.status_code == 422


def test_track_report(client, sample_report):
    response = track(client, sample_report["case_code"])
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUBMITTED"
    assert body["category"] == "SECURITY"
    assert body["updates"][0]["message"] == "Report received"


def test_track_is_case_insensitive_for_code(client, sample_report):
    response = track(client, sample_report["case_code"].lower())
    assert response.status_code == 200


def test_track_invalid_case_code(client):
    response = track(client, "WD-DOESNOTEXIST000")
    assert response.status_code == 404


def test_tracking_response_has_no_reporter_info(client, sample_report):
    body = track(client, sample_report["case_code"]).json()
    for forbidden in ("user", "user_id", "ip", "reporter", "case_code_hash", "id"):
        assert forbidden not in body


def test_case_code_is_not_stored_in_plain_text(client, sample_report):
    from tests.conftest import TestSession
    from app.models.report import Report

    db = TestSession()
    try:
        report = db.query(Report).first()
        assert report.case_code_hash != sample_report["case_code"]
        assert sample_report["case_code"] not in report.case_code_hash
    finally:
        db.close()


def test_track_without_case_code(client):
    response = client.post("/reports/track", json={})
    assert response.status_code == 422
