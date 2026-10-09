def test_app_created_testing_mode(app):
    assert app.testing is True
    assert app.config["FLASK_ENV"] == "testing"


def test_public_home_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Code" in html
    assert "Crews" in html


def test_loader_navbar_footer_present(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'id="ftco-loader"' in html
    assert 'id="ftco-navbar"' in html
    assert '<footer' in html
