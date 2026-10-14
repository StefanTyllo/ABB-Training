from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
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

    def choose_auth(self, value):
        Select(self.visible("auth")).select_by_value(value)
        self.ready()

    def is_shown(self, element_id):
        """Non-waiting visibility check."""
        return self.driver.find_element(By.ID, element_id).is_displayed()

    def wait_hidden(self, element_id):
        self.wait.until(EC.invisibility_of_element_located((By.ID, element_id)))

    def value(self, element_id):
        return self.visible(element_id).get_attribute("value")

    def reload(self):
        self.driver.refresh()
        self.ready()
        return self
