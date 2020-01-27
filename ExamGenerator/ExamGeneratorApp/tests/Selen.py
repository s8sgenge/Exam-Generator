import os

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


class My_selenium_tests(StaticLiveServerTestCase):
    """
    This class is used as a parent for all tests classes who use selenium.
    The class provides a proper setup function and some other help functions.
    """

    @classmethod
    # create test db from fixtures open
    def setUpClass(cls, debug):
        """
        Sets selenium up to be able to run tests.
        :param debug: if debug is True then the tests are run in an open firefox browser window. If debug is False,
                      then the browser window is hidden.
        """
        # resets the auto incrementation
        cls.reset_sequences = True
        super().setUpClass()

        # if debug is TRUE then the tests are run in an open firefox window
        if debug:
            cls.selenium = webdriver.Firefox(
                executable_path=os.path.join('ExamGeneratorApp', 'tests', 'sample_data_for_tests', 'geckodriver'))
            cls.selenium.maximize_window()

        # if debug is FALSE then the tests are run in a non-visible firefox browser.
        # Geckodriver is used for that purpose.
        # If in doubt set debug = True. The tests tend to be more viable then
        else:
            options = Options()
            options.headless = True
            options.add_argument("--window-size=1920,1080");
            cls.selenium = webdriver.Firefox(
                executable_path=os.path.join('ExamGeneratorApp', 'tests', 'sample_data_for_tests', 'geckodriver'),
                options=options)
            cls.selenium.set_window_position(0, 0)
            cls.selenium.set_window_size(1920, 1080)

        cls.selenium.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def login(self, username_arg, password_arg):
        """
        Tries to login with the given username and password
        :param username_arg: The username which will be used to login
        :param password_arg: The password which will be used to login
        """
        selenium = self.selenium
        selenium.get(self.live_server_url)

        # LOGIN

        # Find field for username and password input
        username = selenium.find_element_by_id('id_username')
        password = selenium.find_element_by_id('id_password')

        # insert data in the fields
        username.send_keys(username_arg)
        password.send_keys(password_arg)

        # find login button and click it
        login_button = selenium.find_element_by_xpath("//input[@value='Login']")
        login_button.click()

    def assertalways(self, msg):
        """
        Always asserts with the given error message
        :param msg: A help message which helps the user why the assertion got triggered
        :return: asserts always with 'msg' as the given error message
        """
        self.assert_(1 == 2, msg)

    def find_href(self, value):
        """
        Finds a element on a website which redirects to the given value
        :param value: the value of href
        :return: Object which redirects to the given value.
        """
        return self.selenium.find_element_by_xpath(f"//a[@href='{value}']")
