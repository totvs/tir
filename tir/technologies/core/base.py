import re
import time
import unittest
import inspect
import socket
import sys
import os
import random
import string
import subprocess
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
import tir.technologies.core.enumerations as enum
from tir.technologies.core.log import Log
from tir.technologies.core.config import ConfigLoader
from tir.technologies.core.language import LanguagePack
from tir.technologies.core.third_party.xpath_soup import xpath_soup
from selenium.webdriver.firefox.options import Options as FirefoxOpt
from selenium.webdriver.chrome.options import Options as ChromeOpt
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from datetime import datetime
from tir.technologies.core.logging_config import logger
from tir.version import __version__
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path


class Base(unittest.TestCase):
    """
    Base class for any technology to implement Selenium Interface Tests.

    This class instantiates the browser, reads the config file and prepares the log.

    If no config_path is passed, it will read the config.json file that exists in the same
    folder as the file that would execute this module.

    :param config_path: The path to the config file. - **Default:** "" (empty string)
    :type config_path: str
    :param autostart: Sets whether TIR should open browser and execute from the start. - **Default:** True
    :type: bool

    Usage:

    The Base class must be inherited by every internal class of each technology that would exist in this module.

    The classes must be declared under pwa/technologies/ folder.

    >>> def WebappInternal(Base):
    >>> def APWInternal(Base):
    """

    driver = None
    wait = None
    errors = []
    
    def __init__(self, config_path="", autostart=True):
        """
        Definition of each global variable:

        base_container: A variable to contain the layer element to be used on all methods.

        errors: A list that contains every error that should be sent to log at the end of the execution.

        language: Contains the terms defined in the language defined in config or found in the page.

        log: Object that controls the logs of the entire application.

        log.station: Property of the log that contains the machine's hostname.

        log_file: A variable to control when to generate a log file of each execution of web_scrap. (Debug purposes)

        wait: The global Selenium Wait defined to be used in the entire application.
        """
        #Global Variables:

        self.config_path = config_path

        if self.config_path == "":
            self.config_path = os.path.join(sys.path[0], r"config.json")

        self.config = ConfigLoader(self.config_path)
        self.config.autostart = autostart

        self.language = LanguagePack(self.config.language) if self.config.language else ""
        self.log = Log(folder=self.config.log_folder, config_path=self.config_path)
        self.log.station = socket.gethostname()
        self.test_case = []
        self.last_test_case = None
        self.message = ""
        self.expected = True
        self.webapp_version= ''

        try:
            self.log.user = os.getlogin()
        except Exception:
            import getpass
            self.log.user = getpass.getuser()

        if self.config.smart_test:
            if self.log.user == 'root':
                self.log.user = 'advpr.sp'

        self.base_container = "body"
        self.config.log_file = False
        self.tmenu_out_iframe = False
        self.twebview_context = False

        if autostart:
            self.Start()

