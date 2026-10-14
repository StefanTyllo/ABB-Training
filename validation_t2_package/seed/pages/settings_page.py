from selenium.webdriver.common.by import By
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

    def reload(self):
        self.driver.refresh()
        self.visible("connection")
        self.ready()
        return self

    def value(self, element_id):
        return self.visible(element_id).get_attribute("value")

    def selected(self, element_id):
        return Select(self.visible(element_id)).first_selected_option.get_attribute("value")

    def is_shown(self, element_id):
        return self.driver.find_element(By.ID, element_id).is_displayed()

    def save_tcp(self, host, port):
        self.choose_connection("tcp")
        self.fill("host", host)
        self.fill("port", port)
        return self.save()
