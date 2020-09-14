from typing import Optional, Union, Dict, Any, List
from unittest import main as unittest_main, TestCase

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

base_url: str = "http://localhost:5000"

index_url: str = f"{base_url}/"
login_url: str = f"{base_url}/login"
register_url: str = f"{base_url}/register"

default_driver_options: ChromeOptions = ChromeOptions()
default_driver_options.headless = True
default_driver_options.add_argument('--no-sandbox')


class MyTest(TestCase):
    web_driver: WebDriver

    def setUp(self) -> None:
        self.web_driver = Chrome(options=default_driver_options)

    def tearDown(self) -> None:
        self.web_driver.close()

    def __find_distinct_element__(self, xpath: str, search_path: Optional[WebElement] = None) -> WebElement:
        search_context: Union[WebElement, WebDriver] = search_path if search_path is not None else self.web_driver

        all_elements: List[WebElement] = search_context.find_elements_by_xpath(xpath)

        self.check_value(1, len(all_elements))

        return all_elements[0]

    def __test_element__(
            self,
            xpath: str,
            search_context: Optional[WebElement] = None,
            text: Optional[str] = None,
            attributes: Optional[Dict[str, Any]] = None,
    ) -> WebElement:
        web_element: WebElement = self.__find_distinct_element__(xpath, search_context)

        if text is not None:
            self.check_value(text, web_element.text)

        if attributes is not None:
            for key, value in attributes.items():
                self.check_value(value, web_element.get_attribute(key))

        return web_element

    def __perform_login__(self, username: str = "test", password: str = "1234"):
        self.web_driver.get(login_url)

        # fill out form values
        self.__find_distinct_element__("//form//input[@name='username']").send_keys(username)
        self.__find_distinct_element__("//form//input[@name='password']").send_keys(password)

        # send form
        self.__find_distinct_element__("//form//button").click()

    def __perform_register__(self, username: str = "user", password: str = "1234"):
        self.web_driver.get(register_url)

        # fill out form values
        self.__find_distinct_element__("//form//input[@name='username']").send_keys(username)
        self.__find_distinct_element__("//form//input[@name='password']").send_keys(password)
        self.__find_distinct_element__("//form//input[@name='passwordRepeat']").send_keys(password)

        # send form
        self.__find_distinct_element__("//form//button").click()

    def check_value(self, a, b):
        self.assertEqual(a, b)

    def t_x(self):
        self.fail('TODO!')

    def t_1_redirect_to_login(self):
        self.web_driver.get(base_url)
        self.assertEqual(login_url, self.web_driver.current_url)

    def t_2_register_form(self):
        self.web_driver.get(register_url)

        register_form: WebElement = self.__test_element__(
            "//form", attributes={"method": "post", "action": register_url}
        )

        # username input
        self.__test_element__(
            ".//input[@type='text']", register_form, attributes={"name": "username", "required": "true"}
        )

        # password input
        self.__test_element__(
            ".//input[@name='password']", register_form, attributes={"type": "password", "required": "true"}
        )

        # password repeat input
        self.__test_element__(
            ".//input[@name='passwordRepeat']", register_form, attributes={"type": "password", "required": "true"}
        )

        # submit_button
        self.__test_element__(".//button", register_form, text="Registrieren")

    def t_3_register_functionality(self):
        self.__perform_register__()

        WebDriverWait(self.web_driver, 5).until(expected_conditions.url_changes(register_url))
        self.assertEqual(login_url, self.web_driver.current_url)

    def t_4_login_form(self):
        self.web_driver.get(login_url)

        login_form: WebElement = self.__test_element__("//form", attributes={"method": "post", "action": login_url})

        # username_input
        self.__test_element__(".//input[@type='text']", login_form, attributes={"name": "username", "required": "true"})

        # password_input
        self.__test_element__(
            ".//input[@type='password']", login_form, attributes={"name": "password", "required": "true"}
        )

        # submit_button
        self.__test_element__(".//button", login_form, text="Einloggen")

    def t_5_login_functionality(self):
        self.__perform_login__()

        WebDriverWait(self.web_driver, 5).until(expected_conditions.url_changes(login_url))
        self.assertEqual(index_url, self.web_driver.current_url)

    def test_index(self):
        self.fail('TODO!')


if __name__ == "__main__":
    unittest_main()