# Internal Methods

    def assert_result(self, expected, script_message=""):
        """
        [Internal]

        Asserts the result based on the expected value.

        :param expected: Expected value
        :type expected: bool

        Usage :

        >>> #Calling the method:
        >>> self.assert_result(True)
        """
        expected_assert = expected
        msg = "Passed"
        stack_item = next(iter(list(map(lambda x: x.function, filter(lambda x: re.search('test_', x.function), inspect.stack())))), None)
        test_number = f"{stack_item.split('_')[-1]} -" if stack_item else ""
        log_message = f"{test_number}"
        self.log.set_seconds()

        if self.errors:
            expected = not expected

            for field_msg in self.errors:
                log_message += (" " + field_msg)

            msg = log_message

            self.log.new_line(False, log_message)
        else:
            self.log.new_line(True, "")

        self.log.save_file()

        self.errors = []
        logger().info(msg)
        if expected_assert:
            self.assertTrue(expected, msg)
        else:
            self.assertFalse(expected, msg)

    def click(self, element, click_type=enum.ClickType.JS, right_click=False):
        """
        [Internal]

        Clicks on the Selenium element.

        Supports three types of clicking: JavaScript, pure Selenium and Selenium's ActionChains.

        Default is JavaScript clicking.

        :param element: Selenium element
        :type element: Selenium object
        :param click_type: ClickType enum. - **Default:** enum.ClickType.JS
        :type click_type: enum.ClickType
        :param right_click: Clicks with the right button of the mouse in the last element of the tree.
        :type string: bool

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> self.click(element(), click_type=enum.ClickType.JS)
        """

        logger().debug(f'Click Type: {click_type}')

        try:
            if right_click:
                ActionChains(self.driver).context_click(element).perform()
            else:
                self.scroll_to_element(element)
                if click_type == enum.ClickType.JS:
                    self.driver.execute_script("arguments[0].click()", element)
                elif click_type == enum.ClickType.SELENIUM:
                    element.click()
                elif click_type == enum.ClickType.ACTIONCHAINS:
                    ActionChains(self.driver).move_to_element(element).click().perform()
            
            return True

        except StaleElementReferenceException:
            logger().exception("********Element Stale click*********")
            return False
        except Exception as e:
            logger().exception(f"Warning click method Exception: {str(e)}")
            return False

    def compare_field_values(self, field, user_value, captured_value, message):
        """
        [Internal]

        Validates and stores field in the self.errors array if the values are different.

        :param field: Field name
        :type field: str
        :param user_value: User input value
        :type user_value: str
        :param captured_value: Interface captured value
        :type captured_value: str
        :param message: Error message if comparison fails
        :type message: str

        Usage:

        >>> #Calling the method
        >>> self.compare_field_values("A1_NOME", "JOÃO", "JOOÃ", "Field A1_NOME has different values")
        """
        if str(user_value).strip() != str(captured_value).strip():
            if self.config.screenshot and self.errors == []:
                self.log.take_screenshot_log(self.driver)
                
            self.errors.append(message)
            

    def double_click(self, element, click_type = enum.ClickType.SELENIUM):
        """
        [Internal]

        Clicks two times on the Selenium element.

        :param element: Selenium element
        :type element: Selenium object

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> self.double_click(element())
        """

        logger().debug(f'Click Type: {click_type}')

        try:
            if click_type == enum.ClickType.SELENIUM:
                self.scroll_to_element(element)
                element.click()
                element.click()
            elif click_type == enum.ClickType.ACTIONCHAINS:
                self.scroll_to_element(element)
                actions = ActionChains(self.driver)
                actions.move_to_element(element)
                actions.double_click()
                actions.perform()
            elif click_type == enum.ClickType.JS:
                self.driver.execute_script("arguments[0].click()", element)
                self.driver.execute_script("arguments[0].click()", element)

            return True        

        except Exception as e:
            try:
                logger().warning(f"Warning double_click method Exception: {str(e)}")
                self.scroll_to_element(element)
                actions = ActionChains(self.driver)
                actions.move_to_element(element)
                actions.double_click()
                actions.perform()

                return True
            except Exception as x:
                logger().exception(f"Error double_click method Exception: {str(x)}")
                return False


    def element_exists(self, term, scrap_type=enum.ScrapType.TEXT, position=0, optional_term="", main_container=".tmodaldialog,.ui-dialog"):
        """
        [Internal]

        Returns a boolean if element exists on the screen.

        :param term: The first term to use on a search of element
        :type term: str
        :param scrap_type: Type of element search. - **Default:** enum.ScrapType.TEXT
        :type scrap_type: enum.ScrapType
        :param position: Position which element is located. - **Default:** 0
        :type position: int
        :param optional_term: Second term to use on a search of element. Used in MIXED search. - **Default:** "" (empty string)
        :type optional_term: str

        :return: True if element is present. False if element is not present.
        :rtype: bool

        Usage:

        >>> element_is_present = element_exists(term=".ui-dialog", scrap_type=enum.ScrapType.CSS_SELECTOR)
        >>> element_is_present = element_exists(term=".tmodaldialog.twidget", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1)
        >>> element_is_present = element_exists(term=text, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay")
        """
        if self.config.debug_log:
            logger().info(f"term={term}, scrap_type={scrap_type}, position={position}, optional_term={optional_term}")

        if scrap_type == enum.ScrapType.SCRIPT:
            return bool(self.driver.execute_script(term))
        elif (scrap_type != enum.ScrapType.MIXED and scrap_type != enum.ScrapType.TEXT):
            selector = term
            if scrap_type == enum.ScrapType.CSS_SELECTOR:
                by = By.CSS_SELECTOR
            elif scrap_type == enum.ScrapType.XPATH:
                by = By.XPATH

            if scrap_type != enum.ScrapType.XPATH:
                soup = self.get_current_DOM()
                container_selector = self.base_container
                if (main_container is not None):
                    container_selector = main_container
                containers = self.zindex_sort(soup.select(container_selector), reverse=True)
                container = next(iter(containers), None)
                if not container:
                    return False

                try:
                    container_element = self.driver.find_element_by_xpath(xpath_soup(container))
                except:
                    return False
            else:
                container_element = self.driver

            element_list = container_element.find_elements(by, selector)
        else:
            if scrap_type == enum.ScrapType.MIXED:
                selector = optional_term
            else:
                selector = "div"

            element_list = self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container)
        if position == 0:
            return len(element_list) > 0
        else:
            return len(element_list) >= position

    def filter_displayed_elements(self, elements, reverse=False, twebview=False):
        """
        [Internal]

        Receives a BeautifulSoup element list and filters only the displayed elements.

        :param elements: BeautifulSoup element list
        :type elements: List of BeautifulSoup objects
        :param reverse: Boolean value if order should be reversed or not. - **Default:** False
        :type reverse: bool

        :return: List of filtered BeautifulSoup elements
        :rtype: List of BeautifulSoup objects

        Usage:

        >>> #Defining the element list:
        >>> soup = self.get_current_DOM()
        >>> elements = soup.select("div")
        >>> #Calling the method
        >>> self.filter_displayed_elements(elements, True)
        """

        if twebview:
            self.switch_to_iframe()
        #0 - elements filtered
        elements = list(filter(lambda x: self.soup_to_selenium(x) is not None ,elements ))
        if not elements:
            return
        #1 - Create an enumerated list from the original elements
        indexed_elements = list(enumerate(elements))
        #2 - Convert every element from the original list to selenium objects
        selenium_elements = list(map(lambda x : self.soup_to_selenium(x), elements))
        #3 - Create an enumerated list from the selenium objects
        indexed_selenium_elements = list(enumerate(selenium_elements))
        #4 - Filter elements based on "is_displayed()" and gets the filtered elements' enumeration
        filtered_selenium_indexes = list(map(lambda x: x[0], filter(lambda x: x[1].is_displayed(), indexed_selenium_elements)))
        #5 - Use List Comprehension to build a filtered list from the elements based on enumeration
        filtered_elements = [x[1] for x in indexed_elements if x[0] in filtered_selenium_indexes]
        #6 - Sort the result and return it
        return self.zindex_sort(filtered_elements, reverse)

    def find_first_div_parent(self, element):
        """
        [Internal]

        Finds first div parent element of another BeautifulSoup element.

        If element is already a div, it will return the element.

        :param element: BeautifulSoup element
        :type element: BeautifulSoup object

        :return: The first div parent of the element
        :rtype: BeautifulSoup object

        Usage:

        >>> parent_element = self.find_first_div_parent(my_element)
        """
        current = element
        while(hasattr(current, "name") and self.element_name(current) != "div"):
            current = current.find_parent()
        return current

    def find_first_wa_panel_parent(self, element):
        """
        [Internal]

        Finds first div parent element of another BeautifulSoup element.

        If element is already a div, it will return the element.

        :param element: BeautifulSoup element
        :type element: BeautifulSoup object

        :return: The first div parent of the element
        :rtype: BeautifulSoup object

        Usage:

        >>> parent_element = self.find_first_div_parent(my_element)
        """
        current = element
        while(hasattr(current, "name") and self.element_name(current) != "wa-panel"):
            current = current.find_parent()
        return current

    def element_name(self, element_soup):
        """
        [internal]

        """
        result = ''
        if element_soup:
            result = element_soup.name
        return result

    def find_label_element(self, label_text, container):
        """
        [Internal]

        Find input element next to label containing the label_text parameter.

        :param label_text: The label text to be searched
        :type label_text: str
        :param container: The main container object to be used
        :type container: BeautifulSoup object

        :return: A list containing a BeautifulSoup object next to the label
        :rtype: List of BeautifulSoup objects

        Usage:

        >>> self.find_label_element("User:", container_object)
        """
        element = next(iter(list(map(lambda x: self.find_first_div_parent(x), container.find_all(text=re.compile(f"^{re.escape(label_text)}" + r"(\*?)(\s*?)$"))))), None)
        if element is None:
            return []

        next_sibling = element.find_next_sibling("input")
        if next_sibling:
            return [next_sibling]
        else:
            return []

    def get_current_DOM(self, twebview=False):
        """
        [Internal]

        Returns current HTML DOM parsed as a BeautifulSoup object

        :returns: BeautifulSoup parsed DOM
        :rtype: BeautifulSoup object

        Usage:

        >>> #Calling the method
        >>> soup = self.get_current_DOM()
        """
        try:

            self.driver.switch_to.default_content()

            if self.config.new_log:
                self.execution_flow()

            if twebview:
                self.switch_to_iframe()
                self.twebview_context = False
                return BeautifulSoup(self.driver.page_source, "html.parser")

            soup = BeautifulSoup(self.driver.page_source,"html.parser")

            if self.tmenu_out_iframe:
                self.driver.switch_to.default_content()
                soup = BeautifulSoup(self.driver.page_source,"html.parser")

            elif soup and soup.select('.session'):

                script = """
                var getIframe = () => {
                    if(document.querySelector(".session")){
                        var iframeObject = document.querySelector(".session")
                        var contet = iframeObject.contentDocument;
                        var serializer = new XMLSerializer();
                        return serializer.serializeToString(contet);
                    }
                    return ""
                }

                return getIframe()
                """
                soup = BeautifulSoup(self.driver.execute_script(script),'html.parser')
                self.driver.switch_to.frame(self.driver.find_element_by_css_selector("iframe[class=session]"))

            return soup
            
        except WebDriverException as e:
            self.driver.switch_to.default_content()
            soup = BeautifulSoup(self.driver.page_source,"html.parser")
            return soup

    def switch_to_iframe(self):
        """
        [Internal]
        :return:
        """

        if not self.config.poui:
            iframes = None
            iframe_displayed = None
            endtime = time.time() + self.config.time_out
            while time.time() < endtime and not iframes:
                iframes = self.driver.find_elements_by_css_selector('[class*="twebview"], [class*="dict-twebengine"]')

                if iframes:
                    iframe_displayed = next(iter(list(filter(lambda x: x.is_displayed(), iframes))), None)
                else:
                    self.driver.switch_to.default_content()

                if iframe_displayed:
                    self.driver.switch_to.frame(self.find_shadow_element('iframe', iframe_displayed)[0]) if self.webapp_shadowroot() else self.driver.switch_to.frame(iframe_displayed)

    def get_element_text(self, element):
        """
        [Internal]

        Gets element text.

        :param element: Selenium element
        :type element: Selenium object

        :return: Element text
        :rtype: str

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> text = self.get_element_text(element())
        """
        try:
            return self.driver.execute_script("return arguments[0].innerText", element)
        except StaleElementReferenceException:
            logger().exception("********Element Stale get_element_text*********")
            pass

    def get_element_value(self, element):
        """
        [Internal]

        Gets element value.

        :param element: Selenium element
        :type element: Selenium object

        :return: Element value
        :rtype: str

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> text = self.get_element_value(element())
        """
        try:
            return self.driver.execute_script("return arguments[0].value", element)
        except StaleElementReferenceException:
            logger().exception("********Element Stale get_element_value*********")
            pass

    def log_error(self, message, new_log_line=True):
        """
        [Internal]

        Finishes execution of test case with an error and creates the log information for that test.

        :param message: Message to be logged
        :type message: str
        :param new_log_line: Boolean value if Message should be logged as new line or not. - **Default:** True
        :type new_log_line: bool

        Usage:

        >>> #Calling the method:
        >>> self.log_error("Element was not found")
        """
        stack_item = next(iter(list(map(lambda x: x.function, filter(lambda x: re.search('test_', x.function), inspect.stack())))), None)
        test_number = f"{stack_item.split('_')[-1]} -" if stack_item else ""
        log_message = f"{test_number} {message}"
        self.log.set_seconds()

        if new_log_line:
            self.log.new_line(False, log_message)
        self.log.save_file()
        self.assertTrue(False, log_message)

    def move_to_element(self, element):
        """
        [Internal]

        Move focus to element on the screen.

        :param element: Selenium element
        :type element: Selenium object

        Usage:

        >>> #Defining an element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> self.scroll_to_element(element())
        """
        ActionChains(self.driver).move_to_element(element).perform()

    def normalize_config_name(self, config_name):
        """
        [Internal]

        Normalizes the config name string to respect the config object
        naming convention.

        :param config_name: The config name string to be normalized.
        :type config_name: str
        :return: The config name string normalized.
        :rtype: str

        Usage:

        >>> # Calling the method:
        >>> normalized_name = self.normalize_config_name("InitialProgram") # "initial_program"
        """
        name_letters = list(map(lambda x: x, config_name))
        capitalized = list(filter(lambda x: x[1] in string.ascii_uppercase, enumerate(name_letters)))
        normalized = ""
        if len(capitalized) > 1:
            words = []
            for count in range(0, len(capitalized)):
                if count + 1 < len(capitalized):
                    word = "".join(name_letters[capitalized[count][0]:capitalized[count+1][0]])
                else:
                    word = "".join(name_letters[capitalized[count][0]:])
                words.append(word.lower())
            normalized = "_".join(words)
        else:
            normalized = config_name.lower()

        return normalized

    def take_screenshot(self, filename):
        """
        [Internal]

        Takes a screenshot and saves on the screenshot folder defined in config.

        :param filename: The name of the screenshot file.
        :type: str

        Usage:

        >>> # Calling the method:
        >>> self.take_screenshot(filename="myscreenshot")
        """
        if not filename.endswith(".png"):
            filename += ".png"

        directory = self.config.screenshot_folder if self.config.screenshot_folder else os.path.join(os.getcwd(), "screenshot")

        if not os.path.exists(directory):
            os.makedirs(directory)

        fullpath = os.path.join(directory, filename)

        self.driver.save_screenshot(fullpath)

    def scroll_to_element(self, element):
        """
        [Internal]

        Scroll to element on the screen.

        :param element: Selenium element
        :type element: Selenium object

        Usage:

        >>> #Defining an element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> self.scroll_to_element(element())
        """
        try:
            self.driver.execute_script("return arguments[0].scrollIntoView();", element)
        except Exception as e:
            logger().debug(f"********Warining scroll_to_element exception: {str(e)}*********")
            pass

    def search_zindex(self,element):
        """
        [Internal]

        Returns zindex value of Beautifulget_so object.

        Internal function created to be used inside lambda of zindex_sort method.

        Only works if element has Style attribute.

        :param element: BeautifulSoup element
        :type element: BeautifulSoup object

        :return: z-index value
        :rtype: int

        Usage:

        >>> #Line extracted from zindex_sort method:
        >>> elements.sort(key=lambda x: self.search_zindex(x), reverse=reverse)

        """
        zindex = 0
        if hasattr(element,"attrs") and "style" in element.attrs and "z-index:" in element.attrs['style']:
            zindex = int(element.attrs['style'].split("z-index:")[1].split(";")[0].strip())

        return zindex

    def select_combo(self, element, option, index=False, shadow_root=True, locator=False):
        """
        Selects the option on the combobox.

        :param element: Combobox element
        :type element: Beautiful Soup object
        :param option: Option to be selected
        :type option: str
        :param index: True if option is an integer value
        :type index: bool
        :param shadow_root: Internal control for shadow root objects
        :type shadow_root: bool
        :param locator: bool value for locator True or False
        :type locator: bool

        Usage:

        >>> #Calling the method:
        >>> self.select_combo(element, "Chosen option")
        """

        combo = self.return_combo_object(element, shadow_root=shadow_root, locator=locator)

        if index:
            index_number = self.return_combo_index(combo, option)
            if index_number:
                time.sleep(1)
                combo.select_by_index(str(index_number))
        else:
            value = next(iter(filter(lambda x: x.text.lower().strip() == option.lower().strip() , combo.options)), None)
            if not value:
                value = next(iter(filter(lambda x: x.text[0:len(option)].lower().strip()  == option.lower().strip() , combo.options)), None)
            if value:
                time.sleep(1)
                text_value = value.text
                combo.select_by_visible_text(text_value)
                logger().info(f"Selected value for combo is: {text_value}")

    def return_combo_object(self, element, shadow_root=True, locator=False):
        """
        [Internal]
        """

        if locator:
            combo = Select(element)
        elif self.webapp_shadowroot(shadow_root=shadow_root):
            combo = Select(self.driver.execute_script("return arguments[0].shadowRoot.querySelector('select')",
                                                      self.soup_to_selenium(element)))
        else:
            combo = Select(self.driver.find_element_by_xpath(xpath_soup(element)))

        return combo

    def return_selected_combo_value(self, element):
        """"
        [Internal]
        """

        combo = self.return_combo_object(element)

        if combo.all_selected_options:
            return combo.all_selected_options[0].text
        else:
            return ''

    def send_keys(self, element, arg):
        """
        [Internal]

        Clicks two times on the Selenium element.

        :param element: Selenium element
        :type element: Selenium object
        :param arg: Text or Keys to be sent to the element
        :type arg: str or selenium.webdriver.common.keys

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method with a string
        >>> self.send_keys(element(), "Text")
        >>> #Calling the method with a Key
        >>> self.send_keys(element(), Keys.ENTER)
        """
        try:
            if arg.isprintable():
                element.clear()
                element.send_keys(Keys.CONTROL, 'a')
            element.send_keys(arg)
        except Exception:
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            actions.click()
            if arg.isprintable():
                actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.DELETE)
            actions.send_keys(Keys.HOME)
            actions.send_keys(arg)
            actions.perform()

    def search_stack(self, function):
        """
        Returns True if passed function is present in the call stack.

        :param function: Name of the function
        :type function: str

        :return: Boolean if passed function is present or not in the call stack.
        :rtype: bool

        Usage:

        >>> # Calling the method:
        >>> is_present = self.search_stack("MATA020")
        """
        return len(list(filter(lambda x: x.function == function, inspect.stack()))) > 0

    def set_element_focus(self, element):
        """
        [Internal]

        Sets focus on element.

        :param element: Selenium element
        :type element: Selenium object

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method
        >>> text = self.set_element_focus(element())
        """   
        try:
            self.driver.execute_script("window.focus(); arguments[0].focus();", element)
        except StaleElementReferenceException:
            logger().exception("********Element Stale set_element_focus*********")
            pass
    

    def soup_to_selenium(self, soup_object=None, twebview=False):
        """
        [Internal]

        An abstraction of the Selenium call to simplify the conversion of elements.

        :param soup_object: The BeautifulSoup object to be converted.
        :type soup_object: BeautifulSoup object

        :return: The object converted to a Selenium object.
        :rtype: Selenium object

        Usage:

        >>> # Calling the method:
        >>> selenium_obj = lambda: self.soup_to_selenium(bs_obj)
        """
        if twebview:
            self.switch_to_iframe()

        if soup_object is None:
            raise AttributeError
        return next(iter(self.driver.find_elements_by_xpath(xpath_soup(soup_object))), None)

    def web_scrap(self, term, scrap_type=enum.ScrapType.TEXT, optional_term=None, label=False, main_container=None):
        """
        [Internal]

        Returns a BeautifulSoup object list based on the search parameters.

        Does not support ScrapType.XPATH as scrap_type parameter value.

        :param term: The first search term. A text or a selector
        :type term: str
        :param scrap_type: The type of webscraping. - **Default:** enum.ScrapType.TEXT
        :type scrap_type: enum.ScrapType.
        :param optional_term: The second search term. A selector used in MIXED webscraping. - **Default:** None
        :type optional_term: str
        :param label: If the search is based on a label near the element. - **Default:** False
        :type label: bool
        :param main_container: The selector of a container element that has all other elements. - **Default:** None
        :type main_container: str

        :return: List of BeautifulSoup4 elements based on search parameters.
        :rtype: List of BeautifulSoup4 objects

        Usage:

        >>> #All buttons
        >>> buttons = self.web_scrap(term="button", scrap_type=enum.ScrapType.CSS_SELECTOR)
        >>> #----------------#
        >>> #Elements that contain the text "Example"
        >>> example_elements = self.web_scrap(term="Example")
        >>> #----------------#
        >>> #Elements with class "my_class" and text "my_text"
        >>> elements = self.web_scrap(term="my_text", scrap_type=ScrapType.MIXED, optional_term=".my_class")
        """
        try:
            endtime = time.time() + 60
            container =  None
            while(time.time() < endtime and container is None):
                soup = self.get_current_DOM()

                if self.config.log_file:
                    with open(f"{term + str(scrap_type) + str(optional_term) + str(label) + str(main_container) + str(random.randint(1, 101)) }.txt", "w") as text_file:
                        text_file.write(f" HTML CONTENT: {str(soup)}")

                container_selector = self.base_container
                if (main_container is not None):
                    container_selector = main_container

                containers = self.zindex_sort(soup.select(container_selector), reverse=True)

                container = next(iter(containers), None)

            if container is None:
                raise Exception("Couldn't find container")

            if (scrap_type == enum.ScrapType.TEXT):
                if label:
                    return self.find_label_element(term, container)
                else:
                    return list(filter(lambda x: term.lower() in x.text.lower(), container.select("div > *")))
            elif (scrap_type == enum.ScrapType.CSS_SELECTOR):
                return container.select(term)
            elif (scrap_type == enum.ScrapType.MIXED and optional_term is not None):
                return list(filter(lambda x: term.lower() in x.text.lower(), container.select(optional_term)))
            elif (scrap_type == enum.ScrapType.SCRIPT):
                script_result = self.driver.execute_script(term)
                return script_result if isinstance(script_result, list) else []
            else:
                return []
        except Exception as e:
            self.log_error(str(e))

    def zindex_sort (self, elements, reverse=False, active_tab=True):
        """
        [Internal]

        Sorts list of BeautifulSoup elements based on z-index style attribute.

        Only works if elements have Style attribute.

        :param elements: BeautifulSoup element list
        :type elements: List of BeautifulSoup objects
        :param reverse: Boolean value if order should be reversed or not. - **Default:** False
        :type reverse: bool

        :return: List of sorted BeautifulSoup elements based on zindex.
        :rtype: List of BeautifulSoup objects

        Usage:

        >>> #Defining the element list:
        >>> soup = self.get_current_DOM()
        >>> elements = soup.select("div")
        >>> #Calling the method
        >>> self.zindex_sort(elements, True)
        """
        if active_tab:
            elements = self.return_active_element(elements, reverse)
        else:
            isinstance(elements, list)
            elements.sort(key=lambda x: self.search_zindex(x), reverse=reverse)

        return elements

