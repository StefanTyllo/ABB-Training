"""Run explicitly: python -m pytest browser_preflight.py -q (server running)."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select


def test_browser_preflight(page):
    assert page.driver.title == "Device settings lab"
    assert page.visible("device").is_displayed()
    Select(page.visible("auth")).select_by_value("password")
    page.ready()
    assert page.visible("password").is_displayed()
    Select(page.visible("auth")).select_by_value("none")
    page.ready()
    page.wait.until(EC.invisibility_of_element_located((By.ID, "password")))
