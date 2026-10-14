import json
import os
from pathlib import Path
import urllib.request
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from pages.settings_page import SettingsPage


@pytest.fixture
def case():
    return json.loads(Path(__file__).with_name("case.json").read_text())


@pytest.fixture
def page():
    url = os.environ.get("BASE_URL", "http://127.0.0.1:8765")
    request = urllib.request.Request(url + "/api/reset", b"{}", {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=5) as response:
        assert response.status == 200
    options = webdriver.ChromeOptions()
    if os.environ.get("HEADED") != "1":
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    if os.environ.get("CHROME_BINARY"):
        options.binary_location = os.environ["CHROME_BINARY"]
    service = Service(os.environ["CHROMEDRIVER"]) if os.environ.get("CHROMEDRIVER") else Service()
    driver = webdriver.Chrome(service=service, options=options)
    try:
        yield SettingsPage(driver).open(url)
    finally:
        driver.quit()
