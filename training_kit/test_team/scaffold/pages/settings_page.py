from selenium.webdriver.support.ui import Select
from .base_page import BasePage


class SettingsPage(BasePage):
    def open(self, url):
        self.driver.get(url)
        self.ready()
        return self

    def choose_connection(self, value):
        Select(self.visible("connection")).select_by_value(value)
        self.ready()

    def save(self):
        self.visible("save").click()
        self.ready()
        return self.visible("status").text

    # T1: extend this existing POM for authentication, visibility and reload.
