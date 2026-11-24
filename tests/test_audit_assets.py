from scripts.audit_assets import find_remote_assets, line_loads_remote_asset


def test_remote_url_forms_are_detected():
    assert line_loads_remote_asset('<script src="https://cdn.example/app.js"></script>')
    assert line_loads_remote_asset('<link href="//cdn.example/app.css" rel="stylesheet">')
    assert line_loads_remote_asset("background: url(https://cdn.example/bg.png);")
    assert line_loads_remote_asset('@import "https://cdn.example/font.css";')


def test_local_links_and_svg_namespaces_are_allowed():
    assert not line_loads_remote_asset('<a href="/requests">My requests</a>')
    assert not line_loads_remote_asset('<link rel="stylesheet" href="{{ url_for(\'static\', path=\'style.css\') }}">')
    assert not line_loads_remote_asset('<svg xmlns="http://www.w3.org/2000/svg"></svg>')


def test_application_assets_stay_local():
    assert find_remote_assets() == []