# User Methods

    def AssertFalse(self, expected, message):
        """
        Defines that the test case expects a False response to pass

        Usage:

        >>> #Calling the method
        >>> oHelper.AssertFalse()
        """
        self.assert_result(expected, message)

    def AssertTrue(self, expected, message):
        """
        Defines that the test case expects a True response to pass

        Usage:

        >>> #Calling the method
        >>> oHelper.AssertTrue()
        """
        self.assert_result(expected, message)

    def SetTIRConfig(self, config_name, value):
        """
        Changes a value of a TIR internal config during runtime.

        This could be useful for TestCases that must use a different set of configs
        than the ones defined at **config.json**

        Available configs:

        - Url - str
        - Environment - str
        - User - str
        - Password - str
        - Language - str
        - DebugLog - str
        - TimeOut - int
        - InitialProgram - str
        - Routine - str
        - Date - str
        - Group - str
        - Branch - str
        - Module - str

        :param config_name: The config to be changed.
        :type config_name: str
        :param value: The value that would be set.
        :type value: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetTIRConfig(config_name="date", value="30/10/2018")
        """
        if 'TimeOut' in config_name:
            logger().info('TimeOut setting has been disabled in SetTirConfig')
        else:
            logger().info(f"Setting config: {config_name} = {value}")
            normalized_config = self.normalize_config_name(config_name)
            setattr(self.config, normalized_config, value)

    def Start(self):
        """
        Opens the browser maximized and goes to defined URL.

        Usage:

        >>> # Calling the method:
        >>> oHelper.Start()
        """

        start_program = '#inputStartProg, #selectStartProg'

        if self.config.appserver_service:
            try:
                self.sc_query(self.config.appserver_service)
            except Exception as err:
                logger().debug(f'sc_query exception: {err}')

        logger().info(f'TIR Version: {__version__}')
        logger().info("Starting the browser")
        if self.config.browser.lower() == "firefox":
            if sys.platform == 'linux':
                driver_path = os.path.join(os.path.dirname(__file__), r'drivers/linux64/geckodriver')
            else:
                driver_path = os.path.join(os.path.dirname(__file__), r'drivers\\windows\\geckodriver.exe')
            log_path = os.devnull

            firefox_options = FirefoxOpt()
            firefox_options.set_headless(self.config.headless)
            self.driver = webdriver.Firefox(options=firefox_options, executable_path=driver_path, log_path=log_path)
        elif self.config.browser.lower() == "chrome":
            chrome_options = ChromeOpt()
            chrome_options.set_headless(self.config.headless)
            chrome_options.add_argument('--log-level=3')
            if self.config.headless:
                chrome_options.add_argument('force-device-scale-factor=0.77')

            try:
                if self.config.chromedriver_auto_install:
                    if self.config.ssl_chrome_auto_install_disable:
                        os.environ['WDM_SSL_VERIFY'] = '0'
                    self.driver = webdriver.Chrome(options=chrome_options,
                                                   executable_path=ChromeDriverManager().install())
                else:
                    if sys.platform == 'linux':
                        driver_path = Path(__file__).parent.resolve().joinpath('drivers', 'linux', 'chromedriver.exe')
                    elif sys.platform == 'win32':
                        driver_path = Path(__file__).parent.resolve().joinpath('drivers', 'windows', 'chromedriver.exe')

                    self.driver = webdriver.Chrome(options=chrome_options, executable_path=str(driver_path))
            except Exception as e:
                raise e

        elif self.config.browser.lower() == "electron":
            driver_path = os.path.join(os.path.dirname(__file__), r'drivers\\windows\\electron\\chromedriver.exe')
            chrome_options = ChromeOpt()
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument(f'--environment="{self.config.environment}"')
            chrome_options.add_argument(f'--url="{self.config.url}"')
            chrome_options.add_argument(f'--program="{self.config.start_program}"')
            chrome_options.add_argument('--quiet')
            chrome_options.binary_location = self.config.electron_binary_path
            self.driver = webdriver.Chrome(options=chrome_options, executable_path=driver_path)

        if not self.config.browser.lower() == "electron":
            if self.config.headless:
                self.driver.set_window_position(0, 0)
                self.driver.set_window_size(1366, 768)
            else:
                self.driver.maximize_window()

            self.get_url()

        if self.driver:
            window_size = self.driver.get_window_size()
            logger().info(f"Browser maximized to {window_size['width']}x{window_size['height']}")
            if window_size and not 768 in range(window_size['height'], window_size['height']+ 40):
                logger().info(f"Screen size is different from default used in headless mode")
        self.wait = WebDriverWait(self.driver, self.config.time_out)

        if not self.config.poui:
            if not self.config.skip_environment:
                self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, start_program)))

            self.driver.execute_script("app.resourceManager.storeValue('x:\\\\automation.ini.general.tir', 1)")

    def get_url(self, url=None):

        get_url = False
        start_selector = ".po-page-login-info-field .po-input, #fieldsetStartProg, [name=cGetUser], [name=cUser]"

        url = self.config.url if not url else url

        num_of_trying = 1
        while not get_url and num_of_trying <= 5:
            self.driver.get(url)
            try:
                if self.config.json_data['POUILogin'] and 'StartProg' in url:
                    time.sleep(3)
                    self.switch_to_iframe()

                WebDriverWait(self.driver, int(self.config.time_out / num_of_trying)).until(EC.presence_of_element_located((By.CSS_SELECTOR, start_selector)))
                self.driver.switch_to.default_content()
                logger().info("Page is ready!")
                get_url = True
                break
            except:
                num_of_trying += 1
                logger().info(f"Loading took too much time! num_of_trying: {str(num_of_trying)}")

    def TearDown(self):
        """
        Closes the webdriver and ends the test case.

        Usage:

        >>> #Calling the method
        >>> oHelper.TearDown()
        """
        self.driver.close()

    def execution_flow(self):
        """

        Method that is responsible to control log flow in an execution 

        :return:
        """
        if self.search_stack("TearDown") or (self.search_stack("setUpClass") and self.restart_counter == 3):
            self.last_test_case = "setUpClass"
            self.finish_testcase()
        elif (self.log.get_testcase_stack() in list(map(lambda x: x._testMethodName, self.log.list_of_testcases()))) and \
                self.log.get_testcase_stack() not in self.test_case:
            if self.last_test_case is not None and (self.log.get_testcase_stack() != self.last_test_case) and \
                    (self.last_test_case not in self.log.finish_testcase):
                self.finish_testcase()
            self.start_testcase()

    def start_testcase(self):
        """

        Method that starts testcase time and testcase info.

        :return:
        """

        self.log.testcase_initial_time = datetime.today()
        self.test_case.append(self.log.get_testcase_stack())
        self.last_test_case = self.log.get_testcase_stack()
        self.log.ct_method, self.log.ct_number = self.log.ident_test()
        logger().info(f"Starting TestCase: {self.log.ct_method} CT: {self.log.ct_number}")

    def finish_testcase(self):
        """

        Method that is responsable to finish testcase and send the log and execution time of testcase.

        :return:
        """
        if self.last_test_case not in self.log.finish_testcase:
            logger().info(f"Finishing TestCase: {self.log.ct_method} CT: {self.log.ct_number}")
            self.log.testcase_seconds = self.log.set_seconds(self.log.testcase_initial_time)
            self.log.generate_result(self.expected, self.message)
            self.log.finish_testcase.append(self.last_test_case if not self.log.get_testcase_stack() == "setUpClass" else self.log.get_testcase_stack())
            logger().info(self.log.testcase_seconds)

    def return_combo_index(self, combo, option):
        """

        :param combo:
        :param option:
        :return:
        """

        for i, j in enumerate(combo.options):
            if not j.get_attribute('disabled') and j.text.lower().strip() == option.lower().strip():
                return i

    def return_iframe(self, selector):
        """
        """
        self.driver.switch_to_default_content()
        return self.driver.find_elements_by_css_selector(selector)

    def webapp_shadowroot(self, shadow_root=True):
        """
        [Internal]
        """

        if not shadow_root:
            return False

        if self.webapp_version:
            return self.webapp_version

        current_ver = ''

        for i in range(3):
            endtime = time.time() + self.config.time_out
            while time.time() < endtime and not current_ver:
                try:
                    current_ver = self.driver.execute_script("return app.VERSION")
                    if current_ver:
                        logger().debug(f'Webapp: {current_ver}')
                        current_ver = re.sub(r'\.(.*)', '', current_ver)
                        self.webapp_version = int(current_ver) >= 8
                        return self.webapp_version
                except:
                    current_ver = None

            if not current_ver:
                self.driver.close()
                self.Start()

        if not current_ver:
            self.log_error('Can\'t find WebApp Version' )

    def find_shadow_element(self, term, objects):

        elements = None

        script = f"return arguments[0].shadowRoot.querySelectorAll('{term}')"
        try:
            elements = self.driver.execute_script(script, objects)
        except:
            pass
        return elements if elements else None

    def sc_query(self, service):

        success = False
        endtime = time.time() + self.config.time_out
        while time.time() < endtime and not success:
            try:
                logger().debug(f'Trying start: {service} service.')
                os.system(f'SC QUERY {service} | FIND "RUNNING"')
                stdout = subprocess.check_output(f'SC QUERY {service} | FIND "RUNNING"', shell=True, text=True).split(':')
                success = True if list(filter(lambda x: 'RUNNING' in x, stdout)) else False
                if success:
                    logger().debug(f'{service} is running')
            except:
                logger().debug(f'{service} is being started')
                os.system(f'net start {service}')

    def create_folder(self, path):

        try:
            os.makedirs(path)
        except OSError:
            pass

    def filling_input_by_locator(self, selector, locator, value, shadow_root):

        tag_name = None

        element = self.find_by_locator(locator, selector, shadow_root=shadow_root)

        if element:
            try:
                if element.find_element('css selector', 'select'):
                    element = element.find_element('css selector', 'select')
            except:
                pass

            tag_name = element.tag_name

            self.set_element_focus(element)

            if tag_name == 'select':
                self.filling_select(element, value, locator=True)
            else:
                ActionChains(self.driver).send_keys(Keys.HOME).perform()
                ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
                ActionChains(self.driver).move_to_element(element).send_keys_to_element(element, value).perform()

    def filling_select(self, element, value, locator):

        self.select_combo(element, value, locator=locator)

    def click_by_locator(self, selector, locator, right_click, shadow_root):

        element = self.find_by_locator(locator, selector, shadow_root=shadow_root)

        self.set_element_focus(element)

        self.click(element, right_click=right_click)

    def find_by_locator(self, locator, selector, shadow_root):

        element = None

        self.wait.until(EC.element_to_be_clickable((locator, selector)))

        endtime = time.time() + self.config.time_out
        while time.time() < endtime and not element:
            logger().info(f"Looking for element: '{selector}'")

            if self.webapp_shadowroot(shadow_root=shadow_root):
                element = next(iter(
                    self.find_shadow_element('input, select, button', self.driver.find_element(locator, selector))))
            else:
                element = self.driver.find_element(locator, selector)

        if not element:
            self.log_error(f"Element {element} doesn't found")

        return element

    def return_active_element(self, elements, reverse):

        if isinstance(elements, list):
            filtered_element = list(filter(
                lambda x: self.return_wa_tab_page(x) or self.return_file_picker(x) if x else None,
                elements))

            if filtered_element:
                non_blocked_element = self.return_non_blocked_elements(filtered_element, reverse)
                active_element = list(filter(
                    lambda x: self.return_wa_tab_page(x) and 'active' in x.find_parent(
                        'wa-tab-page').attrs or self.return_file_picker(x), non_blocked_element))
                if active_element:
                    return active_element
                else:
                    return self.return_non_blocked_elements(elements, reverse)
            else:
                return self.return_non_blocked_elements(elements, reverse)
        else:
            return elements

    def return_wa_tab_page(self, element):

        if hasattr(element.find_parent('wa-tab-page'), 'attrs'):
            return element

    def return_file_picker(self, element):

        if element.find('wa-file-picker'):
            return element

    def return_non_blocked_elements(self, elements, reverse):

        non_blocked_elements = list(filter(lambda x: hasattr(x, 'attr') and 'blocked' not in x.attrs, elements))

        if isinstance(non_blocked_elements, list):
            if len(non_blocked_elements) > 1:
                if reverse:
                    return non_blocked_elements[::-1]
            return non_blocked_elements
        else:
            return non_blocked_elements

    def replace_slash(self, path):

        slash = r"/" if (sys.platform.lower() == "linux") else r"\\"

        pattern = re.compile(r'[\/\\]')

        if pattern.findall(path):
            return pattern.sub(slash, path)
