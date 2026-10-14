from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 5)

    def visible(self, element_id):
        return self.wait.until(EC.visibility_of_element_located((By.ID, element_id)))

    def ready(self):
        self.wait.until(lambda driver: driver.find_element(By.ID, "settings").get_attribute("aria-busy") == "false")

    def fill(self, element_id, value):
        field = self.visible(element_id)
        field.clear()
        field.send_keys(str(value))
