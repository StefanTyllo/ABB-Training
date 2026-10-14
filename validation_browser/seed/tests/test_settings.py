import pytest

FIELDS = {"serial": ("device",), "tcp": ("host", "port")}
ALL_CONNECTION_FIELDS = ("device", "host", "port")


def assert_connection_fields(page, mode):
    for field in ALL_CONNECTION_FIELDS:
        if field in FIELDS[mode]:
            assert page.visible(field).is_displayed(), f"{field} should be visible in {mode}"
        else:
            page.wait_hidden(field)
            assert not page.is_shown(field), f"{field} should be hidden in {mode}"


@pytest.mark.requirement("UI-01")
@pytest.mark.requirement("ASYNC-01")
def test_connection_visibility_both_directions(page):
    assert_connection_fields(page, "serial")
    page.choose_connection("tcp")
    assert_connection_fields(page, "tcp")
    page.choose_connection("serial")
    assert_connection_fields(page, "serial")


@pytest.mark.requirement("UI-02")
@pytest.mark.requirement("ASYNC-01")
def test_auth_visibility_both_directions(page):
    page.wait_hidden("password")
    assert not page.is_shown("password")
    page.choose_auth("password")
    assert page.visible("password").is_displayed()
    page.choose_auth("none")
    page.wait_hidden("password")
    assert not page.is_shown("password")


@pytest.mark.requirement("SAVE-01")
@pytest.mark.parametrize("mode", ["serial", "tcp"])
def test_save_reload_password(page, case, mode):
    page.choose_connection(mode)
    if mode == "serial":
        page.fill("device", case["device"])
    else:
        page.fill("host", case["host"])
        page.fill("port", case["port"])
    page.choose_auth(case["auth"])
    page.fill("password", case["password"])
    assert page.save() == "Saved"

    page.reload()
    assert page.value("connection") == mode
    assert_connection_fields(page, mode)
    if mode == "serial":
        assert page.value("device") == case["device"]
    else:
        assert page.value("host") == case["host"]
        assert page.value("port") == case["port"]
    assert page.value("auth") == case["auth"]
    assert page.value("password") == case["password"]


@pytest.mark.requirement("SAVE-01")
@pytest.mark.parametrize("mode", ["serial", "tcp"])
def test_save_reload_none_auth(page, case, mode):
    page.choose_connection(mode)
    if mode == "serial":
        page.fill("device", case["device"])
    else:
        page.fill("host", case["host"])
        page.fill("port", case["port"])
    page.choose_auth("password")
    page.fill("password", case["password"])
    page.choose_auth("none")
    assert page.save() == "Saved"

    page.reload()
    assert page.value("connection") == mode
    assert page.value("auth") == "none"
    page.wait_hidden("password")
    assert not page.is_shown("password")
    if mode == "serial":
        assert page.value("device") == case["device"]
    else:
        assert page.value("host") == case["host"]
        assert page.value("port") == case["port"]
