import os
from time import sleep

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver


class BaseFabric(object):

    TIMEOUT = 10
    ORG = os.environ['ORG']
    TOKEN = os.environ['TOKEN']

    dir_path = os.path.dirname(os.path.realpath(__file__))
    driver = webdriver.Chrome('{}/chromedriver'.format(dir_path))

    def wait_until_visible_by(self, select_type, selector):
        element = WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.visibility_of_element_located((select_type, selector)))

        return element

    def wait_until_clickable_by(self, select_type, selector):
        element = WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.element_to_be_clickable((select_type, selector)))
        return element

    def wait_unit_present_by(self, select_type, selector):
        element = WebDriverWait(self.driver, self.TIMEOUT).until(
            EC.presence_of_element_located((select_type, selector)))

        return element

    def fabric_login(self):
        # Log into fabric.io
        self.driver.get("https://fabric.io/login")
        sleep(1)
        self.wait_until_clickable_by(
            LocatorType.ID, 'email').send_keys(os.environ['USERNAME'])
        self.wait_until_clickable_by(
            LocatorType.ID, 'password').send_keys(os.environ['PASSWORD'])
        sleep(1)
        self.wait_until_clickable_by(LocatorType.CSS_SELECTOR,
                                     '.sdk-button').click()

        self.wait_unit_present_by(LocatorType.ID, 'l_dashboard')


class LocatorType:
    ID = 'id'
    XPATH = "xpath"
    LINK_TEXT = "link text"
    PARTIAL_TEXT = "partial link text"
    NAME = "name"
    TAG_NAME = "tag name"
    CLASS_NAME = "class name"
    CSS_SELECTOR = "css selector"
