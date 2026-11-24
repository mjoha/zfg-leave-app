def test_landing_page_renders_local_layout(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert 'data-testid="landing-title"' in body
    assert "Leave requests, on this computer" in body
    assert 'data-testid="landing-summary"' in body
    assert 'data-testid="brand-link"' in body
    assert 'data-testid="nav-home"' in body
    assert "/static/style.css" in body
    assert "/static/favicon.svg" in body
    lowered = body.lower()
    for external in ("cdn.", "googleapis", "unpkg.com", "jsdelivr", "cloudflare"):
        assert external not in lowered


def test_static_stylesheet_is_served(client):
    response = client.get("/static/style.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert "--text" in response.text


def test_unknown_path_uses_not_found_page(client):
    response = client.get("/missing-page")

    assert response.status_code == 404
    assert 'data-testid="not-found"' in response.text
    assert 'data-testid="not-found-home"' in response.text
