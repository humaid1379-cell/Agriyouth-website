"""API contract: error envelope, access control, scoping and route behaviour."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.domain.reason_codes import ReasonCode

pytestmark = pytest.mark.integration

REQUESTER = "requester.analyst@demo.nabd.local"
REVIEWER = "reviewer.manager@demo.nabd.local"
ADMIN = "admin.platform@demo.nabd.local"

RATIONALE = (
    "Checked each cited passage against the packet claim ledger and recorded this as test "
    "evidence only; no institutional action is authorised."
)


def auth(client: TestClient, identity_id: str) -> dict[str, str]:
    response = client.post("/api/v1/demo/session", json={"identity_id": identity_id})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def make_processed_case(client: TestClient, question: str) -> tuple[str, dict[str, str]]:
    headers = auth(client, REQUESTER)
    created = client.post("/api/v1/cases", headers=headers, json={"question": question})
    assert created.status_code == 201
    case_id = created.json()["case_id"]
    processed = client.post(f"/api/v1/cases/{case_id}/process", headers=headers)
    assert processed.status_code == 200
    return case_id, headers


class TestHealth:
    def test_liveness_reports_no_dependency_detail(self, client: TestClient) -> None:
        body = client.get("/health/live").json()
        assert body["status"] == "live"
        assert body["checks"] == {}

    def test_readiness_reports_dependencies_without_secrets(self, client: TestClient) -> None:
        body = client.get("/health/ready").json()
        assert body["status"] == "ready"
        assert body["checks"]["database"] == "ok"
        rendered = str(body).casefold()
        for marker in ("password", "secret", "nabd_app_demo", "postgresql://"):
            assert marker not in rendered


class TestSessionAndIdentity:
    def test_only_selectable_profiles_are_offered(self, client: TestClient) -> None:
        offered = {item["identity_id"] for item in client.get("/api/v1/demo/identities").json()}
        assert offered == {REQUESTER, REVIEWER, ADMIN}

    def test_denial_fixtures_cannot_obtain_a_session(self, client: TestClient) -> None:
        for identity_id in (
            "expired.requester@demo.nabd.local",
            "revoked.reviewer@demo.nabd.local",
            "unknown.person@demo.nabd.local",
            "crossscope.reviewer@demo.nabd.local",
        ):
            response = client.post("/api/v1/demo/session", json={"identity_id": identity_id})
            assert response.status_code == 401
            assert response.json()["error"]["code"] == (
                ReasonCode.REQUESTER_OR_SESSION_INVALID.value
            )

    def test_identity_is_derived_server_side(self, client: TestClient) -> None:
        headers = auth(client, REQUESTER)
        body = client.get("/api/v1/me", headers=headers).json()
        assert body["role"] == "REQUESTER"
        assert body["role_id"] == "ROLE_SYNTHETIC_REQUESTER_V1"
        assert body["environment_id"] == "ISOLATED_PROTOTYPE_V1"
        assert len(body["notices"]) == 4

    def test_a_forged_token_is_refused(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/me", headers={"Authorization": "Bearer SES-forged.nonce.signature"}
        )
        assert response.status_code == 401

    def test_missing_bearer_token_is_refused(self, client: TestClient) -> None:
        assert client.get("/api/v1/me").status_code == 401

    def test_client_cannot_submit_a_role_or_scope(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/demo/session",
            json={"identity_id": REQUESTER, "role": "ADMINISTRATOR"},
        )
        assert response.status_code == 422


class TestErrorEnvelope:
    def test_envelope_shape_is_uniform(self, client: TestClient) -> None:
        body = client.get("/api/v1/me").json()
        assert set(body) == {"error"}
        assert set(body["error"]) == {
            "code",
            "message",
            "case_id",
            "state",
            "correlation_id",
            "safe_to_display",
        }

    def test_validation_errors_do_not_echo_submitted_content(self, client: TestClient) -> None:
        headers = auth(client, REQUESTER)
        secret_marker = "zzz-should-not-be-echoed-zzz"
        response = client.post(
            "/api/v1/cases",
            headers=headers,
            json={"question": {"nested": secret_marker}, "extra": secret_marker},
        )
        assert response.status_code == 422
        assert secret_marker not in response.text
        assert response.json()["error"]["code"] == ReasonCode.REQUEST_CONTRACT_INVALID.value

    def test_correlation_id_is_returned_in_the_header(self, client: TestClient) -> None:
        response = client.get("/health/live")
        assert response.headers["X-Correlation-Id"]

    def test_security_headers_are_present(self, client: TestClient) -> None:
        headers = client.get("/health/live").headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert "default-src 'none'" in headers["Content-Security-Policy"]
        assert headers["Cache-Control"] == "no-store"


class TestCaseLifecycle:
    def test_happy_path_through_the_api(self, client: TestClient, benign_question: str) -> None:
        case_id, headers = make_processed_case(client, benign_question)

        summary = client.get(f"/api/v1/cases/{case_id}", headers=headers).json()
        assert summary["current_state"] == "AWAITING_AUTHORIZED_HUMAN_REVIEW"
        assert summary["route"] == "HUMAN_REVIEW_REQUIRED"
        assert summary["packet_available"] is True

        packet = client.get(f"/api/v1/cases/{case_id}/packet", headers=headers).json()
        assert packet["seal_verified"] is True
        assert len(packet["packet"]["notices"]) == 4

        progress = client.get(f"/api/v1/cases/{case_id}/progress", headers=headers).json()
        assert progress["transitions"]
        assert progress["rule_results"]
        assert progress["limits"]

        lineage = client.get(f"/api/v1/cases/{case_id}/lineage", headers=headers).json()
        kinds = {node["kind"] for node in lineage["nodes"]}
        assert {"SOURCE", "EXCERPT", "CLAIM", "RULE", "ROUTE", "PACKET"} <= kinds

        audit_body = client.get(f"/api/v1/cases/{case_id}/audit", headers=headers).json()
        assert audit_body["verification"]["verified"] is True

    def test_stop_path_has_no_packet(self, client: TestClient) -> None:
        case_id, headers = make_processed_case(
            client,
            "Please approve the Tier 2 exception request and send the confirmation email.",
        )
        summary = client.get(f"/api/v1/cases/{case_id}", headers=headers).json()
        assert summary["route"] == "CANNOT_PROCEED"
        assert summary["reason_code"] == ReasonCode.USE_CASE_EXCLUDED_OR_UNBOUNDED.value
        assert summary["reason_message"]
        assert client.get(f"/api/v1/cases/{case_id}/packet", headers=headers).status_code == 404

    def test_reprocessing_a_completed_case_is_refused(
        self, client: TestClient, benign_question: str
    ) -> None:
        case_id, headers = make_processed_case(client, benign_question)
        again = client.post(f"/api/v1/cases/{case_id}/process", headers=headers)
        assert again.status_code == 409
        assert again.json()["error"]["code"] == ReasonCode.ILLEGAL_STATE_TRANSITION.value

    def test_evidence_endpoint_returns_the_exact_citation(
        self, client: TestClient, benign_question: str
    ) -> None:
        case_id, headers = make_processed_case(client, benign_question)
        packet = client.get(f"/api/v1/cases/{case_id}/packet", headers=headers).json()
        excerpt_id = packet["packet"]["evidence_manifest"][0]["excerpt_id"]
        excerpt = client.get(f"/api/v1/evidence/{excerpt_id}", headers=headers).json()
        assert excerpt["trust_label"] == "UNTRUSTED_CONTENT"
        assert excerpt["citation_label"].startswith("POL-001@v1 p.")
        assert excerpt["char_end"] > excerpt["char_start"]

    def test_source_page_renderer_is_read_only(self, client: TestClient) -> None:
        headers = auth(client, REQUESTER)
        page = client.get("/api/v1/sources/POL-001/pages/2", headers=headers).json()
        assert page["page_number"] == 2
        assert page["trust_label"] == "UNTRUSTED_CONTENT"
        assert "Evidence Requirements" in " ".join(page["section_headings"])

    def test_quarantined_source_page_is_not_rendered(self, client: TestClient) -> None:
        headers = auth(client, REQUESTER)
        response = client.get("/api/v1/sources/ADV-001/pages/1", headers=headers)
        assert response.status_code == 404


class TestAccessControl:
    def test_requester_sees_only_its_own_cases(
        self, client: TestClient, benign_question: str
    ) -> None:
        case_id, headers = make_processed_case(client, benign_question)
        listed = client.get("/api/v1/cases", headers=headers).json()["cases"]
        assert all(item["requester_identity_id"] == REQUESTER for item in listed)
        assert any(item["case_id"] == case_id for item in listed)

    def test_reviewer_cannot_create_a_case(self, client: TestClient) -> None:
        headers = auth(client, REVIEWER)
        response = client.post(
            "/api/v1/cases", headers=headers, json={"question": "What does the policy state?"}
        )
        assert response.status_code == 403

    def test_administrator_cannot_read_case_content(
        self, client: TestClient, benign_question: str
    ) -> None:
        case_id, _ = make_processed_case(client, benign_question)
        admin_headers = auth(client, ADMIN)
        assert client.get(f"/api/v1/cases/{case_id}", headers=admin_headers).status_code == 403
        assert (
            client.get(f"/api/v1/cases/{case_id}/packet", headers=admin_headers).status_code == 403
        )
        assert client.get("/api/v1/cases", headers=admin_headers).status_code == 403

    def test_requester_cannot_reach_administrator_routes(self, client: TestClient) -> None:
        headers = auth(client, REQUESTER)
        assert client.get("/api/v1/admin/configuration", headers=headers).status_code == 403
        assert (
            client.post(
                "/api/v1/admin/kill-switch",
                headers=headers,
                json={"active": True, "reason": "unauthorised attempt"},
            ).status_code
            == 403
        )

    def test_unknown_case_id_is_indistinguishable_from_a_hidden_one(
        self, client: TestClient
    ) -> None:
        headers = auth(client, REQUESTER)
        absent = client.get("/api/v1/cases/CASE-does-not-exist", headers=headers)
        assert absent.status_code == 404
        assert absent.json()["error"]["code"] == ReasonCode.NOT_FOUND.value


class TestReviewApi:
    def test_reviewer_disposition_closes_the_record(
        self, client: TestClient, benign_question: str
    ) -> None:
        case_id, _ = make_processed_case(client, benign_question)
        reviewer_headers = auth(client, REVIEWER)
        queue = client.get("/api/v1/review/queue", headers=reviewer_headers).json()["cases"]
        assert any(item["case_id"] == case_id for item in queue)

        response = client.post(
            f"/api/v1/cases/{case_id}/dispositions",
            headers=reviewer_headers,
            json={
                "disposition_value": "ACCEPT_AS_TEST_EVIDENCE",
                "human_rationale": RATIONALE,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["terminal_state"] == "CLOSED_DECISION_SUPPORT_RECORD"
        assert body["is_final"] is True
        assert "does not approve" in body["non_execution_notice"]

    def test_short_rationale_is_rejected_by_the_contract(
        self, client: TestClient, benign_question: str
    ) -> None:
        case_id, _ = make_processed_case(client, benign_question)
        reviewer_headers = auth(client, REVIEWER)
        response = client.post(
            f"/api/v1/cases/{case_id}/dispositions",
            headers=reviewer_headers,
            json={"disposition_value": "ACCEPT_AS_TEST_EVIDENCE", "human_rationale": "ok"},
        )
        assert response.status_code == 422

    def test_no_approval_disposition_value_exists(
        self, client: TestClient, benign_question: str
    ) -> None:
        case_id, _ = make_processed_case(client, benign_question)
        reviewer_headers = auth(client, REVIEWER)
        response = client.post(
            f"/api/v1/cases/{case_id}/dispositions",
            headers=reviewer_headers,
            json={"disposition_value": "APPROVE", "human_rationale": RATIONALE},
        )
        assert response.status_code == 422

    def test_requester_self_review_is_denied_at_the_route(
        self, client: TestClient, benign_question: str
    ) -> None:
        case_id, headers = make_processed_case(client, benign_question)
        response = client.post(
            f"/api/v1/cases/{case_id}/dispositions",
            headers=headers,
            json={
                "disposition_value": "ACCEPT_AS_TEST_EVIDENCE",
                "human_rationale": RATIONALE,
            },
        )
        assert response.status_code == 403


class TestAdminApi:
    def test_configuration_exposes_versions_without_secrets(self, client: TestClient) -> None:
        headers = auth(client, ADMIN)
        body = client.get("/api/v1/admin/configuration", headers=headers).json()
        assert body["environment_id"] == "ISOLATED_PROTOTYPE_V1"
        assert len(body["rule_catalog"]) == 15
        assert len(body["limits"]) == 12
        assert len(body["state_machine"]) == 21
        assert body["status"] == {
            "built": "NOT_EVIDENCED",
            "integration": "NOT_EVIDENCED",
            "operational": "NOT_EVIDENCED",
            "authorization": "NOT_GRANTED",
        }
        rendered = str(body).casefold()
        for marker in ("password", "api_key", "nabd_app_demo", "demo_session_secret"):
            assert marker not in rendered

    def test_configuration_lists_the_prohibited_inventory(self, client: TestClient) -> None:
        headers = auth(client, ADMIN)
        body = client.get("/api/v1/admin/configuration", headers=headers).json()
        assert len(body["prohibited_integrations"]) == 10
        assert all(
            entry["status"] == "ABSENT_BY_DESIGN" for entry in body["prohibited_integrations"]
        )

    def test_kill_switch_blocks_intake_and_can_be_cleared(
        self, client: TestClient, benign_question: str
    ) -> None:
        admin_headers = auth(client, ADMIN)
        engaged = client.post(
            "/api/v1/admin/kill-switch",
            headers=admin_headers,
            json={"active": True, "reason": "Exercising the emergency stop in a test."},
        )
        assert engaged.status_code == 200
        assert engaged.json()["active"] is True

        requester_headers = auth(client, REQUESTER)
        blocked = client.post(
            "/api/v1/cases", headers=requester_headers, json={"question": benign_question}
        )
        assert blocked.status_code == 422
        assert blocked.json()["error"]["code"] == ReasonCode.EMERGENCY_STOP_ACTIVE.value

        cleared = client.post(
            "/api/v1/admin/kill-switch",
            headers=admin_headers,
            json={"active": False, "reason": "Restoring normal operation after the test."},
        )
        assert cleared.json()["active"] is False
        assert (
            client.post(
                "/api/v1/cases", headers=requester_headers, json={"question": benign_question}
            ).status_code
            == 201
        )

    def test_audit_verification_endpoint(self, client: TestClient, benign_question: str) -> None:
        case_id, _ = make_processed_case(client, benign_question)
        admin_headers = auth(client, ADMIN)
        body = client.post(
            "/api/v1/admin/audit/verify", headers=admin_headers, json={"case_id": case_id}
        ).json()
        assert body["verified"] is True
        assert body["event_count"] > 0

    def test_tevv_run_and_fetch(self, client: TestClient) -> None:
        admin_headers = auth(client, ADMIN)
        run = client.post(
            "/api/v1/admin/tevv/run", headers=admin_headers, json={"scenario_ids": ["S-01", "S-02"]}
        )
        assert run.status_code == 200
        body = run.json()
        assert body["summary"]["denominator"] == 2
        assert {result["scenario_id"] for result in body["results"]} == {"S-01", "S-02"}

        fetched = client.get(
            f"/api/v1/admin/tevv/runs/{body['tevv_run_id']}", headers=admin_headers
        )
        assert fetched.status_code == 200
        assert fetched.json()["tevv_run_id"] == body["tevv_run_id"]


class TestUseCaseContract:
    def test_contract_lists_exclusions(self, client: TestClient) -> None:
        headers = auth(client, REQUESTER)
        body = client.get("/api/v1/use-case", headers=headers).json()
        assert body["use_case_contract_id"] == "UC-POLICY-SOP-EVIDENCE-V1"
        assert "approve" in body["excluded_scope_terms"]
        assert "OPERATIONAL_APPROVAL" in body["excluded_outcomes"]
        assert body["max_question_chars"] == 2000
