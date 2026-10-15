import pytest

TCP_CONFIGS = [
    ("lab.example.test", "1502"),
    ("10.1.2.3", "65535"),
]


@pytest.mark.requirement("SAVE-01")
def test_weak_save_smoke(page):
    page.choose_connection("tcp")
    page.fill("host", "lab.example.test")
    page.fill("port", "1502")
    assert page.save() == "Saved"


@pytest.mark.requirement("VAL-01")
@pytest.mark.parametrize("port", ["1", "65535"])
def test_port_boundary_valid_accepted_and_restored(page, port):
    status = page.save_tcp("lab.example.test", port)
    assert status == "Saved", f"VAL-01: valid port {port} must be accepted, status was {status!r}"
    page.reload()
    assert page.selected("connection") == "tcp"
    assert page.value("port") == port


@pytest.mark.requirement("VAL-01")
@pytest.mark.parametrize("port", ["0", "65536", "abc"])
def test_port_boundary_invalid_rejected(page, port):
    status = page.save_tcp("lab.example.test", port)
    assert status != "Saved", f"VAL-01: invalid port {port!r} must be rejected, status was {status!r}"


@pytest.mark.requirement("SAVE-01")
@pytest.mark.parametrize("host,port", TCP_CONFIGS)
def test_save_reload_tcp_values_survive(page, host, port):
    assert page.save_tcp(host, port) == "Saved"
    page.reload()
    assert page.selected("connection") == "tcp", "SAVE-01: saved connection must be restored"
    assert page.value("host") == host
    assert page.value("port") == port


@pytest.mark.requirement("SAVE-01")
def test_save_reload_case_with_password(page, case):
    page.choose_connection(case["connection"])
    page.fill("host", case["host"])
    page.fill("port", case["port"])
    page.choose_auth(case["auth"])
    page.fill("password", case["password"])
    assert page.save() == "Saved"
    page.reload()
    assert page.selected("connection") == "tcp"
    assert page.selected("auth") == "password", "SAVE-01: authentication mode must be restored"
    assert page.value("host") == case["host"]
    assert page.value("port") == case["port"]
    assert page.value("password") == case["password"]


@pytest.mark.requirement("SAVE-01")
@pytest.mark.parametrize("bad_port", ["0", "65536", "abc"])
def test_invalid_save_preserves_baseline(page, bad_port):
    assert page.save_tcp("baseline.example.test", "1502") == "Saved"
    page.reload()
    assert page.selected("connection") == "tcp"
    page.fill("host", "other.example.test")
    page.fill("port", bad_port)
    assert page.save() != "Saved", f"VAL-01: invalid port {bad_port!r} must not be accepted"
    page.reload()
    assert page.selected("connection") == "tcp", "SAVE-01: baseline connection must remain"
    assert page.value("host") == "baseline.example.test"
    assert page.value("port") == "1502"
