from app.models.marketplace import MarketplaceItem


def _register_admin(client, org_name, email, org_slug):
    return client.post(
        "/auth/register",
        json={
            "email": email, "password": "correct-horse-battery-staple", "name": "Admin",
            "role": "admin", "organizationName": org_name, "organizationSlug": org_slug,
        },
    )


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _seed_catalog(db_session):
    """
    Migration 0009 seeds the real catalog, but tests build their schema
    straight from the SQLAlchemy models (see conftest.py's `db_session`
    fixture) rather than running Alembic — so tests seed their own small
    catalog directly, the same way test_tenancy.py pokes at ORM rows
    the API itself doesn't expose a way to set up.
    """
    items = [
        MarketplaceItem(
            id="mkt_test_free_bank", category="question_bank", name="Free Bank",
            description="A free question bank.", price_cents=0, is_premium=False,
        ),
        MarketplaceItem(
            id="mkt_test_theme", category="theme", name="Test Theme",
            description="A themed color scheme.", price_cents=499, is_premium=True,
            config_json='{"primaryColor": "#123456"}',
        ),
    ]
    db_session.add_all(items)
    db_session.commit()
    return items


def test_catalog_is_visible_to_any_admin(client, db_session):
    _seed_catalog(db_session)
    admin = _register_admin(client, "Cat Org", "cat-admin@example.com", "cat-org").json()

    response = client.get("/admin/marketplace/catalog", headers=_auth_header(admin["accessToken"]))
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_install_and_list_installed_items(client, db_session):
    _seed_catalog(db_session)
    admin = _register_admin(client, "Install Org", "install-admin@example.com", "install-org").json()
    headers = _auth_header(admin["accessToken"])

    response = client.post("/admin/marketplace/install", json={"itemId": "mkt_test_free_bank"}, headers=headers)
    assert response.status_code == 201

    installed = client.get("/admin/marketplace/installed", headers=headers)
    assert installed.status_code == 200
    assert len(installed.json()) == 1
    assert installed.json()[0]["item"]["id"] == "mkt_test_free_bank"


def test_cannot_install_the_same_item_twice(client, db_session):
    _seed_catalog(db_session)
    admin = _register_admin(client, "Dup Org", "dup-admin@example.com", "dup-org").json()
    headers = _auth_header(admin["accessToken"])

    client.post("/admin/marketplace/install", json={"itemId": "mkt_test_free_bank"}, headers=headers)
    second = client.post("/admin/marketplace/install", json={"itemId": "mkt_test_free_bank"}, headers=headers)
    assert second.status_code == 400


def test_installing_a_theme_applies_its_primary_color_to_the_organization(client, db_session):
    _seed_catalog(db_session)
    admin = _register_admin(client, "Theme Org", "theme-admin@example.com", "theme-org").json()
    headers = _auth_header(admin["accessToken"])

    client.post("/admin/marketplace/install", json={"itemId": "mkt_test_theme"}, headers=headers)

    org = client.get("/admin/organization", headers=headers).json()
    assert org["primaryColor"] == "#123456"


def test_uninstall_removes_the_install_record(client, db_session):
    _seed_catalog(db_session)
    admin = _register_admin(client, "Uninstall Org", "uninstall-admin@example.com", "uninstall-org").json()
    headers = _auth_header(admin["accessToken"])

    client.post("/admin/marketplace/install", json={"itemId": "mkt_test_free_bank"}, headers=headers)
    response = client.delete("/admin/marketplace/installed/mkt_test_free_bank", headers=headers)
    assert response.status_code == 204

    installed = client.get("/admin/marketplace/installed", headers=headers).json()
    assert installed == []


def test_installs_are_scoped_to_the_installing_organization(client, db_session):
    _seed_catalog(db_session)
    admin_a = _register_admin(client, "Mkt Org A", "mkt-admina@example.com", "mkt-org-a").json()
    admin_b = _register_admin(client, "Mkt Org B", "mkt-adminb@example.com", "mkt-org-b").json()

    client.post(
        "/admin/marketplace/install",
        json={"itemId": "mkt_test_free_bank"},
        headers=_auth_header(admin_a["accessToken"]),
    )

    installed_a = client.get("/admin/marketplace/installed", headers=_auth_header(admin_a["accessToken"])).json()
    installed_b = client.get("/admin/marketplace/installed", headers=_auth_header(admin_b["accessToken"])).json()
    assert len(installed_a) == 1
    assert len(installed_b) == 0
