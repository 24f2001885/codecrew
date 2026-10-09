from app.extensions import db
from app.models.audit_log import AuditLog
from app.services.audit import record_audit


def test_audit_log_recording_and_listing(app, logged_in_client, admin_user):
    with app.app_context():
        # Record sample audit entries
        record_audit("admin", admin_user.id, "coder.created", "coder_user", "target-123", {"note": "created"})
        record_audit("coder", "coder-456", "project.created", "project", "target-789", {"title": "App"})
        db.session.commit()

    resp = logged_in_client.get("/admin/audit-log")
    assert resp.status_code == 200
    assert b"coder.created" in resp.data
    assert b"project.created" in resp.data

    # Filter by action
    filter_resp = logged_in_client.get("/admin/audit-log?action=coder.created")
    assert filter_resp.status_code == 200
    assert b"target-123" in filter_resp.data
    assert b"target-789" not in filter_resp.data


def test_no_audit_log_mutation_routes(app):
    # Enforces that no route exists in the entire URL map to update or delete audit logs
    mutation_endpoints = []
    for rule in app.url_map.iter_rules():
        rule_str = str(rule)
        if "audit" in rule_str and any(verb in rule_str for verb in ["delete", "edit", "update"]):
            mutation_endpoints.append(rule_str)
        if "audit" in rule.endpoint and any(verb in rule.endpoint for verb in ["delete", "edit", "update"]):
            mutation_endpoints.append(rule.endpoint)

    assert len(mutation_endpoints) == 0, f"Found mutable audit endpoints: {mutation_endpoints}"
