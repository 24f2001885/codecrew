import pytest
from datetime import datetime, timezone
from app.extensions import db
from app.models.group import Group
from app.models.member import Member
from app.models.coder_user import CoderUser
from app.models.project_request import ProjectRequest
from app.models.project_milestone import ProjectMilestone
from app.models.project_payment import ProjectPayment
from app.models.app_notification import AppNotification


def test_client_deposit_escrow(app, client):
    with app.app_context():
        group = Group(name="Escrow Devs", slug="escrow-devs")
        db.session.add(group)
        db.session.flush()

        member = Member(name="Alice Coder", group_id=group.id, role="Lead Architect")
        db.session.add(member)
        db.session.flush()

        coder = CoderUser(
            member_id=member.id,
            username="alicecoder",
            email="alice@example.com",
            status="active",
        )
        coder.set_password("AlicePass1234!")
        db.session.add(coder)

        req = ProjectRequest(
            name="Bob Client",
            email="bob@example.com",
            company="Bob Enterprises",
            project_type="fullstack",
            description="Build platform with escrow.",
            status="assigned",
            assigned_group_id=group.id,
        )
        db.session.add(req)
        db.session.flush()

        ms = ProjectMilestone(
            project_request_id=req.id,
            created_by_coder_id=coder.id,
            title="Sprint 1: Core Architecture",
            status="in_progress",
        )
        db.session.add(ms)
        db.session.commit()

        req_id = req.id
        ms_id = ms.id
        group_id = group.id
        coder_id = coder.id

    # Post escrow deposit
    resp = client.post(
        f"/request/{req_id}/hub/deposit",
        data={
            "amount": "3500.00",
            "milestone_id": ms_id,
            "title": "Sprint 1 Funding",
            "payer_name": "Bob Client",
            "payer_email": "bob@example.com",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"securely deposited into escrow" in resp.data

    with app.app_context():
        # Verify payment record
        payment = ProjectPayment.query.filter_by(project_request_id=req_id).first()
        assert payment is not None
        assert payment.amount == 3500.0
        assert payment.status == "held_in_escrow"
        assert payment.group_id == group_id
        assert payment.transaction_reference.startswith("ESC-")

        # Verify milestone updated
        m = db.session.get(ProjectMilestone, ms_id)
        assert m.escrow_amount == 3500.0
        assert m.escrow_status == "funded"

        # Verify group escrow counters
        g = db.session.get(Group, group_id)
        assert g.current_escrow_holding == 3500.0
        assert g.total_lifetime_earnings == 0.0

        # Verify notification dispatched to coder
        notif = AppNotification.query.filter_by(
            recipient_type="coder",
            recipient_id=str(coder_id),
        ).first()
        assert notif is not None
        assert "$3,500.00 Escrow Funded" in notif.title


def test_client_release_escrow_payment(app, client):
    with app.app_context():
        group = Group(name="Release Squad", slug="release-squad")
        db.session.add(group)
        db.session.flush()

        member = Member(name="Sam Coder", group_id=group.id, role="Lead")
        db.session.add(member)
        db.session.flush()

        coder = CoderUser(
            member_id=member.id,
            username="samcoder",
            email="sam@example.com",
            status="active",
        )
        coder.set_password("SamPass1234!")
        db.session.add(coder)

        req = ProjectRequest(
            name="Diana Client",
            email="diana@example.com",
            project_type="api",
            description="API backend.",
            status="assigned",
            assigned_group_id=group.id,
        )
        db.session.add(req)
        db.session.flush()

        ms = ProjectMilestone(
            project_request_id=req.id,
            created_by_coder_id=coder.id,
            title="Sprint 1 API Delivery",
            status="submitted",
            escrow_amount=5000.0,
            escrow_status="funded",
        )
        db.session.add(ms)
        db.session.flush()

        payment = ProjectPayment(
            project_request_id=req.id,
            group_id=group.id,
            milestone_id=ms.id,
            title="Sprint 1 Escrow",
            amount=5000.0,
            status="held_in_escrow",
            transaction_reference="ESC-TEST-REF-001",
            payer_name="Diana Client",
            payer_email="diana@example.com",
        )
        db.session.add(payment)
        db.session.commit()

        req_id = req.id
        ms_id = ms.id
        group_id = group.id
        coder_id = coder.id

    # Release milestone payment
    resp = client.post(
        f"/request/{req_id}/hub/milestone/{ms_id}/release-payment",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"successfully released from escrow" in resp.data

    with app.app_context():
        p = ProjectPayment.query.filter_by(transaction_reference="ESC-TEST-REF-001").first()
        assert p.status == "released"
        assert p.released_at is not None

        m = db.session.get(ProjectMilestone, ms_id)
        assert m.escrow_status == "released"

        g = db.session.get(Group, group_id)
        assert g.total_lifetime_earnings == 5000.0
        assert g.current_escrow_holding == 0.0

        notif = AppNotification.query.filter_by(
            recipient_type="coder",
            recipient_id=str(coder_id),
        ).first()
        assert notif is not None
        assert "$5,000.00 Payout Released" in notif.title


def test_deposit_validation(app, client):
    with app.app_context():
        group = Group(name="Val Squad", slug="val-squad")
        db.session.add(group)
        db.session.flush()

        req = ProjectRequest(
            name="Test User",
            email="test@example.com",
            project_type="web",
            description="Validation test.",
            status="assigned",
            assigned_group_id=group.id,
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    # Negative amount
    resp = client.post(
        f"/request/{req_id}/hub/deposit",
        data={"amount": "-100"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Deposit amount must be greater than $0" in resp.data


def test_payment_receipt_view(app, client):
    with app.app_context():
        group = Group(name="Receipt Squad", slug="receipt-squad")
        db.session.add(group)
        db.session.flush()

        req = ProjectRequest(
            name="Acme Corp Client",
            email="client@acme.example",
            company="Acme Global",
            project_type="fullstack",
            description="Receipt view test.",
            status="assigned",
            assigned_group_id=group.id,
        )
        db.session.add(req)
        db.session.flush()

        payment = ProjectPayment(
            project_request_id=req.id,
            group_id=group.id,
            title="Sprint 1 Milestone Payment",
            amount=7500.0,
            status="released",
            transaction_reference="ESC-RECEIPT-VIEW-123",
            payer_name="Acme Corp Client",
            payer_email="client@acme.example",
            released_at=datetime.now(timezone.utc),
        )
        db.session.add(payment)
        db.session.commit()
        req_id = req.id

    resp = client.get(f"/request/{req_id}/receipt/ESC-RECEIPT-VIEW-123")
    assert resp.status_code == 200
    assert b"OFFICIAL ESCROW RECEIPT" in resp.data
    assert b"ESC-RECEIPT-VIEW-123" in resp.data
    assert b"7,500.00" in resp.data
    assert b"PAID &amp; RELEASED" in resp.data or b"PAID & RELEASED" in resp.data


def test_coder_wallet_view(app, logged_in_coder_client, coder_user):
    with app.app_context():
        coder = db.session.get(CoderUser, coder_user.id)
        group = db.session.get(Group, coder.member.group_id)

        req = ProjectRequest(
            name="Wallet Client",
            email="wallet@example.com",
            project_type="web",
            description="Wallet test.",
            status="assigned",
            assigned_group_id=group.id,
        )
        db.session.add(req)
        db.session.flush()

        p1 = ProjectPayment(
            project_request_id=req.id,
            group_id=group.id,
            title="Sprint 1 Architecture",
            amount=4000.0,
            status="released",
            transaction_reference="ESC-WALLET-001",
            payer_name="Wallet Client",
            payer_email="wallet@example.com",
            released_at=datetime.now(timezone.utc),
        )
        p2 = ProjectPayment(
            project_request_id=req.id,
            group_id=group.id,
            title="Sprint 2 Testing",
            amount=2000.0,
            status="held_in_escrow",
            transaction_reference="ESC-WALLET-002",
            payer_name="Wallet Client",
            payer_email="wallet@example.com",
        )
        db.session.add(p1)
        db.session.add(p2)
        db.session.commit()

    resp = logged_in_coder_client.get("/coder/wallet")
    assert resp.status_code == 200
    assert b"Financial Ledger" in resp.data
    assert b"4,000.00" in resp.data
    assert b"2,000.00" in resp.data
    assert b"ESC-WALLET-001" in resp.data
    assert b"ESC-WALLET-002" in resp.data
