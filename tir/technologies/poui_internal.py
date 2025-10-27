import re
import time
import pandas as pd
import inspect
import os
import random
import uuid
from functools import reduce
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
import tir.technologies.core.enumerations as enum
from tir.technologies.core.log import Log
from tir.technologies.core.config import ConfigLoader
from tir.technologies.core.language import LanguagePack
from tir.technologies.core.third_party.xpath_soup import xpath_soup
from tir.technologies.core.psutil_info import system_info
from tir.technologies.core.base import Base
from tir.technologies.core.numexec import NumExec
from math import sqrt, pow
from selenium.common.exceptions import *
from datetime import datetime
from tir.technologies.core.logging_config import logger
import pathlib
import json

class PouiInternal(Base):
    """
    Internal implementation of POUI class.

    This class contains all the methods defined to run Selenium Interface Tests on POUI.

    Internal methods should have the **[Internal]** tag and should not be accessible to the user.

    :param config_path: The path to the config file. - **Default:** "" (empty string)
    :type config_path: str
    :param autostart: Sets whether TIR should open browser and execute from the start. - **Default:** True
    :type: bool

    Usage:

    >>> # Inside __init__ method in Webapp class of main.py
    >>> def __init__(self, config_path="", autostart=True):
    >>>     self.__webapp = PouiInternal(config_path, autostart)
    """
    def __init__(self, config_path="", autostart=True):
        """
        Definition of each global variable:

        base_container: A variable to contain the layer element to be used on all methods.

        grid_check: List with fields from a grid that must be checked in the next LoadGrid call.

        grid_counters: A global counter of grids' last row to be filled.

        grid_input: List with fields from a grid that must be filled in the next LoadGrid call.

        used_ids: Dictionary of element ids and container already captured by a label search.
        """
        webdriver_exception = None

        try:
            super().__init__(config_path, autostart)
        except WebDriverException as e:
            webdriver_exception = e

        self.containers_selectors = {
            "SetButton" : ".tmodaldialog,.ui-dialog",
            "GetCurrentContainer": ".tmodaldialog",
            "AllContainers": "body,.tmodaldialog,.ui-dialog",
            "ClickImage": ".tmodaldialog",
            "BlockerContainers": ".tmodaldialog,.ui-dialog",
            "Containers": ".tmodaldialog,.ui-dialog"
        }
        self.base_container = ".tmodaldialog"

        self.grid_check = []
        self.grid_counters = {}
        self.grid_input = []
        self.down_loop_grid = False
        self.num_exec = NumExec()
        self.restart_counter = 0
        self.used_ids = {}
        self.tss = False
        self.restart_coverage = True

        self.parameters = []
        self.backup_parameters = []
        self.tree_base_element = ()
        self.tmenu_screen = None
        self.grid_memo_field = False
        self.range_multiplier = None
        
        if not Base.driver:
            Base.driver = self.driver

        if not Base.wait:
            Base.wait = self.wait

        if not Base.errors:
            Base.errors = self.errors

        if not self.config.smart_test and self.config.issue:
            self.check_mot_exec()

        if webdriver_exception:
            message = f"Wasn't possible execute Start() method: {next(iter(webdriver_exception.msg.split(':')), None)}"
            self.restart_counter = 3
            self.log_error(message)
            self.assertTrue(False, message)

    def service_process_bat_file(self):
        """
        [Internal]
        This method creates a batfile in the root path to kill the process and its children.
        """
        if self.config.smart_test:
            with open("firefox_task_kill.bat", "w", ) as firefox_task_kill:
                firefox_task_kill.write(f"taskkill /f /PID {self.driver.service.process.pid} /T")

    def program_screen(self, initial_program="", environment="", coverage=False):
        """
        [Internal]

        Fills the first screen of Protheus with the first program to run and the environment to connect.

        :param initial_program: The initial program to load
        :type initial_program: str
        :param environment: The environment to connect
        :type environment: str

        Usage:

        >>> # Calling the method
        >>> self.program_screen("SIGAADV", "MYENVIRONMENT")
        """
        if coverage:
            self.open_url_coverage(url=self.config.url, initial_program=initial_program, environment=self.config.environment)
        else:
            try_counter = 0
            self.wait_element(term='#inputStartProg', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
            self.wait_element(term='#inputEnv', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
            soup = self.get_current_DOM()

            logger().info("Filling Initial Program")
            start_prog_element = next(iter(soup.select("#inputStartProg")), None)
            if start_prog_element is None:
                self.restart_counter += 1
                message = "Couldn't find Initial Program input element."
                self.log_error(message)
                raise ValueError(message)

            start_prog = lambda: self.soup_to_selenium(start_prog_element)
            start_prog_value = self.get_web_value(start_prog())
            endtime = time.time() + self.config.time_out
            while (time.time() < endtime and (start_prog_value.strip() != initial_program.strip())):

                if try_counter == 0:
                    start_prog = lambda: self.soup_to_selenium(start_prog_element)
                else:
                    start_prog = lambda: self.soup_to_selenium(start_prog_element.parent)

                self.set_element_focus(start_prog())
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.HOME).key_up(Keys.CONTROL).perform()
                ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys(
                    Keys.END).key_up(Keys.CONTROL).key_up(Keys.SHIFT).perform()
                self.send_keys(start_prog(), initial_program)
                start_prog_value = self.get_web_value(start_prog())
                try_counter += 1 if(try_counter < 1) else -1
            
            if (start_prog_value.strip() != initial_program.strip()):
                self.restart_counter += 1
                message = "Couldn't fill Program input element."
                self.log_error(message)
                raise ValueError(message)

            logger().info("Filling Environment")
            env_element = next(iter(soup.select("#inputEnv")), None)
            if env_element is None:
                self.restart_counter += 1
                message = "Couldn't find Environment input element."
                self.log_error(message)
                raise ValueError(message)

            env = lambda: self.soup_to_selenium(env_element)
            env_value = self.get_web_value(env())
            endtime = time.time() + self.config.time_out
            try_counter = 0
            while (time.time() < endtime and (env_value.strip() != self.config.environment.strip())):

                if try_counter == 0:
                    env = lambda: self.soup_to_selenium(env_element)
                else:
                    env = lambda: self.soup_to_selenium(env_element.parent)

                self.set_element_focus(env())
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.HOME).key_up(Keys.CONTROL).perform()
                ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys(
                    Keys.END).key_up(Keys.CONTROL).key_up(Keys.SHIFT).perform()
                self.send_keys(env(), self.config.environment)
                env_value = self.get_web_value(env())
                try_counter += 1 if(try_counter < 1) else -1

            if (env_value.strip() != self.config.environment.strip()):
                self.restart_counter += 1
                message = "Couldn't fill Environment input element."
                self.log_error(message)
                raise ValueError(message)

            button = self.driver.find_element(By.CSS_SELECTOR, ".button-ok")
            self.click(button)

    def user_screen(self, admin_user = False):
        """
        [Internal]

        Fills the user login screen of Protheus with the user and password located on config.json.

        Usage:

        >>> # Calling the method
        >>> self.user_screen()
        """
        user_text = self.config.user_cfg if  admin_user and self.config.user_cfg else self.config.user
        password_text = self.config.password_cfg if admin_user and self.config.password_cfg else self.config.password

        if self.config.smart_test and admin_user and not self.config.user_cfg :
            user_text = "admin"
            password_text = "1234"

        self.twebview_context = True
        if not self.wait_element_timeout(term=".po-page-login-info-field .po-input",
        scrap_type=enum.ScrapType.CSS_SELECTOR, timeout=self.config.time_out * 3,main_container='body'):
            self.reload_user_screen()

        self.set_multilanguage()

        try_counter = 0
        soup = self.get_current_DOM()

        logger().info("Filling User")

        try:
            user_element = next(iter(soup.select(".po-page-login-info-field .po-input")), None)
        
            if user_element is None:
                self.restart_counter += 1
                message = "Couldn't find User input element."
                self.log_error(message)
                raise ValueError(message)

            user = lambda: self.soup_to_selenium(user_element)
            user_value = self.get_web_value(user())
        except AttributeError as e:
            self.log_error(str(e))
            raise AttributeError(e)
            
        endtime = time.time() + self.config.time_out
        while (time.time() < endtime and (user_value.strip() != user_text.strip())):

            if try_counter == 0:
                user = lambda: self.soup_to_selenium(user_element)
            else:
                user = lambda: self.soup_to_selenium(user_element.parent)

            self.set_element_focus(user())
            self.wait_until_to(expected_condition="element_to_be_clickable", element = user_element, locator = By.XPATH, timeout=True)
            self.double_click(user())
            self.send_keys(user(), user_text)
            self.send_keys(user(), Keys.TAB)
            user_value = self.get_web_value(user())
            try_counter += 1 if(try_counter < 1) else -1

        if (user_value.strip() != user_text.strip()):
            self.restart_counter += 1
            message = "Couldn't fill User input element."
            self.log_error(message)
            raise ValueError(message)

        logger().info("Filling Password")
        
        password_element = next(iter(soup.select(".po-input-icon-right")), None)

        if password_element is None:
            self.restart_counter += 1
            message = "Couldn't find User input element."
            self.log_error(message)
            raise ValueError(message)

        password = lambda: self.soup_to_selenium(password_element)
        password_value = self.get_web_value(password())
        endtime = time.time() + self.config.time_out
        try_counter = 0
        while (time.time() < endtime and not password_value.strip() and self.config.password != ''):

            if try_counter == 0:
                password = lambda: self.soup_to_selenium(password_element)
            else:
                password = lambda: self.soup_to_selenium(password_element.parent)

            self.set_element_focus(password())
            self.wait_until_to( expected_condition="element_to_be_clickable", element = password_element, locator = By.XPATH, timeout=True)
            self.click(password())
            self.send_keys(password(), Keys.HOME)
            self.send_keys(password(), password_text)
            self.send_keys(password(), Keys.TAB)
            password_value = self.get_web_value(password())
            try_counter += 1 if(try_counter < 1) else -1
        
        if not password_value.strip() and self.config.password != '':
            self.restart_counter += 1
            message = "Couldn't fill User input element."
            self.log_error(message)
            raise ValueError(message)

        button_element = next(iter(list(filter(lambda x: self.language.enter in x.text, soup.select("button")))), None)
        if button_element is None:
            self.restart_counter += 1
            message = "Couldn't find Enter button."
            self.log_error(message)
            raise ValueError(message)

        button = lambda: self.driver.find_element(By.XPATH, xpath_soup(button_element))
        self.click(button())

    def reload_user_screen(self):
        """
        [Internal]

        Refresh the page - retry load user_screen
        """

        self.driver_refresh()

        if self.config.coverage:
            self.driver.get(f"{self.config.url}/?StartProg=CASIGAADV&A={self.config.initial_program}&Env={self.config.environment}")

        if not self.config.skip_environment and not self.config.coverage:
            self.program_screen(self.config.initial_program)

        self.wait_element_timeout(term="[name='cGetUser'] > input",
         scrap_type=enum.ScrapType.CSS_SELECTOR, timeout = self.config.time_out , main_container='body')

    def environment_screen(self, change_env=False):
        """
        [Internal]

        Fills the environment screen of Protheus with the values passed on the Setup method.
        Used to fill the fields triggered by the ChangeEnvironment method as well.

        :param change_env: Boolean if the method is being called by ChangeEnvironment. - **Default:** False
        :type change_env: bool

        Usage:

        >>> # Calling the method
        >>> self.environment_screen()
        """
        if not self.config.date:
            self.config.date = datetime.today().strftime('%d/%m/%Y')

        if change_env:
            label = self.language.confirm
            container = "body"
        else:
            label = self.language.enter
            container = ".twindow"

        self.wait_element(term=".po-datepicker", main_container='body', scrap_type=enum.ScrapType.CSS_SELECTOR)

        logger().info("Filling Date")
        base_dates = self.web_scrap(term=".po-datepicker", main_container='body', scrap_type=enum.ScrapType.CSS_SELECTOR)

        if len(base_dates) > 1:
            base_date = base_dates.pop()
        else:
            base_date = next(iter(base_dates), None)
            
        if base_date is None:
            self.restart_counter += 1
            message = "Couldn't find Date input element."
            self.log_error(message)
            raise ValueError(message)

        date = lambda: self.soup_to_selenium(base_date)
        base_date_value = ''
        endtime = time.time() + self.config.time_out
        while (time.time() < endtime and (base_date_value.strip() != self.config.date.strip())):
            self.double_click(date())
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.HOME).key_up(Keys.CONTROL).perform()
            ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys(
                Keys.END).key_up(Keys.CONTROL).key_up(Keys.SHIFT).perform()
            self.send_keys(date(), self.config.date)
            base_date_value = self.get_web_value(date())
            ActionChains(self.driver).send_keys(Keys.TAB).perform()

        logger().info("Filling Group")
        group_elements = self.web_scrap(term=self.language.group, main_container='body',scrap_type=enum.ScrapType.TEXT)
        group_element = next(iter(group_elements))
        group_element = group_element.find_parent('pro-company-lookup')
        group_element = next(iter(group_element.select('input')), None)

        if group_element is None:
            self.restart_counter += 1
            message = "Couldn't find Group input element."
            self.log_error(message)
            raise ValueError(message)
        
        group = lambda: self.soup_to_selenium(group_element)
        group_value = ''
        endtime = time.time() + self.config.time_out
        while (time.time() < endtime and (group_value.strip() != self.config.group.strip())):
            self.double_click(group())
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.HOME).key_up(Keys.CONTROL).perform()
            ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys(
                Keys.END).key_up(Keys.CONTROL).key_up(Keys.SHIFT).perform()
            self.send_keys(group(), self.config.group)
            group_value = self.get_web_value(group())
            ActionChains(self.driver).send_keys(Keys.TAB).perform()

        logger().info("Filling Branch")
        branch_elements = self.web_scrap(term=self.language.branch, main_container='body',scrap_type=enum.ScrapType.TEXT)
        branch_element = next(iter(branch_elements))
        branch_element = branch_element.find_parent('pro-branch-lookup')
        branch_element = next(iter(branch_element.select('input')), None)

        if branch_element is None:
            self.restart_counter += 1
            message = "Couldn't find Branch input element."
            self.log_error(message)
            raise ValueError(message)

        branch = lambda: self.soup_to_selenium(branch_element)
        branch_value = ''
        endtime = time.time() + self.config.time_out
        while (time.time() < endtime and (branch_value.strip() != self.config.branch.strip())):
            self.double_click(branch())
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.HOME).key_up(Keys.CONTROL).perform()
            ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys(
                Keys.END).key_up(Keys.CONTROL).key_up(Keys.SHIFT).perform()
            self.send_keys(branch(), self.config.branch)
            branch_value = self.get_web_value(branch())
            ActionChains(self.driver).send_keys(Keys.TAB).perform()

        logger().info("Filling Environment")
        environment_elements = self.web_scrap(term=self.language.environment, main_container='body',scrap_type=enum.ScrapType.TEXT)
        environment_element = next(iter(environment_elements))
        environment_element = environment_element.find_parent('pro-system-module-lookup')
        environment_element = next(iter(environment_element.select('input')), None)

        if environment_element is None:
            self.restart_counter += 1
            message = "Couldn't find Module input element."
            self.log_error(message)
            raise ValueError(message)


        env = lambda: self.soup_to_selenium(environment_element)
        enable = env().is_enabled()

        if enable:
            env_value = self.get_web_value(env())
            endtime = time.time() + self.config.time_out
            while (time.time() < endtime and env_value != self.config.module):
                self.double_click(env())
                self.send_keys(env(), Keys.HOME)
                self.send_keys(env(), self.config.module)
                env_value = self.get_web_value(env())
                ActionChains(self.driver).send_keys(Keys.TAB).perform()
                time.sleep(1)
                self.close_warning_screen()

        buttons = self.filter_displayed_elements(self.web_scrap(label, scrap_type=enum.ScrapType.MIXED, optional_term="button", main_container="body"), True)
        button_element = next(iter(buttons), None) if buttons else None

        if button_element  and hasattr(button_element, "name") and hasattr(button_element, "parent"):
            button = lambda: self.driver.find_element(By.XPATH, xpath_soup(button_element))
            self.click(button())
        elif not change_env:
            self.restart_counter += 1
            message = f"Couldn't find {label} button."
            self.log_error(message)
            raise ValueError(message)

        self.driver.switch_to.default_content()
            
    def ChangeEnvironment(self, date="", group="", branch="", module=""):
        """
        Clicks on the change environment area of Protheus Webapp and
        fills the environment screen.

        :param date: The date to fill on the environment screen. - **Default:** "" (empty string)
        :type date: str
        :param group: The group to fill on the environment screen. - **Default:** "" (empty string)
        :type group: str
        :param branch: The branch to fill on the environment screen. - **Default:** "" (empty string)
        :type branch: str
        :param module: The module to fill on the environment screen. - **Default:** "" (empty string)
        :type module: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.ChangeEnvironment(date="13/11/2018", group="T1", branch="D MG 01 ")
        """
        if date:
            self.config.date = date
        if group:
            self.config.group = group
        if branch:
            self.config.branch = branch
        if module:
            self.config.module = module

        element = self.change_environment_element_home_screen()
        if element:
            self.click(self.driver.find_element(By.XPATH, xpath_soup(element)))
            self.environment_screen(True)
        else:
            self.log_error("Change Envirioment method did not find the element to perform the click or the element was not visible on the screen.")

        self.close_warning_screen()
        self.close_coin_screen()
        
    def change_environment_element_home_screen(self):
        """
        [Internal]

        This method wait the element to perform ChangeEnvirionmentm return a soup element.

        Usage:

        >>> # Calling the method:
        >>> self.change_environment_element_home_screen()
        """
        endtime = time.time() + self.config.time_out
        while time.time() < endtime:

            if self.wait_element_timeout(term=self.language.change_environment, scrap_type=enum.ScrapType.MIXED, timeout = 1, optional_term="button", main_container="body"):
                return next(iter(self.web_scrap(term=self.language.change_environment, scrap_type=enum.ScrapType.MIXED, optional_term="button", main_container="body")), None)
            elif self.wait_element_timeout(term=".tpanel > .tpanel > .tbutton", scrap_type=enum.ScrapType.CSS_SELECTOR, timeout = 1, main_container="body"):
                tbuttons = self.filter_displayed_elements(self.web_scrap(term=".tpanel > .tpanel > .tbutton", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body"), True)
                element = next(iter(list(filter(lambda x: 'TOTVS' in x.text, tbuttons))), None)
                if element:
                    return element

        return False

    def ChangeUser(self, user, password, initial_program = "", date='', group='', branch=''):
        """
        Change the user then init protheus on home page.

        :param initial_program: The initial program to load. - **Default:** "" (previous initial_program)
        :type initial_program: str
        :param date: The date to fill on the environment screen. - **Default:** "" (previous date)
        :type date: str
        :param group: The group to fill on the environment screen. - **Default:** "previous date group"
        :type group: str
        :param branch: The branch to fill on the environment screen. - **Default:** "previous branch"
        :type branch: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.ChangeUser("userTest", "a", "SIGAFAT", "18/08/2018", "T1", "D MG 01 ")
        >>> #------------------------------------------------------------------------
        >>> # Calling the method:
        >>> oHelper.ChangeUser(user="user08", password="8" )
        >>> #------------------------------------------------------------------------
        """
        if not user and not password:
            self.log_error("You must enter a user and a password to use ChangeUser!")
            return

        initial_program = self.config.initial_program if not self.config.initial_program else initial_program
        date = self.config.date if not self.config.date else date
        group = self.config.group if not self.config.group else group
        branch = self.config.branch if not self.config.branch else branch

        self.config.user = user
        self.config.password = password

        self.driver.refresh()
        logger().info(f"Change to the user: {user}")
        self.Setup(initial_program, date, group, branch)

    def close_modal(self):
        """
        [Internal]

        This method closes the modal in the opening screen.

        Usage:

        >>> # Calling the method:
        >>> self.close_modal()
        """
        soup = self.get_current_DOM()
        modals = self.zindex_sort(soup.select(".tmodaldialog"), True)
        if modals and self.element_exists(term=".tmodaldialog .tbrowsebutton", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body", check_error = False):
            buttons = modals[0].select(".tbrowsebutton")
            if buttons:
                close_button = next(iter(list(filter(lambda x: x.text == self.language.close, buttons))), None)
                time.sleep(0.5)
                selenium_close_button = lambda: self.driver.find_element(By.XPATH, xpath_soup(close_button))
                if close_button:
                    try:
                        self.wait_until_to( expected_condition = "element_to_be_clickable", element = close_button , locator = By.XPATH)
                        self.click(selenium_close_button())
                    except:
                        pass

    def close_coin_screen(self):
        """
        [Internal]

        Closes the coin screen.

        Usage:

        >>> # Calling the method:
        >>> self.close_coin_screen()
        """
        soup = self.get_current_DOM()
        modals = self.zindex_sort(soup.select(".tmodaldialog"), True)
        if modals and self.element_exists(term=self.language.coins, scrap_type=enum.ScrapType.MIXED,
         optional_term=".tmodaldialog > .tpanel > .tsay", main_container="body", check_error = False):
            self.SetButton(self.language.confirm)

    def close_coin_screen_after_routine(self):
        """
        [internal]
        This method is responsible for closing the "coin screen" that opens after searching for the routine
        """
        endtime = time.time() + self.config.time_out

        self.wait_element_timeout(term=".workspace-container", scrap_type=enum.ScrapType.CSS_SELECTOR,
            timeout = self.config.time_out, main_container="body", check_error = False)

        tmodaldialog_list = []

        while(time.time() < endtime and not tmodaldialog_list):
            try:
                soup = self.get_current_DOM()
                tmodaldialog_list = soup.select('.tmodaldialog')

                self.wait_element_timeout(term=self.language.coins, scrap_type=enum.ScrapType.MIXED,
                 optional_term=".tsay", timeout=10, main_container = "body", check_error = False)
                 
                tmodal_coin_screen = next(iter(self.web_scrap(term=self.language.coins, scrap_type=enum.ScrapType.MIXED,
                    optional_term=".tmodaldialog > .tpanel > .tsay", main_container="body", check_error = False, check_help = False)), None)

                if tmodal_coin_screen and tmodal_coin_screen in tmodaldialog_list:
                    tmodaldialog_list.remove(tmodal_coin_screen.parent.parent)
                    
                self.close_coin_screen()
                
            except Exception as e:
                logger().exception(str(e))

    def close_warning_screen(self):
        """
        [Internal]
        Closes the warning screen.

        Usage:
        >>> # Calling the method:
        >>> self.close_warning_screen()
        """
        soup = self.get_current_DOM()
        modals = self.zindex_sort(soup.select(".ui-dialog"), True)
        if modals and self.element_exists(term=self.language.warning, scrap_type=enum.ScrapType.MIXED,
         optional_term=".ui-dialog > .ui-dialog-titlebar", main_container="body", check_error = False):
            self.set_button_x()

    def set_button_x(self, position=1, check_error=True):
        position -= 1
        term_button = ".ui-button.ui-dialog-titlebar-close[title='Close'], img[src*='fwskin_delete_ico.png'], img[src*='fwskin_modal_close.png']"
        wait_button = self.wait_element(term=term_button, scrap_type=enum.ScrapType.CSS_SELECTOR, position=position, check_error=check_error)
        soup = self.get_current_DOM() if not wait_button else self.get_current_container()

        close_list = soup.select(term_button)
        if not close_list:
            self.log_error(f"Element not found")
        if len(close_list) < position+1:
            self.log_error(f"Element x position: {position} not found")
        if position == 0:
            element_soup = close_list.pop()
        else:
            element_soup = close_list.pop(position)
        element_selenium = self.soup_to_selenium(element_soup)
        self.scroll_to_element(element_selenium)
        self.wait_until_to( expected_condition = "element_to_be_clickable", element = element_soup, locator = By.XPATH )
        
        self.click(element_selenium)
        
    def close_warning_screen_after_routine(self):
        """
        [internal]
        This method is responsible for closing the "warning screen" that opens after searching for the routine
        """
        endtime = time.time() + self.config.time_out

        self.wait_element_timeout(term=".workspace-container", scrap_type=enum.ScrapType.CSS_SELECTOR,
            timeout = self.config.time_out, main_container="body", check_error = False)

        uidialog_list = []

        while(time.time() < endtime and not uidialog_list):
            try:
                soup = self.get_current_DOM()
                uidialog_list = soup.select('.ui-dialog')

                self.wait_element_timeout(term=self.language.warning, scrap_type=enum.ScrapType.MIXED,
                 optional_term=".ui-dialog-titlebar", timeout=10, main_container = "body", check_error = False)
                 
                tmodal_warning_screen = next(iter(self.web_scrap(term=self.language.warning, scrap_type=enum.ScrapType.MIXED,
                    optional_term=".ui-dialog > .ui-dialog-titlebar", main_container="body", check_error = False, check_help = False)), None)

                if tmodal_warning_screen and tmodal_warning_screen in uidialog_list:
                    uidialog_list.remove(tmodal_warning_screen.parent.parent)
                    
                self.close_warning_screen()
                
            except Exception as e:
                logger().exception(str(e))

    def close_resolution_screen(self):
        """
        [Internal]

        Closes the Alert of resolution screen.

        Usage:

        >>> # Calling the method:
        >>> self.close_resolution_screen()
        """
        endtime = time.time() + self.config.time_out
        container = self.get_current_container()
        while (time.time() < endtime and container and self.element_exists(term="img[src*='fwskin_alert_ico.png']", scrap_type=enum.ScrapType.CSS_SELECTOR)):
            self.SetButton(self.language.close)
            time.sleep(1)
        self.wait_element_timeout(term="[name='cGetUser']", scrap_type=enum.ScrapType.CSS_SELECTOR, timeout = self.config.time_out, main_container='body')

    def set_log_info(self):
        """
        [Internal]
        Fills the log information needed by opening the About page.

        Usage:

        >>> # Calling the method:
        >>> self.set_log_info()
        """
        self.SetLateralMenu(self.language.menu_about, save_input=False)
        self.wait_element(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        self.wait_until_to(expected_condition = "presence_of_all_elements_located", element = ".tmodaldialog", locator= By.CSS_SELECTOR)

        soup = self.get_current_DOM()
        labels = list(soup.select(".tmodaldialog .tpanel .tsay"))

        release_element = next(iter(filter(lambda x: x.text.startswith("Release"), labels)), None)
        database_element = next(iter(filter(lambda x: x.text.startswith("Top DataBase"), labels)), None)
        lib_element = next(iter(filter(lambda x: x.text.startswith("Versão da lib"), labels)), None)
        build_element = next(iter(filter(lambda x: x.text.startswith("Build"), labels)), None)

        if release_element:
            release = release_element.text.split(":")[1].strip()
            self.log.release = release
            self.log.version = release.split(".")[0]

        if database_element:
            self.log.database = database_element.text.split(":")[1].strip()

        if build_element:
            self.log.build_version = build_element.text.split(":")[1].strip()

        if lib_element:
            self.log.lib_version = lib_element.text.split(":")[1].strip()

        self.SetButton(self.language.close)

    def set_log_info_tss(self):

        self.log.country = self.config.country
        self.log.execution_id = self.config.execution_id
        self.log.issue = self.config.issue

        label_element = None

        self.SetButton("Sobre")
        
        soup = self.get_current_DOM()
        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not label_element):
            soup = self.get_current_DOM()
            label_element = soup.find_all("label", string="Versão do TSS:") 
               
        if not label_element:
            raise ValueError("SetupTss fail about screen not found")
            
        labels = list(map(lambda x: x.text, soup.select("label")))
        label = labels[labels.index("Versão do TSS:")+1]
        self.log.release = next(iter(re.findall(r"[\d.]*\d+", label)), None)

        self.SetButton('x')

    def get_language(self):
        """
        [Internal]

        Gets the current language of the html.

        :return: The current language of the html.
        :rtype: str

        Usage:

        >>> # Calling the method:
        >>> language = self.get_language()
        """
        language = self.driver.find_element(By.CSS_SELECTOR, "html").get_attribute("lang")
        return language

    def search_element_position(self, field, position=1, input_field=True, direction=None):
        """
        [Internal]
        Usage:
        >>> # Calling the method
        >>> self.search_element_position(field)
        """
        endtime = (time.time() + self.config.time_out)
        label = None
        elem = []
        term=".tget, .tcombobox, .tmultiget"
        position-=1

        if not input_field:
            term=".tsay"

        try:
            while( time.time() < endtime and not label ):
                container = self.get_current_container()
                labels = container.select("label")
                labels_displayed = list(filter(lambda x: self.element_is_displayed(x) ,labels))
                labels_list  = list(filter(lambda x: re.search(r"^{}([^a-zA-Z0-9]+)?$".format(re.escape(field)),x.text) ,labels_displayed))
                labels_list_filtered = list(filter(lambda x: 'th' not in self.element_name(x.parent.parent) , labels_list))
                if labels_list_filtered and len(labels_list_filtered) -1 >= position:
                    label = labels_list_filtered[position]

            if not label:
                self.log_error(f"Label: '{field}'' wasn't found.")

            self.wait_until_to( expected_condition = "element_to_be_clickable", element = label, locator = By.XPATH )
            
            container_size = self.get_element_size(container['id'])
            # The safe values add to postion of element
            width_safe, height_safe = self.width_height(container_size)

            label_s  = lambda:self.soup_to_selenium(label)
            xy_label =  self.driver.execute_script('return arguments[0].getPosition()', label_s())
            list_in_range = self.web_scrap(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR) 
            list_in_range = list(filter(lambda x: self.element_is_displayed(x) and 'readonly' not in self.soup_to_selenium(x).get_attribute("class") or 'readonly focus' in self.soup_to_selenium(x).get_attribute("class"), list_in_range))

            if not input_field:
                list_in_range = list(filter(lambda x: field.strip().lower() != x.text.strip().lower(), list_in_range))

            position_list = list(map(lambda x:(x[0], self.get_position_from_bs_element(x[1])), enumerate(list_in_range)))
            position_list = self.filter_by_direction(xy_label, width_safe, height_safe, position_list, direction)
            distance      = self.get_distance_by_direction(xy_label, position_list, direction)
            if distance:
                elem          = min(distance, key = lambda x: x[1])
                elem          = list_in_range[elem[0]]

            if not elem:
                self.log_error(f"Label '{field}' wasn't found")
            return elem
            
        except AssertionError as error:
            raise error
        except Exception as error:
            logger().exception(str(error))
            self.log_error(str(error))

    def width_height(self, container_size):

        if not self.range_multiplier:
            width_safe  = (container_size['width']  * 0.015)
            height_safe = (container_size['height'] * 0.01)
        elif self.range_multiplier == 1:
            width_safe  = (container_size['width']  * 0.03)
            height_safe = (container_size['height'] * 0.02)
        else:
            width_safe  = (container_size['width']  * (0.015 * self.range_multiplier))
            height_safe = (container_size['height'] * (0.01 * self.range_multiplier))

        return (width_safe, height_safe)


    def get_position_from_bs_element(self,element):
        """
        [Internal]

        """
        selenium_element = self.soup_to_selenium(element)
        position = self.driver.execute_script('return arguments[0].getPosition()', selenium_element)
        return position

    def get_distance(self,label_pos,element_pos):
        """
        [internal]

        """
        return sqrt((pow(element_pos['x'] - label_pos['x'], 2)) + pow(element_pos['y'] - label_pos['y'],2))

    def get_element_size(self, id):
        """
        Internal
        Return Height/Width

        """
        script = f'return document.getElementById("{id}").offsetHeight;'
        height = self.driver.execute_script(script)
        script = f'return document.getElementById("{id}").offsetWidth;'
        width  = self.driver.execute_script(script)
        return {'height': height, 'width':width}

    def get_distance_x(self, x_label, x_element):
        """
        [Internal]

        """

        return (x_element['x'] - x_label['x'])

    def get_distance_y(self, y_label, y_element):
        """
        [Internal]

        """

        return (y_element['y'] - y_label['y'])

    def filter_by_direction(self, xy_label, width_safe, height_safe, position_list, direction):
        """
        [Internal]
        
        """

        if not direction:

            return list(filter(lambda xy_elem: (
                        xy_elem[1]['y'] + width_safe >= xy_label['y'] and xy_elem[1]['x'] + height_safe >= xy_label['x']),
                        position_list))

        elif direction.lower() == 'right':
            return list(filter(
                lambda xy_elem: (xy_elem[1]['x'] > xy_label['x']) and (xy_elem[1]['y'] >= xy_label['y'] - height_safe and xy_elem[1]['y'] <= xy_label[
                    'y'] + height_safe), position_list))
        
        elif direction.lower() == 'down':
            return list(filter(
                lambda xy_elem: (xy_elem[1]['y'] > xy_label['y']) and (xy_elem[1]['x'] + width_safe >= xy_label['x'] and
                               xy_elem[1]['x'] - width_safe <= xy_label['x']), position_list))

    def get_distance_by_direction(self, xy_label, position_list, direction):
        
        if not direction:
            get_distance = self.get_distance
        
        elif direction.lower() == 'right':
            get_distance = self.get_distance_x

        elif direction.lower() == 'down':
            get_distance = self.get_distance_y
        
        return list(map(lambda x: (x[0], get_distance(xy_label, x[1])), position_list))

    def SetValue(self, field, value, grid=False, grid_number=1, ignore_case=True, row=None, name_attr=False, position = 1, check_value=None, grid_memo_field=False, range_multiplier=None, direction=None):
        """
        Sets value of an input element.
        
        .. note::
            Attention on the grid use the field mask.
         
        :param field: The field name or label to receive the value
        :type field: str
        :param value: The value to be inputted on the element.
        :type value: str or bool
        :param grid: Boolean if this is a grid field or not. - **Default:** False
        :type grid: bool
        :param grid_number: Grid number of which grid should be inputted when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int
        :param ignore_case: Boolean if case should be ignored or not. - **Default:** True
        :type ignore_case: bool
        :param check_value: Boolean ignore input check - **Default:** True
        :type name_attr: bool
        :param row: Row number that will be filled
        :type row: int
        :param name_attr: Boolean if search by Name attribute must be forced. - **Default:** False
        :type name_attr: bool
        :param grid_memo_field: Boolean if this is a memo grid field. - **Default:** False
        :type grid_memo_field: bool
        :param range_multiplier: Integer value that refers to the distance of the label from the input object. The safe value must be between 1 to 10.
        :type range_multiplier: int
        :param direction: Desired direction to search for the element from a label, currently accepts right and down.
        :type direction: str

        Usage:

        >>> # Calling method to input value on a field:
        >>> oHelper.SetValue("A1_COD", "000001")
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field from a label text and looking an input field for a specific direction:
        >>> oHelper.SetValue("Codigo", "000001", direction='right')
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field that is a grid:
        >>> oHelper.SetValue("Client", "000001", grid=True)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Calling method to checkbox value on a field that is a grid:
        >>> oHelper.SetValue('Confirmado?', True, grid=True)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Calling method to checkbox value on a field that isn't a grid:
        >>> oHelper.SetValue('', True, name_attr=True, position=1)
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field that is on the second grid of the screen:
        >>> oHelper.SetValue("Order", "000001", grid=True, grid_number=2)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field that is a grid *Will not attempt to verify the entered value. Run only once.* :
        >>> oHelper.SetValue("Order", "000001", grid=True, grid_number=2, check_value = False)
        >>> oHelper.LoadGrid()
        """

        check_value = self.check_value(check_value)

        if grid_memo_field:
            self.grid_memo_field = True

        if range_multiplier:
            self.range_multiplier = range_multiplier
            
        if grid:
            self.input_grid_appender(field, value, grid_number - 1, row = row, check_value = check_value)
        elif isinstance(value, bool):
            self.click_check_radio_button(field, value, name_attr, position)
        else:
            self.input_value(field, value, ignore_case, name_attr, position, check_value, direction)

    def check_value(self, check_value):

        if check_value != None:
            check_value = check_value
        elif self.config.check_value != None:
            check_value = self.config.check_value
        else:
            check_value = True

        return check_value

    def get_field(self, field, name_attr=False, position=1, input_field=True, direction=None):
        """
        [Internal]

        This method decides if field would be found by either it's name or by it's label.
        Internal method of input_value and CheckResult.

        :param field: Field name or field label to be searched
        :type field: str
        :param name_attr: Boolean if search by Name attribute must be forced. - **Default:** False
        :type name_attr: bool

        :return: Field element
        :rtype: Beautiful Soup object

        Usage:

        >>> # Calling the method:
        >>> element1 = self.get_field("A1_COD")
        >>> element2 = self.get_field("Product")
        """
        endtime = time.time() + self.config.time_out
        element =  None

        if re.match(r"\w+(_)", field) or name_attr:
            position -= 1

        while(time.time() < endtime and element is None):
            if re.match(r"\w+(_)", field) or name_attr:
                element_list = self.web_scrap(f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR)
                if element_list and len(element_list) -1 >= position:
                    element = element_list[position]
            else:
                element = next(iter(self.web_scrap(field, scrap_type=enum.ScrapType.TEXT, label=True, input_field=input_field, direction=direction, position=position)), None)

        if element:
            element_children = next((x for x in element.contents if self.element_name(x) in ["input", "select"]), None)
            return element_children if element_children is not None else element
        else:
            self.log_error("Element wasn't found.")

    def get_web_value(self, element):
        """
        [Internal]

        Gets the current value or text of element.

        :param element: The element to get value or text from
        :type element: Selenium object

        :return: The value or text of passed element
        :rtype: str

        Usage:

        >>> # Calling the method:
        >>> current_value = self.get_web_value(selenium_field_element)
        """
        self.switch_to_iframe()
        if element.tag_name == "div":
            element_children = element.find_element(By.CSS_SELECTOR, "div > * ")
            if element_children is not None:
                element = element_children

        if element.tag_name == "label":
            web_value = element.get_attribute("text")
            if not web_value:
                web_value = element.text.strip()
        elif element.tag_name == "select":
            current_select = 0 if element.get_attribute('value') == '' else int(element.get_attribute('value')) 
            selected_element = element.find_elements(By.CSS_SELECTOR, "option")[current_select]
            web_value = selected_element.text
        else:
            web_value = element.get_attribute("value")

        return web_value

    def CheckResult(self, field, user_value, po_component, position):
        """
        Checks if a field has the value the user expects.

        :param field: The field or label of a field that must be checked.
        :type field: str
        :param user_value: The value that the field is expected to contain.
        :type user_value: str
        :param po_component:  POUI component name that you want to check content on screen
        :type po_component: str

        Usage:

        >>> # Calling method to check a value of a field:
        >>> oHelper.CheckResult("Código", "000001", 'po-input')

        """

        if po_component == 'po-input':
            po_component = "[class*='po-input']"
            input_field = self.return_input_element(field, position, term=po_component)
            input_field_element = lambda: self.soup_to_selenium(input_field, twebview=True)
            if input_field_element():
                current_value = self.get_web_value(input_field_element())

        self.log_result(field, user_value, current_value)

    def log_result(self, field, user_value, captured_value):
        """
        [Internal]

        Logs the result of comparison between user value and captured value.

        :param field: The field whose values would be compared
        :type field: str
        :param user_value: The value the user expects
        :type user_value: str
        :param captured_value: The value that was captured on the screen
        :type captured_value: str

        Usage:

        >>> # Calling the method:
        >>> self.log_result("A1_COD", "000001", "000001")
        """
        txtaux = ""
        message = ""

        if user_value != captured_value:
            message = self.create_message([txtaux, field, user_value, captured_value], enum.MessageType.INCORRECT)

        self.compare_field_values(field, user_value, captured_value, message)

    def GetValue(self, field, grid=False, line=1, grid_number=1, grid_memo_field=False):
        """
        Gets the current value or text of element.

        :param field: The field or label of a field that must be checked.
        :type field: str
        :param grid: Boolean if this is a grid field or not. - **Default:** False
        :type grid: bool
        :param line: Grid line that contains the column field to be checked.- **Default:** 1
        :type line: int
        :param grid_number: Grid number of which grid should be checked when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int
        :param grid_memo_field: Boolean if this is a memo grid field. - **Default:** False
        :type grid_memo_field: bool

        Usage:

        >>> # Calling the method:
        >>> current_value = oHelper.GetValue("A1_COD")
        """
        endtime = time.time() + self.config.time_out
        element = None

        if grid_memo_field:
            self.grid_memo_field = True

        if not grid:
            while ( (time.time() < endtime) and (not element) and (not hasattr(element, "name")) and (not hasattr(element, "parent"))):           
                element = self.get_field(field)
                if ( hasattr(element, "name") and hasattr(element, "parent") ):
                    selenium_element = lambda: self.driver.find_element(By.XPATH, xpath_soup(element))
                    value = self.get_web_value(selenium_element())
        else:
            field_array = [line-1, field, "", grid_number-1]
            x3_dictionaries = self.create_x3_tuple()
            value = self.check_grid(field_array, x3_dictionaries, get_value=True)

        if ( not value ):
            self.log_error("GetValue element is none")
       
        return value


    def restart(self):
        """
        [Internal]

        Restarts the Protheus Webapp and fills the initial screens.

        Usage:

        >>> # Calling the method:
        >>> self.restart()
        """
        webdriver_exception = None

        try:
            if self.restart_counter == 2:
                logger().info("Closing the Browser")
                self.driver.close()
                logger().info("Starting the Browser")
                self.Start()
            else:
                logger().info("Refreshing the Browser")
                self.driver_refresh()
        except WebDriverException as e:
            webdriver_exception = e

        if webdriver_exception:
            message = f"Wasn't possible execute Start() method: {next(iter(webdriver_exception.msg.split(':')), None)}"
            self.assertTrue(False, message)
        
        if self.config.coverage and self.config.initial_program != ''  and self.restart_counter < 3:
            self.open_url_coverage(url=self.config.url, initial_program=self.config.initial_program, environment=self.config.environment)

        try:
            self.driver.switch_to_alert().accept()
        except:
            pass

        if self.config.initial_program != ''  and self.restart_counter < 3:

            if not self.config.skip_environment and not self.config.coverage:
                self.program_screen(self.config.initial_program)
            self.user_screen()
            self.environment_screen()

            endtime = time.time() + self.config.time_out
            while(time.time() < endtime and not self.element_exists(term=".tmenu", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")):
                self.close_warning_screen()
                self.close_modal()

            
            if self.config.routine:
                if self.config.routine_type.lower() == 'setlateralmenu':
                    self.SetLateralMenu(self.config.routine, save_input=False)
                elif self.config.routine_type.lower() == 'program':
                    self.set_program(self.config.routine)

    def driver_refresh(self):
        """
        [Internal]

        Refresh the driver.

        Usage:

        >>> # Calling the method:
        >>> self.driver_refresh()
        """
        if self.config.smart_test or self.config.debug_log:
            logger().info("Driver Refresh")

        self.driver.refresh()
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.F5).key_up(Keys.CONTROL).perform()

    def Finish(self):
        """
        Exit the protheus Webapp.

        Usage:

        >>> # Calling the method.
        >>> oHelper.Finish()
        """
        element = None
        text_cover = None
        string = "Aguarde... Coletando informacoes de cobertura de codigo."
        timeout = 900
        click_counter = 1
        
        if self.config.coverage:
            endtime = time.time() + timeout

            while((time.time() < endtime) and (not element or not text_cover)):

                ActionChains(self.driver).key_down(Keys.CONTROL).perform()
                ActionChains(self.driver).key_down('q').perform()
                ActionChains(self.driver).key_up(Keys.CONTROL).perform()

                element = self.wait_element_timeout(term=self.language.finish, scrap_type=enum.ScrapType.MIXED,
                 optional_term=".tsay", timeout=5, step=1, main_container="body", check_error = False)

                if element:
                    if self.click_button_finish(click_counter):                        
                        self.WaitShow(string)
                        text_cover = self.search_text(selector=".tsay", text=string)
                        if text_cover:
                            logger().info(string)
                            timeout = endtime - time.time()
                            if timeout > 0:
                                self.wait_element_timeout(term=string, scrap_type=enum.ScrapType.MIXED,
                                optional_term=".tsay", timeout=timeout, step=0.1, main_container="body", check_error = False)
                    click_counter += 1
                    if click_counter > 3:
                        click_counter = 1
        else:
            endtime = time.time() + self.config.time_out
            while( time.time() < endtime and not element ):

                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('q').key_up(Keys.CONTROL).perform()
                soup = self.get_current_DOM()
                element = soup.find_all(text=self.language.finish)

                self.wait_element_timeout(term=self.language.finish, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay", timeout=5, step=0.5, main_container="body")

            if not element:
                logger().warning("Warning method finish use driver.refresh. element not found")

            self.driver_refresh() if not element else self.SetButton(self.language.finish)

    def click_button_finish(self, click_counter=None):
        """
        [internal]

        This method is reponsible to click on button finish

        """
        button = None
        listButtons = []
        try:
            soup = self.get_current_DOM()
            listButtons = soup.select('button')
            button = next(iter(list(filter(lambda x: x.text == self.language.finish ,listButtons ))), None)
            if button:
                button_element = lambda : self.soup_to_selenium(button)            
                self.scroll_to_element(button_element())
                self.set_element_focus(button_element())
                if self.click(button_element(), click_type=enum.ClickType(click_counter)):
                    return True
                else:
                    return False
        except Exception as e:
            logger().exception(f"Warning Finish method exception - {str(e)}")
            return False

    def LogOff(self):
        """
        Logs out of the Protheus Webapp.

        Usage:

        >>> # Calling the method.
        >>> oHelper.LogOff()
        """
        element = None
        text_cover = None
        string = "Aguarde... Coletando informacoes de cobertura de codigo."
        timeout = 900
        click_counter = 1
        
        if self.config.coverage:
            endtime = time.time() + timeout

            while((time.time() < endtime) and (not element or not text_cover)):

                ActionChains(self.driver).key_down(Keys.CONTROL).perform()
                ActionChains(self.driver).key_down('q').perform()
                ActionChains(self.driver).key_up(Keys.CONTROL).perform()

                element = self.wait_element_timeout(term=self.language.logOff, scrap_type=enum.ScrapType.MIXED,
                 optional_term=".tsay", timeout=5, step=1, main_container="body", check_error = False)

                if element:
                    if self.click_button_logoff(click_counter):                        
                        text_cover = self.search_text(selector=".tsay", text=string)
                        if text_cover:
                            logger().info(string)
                            timeout = endtime - time.time()
                            if timeout > 0:
                                self.wait_element_timeout(term=string, scrap_type=enum.ScrapType.MIXED,
                                optional_term=".tsay", timeout=timeout, step=0.1, main_container="body", check_error = False)
                    click_counter += 1
                    if click_counter > 3:
                        click_counter = 1
        else:
            endtime = time.time() + self.config.time_out
            while( time.time() < endtime and not element ):

                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('q').key_up(Keys.CONTROL).perform()
                soup = self.get_current_DOM()
                element = soup.find_all(text=self.language.logOff)

                self.wait_element_timeout(term=self.language.logOff, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay", timeout=5, step=0.5, main_container="body")

            if not element:
                logger().warning("Warning method finish use driver.refresh. element not found")

            self.driver_refresh() if not element else self.SetButton(self.language.logOff)

    def click_button_logoff(self, click_counter=None):
        """
        [internal]

        This method is reponsible to click on button finish

        """
        button = None
        listButtons = []
        try:
            soup = self.get_current_DOM()
            listButtons = soup.select('button')
            button = next(iter(list(filter(lambda x: x.text == self.language.logOff ,listButtons ))), None)
            if button:
                button_element = lambda : self.soup_to_selenium(button)            
                self.scroll_to_element(button_element())
                self.set_element_focus(button_element())
                if self.click(button_element(), click_type=enum.ClickType(click_counter)):
                    return True
                else:
                    return False
        except Exception as e:
            logger().exception(f"Warning Finish method exception - {str(e)}")
            return False


    def web_scrap(self, term, scrap_type=enum.ScrapType.TEXT, optional_term=None, label=False, main_container=None, check_error=True, check_help=True, input_field=True, direction=None, position=1, twebview=False):
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
        :param position: Position which element is located. - **Default:** 1
        :type position: int

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

        twebview = True if not self.config.poui else False

        try:
            endtime = time.time() + self.config.time_out
            container =  None
            while(time.time() < endtime and container is None):
                soup = self.get_current_DOM(twebview)

                if check_error:
                    self.search_for_errors(check_help)

                if self.config.log_file:
                    with open(f"{term + str(scrap_type) + str(optional_term) + str(label) + str(main_container) + str(random.randint(1, 101)) }.txt", "w") as text_file:
                        text_file.write(f" HTML CONTENT: {str(soup)}")

                container_selector = self.base_container
                if (main_container is not None):
                    container_selector = main_container

                containers = self.zindex_sort(soup.select(container_selector), reverse=True) 

                if self.base_container in container_selector:
                    container = self.containers_filter(containers)

                container = next(iter(containers), None) if isinstance(containers, list) else container

            if container is None:
                raise Exception(f"Web Scrap couldn't find container - term: {term}")

            if (scrap_type == enum.ScrapType.TEXT):
                if label:
                    return self.find_label_element(term, container, input_field=input_field, direction=direction, position=position)
                elif not re.match(r"\w+(_)", term):
                    return self.filter_label_element(term, container) if self.filter_label_element(term, container) else []
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
        except AssertionError:
            raise
        except Exception as e:
            self.log_error(str(e))

    def search_for_errors(self, check_help=True):
        """
        [Internal]
        Searches for errors and alerts in the screen.
        Usage:
        >>> # Calling the method:
        >>> self.search_for_errors()
        """
        endtime = time.time() + self.config.time_out
        soup = None
        top_layer = None

        while(time.time() < endtime and not soup):
            soup = self.get_current_DOM()

        try:   
            if not soup:
                self.log_error("Search for erros couldn't find DOM")
            message = ""
            top_layer = next(iter(self.zindex_sort(soup.select(".tmodaldialog, .ui-dialog"), True)), None)

        except AttributeError as e:
            self.log_error(f"Search for erros couldn't find DOM\n Exception: {str(e)}")

        if not top_layer:
            return None

        icon_alert = next(iter(top_layer.select("img[src*='fwskin_info_ico.png']")), None)
        icon_error_log = next(iter(top_layer.select("img[src*='openclosing.png']")), None)
        if (not icon_alert or not check_help) and not icon_error_log:
            return None

        if icon_alert:
            label = reduce(lambda x,y: f"{x} {y}", map(lambda x: x.text.strip(), top_layer.select(".tsay label")))
            if self.language.messages.error_msg_required in label:
                message = self.language.messages.error_msg_required
            elif "help:" in label.lower() and self.language.problem in label:
                message = label
            else:
                return None

        elif icon_error_log:
            label = reduce(lambda x,y: f"{x} {y}", map(lambda x: x.text.strip(), top_layer.select(".tsay label")))
            textarea = next(iter(top_layer.select("textarea")), None)
            textarea_value = self.driver.execute_script(f"return arguments[0].value", self.driver.find_element(By.XPATH, xpath_soup(textarea)))

            error_paragraphs = textarea_value.split("\n\n")
            error_message = f"Error Log: {error_paragraphs[0]} - {error_paragraphs[1]}" if len(error_paragraphs) > 2 else label
            message = error_message.replace("\n", " ")

            button = next(iter(filter(lambda x: self.language.details.lower() in x.text.lower(),top_layer.select("button"))), None)
            self.click(self.driver.find_element(By.XPATH, xpath_soup(button)))
            time.sleep(1)
        self.restart_counter += 1
        self.log_error(message)

    def get_function_from_stack(self):
        """
        [Internal]

        Gets the function name that called the Webapp class from the call stack.

        Usage:

        >>> # Calling the method:
        >>> self.get_function_from_stack()
        """
        stack_item = next(iter(filter(lambda x: x.filename == self.config.routine, inspect.stack())), None)
        return stack_item.function if stack_item and stack_item.function else "function_name"

    def create_message(self, args, message_type=enum.MessageType.CORRECT):
        """
        [Internal]

        Returns default messages used all throughout the class based on input parameters.

        Each message type has a different number of placeholders to be passed as a list through args parameter:

        Correct Message = *"{} Value of field {} is correct!"* - **2 placeholders**

        Incorrect Message = *"{} Value expected for field \"{}\" ({}) is not equal to what was found ({})."* - **3 placeholders**

        Disabled Message = *"{} Field \"{}\" is disabled."* - **2 placeholders**

        AssertError Message = *"Failed: Value expected for field {}: \"{}\" is different from what was found \"{}\"."* - **2 placeholders**

        :param args: A list of strings to be replaced in each message.
        :type args: List of str
        :param message_type: Enum of which message type should be created. - **Default:** enum.MessageType.Correct
        :type message_type: enum.MessageType

        Usage:

        >>> # Calling the method:
        >>> message = self.create_message([txtaux, field, user_value, captured_value], enum.MessageType.INCORRECT)
        """
        correctMessage = "{} Value of field {} is correct!"
        incorrectMessage = "{} Value expected for field \"{}\" ({}) is not equal to what was found ({})."
        disabledMessage = "{} Field \"{}\" is disabled."
        assertErrorMessage = "Failed: Value expected for field {}: \"{}\" is different from what was found \"{}\"."

        if message_type == enum.MessageType.INCORRECT:
            return incorrectMessage.format(args[0], args[1], args[2], args[3])
        elif message_type == enum.MessageType.DISABLED:
            return disabledMessage.format(args[0], args[1])
        elif message_type == enum.MessageType.ASSERTERROR:
            return assertErrorMessage.format(args[0], args[1], args[2])
        else:
            return correctMessage.format(args[0], args[1])

    def element_exists(self, term, scrap_type=enum.ScrapType.TEXT, position=0, optional_term="", main_container=".body", check_error=True, twebview=True):
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

        element_list = []
        containers = None

        if scrap_type == enum.ScrapType.SCRIPT:
            return bool(self.driver.execute_script(term))
        elif (scrap_type != enum.ScrapType.MIXED and not (scrap_type == enum.ScrapType.TEXT and not re.match(r"\w+(_)", term))):
            selector = term
            if scrap_type == enum.ScrapType.CSS_SELECTOR:
                by = By.CSS_SELECTOR
            elif scrap_type == enum.ScrapType.XPATH:
                by = By.XPATH
            elif scrap_type == enum.ScrapType.TEXT:
                by = By.CSS_SELECTOR
                selector = f"[name*='{term}']"

            if scrap_type != enum.ScrapType.XPATH:
                soup = self.get_current_DOM(twebview)

                if not soup:
                    return False

                if check_error:
                    self.search_for_errors()

                container_selector = self.base_container
                if (main_container is not None):
                    container_selector = main_container

                try:
                    containers_soup = soup.select(container_selector)

                    if not containers_soup:
                        return False

                    containers = self.zindex_sort(containers_soup, reverse=True)

                except Exception as e:
                    logger().exception(f"Warning element_exists containers exception:\n {str(e)}")
                    pass

                if self.base_container in container_selector:
                    container = self.containers_filter(containers)

                container = next(iter(containers), None) if isinstance(containers, list) else containers

                if not container:
                    return False

                try:
                    container_element = self.driver.find_element(By.XPATH, xpath_soup(container))
                except:
                    return False
            else:
                container_element = self.driver
            try:
                if twebview:
                    self.switch_to_iframe()
                    return self.driver.find_element(By.CSS_SELECTOR, selector)
                else:
                    element_list = container_element.find_elements(by, selector)
            except:
                return None
        else:
            if scrap_type == enum.ScrapType.MIXED:
                selector = optional_term
            else:
                selector = "div"

        if not element_list:
            element_list = self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container, check_error=check_error, twebview=twebview)
            if not element_list:
                return None

        if position == 0:
            return len(element_list) > 0
        else:
            return len(element_list) >= position

    def children_element_count(self, element_selector, children_selector):
        """
        [Internal]

        Returns the count of elements of a certain CSS Selector that exists within a certain element located also via CSS Selector.

        :param element_selector: The selector to find the first element.
        :type element_selector: str
        :param children_selector: The selector to find the children elements inside of the first element.
        :type children_selector: str

        :return: The count of elements matching the children_selector inside of element_selector.
        :rtype: int

        Usage:

        >>> # Calling the method:
        >>> self.children_element_count(".tmenu", ".tmenuitem")
        """
        script = f"return document.querySelector('{element_selector}').querySelectorAll('{children_selector}').length;"
        return int(self.driver.execute_script(script))

    def WaitHide(self, string, timeout=None, throw_error = True):
        """
        Search string that was sent and wait hide the element.

        :param string: String that will hold the wait.
        :type string: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitHide("Processing")
        """
        logger().info("Waiting processing...")

        if not timeout:
            timeout = 1200
        
        endtime = time.time() + timeout
        while(time.time() < endtime):

            element = None
            
            element = self.web_scrap(term=string, scrap_type=enum.ScrapType.MIXED, optional_term="po-loading-overlay", main_container = self.containers_selectors["AllContainers"], check_help=False)
            element = next(iter(element), None)
            if hasattr(element, "attrs") and "hidden" in element.attrs:
                element = []

            if not element:
                return
            if endtime - time.time() < 1180:
                time.sleep(0.5)

        if not throw_error:
            return False
        else:
            self.log_error(f"Element {string} not found")

    def WaitShow(self, string, timeout=None, throw_error = True):
        """
        Search string that was sent and wait show the elements.

        :param string: String that will hold the wait.
        :type string: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitShow("Processing")
        """
        logger().info(f"Waiting show text '{string}'...")

        if not timeout:
            timeout = 1200

        endtime = time.time() + timeout
        while(time.time() < endtime):

            element = None

            element = self.web_scrap(term=string, scrap_type=enum.ScrapType.MIXED, optional_term="po-loading-overlay, span, .po-modal-title", main_container = self.containers_selectors["AllContainers"], check_help=False)

            if element:
                return element

            if endtime - time.time() < 1180:
                time.sleep(0.5)

        if not throw_error:
            return False
        else:
            self.log_error(f"Element {string} not found")

    def WaitProcessing(self, itens, timeout=None):
        """
        Uses WaitShow and WaitHide to Wait a Processing screen

        :param itens: List of itens that will hold the wait.
        :type itens: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitProcessing("Processing")
        """
        if not timeout:
            timeout = 1200

        self.WaitShow(itens, timeout, throw_error = False)

        self.WaitHide(itens, timeout, throw_error = False)

    def wait_element_is_blocked(self, parent_id):
        """

        :param parent_id:
        :return:
        """

        logger().debug("Wait for element to be blocked...")

        element = False

        endtime = time.time() + 10

        while(time.time() < endtime and not element):

            tpanels = self.get_current_container().select(".tpanel")

            if tpanels:

                tpanels_filtered = list(filter(lambda x: self.element_is_displayed(x), tpanels))

                element = next(iter(list(filter(lambda x: x.attrs["id"] == parent_id, tpanels_filtered))), None)

        if element:
            return  "readonly" in element.get_attribute_list("class") or "hidden"  in element.get_attribute_list("class")
        else:
            return False
    
    def wait_element_is_not_displayed(self, element_soup, timeout = 5 , step=0.3):
        """
        [Internal]

        Wait element.is_displayed() return false
        :param element_soup: The element soup.
        :type element_soup: BeautifulSoup object.
        :param timeout: The maximum amount of time of wait. - **Default:** 5.0
        :type timeout: float
        :param step: The amount of time each step should wait. - **Default:** 0.1
        :type step: float

        Usage:

        >>> # Calling the method:
        >>> self.wait_element_is_not_displayed(soup_element, 10, 0.5)
        """
        endtime = time.time() + timeout
        try:
            logger().debug('Waiting for element to disappear')
            while(self.element_is_displayed(element_soup) and time.time() <= endtime):
                time.sleep(step)
        except Exception:
            return

    def wait_element_is_focused(self, element_selenium = None, time_out = 5, step = 0.1):
        """
        [ Internal ]
        Wait element Lose focus
        """
        endtime = time.time() + time_out
        while( element_selenium and time.time() < endtime and self.switch_to_active_element() != element_selenium() ):
            time.sleep(step)

    def wait_element_is_not_focused(self, element_selenium = None, time_out = 5, step = 0.1):
        """
        [ Internal ]
        Wait element Lose focus
        """
        endtime = time.time() + time_out
        while( element_selenium and time.time() < endtime and self.switch_to_active_element() == element_selenium() ):
            time.sleep(step)

    def switch_to_active_element(self):
        """
        [Internal]
        Call switch_to_active_element method
        """
        try:
            return self.driver.switch_to.active_element
        except NoSuchElementException:
            return None
        except Exception as e:
            logger().debug(f"Warning switch_to.active_element exception : {str(e)}")
            return None

    def wait_element(self, term, scrap_type=enum.ScrapType.CSS_SELECTOR, presence=True, position=0, optional_term=None, main_container="body", check_error=True):
        """
        [Internal]

        Waits until the desired element is located on the screen.

        :param term: The first search term. A text or a selector.
        :type term: str
        :param scrap_type: The type of webscraping. - **Default:** enum.ScrapType.TEXT
        :type scrap_type: enum.ScrapType.
        :param presence: If the element should exist or not in the screen. - **Default:** False
        :type presence: bool
        :param position: If the element should exist at a specific position. e.g. The fourth button. - **Default:** 0
        :type position: int
        :param optional_term: The second search term. A selector used in MIXED webscraping. - **Default:** None
        :type optional_term: str
        :param main_container: The selector of a container element that has all other elements. - **Default:** None
        :type main_container: str

        Usage:

        >>> # Calling the method:
        >>> self.wait_element(term=".ui-button.ui-dialog-titlebar-close[title='Close']", scrap_type=enum.ScrapType.CSS_SELECTOR)
        """

        twebview = True if not self.config.poui else False

        endtime = time.time() + self.config.time_out
        if self.config.debug_log:
            logger().debug("Waiting for element")

        if presence:
            while (not self.element_exists(term, scrap_type, position, optional_term, main_container, check_error,
                                           twebview) and time.time() < endtime):
                time.sleep(0.1)
        else:
            while (self.element_exists(term, scrap_type, position, optional_term, main_container, check_error,
                                       twebview) and time.time() < endtime):
                time.sleep(0.1)

        if time.time() > endtime:
            if term == "[name='cGetUser']":
                self.close_resolution_screen()
            else:
                if ".ui-button.ui-dialog-titlebar-close[title='Close']" in term:
                    return False
                self.restart_counter += 1
                self.log_error(f"Element {term} not found!")

        presence_endtime = time.time() + 10
        if presence:

            if self.config.debug_log:
                logger().debug("Element found! Waiting for element to be displayed.")

            element = next(iter(self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container, check_error=check_error, twebview=twebview)), None)

            if element is not None:

                if twebview:
                    self.switch_to_iframe()

                sel_element = lambda:self.soup_to_selenium(element)
                sel_element_isdisplayed = False

                while(not sel_element_isdisplayed and time.time() < presence_endtime):
                    try:
                        if sel_element != None:
                            sel_element_isdisplayed = sel_element().is_displayed()
                        else:
                            sel_element = lambda:self.soup_to_selenium(element)
                        time.sleep(0.1)
                    except AttributeError:
                        pass
                    except StaleElementReferenceException:
                        pass


    def wait_element_timeout(self, term, scrap_type=enum.ScrapType.TEXT, timeout=5.0, step=0.1, presence=True, position=0, optional_term=None, main_container=".tmodaldialog,.ui-dialog, body", check_error=True):
        """
        [Internal]

        Waits until the desired element is located on the screen or until the timeout is met.

        :param term: The first search term. A text or a selector.
        :type term: str
        :param scrap_type: The type of webscraping. - **Default:** enum.ScrapType.TEXT
        :type scrap_type: enum.ScrapType.
        :param timeout: The maximum amount of time of wait. - **Default:** 5.0
        :type timeout: float
        :param timeout: The amount of time each step should wait. - **Default:** 0.1
        :type timeout: float
        :param presence: If the element should exist or not in the screen. - **Default:** False
        :type presence: bool
        :param position: If the element should exist at a specific position. e.g. The fourth button. - **Default:** 0
        :type position: int
        :param optional_term: The second search term. A selector used in MIXED webscraping. - **Default:** None
        :type optional_term: str
        :param main_container: The selector of a container element that has all other elements. - **Default:** None
        :type main_container: str

        Usage:

        >>> # Calling the method:
        >>> self.wait_element_timeout(term=button, scrap_type=enum.ScrapType.MIXED, optional_term="button", timeout=10, step=0.1)
        """
        success = False
        if presence:
            endtime = time.time() + timeout
            while time.time() < endtime:
                time.sleep(step)
                if self.element_exists(term, scrap_type, position, optional_term, main_container, check_error):
                    success = True
                    break
        else:
            endtime = time.time() + timeout
            while time.time() < endtime:
                time.sleep(step)
                if not self.element_exists(term, scrap_type, position, optional_term, main_container, check_error):
                    success = True
                    break

        if presence and success:
            if self.config.debug_log:
                logger().debug("Element found! Waiting for element to be displayed.")
            element = next(iter(self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container, check_error=check_error)), None)
            if element is not None:
                sel_element = lambda: self.driver.find_element(By.XPATH, xpath_soup(element))
                endtime = time.time() + timeout
                while(time.time() < endtime and not self.element_is_displayed(element)):
                    try:
                        time.sleep(0.1)
                        self.scroll_to_element(sel_element())
                        if(sel_element().is_displayed()):
                            break
                    except:
                        continue
        return success

    def get_selected_row(self, rows):
        """
        [Internal]

        From a list of rows, filter the selected one.

        :param rows: List of rows.
        :type rows: List of Beautiful Soup objects

        :return: The selected row.
        :rtype: Beautiful Soup object.

        Usage:

        >>> # Calling the method:
        >>> selected_row = self.get_selected_row(rows)
        """
        filtered_rows = list(filter(lambda x: len(x.select("td.selected-cell")), rows))
        if filtered_rows:
            return next(iter(filtered_rows))
        else:
            filtered_rows = list(filter(lambda x: "selected-row" == self.soup_to_selenium(x).get_attribute('class'), rows))
            if filtered_rows:
                return next(iter(list(filter(lambda x: "selected-row" == self.soup_to_selenium(x).get_attribute('class'), rows))), None)

    def try_send_keys(self, element_function, key, try_counter=0):
        """
        [Internal]

        Tries to send value to element using different techniques.
        Meant to be used inside of a loop.

        :param element_function: The function that returns the element that would receive the value.
        :type element_function: function object
        :param key: The value that would be sent to the element.
        :type key: str or selenium.webdriver.common.keys
        :param try_counter: This counter will decide which technique should be used. - **Default:** 0
        :type try_counter: int

        Usage:

        >>> # Calling the method:
        >>> self.try_send_keys(selenium_input, user_value, try_counter)
        """
        self.wait_until_to( expected_condition = "visibility_of", element = element_function )
        
        if try_counter == 0:
            element_function().send_keys(Keys.HOME)
            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
            element_function().send_keys(key)
        elif try_counter == 1:
            element_function().send_keys(Keys.HOME)
            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
            ActionChains(self.driver).move_to_element(element_function()).send_keys_to_element(element_function(), key).perform()
        else:
            element_function().send_keys(Keys.HOME)
            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
            ActionChains(self.driver).move_to_element(element_function()).send_keys(key).perform()

    def find_label_element(self, label_text, container= None, position = 1, input_field=True, direction=None):
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
        try:
            if container:
                elements = self.filter_label_element(label_text, container)
            if elements:
                for element in elements:
                    elem = self.search_element_position(label_text, position, input_field, direction)
                    if elem:
                        return elem

                    #Checking previous and next element:
                    next_sibling = element.find_next_sibling("div")
                    second_next_sibling = next_sibling.find_next_sibling("div")

                    previous_sibling = element.find_next_sibling("div")
                    second_previous_sibling = previous_sibling.find_next_sibling("div")

                    #If current element is tsay and next or second next element is tget or tcombobox => return tget or tcombobox
                    if (hasattr(element, "attrs") and "class" in element.attrs
                        and "tsay" in element.attrs["class"]
                        and (hasattr(next_sibling, "attrs") and "class" in next_sibling.attrs and "id" in next_sibling.attrs
                        and ("tget" in next_sibling.attrs["class"] or "tcombobox" in next_sibling.attrs["class"])
                        and next_sibling.attrs["id"] not in self.used_ids)
                        or (hasattr(second_next_sibling, "attrs") and "class" in second_next_sibling.attrs and "id" in second_next_sibling.attrs
                        and ("tget" in second_next_sibling.attrs["class"] or "tcombobox" in second_next_sibling.attrs["class"])
                        and second_next_sibling.attrs["id"] not in self.used_ids)):

                        if (("tget" in next_sibling.attrs["class"]
                                or "tcombobox" in next_sibling.attrs["class"])
                                and next_sibling.attrs["id"] not in self.used_ids):
                            self.used_ids[next_sibling.attrs["id"]] = container.attrs["id"]
                            return [next_sibling]
                        elif (("tget" in second_next_sibling.attrs["class"]
                                or "tcombobox" in second_next_sibling.attrs["class"])
                                and second_next_sibling.attrs["id"] not in self.used_ids):
                            self.used_ids[second_next_sibling.attrs["id"]] = container.attrs["id"]
                            return [second_next_sibling]
                        else:
                            return[]

                    #If current element is tsay and previous or second previous element is tget or tcombobox => return tget or tcombobox
                    elif (hasattr(element, "attrs") and "class" in element.attrs
                        and "tsay" in element.attrs["class"]
                        and (hasattr(previous_sibling, "attrs") and "class" in previous_sibling.attrs and "id" in previous_sibling.attrs
                        and ("tget" in previous_sibling.attrs["class"] or "tcombobox" in previous_sibling.attrs["class"])
                        and previous_sibling.attrs["id"] not in self.used_ids)
                        or (hasattr(second_previous_sibling, "attrs") and "class" in second_previous_sibling.attrs and "id" in second_previous_sibling.attrs
                        and ("tget" in second_previous_sibling.attrs["class"] or "tcombobox" in second_previous_sibling.attrs["class"])
                        and second_previous_sibling.attrs["id"] not in self.used_ids)):

                        if (("tget" in previous_sibling.attrs["class"]
                                or "tcombobox" in previous_sibling.attrs["class"])
                                and previous_sibling.attrs["id"] not in self.used_ids):
                            self.used_ids[previous_sibling.attrs["id"]] = container.attrs["id"]
                            return [previous_sibling]
                        elif (("tget" in second_previous_sibling.attrs["class"]
                                or "tcombobox" in second_previous_sibling.attrs["class"])
                                and second_previous_sibling.attrs["id"] not in self.used_ids):
                            self.used_ids[second_previous_sibling.attrs["id"]] = container.attrs["id"]
                            return [second_previous_sibling]
                        else:
                            return []

                    #If element is not tsay => return it
                    elif (hasattr(element, "attrs") and "class" in element.attrs
                        and "tsay" not in element.attrs["class"]):
                        return self.search_element_position(label_text)
                        
                #If label exists but there is no element associated with it => return empty list
                if not element:
                    return []
                else:
                    return self.search_element_position(label_text)
            else:
                return []
        except AttributeError:
            return self.search_element_position(label_text)
            
    def log_error(self, message, new_log_line=True, skip_restart=False):
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
        logger().warning(f"Warning log_error {message}")

        if self.config.coverage:
            self.coverage()

        if self.config.smart_test or self.config.debug_log:
            logger().debug(f"***System Info*** in log_error():")
            system_info()

        routine_name = self.config.routine if ">" not in self.config.routine else self.config.routine.split(">")[-1].strip()
        routine_name = routine_name if routine_name else "error"

        stack_item = self.log.get_testcase_stack()
        test_number = f"{stack_item.split('_')[-1]} -" if stack_item else ""
        log_message = f"{test_number} {message}"
        self.message = log_message
        self.expected = False
        self.log.seconds = self.log.set_seconds(self.log.initial_time)
        self.log.testcase_seconds = self.log.set_seconds(self.log.testcase_initial_time)
        self.log.ct_method, self.log.ct_number = self.log.ident_test()

        if self.config.new_log:
            self.execution_flow()

        proceed_action = lambda: (
                    (stack_item != "setUpClass") or (stack_item == "setUpClass" and self.restart_counter == 3))

        if self.config.screenshot and proceed_action() and stack_item not in self.log.test_case_log and self.driver:
            self.log.take_screenshot_log(self.driver, stack_item, test_number)

        if new_log_line and proceed_action():
            self.log.new_line(False, log_message)
        if proceed_action() and self.log.has_csv_condition():
            self.log.generate_log()
        if not self.config.skip_restart and len(self.log.list_of_testcases()) > 1 and self.config.initial_program != '':
            self.restart()
        elif self.config.coverage and self.config.initial_program != '':
            self.restart()
        else:            
            try:
                self.driver.close()
            except Exception as e:
                logger().exception(f"Warning Log Error Close {str(e)}")

        if self.restart_counter > 2:

            if self.config.num_exec and stack_item == "setUpClass" and self.log.checks_empty_line():
                if not self.num_exec.post_exec(self.config.url_set_end_exec, 'ErrorSetFimExec'):
                    self.restart_counter = 3
                    self.log_error(f"WARNING: Couldn't possible send num_exec to server please check log.")
                
            if (stack_item == "setUpClass") :
                try:
                    self.driver.close()
                except Exception as e:
                    logger().exception(f"Warning Log Error Close {str(e)}")

        if ((stack_item != "setUpClass") or (stack_item == "setUpClass" and self.restart_counter == 3)):
            if self.restart_counter >= 3:
                self.restart_counter = 0
            self.assertTrue(False, log_message)

    def filter_by_tooltip_value(self, element_list, expected_text):
        """
        [Internal]

        Filters elements by finding the tooltip value that is shown when mouseover event
        is triggered.

        :param element_list: The list to be filtered
        :type element_list: Beautiful Soup object list
        :param expected_text: The expected tooltip text.
        :type expected_text: str

        :return: The filtered list of elements.
        :rtype: Beautiful Soup object list

        Usage:

        >>> # Calling the method:
        >>> filtered_elements = self.filter_by_tooltip_value(my_element_list, "Edit")
        """

        for element in element_list:
            if self.check_element_tooltip(element, expected_text, contains=True):
                return element

    def check_element_tooltip(self, element, expected_text, contains=False):
        """
        [Internal]

        Internal method of ClickIcon.

        Fires the MouseOver event of an element, checks tooltip text, fires the MouseOut event and
        returns a boolean whether the tooltip has the expected text value or not.

        :param element: The target element object.
        :type element: BeautifulSoup object
        :param expected_text: The text that is expected to exist in button's tooltip.
        :type expected_text: str

        :return: Boolean value whether element has tooltip text or not.
        :rtype: bool

        Usage:

        >>> # Call the method:
        >>> has_add_text = self.check_element_tooltip(button_object, "Add")
        """

        has_text = False

        element_function = lambda: self.driver.find_element(By.XPATH, xpath_soup(element))
        self.switch_to_iframe()
        ActionChains(self.driver).move_to_element(element_function()).perform()
        tooltips = self.driver.find_elements(By.CSS_SELECTOR, "[class*=po-tooltip]")

        if not tooltips:
            tooltips = self.get_current_DOM().select("[class*=po-tooltip]")

        if tooltips:
            tooltips = list(filter(lambda x: x.is_displayed(), tooltips))

            if tooltips:
                has_text = (len(list(
                    filter(lambda x: expected_text.lower() in x.text.lower(), tooltips))) > 0 if contains else (
                        tooltips[0].text.lower() == expected_text.lower()))

        return has_text

    def assert_result(self, expected, script_message):
        """
        [Internal]

        Asserts the result based on the expected value.

        :param expected: Expected value
        :type expected: bool

        Usage :

        >>> #Calling the method:
        >>> self.assert_result(True)
        """
        assert_false = self.search_stack('AssertFalse')
        self.expected = expected
        log_message = f"{self.log.ident_test()[1]} - "
        self.log.seconds = self.log.set_seconds(self.log.initial_time)

        if self.grid_input or self.grid_check:
            self.log_error("Grid fields were queued for input/check but weren't added/checked. Verify the necessity of a LoadGrid() call.")

        if self.errors:
            
            if self.expected:
                for field_msg in self.errors:
                    log_message += (" " + field_msg)
            else:
                log_message = ""
            
            self.expected = not self.expected

        if self.expected:
            self.message = "" if not self.errors else log_message
            self.log.new_line(True, self.message)
        elif script_message:
            self.message = f"{log_message}{script_message}"
            self.log.new_line(False, self.message)
        else:
            self.message = self.language.assert_false_message if assert_false and not self.errors else log_message
            self.log.new_line(False, self.message)

        if self.log.has_csv_condition():
            self.log.generate_log()

        self.errors = []

        logger().info(self.message) if self.message else None
        
        if self.expected:
            self.assertTrue(True, "Passed")
        else:
            self.assertTrue(False, self.message)

        self.message = ""
            
    def containers_filter(self, containers):
        """
        [Internal]
        Filter and remove tsvg class an return a container_filtered
        
        Usage:

        >>> #Calling the method
        >>> containers = self.containers_filter(containers)
        """
        class_remove = "tsvg"
        container_filtered = []

        for container in containers:
            iscorrect = True
            container_class = list(filter(lambda x: "class" in x.attrs, container.select("div")))
            if list(filter(lambda x: class_remove in x.attrs['class'], container_class)):
                iscorrect = False
            if iscorrect:
                container_filtered.append(container)

        return container_filtered

    def filter_label_element(self, label_text, container):
        """
        [Internal]
        Filter and remove a specified character with regex, return only displayed elements if > 1.

        Usage:

        >>> #Calling the method
        >>> elements = self.filter_label_element(label_text, container)
        """
        
        elements = list(map(lambda x: self.find_first_div_parent(x), container.find_all(text=re.compile(f"^{re.escape(label_text)}" + r"([\s\?:\*\.]+)?"))))
        return list(filter(lambda x: self.element_is_displayed(x), elements)) if len(elements) > 1 else elements

    def filter_is_displayed(self, elements):
        """
        [Internal]
        Returns only displayed elements.

        Usage:

        >>> #Calling the method
        >>> elements = self.filter_is_displayed(elements)
        """
        return list(filter(lambda x: self.element_is_displayed(x), elements))

    def element_is_displayed(self, element):
        """
        [Internal]

        """
        self.switch_to_iframe()
        element_selenium = self.soup_to_selenium(element)
        if element_selenium:
            return element_selenium.is_displayed()
        else:
            return False

    def search_text(self, selector, text):
        """
        [Internal]
        Return a element based on text and selector.

        Usage:

        >>> #Calling the method
        >>> element = self.search_text(selector, text)
        """
        container = self.get_current_container()

        if container:
            container_selector = container.select(selector)

            if container_selector:
                self.wait_element_timeout(term=text, scrap_type=enum.ScrapType.MIXED,
                 optional_term=".tsay", timeout=10, step=1, main_container="body", check_error = False)

            return next(iter(list(filter(lambda x: text in re.sub(r"\t|\n|\r", " ", x.text), container_selector))), None)

    def pop_dict_itens(self, dict_, element_id):
        """
        [Internal]
        """
        new_dictionary = {k: v  for k, v in dict_.items() if v == element_id}

        for key in list(new_dictionary.keys()):
            dict_.pop(key)

        return dict_

    def get_program_name(self):
        """
        [Internal]
        """
        stack_item_splited = next(iter(map(lambda x: x.filename.split(self.replace_slash("\\")), filter(lambda x: "TESTSUITE.PY" in x.filename.upper() or "TESTCASE.PY" in x.filename.upper(), inspect.stack()))), None)

        if stack_item_splited:
            get_file_name = next(iter(list(map(lambda x: "TESTSUITE.PY" if "TESTSUITE.PY" in x.upper() else "TESTCASE.PY", stack_item_splited))))

            program_name = next(iter(list(map(lambda x: re.findall(fr"(\w+)(?:{get_file_name})", x.upper()), filter(lambda x: ".PY" in x.upper(), stack_item_splited)))), None)

            if program_name:
                return next(iter(program_name))
            else:
                return None
        else:
            return None

    def GetText(self, string_left="", string_right=""):
        """
        This method returns a string from modal based on the string in the left or right position that you send on parameter.

        If the string_left was filled then the right side content is return.

        If the string_right was filled then the left side content is return.

        If no parameter was filled so the full content is return.

        :param string_left: String of the left side of content.
        :type string_left: str
        :param string_right: String of the right side of content.
        :type string_right: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.GetText(string_left="Left Text", string_right="Right Text")
        >>> oHelper.GetText(string_left="Left Text")
        >>> oHelper.GetText()
        """

        return self.get_text(string_left, string_right)

    def get_text(self, string_left, string_right):
        """

        :param string:
        :return:
        """
        if string_left:
            string = string_left
        else:
            string = string_right

        if string:
            self.wait_element(string)

        container = self.get_current_container()

        labels = container.select('label')

        label = next(iter(list(filter(lambda x: string.lower() in x.text.lower(), labels))))

        return self.get_text_position(label.text, string_left, string_right)

    def get_text_position(self, text="", string_left="", string_right=""):
        """

        :param string_left:
        :param srting_right:
        :return:
        """
        if string_left and string_right:
            return text[len(string_left):text.index(string_right)].strip()
        elif string_left:
            return text[len(string_left):].strip()
        elif string_right:
            return text[:-len(string_right)].strip()
        else:
            return text.strip()

    def wait_until_to(self, expected_condition = "element_to_be_clickable", element = None, locator = None , timeout=False):
        """
        [Internal]
        
        This method is responsible for encapsulating "wait.until".
        """

        self.switch_to_iframe()

        expected_conditions_dictionary = {

            "element_to_be_clickable" : EC.element_to_be_clickable,
            "presence_of_all_elements_located" : EC.presence_of_all_elements_located,
            "visibility_of" : EC.visibility_of,
            "alert_is_present" : EC.alert_is_present,
            "visibility_of_element_located" : EC.visibility_of_element_located
        }

        if not element and expected_condition != "alert_is_present" : self.log_error("Error method wait_until_to() - element is None")

        element = xpath_soup(element) if locator == By.XPATH else element

        if timeout:
            setattr(self.wait, '_timeout', self.config.time_out / 10)

        try:

            if locator:
                self.wait.until(expected_conditions_dictionary[expected_condition]((locator, element)))
            elif element:
                self.wait.until(expected_conditions_dictionary[expected_condition]( element() ))
            elif expected_condition == "alert_is_present":
                self.wait.until(expected_conditions_dictionary[expected_condition]())

        except TimeoutException as e:
            logger().exception(f"Warning waint_until_to TimeoutException - Expected Condition: {expected_condition}")
            pass

        if timeout:
            setattr(self.wait, '_timeout', self.config.time_out)
    
    def get_release(self):
        """
        Gets the current release of the Protheus.

        :return: The current release of the Protheus.
        :type: str
        
        Usage:

        >>> # Calling the method:
        >>> oHelper.get_release()
        >>> # Conditional with method:
        >>> # Situation: Have a input that only appears in release greater than or equal to 12.1.023
        >>> if self.oHelper.get_release() >= '12.1.023':
        >>>     self.oHelper.SetValue('AK1_CODIGO', 'codigoCT001')
        """

        return self.log.release

    def try_click(self, element):
        """
        [Internal]
        """
        try:
            self.soup_to_selenium(element).click()
        except:
            pass

    def open_csv(self, csv_file, delimiter, column, header, filter_column, filter_value):
        """
        Returns a dictionary when the file has a header in another way returns a list
        The folder must be entered in the CSVPath parameter in the config.json. Ex:

        .. note::
            This method return data as a string if necessary use some method to convert data like int().

        >>> config.json
        >>> CSVPath : 'C:\\temp'

        :param csv_file: .csv file name
        :type csv_file: str
        :param delimiter: Delimiter option such like ';' or ',' or '|'
        :type delimiter: str
        :param column: To files with Header is possible return only a column by header name or Int value for no header files 
        :type column: str
        :param header: Indicate with the file contains a Header or not default is Header None
        :type header: bool
        :param filter_column: Is possible to filter a specific value by column and value content, if value is int starts with number 1
        :type filter_column: str or int
        :param filter_value: Value used in pair with filter_column parameter
        :type filter_value: str

        >>> # Call the method:
        >>> file_csv = test_helper.OpenCSV(delimiter=";", csv_file="no_header.csv")

        >>> file_csv_no_header_column = self.oHelper.OpenCSV(column=0, delimiter=";", csv_file="no_header_column.csv")

        >>> file_csv_column = self.oHelper.OpenCSV(column='CAMPO', delimiter=";", csv_file="header_column.csv", header=True)

        >>> file_csv_pipe = self.oHelper.OpenCSV(delimiter="|", csv_file="pipe_no_header.csv")

        >>> file_csv_header = self.oHelper.OpenCSV(delimiter=";", csv_file="header.csv", header=True)

        >>> file_csv_header_column = self.oHelper.OpenCSV(delimiter=";", csv_file="header.csv", header=True)

        >>> file_csv_header_pipe = self.oHelper.OpenCSV(delimiter="|", csv_file="pipe_header.csv", header=True)

        >>> file_csv_header_filter = self.oHelper.OpenCSV(delimiter=";", csv_file="header.csv", header=True, filter_column='CAMPO', filter_value='A00_FILIAL')

        >>> file_csv _no_header_filter = self.oHelper.OpenCSV(delimiter=";", csv_file="no_header.csv", filter_column=0, filter_value='A00_FILIAL')
        """

        has_header = 'infer' if header else None
        
        if self.config.csv_path:
            data = pd.read_csv(self.replace_slash(f"{self.config.csv_path}\\{csv_file}"), sep=delimiter, encoding='latin-1', error_bad_lines=False, header=has_header, index_col=False, dtype=str)
            df = pd.DataFrame(data)
            df = df.dropna(axis=1, how='all')

            filter_column_user = filter_column
            
            if filter_column and filter_value:
                if isinstance(filter_column, int):
                    filter_column_user = filter_column - 1
                df = self.filter_dataframe(df, filter_column_user, filter_value)
            elif (filter_column and not filter_value) or (filter_value and not filter_column):
                logger().warning('WARNING: filter_column and filter_value is necessary to filter rows by column content. Data wasn\'t filtered')
                
            return self.return_data(df, has_header, column)
        else:
            self.log_error("CSV Path wasn't found, please check 'CSVPath' key in the config.json.")

    def filter_dataframe(self, df, column, value):
        """
        [Internal]
        """
        return df[df[column] == value]

    def return_data(self, df, has_header, column):
        """
        [Internal]
        """
        if has_header == 'infer':
            return df[column].to_dict() if column else df.to_dict()
        else:
            return df[column].values.tolist() if isinstance(column, int) else df.values.tolist()

    def open_url_coverage(self, url='', initial_program='', environment=''):
        """
        [Internal]
        Open a webapp url with line parameters
        :param url: server url.
        :type url: str
        :param initial_program: program name.
        :type initial_program: str
        :param environment: environment server.
        :type environment: str
        Usage:
        >>> # Call the method:  
        >>> self.open_url_coverage(url=self.config.url, initial_program=initial_program, environment=self.config.environment)
        """
        self.driver.get(f"{url}/?StartProg=CASIGAADV&A={initial_program}&Env={environment}") 
        
    def returns_printable_string(self, string):
        """
        Returns a string only is printable characters
        [Internal]
        :param string: string value
        :type string: str
        """
        return "".join(list(filter(lambda x: x.isprintable(), string)))

    def get_config_value(self, json_key):
        """

        :param json_key: Json Key in config.json
        :type json_key: str
        :return: Json Key item in config.json
        """
        json_key = json_key.lower()

        config_dict = dict((k.lower(), v) for k, v in self.config.json_data.items())

        if list(filter(lambda x: json_key in x, config_dict.keys())):
            return config_dict[json_key]
        else:
            self.log_error("Doesn't contain that key in json object")

    def check_mot_exec(self):
        """
        Check MotExec key content
        
        :return:
        """
        m = re.match(pattern='((^TIR$)|(^TIR_))', string=self.config.issue)
        if m:
            self.driver.close()
            self.assertTrue(False, f'Current "MotExec" are using a reserved word: "{m.group(0)}", please check "config.json" key and execute again.')

    def report_comparison(self, base_file="", current_file=""):
        """

        Compare two reports files and if exists show the difference between then if exists.

        .. warning::
            Important to use BaseLine_Spool key in config.json to work appropriately. Baseline_Spool is the path of report spool in yout environment

        .. warning::
            Some words are changed to this pattern below:

            'Emissão: 01-01-2015'
            'Emision: 01-01-2015'
            'DT.Ref.: 01-01-2015'
            'Fc.Ref.: 01-01-2015'
            'Hora...: 00:00:00'
            'Hora Término: 00:00:00'
            '/' to '@'

            Only .xml

            'encoding=""'
            '"DateTime">2015-01-01T00:00:00'
            'ss:Width="100"'

        :param base_file: Base file that reflects the expected. If doesn't exist make a copy of auto and then rename to base
        :param current_file: Current file recently impressed, this file is use to generate file_auto automatically.
        >>> # File example:
        >>> # acda080rbase.##r
        >>> # acda080rauto.##r
        >>> # Calling the method:
        >>> self.oHelper.ReportComparison(base_file="acda080rbase.##r", current_file="acda080rauto.##r")
        :return:
        """

        message = ""

        if not self.config.baseline_spool:
            self.log_error("No path in BaseLine_Spool in config.json! Please make sure to put a valid path in this key")

        if not current_file:
            self.log_error("Report current file not found! Please inform a valid file")
        else:
            auto_file = self.create_auto_file(current_file)
            logger().warning(
                self.replace_slash(f'We created a "auto" based in current file in "{self.config.baseline_spool}\\{current_file}". please, if you dont have a base file, make a copy of auto and rename to base then run again.'f'We created a "auto" based in current file in "{self.config.baseline_spool}\\{current_file}". please, if you dont have a base file, make a copy of auto and rename to base then run again.'))
            self.check_file(base_file, current_file)

            with open(self.replace_slash(f'{self.config.baseline_spool}\\{base_file}')) as base_file:
                with open(auto_file) as auto_file:
                    for line_base_file, line_auto_file in zip(base_file, auto_file):
                        if line_base_file != line_auto_file:
                            logger().warning("Make sure you are comparing two treated files")
                            message = f'Base line content: "{line_base_file}" is different of Auto line content: "{line_auto_file}"'
                            self.errors.append(message)
                            break

    def create_auto_file(self, file=""):
        """

        :param file:
        :return:
        """

        file_extension = file[-4:].lower()

        full_path = self.replace_slash(f'{self.config.baseline_spool}\\{file}')

        auto_file_path = self.replace_slash(f'{self.config.baseline_spool}\\{next(iter(file.split(".")))}auto{file_extension}')

        if pathlib.Path(f'{auto_file_path}').exists():
            pathlib.Path(f'{auto_file_path}').unlink()

        with open(full_path) as file_obj:
            readlines = file_obj.readlines()

            for line in readlines:
                content = self.sub_string(line, file_extension)

                with open(
                            self.replace_slash(rf'{self.config.baseline_spool}\\{next(iter(file.split(".")))}auto{file_extension}'),
                            "a") as write_file:
                        write_file.write(content)

        logger().warning(
                f'Auto file created in: "{auto_file_path}"')

        return auto_file_path

    def sub_string(self, line, file_extension):
        """

        :param line:
        :param file_extension:
        :return:
        """

        if not file_extension == '.xml':

            emissao = re.search(r'(Emissão: )(?:(\d{2}-\d{2}-\d{4}))', line)

            emision = re.search(r'(Emision: )(?:(\d{2}-\d{2}-\d{4}))', line)

            dtref = re.search(r'(DT\.Ref\.: )(?:(\d{2}-\d{2}-\d{4}))', line)

            fcref = re.search(r'(Fc\.Ref\.: )(?:(\d{2}-\d{2}-\d{4}))', line)

            hora = re.search(r'(Hora\.\.\.: )(?:(\d{2}:\d{2}:\d{2}))', line)

            hora_termino = re.search(r'(Hora Término: )(?:(\d{2}:\d{2}:\d{2}))', line)

            slash = re.search(r'(/)', line)

            if emissao:
                line = re.sub(emissao.group(0), 'Emissão: 01-01-2015', line)
            if emision:
                line = re.sub(emision.group(0), 'Emision: 01-01-2015', line)
            if dtref:
                line = re.sub(dtref.group(0), 'DT.Ref.: 01-01-2015', line)
            if fcref:
                line = re.sub(fcref.group(0), 'Fc.Ref.: 01-01-2015', line)
            if hora:
                line = re.sub(hora.group(0), 'Hora...: 00:00:00', line)
            if hora_termino:
                line = re.sub(hora_termino.group(0), 'Hora Término: 00:00:00', line)
            if slash:
                line = re.sub(slash.group(0), '@', line)

        else:

            encoding = re.search(r'(encoding=)(?:("UTF-8")|(""))', line)

            datetime = re.search(r'("DateTime">)(?:(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}))', line)

            width = re.search(r'(ss:Width=)"(?:(\d+))"', line)

            if encoding:
                line = re.sub(encoding.group(0), 'encoding=""', line)
            if datetime:
                line = re.sub(datetime.group(0), '"DateTime">2015-01-01T00:00:00', line)
            if width:
                line = re.sub(datetime.group(0), 'ss:Width="100"', line)

        return line

    def check_file(self, base_file="", current_file=""):
        """

        :param base_file:
        :param current_file:
        :return:
        """

        if not base_file:
            base_file = None

        if not pathlib.Path(self.replace_slash(f'{self.config.baseline_spool}\\{base_file}')).exists():
            self.log_error("Base file doesn't exist! Please confirm the file name and path. Now you can use auto file to rename to base.")

        if not pathlib.Path(self.replace_slash(f'{self.config.baseline_spool}\\{current_file}')).exists():
            self.log_error("Current file doesn't exist! Please confirm the file name and path.")

    def set_multilanguage(self):

        soup = self.get_current_DOM()
        po_select = next(iter(soup.select(".po-select-container")), None)
        if po_select:
            span_label = next(iter(po_select.select('span')), None)
            if span_label:
                language = self.return_select_language()
                if not span_label.text.lower() in language:
                    self.set_language_poui(language, po_select)

    def set_language_poui(self, language, container):

        icon = next(iter(list(filter(lambda x: "class" in x.attrs, container.select('span')))), None)
        if icon:
            icon_element = self.soup_to_selenium(icon)
            icon_element.click()

            container_ul = next(iter(container.select('ul')), None)
            if container_ul:
                item = next(iter(list(filter(lambda x: x.text.lower() in language ,container_ul.select('li')))), None)
                element = self.soup_to_selenium(item)
                element.click()

    def return_select_language(self):

        if self.config.language == 'pt-br':
            language = ['português', 'portugués', 'portuguese']
        elif self.config.language == 'es-es':
            language = ['espanhol', 'español', 'spanish']
        elif self.config.language == 'en-us':
            language = ['inglês', 'inglés', 'english']

        return language

    def get_grid_content(self, grid_number, grid_element):
        """

        :param grid_number:
        :param grid_element:
        :return:
        """

        grid_number -= 1
        
        self.wait_element(term=".tgetdados tbody tr, .tgrid tbody tr, .tcbrowse",
                          scrap_type=enum.ScrapType.CSS_SELECTOR)
        grid = self.get_grid(grid_number, grid_element)

        return grid.select('tbody tr')

    def LengthGridLines(self, grid):
        """
        Returns the length of the grid.
        :return:
        """
        
        return len(grid)


    def ClickMenu(self, menu_item):
        """
        Clicks on the menuitem of POUI component.
        https://po-ui.io/documentation/po-menu?view=doc

        :param menu_item: The Menu item name
        :type label_name: str

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickMenu("Contracts")
        """
        menu = ''
        logger().info(f"Clicking on {menu_item}")
        self.wait_element(term="[class='po-menu']")
        endtime = time.time() + self.config.time_out
        while(not menu and time.time() < endtime):
            po_menu = next(iter(self.web_scrap(term="[class='po-menu']", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body')), None)
            if po_menu:
                po_menu_item = po_menu.select('div[class*="po-menu-item"]')
                po_menu_item_filtered = list(filter(lambda x: EC.element_to_be_clickable((By.XPATH, xpath_soup(x))), po_menu_item))
                po_menu_item_filtered = list(filter(lambda x: menu_item.lower() in x.text.lower(), po_menu_item_filtered))

                if len(po_menu_item_filtered) > 1:
                    menu = next(iter(list(filter(lambda x: x.attrs['class'][0] == 'po-menu-item' , po_menu_item_filtered))))
                else:
                    menu = next(iter(po_menu_item_filtered), None)
            
        if not menu:
            self.log_error("Couldn't find any labels.")

        self.poui_click(menu)

    def InputValue(self, field, value, position):
        """
        Filling input component of POUI
        https://po-ui.io/documentation/po-input

        :param field: Input text title that you want to fill
        :type field: str
        :param value: Value that fill in input
        :type value: str
        :param position: Position which element is located. - **Default:** 1
        :type position: int

        Usage:

        >>> # Call the method:
        >>> oHelper.InputValue('Name', 'Test')
        :return: None
        """

        logger().info(f"Input Value in:'{field}'")

        success = False

        endtime = time.time() + self.config.time_out
        while time.time() < endtime and not success:

            input_field = self.return_input_element(field, position, term="[class*='po-input']")

            self.switch_to_iframe()

            input_field_element = lambda: self.soup_to_selenium(input_field)

            self.scroll_to_element(input_field_element())
            self.wait_until_to(expected_condition="element_to_be_clickable", element = input_field, locator = By.XPATH )
            self.set_element_focus(input_field_element())
            self.wait_until_to(expected_condition="element_to_be_clickable", element = input_field, locator = By.XPATH )
            self.click(input_field_element())
            input_field_element().clear()
            input_field_element().send_keys(value)

            if self.switch_to_active_element() == input_field_element():
                time.sleep(1)
                ActionChains(self.driver).key_down(Keys.ENTER).perform()
                time.sleep(1)
                ActionChains(self.driver).key_down(Keys.TAB).perform()

            time.sleep(2)
            success = self.get_web_value(input_field_element()).strip() != ''

    def return_input_element(self, field=None, position=1, term=None):
        """
        [Internal]
        Returns input element based on field
        """

        position -= 1
        input_field = ''
        self.twebview_context = True
        self.wait_element(term=term)
        endtime = time.time() + self.config.time_out
        while(not input_field and time.time() < endtime):
            po_input = self.web_scrap(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body')
            if po_input:
                po_input_filtered = list(filter(lambda x: x.find_parent('po-field-container') is not None, po_input))
                po_input_filtered = list(
                    filter(lambda x: x.find_parent('po-field-container').select('span, label'), po_input_filtered))
                po_input_text = list(filter(lambda x: field.lower() in x.text.lower(), list(
                    map(lambda x: x.find_parent('po-field-container').select('span, label')[0],
                        po_input_filtered))))
                if po_input_text:
                    if len(po_input_text) >= position:
                        po_input_text = po_input_text[position]
                        input_field = next(iter(po_input_text.find_parent('po-field-container').select('input')), None)

        if not input_field:
            self.log_error("Couldn't find any labels.")

        return input_field

    def return_main_element(self, field, position, selector, container):
        """

        :return:
        """
        po_component = self.web_scrap(term=selector, scrap_type=enum.ScrapType.CSS_SELECTOR,
                                  main_container='body')
        if po_component:
            po_component = list(filter(lambda x: self.element_is_displayed(x), po_component))
            if container:
                po_component_filtered = list(
                    filter(lambda x: x.find('po-field-container').select('span, label') != [], po_component))
                po_component_span = list(filter(lambda x: field.lower() in x.text.lower(), list(
                    map(lambda x: x.find('po-field-container').select('span, label')[0], po_component_filtered))))
            else:
                po_component_span = list(filter(lambda x: field.lower() in x.text.lower(), po_component))
                if len(po_component_span) > 1:
                    has_index = list(filter(lambda x: self.return_index_element(x), po_component_span))
                    if has_index:
                        po_component_span = has_index

            if po_component_span and len(po_component_span) >= position:
                po_component_span = po_component_span[position]
                return next(iter(po_component_span.find_parent('po-field-container')), None) if container else po_component_span

    def return_index_element(self, element):
        if hasattr(element.find_parent('div', {'tabindex': '-1'}), 'attr'):
            return element if element.find_parent('div', {'tabindex': '-1'}) else None

    def po_loading(self, selector):
        """

        :return:
        """
        loading = True

        endtime = time.time() + 300
        while loading and time.time() < endtime:
            container = self.web_scrap(term=selector, scrap_type=enum.ScrapType.CSS_SELECTOR,
                                       main_container='body')

            loading = True if list(filter(lambda x: x.select('po-loading'), container)) else False

    def click_select(self, field, value, position):
        """
        
        :param field: Combo text title that you want to click.
        :param value: Value that you want to select in Combo.
        :param position: Position which element is located. - **Default:** 1
        """

        position -= 1
        main_element = None
        trated_field = field.strip()
        select_bs = []
        success = False

        if not self.config.poui:
            self.twebview_context = True

        logger().info(f"Clicking on {field}")
        self.wait_element(term='po-select')
        endtime = time.time() + self.config.time_out
        while (not success and time.time() < endtime):
            po_select_bs = self.web_scrap(term='po-select', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body')

            if po_select_bs:
                select_element_filtred = next(iter(list(filter(lambda x: self.filter_label_element(trated_field, x), po_select_bs))), None)
                if select_element_filtred:
                    self.switch_to_iframe()
                    select_bs = select_element_filtred.find_next('select')
                    if select_bs:
                        self.select_combo(select_bs, value, shadow_root=False)
                        current_option = self.return_selected_combo_value(select_bs, shadow_root=False)
                        success = current_option == value

        if not success:
            self.log_error(f"Couldn't set {field}. Please check it")


    def poui_click(self, element):

        self.switch_to_iframe()
        click_element = lambda: self.soup_to_selenium(element)

        self.scroll_to_element(click_element())
        self.wait_until_to(expected_condition="element_to_be_clickable", element=element, locator=By.XPATH)
        self.set_element_focus(click_element())
        self.wait_until_to(expected_condition="element_to_be_clickable", element=element, locator=By.XPATH)
        time.sleep(1)
        self.click(click_element())

    def click_button(self, button, position, selector, container):
        """

        :param field: Button to be clicked.
        :param position: Position which element is located. - **Default:** 1

        """
        position -= 1
        element = None

        if not self.config.poui:
            self.twebview_context = True

        logger().info(f"Clicking on {button}")
        self.wait_element(term=button, optional_term=selector, scrap_type=enum.ScrapType.MIXED)
        endtime = time.time() + self.config.time_out
        while (not element and time.time() < endtime):
            element = self.return_main_element(button, position, selector=selector, container=container)

            if element:
                button_element = next(iter(element.select('button')), None)

        if not element:
            self.log_error("Couldn't find element")

        self.poui_click(button_element)

    def ClickWidget(self, title, action, position):
        """
        Clicks on the Widget or Widget action of POUI component.
        https://po-ui.io/documentation/po-widget

        :param tittle: Widget text title that you want to click.
        :param action: The name of action to be clicked
        :param position: Position which element is located. - **Default:** 1

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickWidget(title='LEad Time SC x PC', action='Detalhes', position=1)
        :return:
        """
        position -= 1
        element = None

        if not self.config.poui:
            self.twebview_context = True

        logger().info(f"Clicking on Widget")
        self.wait_element(term="po-widget")
        endtime = time.time() + self.config.time_out
        while (not element and time.time() < endtime):
            po_widget = self.web_scrap(term="po-widget", scrap_type=enum.ScrapType.CSS_SELECTOR,
                                  main_container='body')

            if po_widget:
            
                if title:
                    po_widget = list(filter(lambda x: title.lower() in x.text.lower(), po_widget))

                if action:
                    po_widget = list(filter(lambda x: action.lower() in x.text.lower(), po_widget))

                if po_widget:
                    if len(po_widget) >= position:
                        element = po_widget[position]

                        if action:
                            element = next(iter(list(filter(lambda x: action.lower() in x.text.lower(),
                                                            element.select("[class*='po-widget-action']")))), None)
                    else:
                        self.log_error("Couldn't find element")

        if not element:
            self.log_error("Couldn't find element")

        self.poui_click(element)

    def TearDown(self):
        """
        Closes the webdriver and ends the test case.

        Usage:

        >>> #Calling the method
        >>> self.TearDown()
        """

        if self.config.new_log:
            self.execution_flow()

        if self.config.coverage:
            self.coverage()

        if self.config.num_exec:
            if not self.num_exec.post_exec(self.config.url_set_end_exec, 'ErrorSetFimExec'):
                self.restart_counter = 3
                self.log_error(f"WARNING: Couldn't possible send num_exec to server please check log.")

        try:
            self.driver.close()
        except Exception as e:
            logger().exception(f"Warning tearDown Close {str(e)}")

    def coverage(self):
        """
        [Internal]
        """
        # Put coverage data into file.
        data = self.driver.execute_script('return window.__coverage__')

        project_folder = list(data)[0].split('src')[0]

        folder_path = os.path.join(project_folder, ".nyc_output")

        self.create_folder(folder_path)

        file_name = f"out{str(time.time())}.json"
        file_path = os.path.join(folder_path, file_name)

        with open(file_path, 'w') as outfile:
            json.dump(data, outfile)

        # Generate HTML coverage report
        os.system("cd %s && %s report --reporter=lcov --reporter=text-summary" % (
            project_folder,
            os.path.join(project_folder, "node_modules", ".bin", "nyc")))
            
    def POSearch(self, content, placeholder):
        """
        Fill the POUI Search component.
        https://po-ui.io/documentation/po-page-dynamic-search

        :param content: Content to be Search.
        :type content: str
        Usage:

        >>> # Call the method:
        >>> oHelper.POSearch(content='Content to be Search')
        :return: None
        """
        element = None

        if not self.config.poui:
            self.twebview_context = True

        logger().info(f"Searching: {content}")
        self.wait_element(term='po-page')
        endtime = time.time() + self.config.time_out
        while (not element and time.time() < endtime):
            po_page = next(iter(self.web_scrap(term="[class='po-page']", scrap_type=enum.ScrapType.CSS_SELECTOR,
                               main_container='body')),None)
            if po_page:
                page_list = po_page.find_all_next('div', 'po-page-list-filter-wrapper')
                page_list = next(iter(list(filter(lambda x: self.element_is_displayed(x), page_list))),None)
                if page_list:
                    input = page_list.select('input')

                    if placeholder:
                        input = next(iter(list(filter(lambda x: x.attrs['placeholder'].lower() == placeholder.lower(), input))))
                    else:
                        input = next(iter(page_list.select('input')), None)

                    if input:
                        element = lambda: self.soup_to_selenium(input)

        if not element:
            self.log_error("Couldn't find element")
        
        self.switch_to_iframe()
        element().clear()
        element().send_keys(content)

        action = lambda: self.soup_to_selenium(next(iter(input.parent.select('po-icon'))))
        ActionChains(self.driver).move_to_element(action()).click().perform()


    def ClickTable(self, first_column, second_column, first_content, second_content, table_number, itens, click_cell,
                   checkbox, radio_input):
        """
        Clicks on the Table of POUI component.
        https://po-ui.io/documentation/po-table

        :param first_column: Column name to be used as reference.
        :type first_column: str
        :param second_column: Column name to be used as reference.
        :type second_column: str
        :param first_content: Content of the column to be searched.
        :type first_content: str
        :param second_content: Content of the column to be searched.
        :type second_content: str
        :param table_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type table_number: int
        :param itens: Bool parameter that click in all itens based in the field and content reference.
        :type itens: bool
        :param click_cell: Content to click based on a column position to close the axis
        :type click_cell: str
        :param checkbox: If you want to click on the checkbox component in the table
        :type checkbox: bool

        >>> # Call the method:
        >>> oHelper.ClickTable(first_column='Código', first_content='000003', click_cell='Editar')
        :return: None
        """
        element = None
        UNNAMED_COLUMN = 'Unnamed: 0'

        if not self.config.poui:
            self.twebview_context = True

        index_number = []
        count = 0
        column_index_number = None
        term = "[class='po-table'], po-table"
        logger().info(f"Clicking on Table")
        self.wait_element(term=term)

        endtime = time.time() + self.config.time_out
        while time.time() < endtime and len(index_number) < 1 and count <= 3:

            try:
                table = self.return_table(selector=term, table_number=table_number)

                df = self.data_frame(object=table)

                last_df = df

                if not df.empty:
                    if click_cell:
                        column_index_number = df.columns.get_loc(click_cell)

                    if first_column and second_column and first_column != UNNAMED_COLUMN:
                        index_number = df.loc[(df[first_column] == first_content) & (df[second_column] == second_content)].index.array
                    elif first_column and (first_content and second_content):
                        index_number = df.loc[(df[first_column[0]] == first_content) | (df[first_column[0]] == second_content)].index.array
                    elif itens:
                        index_number = df.loc[(df[first_column] == first_content)].index.array
                    elif first_column and first_content:
                        first_column = next(iter(list(filter(lambda x: first_column.lower().strip() in x.lower().strip(), df.columns))))
                        first_column_values = df[first_column].values
                        first_column_formatted_values = list(map(lambda x: x.replace(' ', ''), first_column_values))
                        content = next(iter(list(filter(lambda x: x == first_content.replace(' ', ''), first_column_formatted_values))), None)
                        if content:
                            index_number.append(first_column_formatted_values.index(content))
                            if len(index_number) > 0:
                                index_number = [index_number[0]]
                    elif first_column and second_column and second_content:
                        second_column = next(iter(list(filter(lambda x: second_column.lower().strip() in x.lower().strip(), df.columns))), None)
                        second_column_values = df[second_column].values
                        second_column_formatted_values = list(map(lambda x: x.replace(' ', ''), second_column_values))
                        content = next(iter(list(filter(lambda x: x == second_content.replace(' ', ''), second_column_formatted_values))), None)
                        if content:
                            index_number.append(second_column_formatted_values.index(content))
                            if len(index_number) > 0:
                                index_number = [index_number[0]]
                    else:
                        index_number.append(0)

                    if len(index_number) < 1 and count <= 3:
                        first_element_focus = table.select('th')[column_index_number]
                        if first_element_focus:
                            self.wait_until_to(expected_condition="element_to_be_clickable",
                                               element=first_element_focus, locator=By.XPATH)
                            self.soup_to_selenium(first_element_focus).click()
                        ActionChains(self.driver).key_down(Keys.PAGE_DOWN).perform()
                        table = self.return_table(selector=term, table_number=table_number)
                        df = self.data_frame(object=table)
                        if df.equals(last_df):
                            count += 1

            except Exception as e:
                self.log_error(f"Content doesn't found on the screen! {str(e)}")

        if len(index_number) < 1:
            self.log_error(f"Content doesn't found on the screen! {first_content}")

        tr = table.select('tbody > tr')

        if hasattr(index_number, '__iter__'):
            for index in index_number:
                if checkbox:
                    self.click_table_checkbox(selector=term, index=index, table_number=table_number)
                elif radio_input:
                    row_radio_component = tr[index].select_one('po-radio')
                    if row_radio_component:
                        self.toggle_radio(row_radio_component, radio_input)
                else:
                    if column_index_number:
                        element_bs4 = tr[index].select('td')[column_index_number].select('span')[0]

                    else:
                        element_bs4 = next(iter(tr[index].select('td')))
                        if first_column == UNNAMED_COLUMN:
                            clickable_spans = tr[index].select('td')[0].select('.po-clickable')
                            if clickable_spans:
                                element_bs4 = clickable_spans[0]
                            else:
                                self.log_error("No clickable spans found in the table row.")
                    self.poui_click(element_bs4)
        else:
            index = index_number
            element_bs4 = next(iter(tr[index].select('td')))
            self.poui_click(element_bs4)

    def toggle_radio(self, po_radio, active=True):
        '''Set input Radio from a tr Tag element

        :param po_radio: BeautifulSoup4
        :return:
        '''
        # method prepared only to radios in tr(rows) until this moment
        # it still be changed to another cases

        radio_input = po_radio.select_one('input')

        if radio_input:
            selenium_radio = self.soup_to_selenium(radio_input, twebview=True)
        else:
            selenium_radio = self.soup_to_selenium(po_radio, twebview=True)

        radio_status = lambda: self.radio_is_active(po_radio)

        success = lambda: radio_status() == active

        endtime = time.time() + self.config.time_out
        while time.time() < endtime and not success():
            self.click(selenium_radio, click_type=enum.ClickType.SELENIUM)

    def radio_is_active(self, radio):
        '''Check if radio is active

        :param radio: BeautifulSoup4
        :return: Boolean
        '''

        # check if po-radio is active in tr
        radio_tr = radio.find_parent('tr')
        if radio_tr:
            self.switch_to_iframe()
            radio_selenium = self.soup_to_selenium(radio_tr, twebview=True)
            return 'active' in radio_selenium.get_attribute('class')

        return False


    def click_table_checkbox(self, selector, index, table_number):

        checked = False

        endtime = time.time() + self.config.time_out
        while time.time() < endtime and not checked:
            table = self.return_table(selector=selector, table_number=table_number)

            tr = table.select('tbody > tr')

            checkbox = next(iter(tr[index].select("[name='checkbox']")), None)

            if checkbox:
                element = checkbox.select('span')[0]

                if 'checked' in checkbox.contents[0].attrs:
                    checked = 'true' in checkbox.contents[0].attrs['checked']

            if not checked:
                self.poui_click(element)

    def return_table(self, selector, table_number):

        table_number -= 1

        self.wait_element(term=selector, scrap_type=enum.ScrapType.CSS_SELECTOR)

        tables = self.web_scrap(term=selector, scrap_type=enum.ScrapType.CSS_SELECTOR,
                               main_container='body')
        
        tables = list(filter(lambda x: self.element_is_displayed(x), tables))
        
        if tables:
            if len(tables) - 1 >= table_number:
                return tables[table_number]

    def data_frame(self, object):
        '''Return a DataFrame from a Beautiful Soup Table

        :param object: BeautifulSoup4 Table
        :return: Pandas dataframe
        '''

        df = (next(iter(pd.read_html(str(object)))))

        converters = {c: lambda x: str(x) for c in df.columns}

        df = (next(iter(pd.read_html(str(object), converters=converters)), None))

        if not df.empty:
            return df.fillna('Not Value')

    def POTabs(self, label):
        """
        Clicks on a Label in po-tab.
        https://po-ui.io/documentation/po-tabs

        :param label: The tab label name
        :type label: str

        >>> # Call the method:
        >>> oHelper.POTabs(label='Test')
        :return: None
        """

        self.wait_element(term="[class='po-tabs-container']", scrap_type=enum.ScrapType.CSS_SELECTOR)

        po_tab_button = self.web_scrap(term="po-tab-button", scrap_type=enum.ScrapType.CSS_SELECTOR,
                                       main_container='body')

        label_element = next(
            iter(list(filter(lambda x: x.text.lower().strip() == label.lower().strip(), po_tab_button))))

        element = next(iter(label_element.select('div')))

        self.poui_click(element)

    def click_icon(self, label, class_name, position):
        """

        Click on the POUI Icon by label, class_name or both.
        https://po-ui.io/guides/icons

        :param label: The tooltip name for icon
        :type label: str
        :param class_name: The POUI class name for icon
        :type class_name: str
        :param position:
        :type position: int
        :return: None

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickIcon(label='Delete')
        >>> oHelper.ClickIcon(class_name='po-icon po-icon-delete')
        >>> oHelper.ClickIcon(label='Delete', class_name='po-icon po-icon-delete')
        """

        position -= 1
        element = None

        term = '[class*="po-icon"]'

        self.wait_element(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR)

        endtime = time.time() + self.config.time_out
        while time.time() < endtime and not element:

            logger().info("Clicking on Icon")

            po_icon = self.web_scrap(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR,
                                     main_container='body')

            if po_icon:
                po_icon_filtered = list(filter(lambda x: self.element_is_displayed(x), po_icon))

                if label and class_name:
                    class_element = self.return_icon_class(class_name, po_icon_filtered)
                    element = class_element if self.check_element_tooltip(class_element, label, contains=True) else None
                elif class_name:
                    element = self.return_icon_class(class_name, po_icon_filtered)
                else:
                    element = self.filter_by_tooltip_value(po_icon_filtered, label)

                if element:
                    if position > 0 and position >= len(element):
                        element = element[position]

                    self.poui_click(element)

        if not element:
            self.log_error(f"Element '{element}' doesn't found!")

    def return_icon_class(self, class_name, elements):
        """

        :param class_name: The POUI class name for icon
        :type class_name: str
        :param elements: bs4 element
        :type elements: object
        :return: filtered bs4 object
        """

        icon_classes = list(filter(lambda x: any(
            class_name.lower().strip() == f'po-icon {attr.lower().strip()}' for attr in x.attrs.get('class', [])),
                                     elements))
        if icon_classes:
            return next(iter(icon_classes))

    def click_avatar(self, position):
        """
        Click on the POUI Profile Avatar icon.
        https://po-ui.io/guides/Avatar

        :param position: - **Default:** 1
        :type position: int

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickAvatar(position=1)
        >>> oHelper.ClickAvatar()
        """

        logger().info("Clicking on Avatar profile")
        position = position-1 if position > 0 else 0
        element = None
        term = 'po-avatar'

        self.wait_element(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR)

        endtime = time.time() + self.config.time_out
        while time.time() < endtime and not element:
            po_avatar = self.web_scrap(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR,
                                     main_container='body')

            if po_avatar:
                po_avatar_filtered = list(filter(lambda x: self.element_is_displayed(x), po_avatar))

                if po_avatar_filtered:
                    if len(po_avatar_filtered) > position:
                        element = po_avatar_filtered[position]

                        self.poui_click(element)

        if not element:
            self.log_error(f"Element '{element}' doesn't found!")

    def click_popup(self, label):
        """Click on the POUI Profile Avatar icon.
        https://po-ui.io/documentation/po-popup

        :param label:
        :type label: str

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickPopup(label="Popup Item")
        >>> oHelper.ClickPopup()
        """
        logger().info(f"Clicking on Popup: {label}")

        element = None
        term = 'po-item-list'
        label = label.lower().strip()

        self.wait_element(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR)

        endtime = time.time() + self.config.time_out
        while time.time() < endtime and not element:
            po_list_item = self.web_scrap(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body')
            if po_list_item:
                po_item = list(filter(lambda x: x.text.lower().strip() == label, po_list_item))
                element = next(iter(po_item), None)

                if element:
                    self.poui_click(element)


    def click_checkbox(self, label):
        """Click on the POUI Checkbox.
        https://po-ui.io/documentation/po-checkbox

        :param label:
        :type label: str

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickCheckBox(label="CheckBox label")
        """

        label = label.strip().lower()
        term = 'po-checkbox'
        container_element = None
        self.wait_element(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR)

        endtime = time.time() + self.config.time_out
        while time.time() < endtime and not container_element:
            po_checkbox_itens = self.web_scrap(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body')
            if po_checkbox_itens:
                checkbox_filtered = list(filter(lambda x: x.text.lower().strip() == label, po_checkbox_itens))

                if checkbox_filtered:
                    po_element = next(iter(checkbox_filtered), None)
                    container_element = next(iter(po_element.select('.container-po-checkbox')),None)
                    if container_element:
                        self.poui_click(container_element)

        if not container_element:
            self.log_error(f"CheckBox '{label}' doesn't found!")


    def click_combo(self, field, value, position, second_value):
        '''Select a value for list combo inputs.

        :param field: label of field
        :type : str
        :param value: value to input on field
        :type : str
        :param position:
        :type : int
        :param second_value: value below the principal value (after the ":")
        :type : str
        :return:
        '''

        success = None
        position -= 1
        current_value = None
        main_value = ''

        logger().info(f"Clicking on {field}")
        self.wait_element(term='po-combo')

        endtime = time.time() + self.config.time_out
        while (not success and time.time() < endtime):
            po_combo_list = self.web_scrap(term='po-combo', scrap_type=enum.ScrapType.CSS_SELECTOR,
                                            position=position, main_container='body')
            po_combo_displayeds = list(filter(lambda x: self.element_is_displayed(x), po_combo_list))
            if po_combo_displayeds:
                po_combo_filtred = next(iter(filter(lambda x: self.filter_label_element(field.strip(), x),
                                                    po_combo_displayeds)),None)
                po_input = po_combo_filtred.find_next('input')
                if po_input:
                    po_input_sel = self.soup_to_selenium(po_input, twebview=True)

                    main_value = self.get_web_value(self.soup_to_selenium(po_input, twebview=True))
                    self.open_input_combo(po_combo_filtred)
                    self.send_keys(po_input_sel, value if value else second_value)
                    self.click_po_list_box(value, second_value)
                    current_value = self.get_web_value(self.soup_to_selenium(po_input, twebview=True))
                    success = current_value.strip().lower() == main_value.strip().lower() if value else True

        if not success:
            self.log_error(f'Click on {value} of {field} Fail. Please Check')


    def click_po_list_box(self, value, second_value):
        '''
        :param value: Value to select on po-list-box
        :type str
        :param second_value: value below the principal value (after the ":")
        :type : str
        :return:
        '''
        orig_value = value
        orig_second_value = second_value
        value = value.strip().lower()
        second_value = second_value.strip().lower()

        self.wait_element(term='po-listbox')

        po_items_list = self.web_scrap(term='po-item-list', scrap_type=enum.ScrapType.CSS_SELECTOR,
                                       main_container='body')

        if po_items_list:
            item_filtered = next(iter(list(filter(lambda x: self.find_po_item_list(x, value, second_value), po_items_list))), None)
            if item_filtered:
                item_filtered_div = item_filtered.find_next('div')
                self.scroll_to_element(self.soup_to_selenium(item_filtered_div, twebview=True))
                self.click(self.soup_to_selenium(item_filtered_div, twebview=True))
            else:
                self.log_error(f'Item list {orig_value if orig_value else orig_second_value} not found')


    def find_po_item_list(self, po_item_list, param_label, param_value):
        '''This method is used to filter the po-item-list elements based on the label and value match.


        :param list_elements: list of BeautifulSoup po-item-list elements
        :type list_elements: list
        :param label_text:
        :param value_text:
        :param attr: attribute to be checked in the po-item-list
        :return: Filtered BeautifulSoup element or None if not found
        '''


        element_data_str = po_item_list.get(f'data-item-list')
        if element_data_str:
            atr_value_dict = self.string_to_json(element_data_str)

            if atr_value_dict:
                normalized_dict = self.normalize_json(atr_value_dict)

                elem_label = normalized_dict.get('label')
                elem_value = normalized_dict.get('value')

                if param_label and param_value:
                    return param_label == elem_label and param_value == elem_value

                elif param_label and not param_value:
                    return param_label == elem_label

                elif not param_label and param_value:
                    return param_value == elem_value


    def normalize_json(self, json, lower_case=True):
        if lower_case:
            return {str(k).strip().lower(): self.normalize_json(v) if isinstance(v, dict) else str(v).strip().lower() for k, v in json.items()}
        else:
            return {str(k).strip(): self.normalize_json(v) if isinstance(v, dict) else str(v).strip() for k, v in json.items()}


    def string_to_json(self, string):
        '''Convert a string to a json object

        :param string: String to be converted
        :type string: str
        :return: json object
        '''
        try:
            return json.loads(string)
        except json.JSONDecodeError as e:
            logger().debug(f"Error decoding JSON data: {e}")
            return None


    def open_input_combo(self, po_combo):
        '''
        :param po_combo: po-combo object
        :type: Bs4 object
        :return:
        '''

        combo_container = next(iter(po_combo.select('.po-combo-container')),None)
        combo_input = next(iter(po_combo.select('input')), None)

        if combo_container:
            closed_combo = lambda: self.soup_to_selenium(combo_container, twebview=True).get_attribute('hidden')
            endtime = time.time() + self.config.time_out
            while (closed_combo() and time.time() < endtime):
                self.click(self.soup_to_selenium(combo_input, twebview=True))
                
    def click_look_up(self, label=None, search_value=None):
        """Use to click and search value in Lookup components

        https://po-ui.io/documentation/po-lookup
        :param label: field from lookup input
        :type: str
        :param search_value: Value to input in search field
        :type: str
        :return:
        """

        try:
            self.wait_element(term='po-lookup', scrap_type=enum.ScrapType.CSS_SELECTOR)
            lookup_filtered = []

            lookup_components = self.web_scrap(term="po-lookup", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body', check_help=False)
            if lookup_components is not None:
                if label:
                    #filter lookup by label match
                    lookup_filtered = list(filter(lambda x: hasattr(x, 'label') and label.lower().strip() in x.text.lower().strip() ,lookup_components))
                    lookup_filtered = next(iter(lookup_filtered), None)

            if lookup_filtered:
                # find search po-icon component in lookup window
                search_icon = lookup_filtered.select_one('po-icon')
                if search_icon:
                    selenium_icon = self.wait_soup_to_selenium(search_icon, twebview=True)
                    self.scroll_to_element(selenium_icon)
                    self.set_element_focus(selenium_icon)
                    self.click(selenium_icon)

                    logger().info(f"Search icon for the '{label}' field clicked successfully.")

                    # Wait table show up
                    self.wait_element_timeout(term=".po-table-row", scrap_type=enum.ScrapType.CSS_SELECTOR, timeout=10,
                                              main_container='body')

                    if search_value:
                        # Scrap lookup filter component
                        search_field = next(iter(self.web_scrap(term=".po-lookup-filter-content",
                                                      scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body')), None)
                        if search_field:
                            search_input_field = search_field.select_one('.po-input')
                            if search_input_field:
                                # Click on component and send search_value keys
                                self.switch_to_iframe()
                                selenium_input_field = self.wait_soup_to_selenium(search_input_field, twebview=True)
                                self.set_element_focus(selenium_input_field)
                                self.click(selenium_input_field, click_type=enum.ClickType.SELENIUM)
                                self.send_keys(selenium_input_field, search_value)

                                # Click on search icon to filter inputed value
                                po_search_icon = search_field.select_one('po-icon')
                                selenium_search_icon = self.wait_soup_to_selenium(po_search_icon, twebview=True)
                                self.click(selenium_search_icon, click_type=enum.ClickType.SELENIUM)

                        if not search_field:
                            self.log_error(f"Field '{search_value}' not found.")
                else:
                    self.log_error(f"Search icon for the '{label}' field not found in the DOM.")
            else:
                self.log_error(f"Lookup to {label} component not found in the DOM.")
        except Exception as e:
            self.log_error(f"Error clicking the search icon for the '{label}' field: {e}")

    def wait_soup_to_selenium(self, soup_object, twebview=False, timeout=60):

        success = False
        endtime = time.time() + timeout
        while (not success and time.time() < endtime):
            success = self.soup_to_selenium(soup_object=soup_object, twebview=twebview)

        if time.time() > endtime:
            logger().debug(f'SOUP:{element} to Selenium element not found')

        return success