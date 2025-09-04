import re
import time
import pandas as pd
import inspect
import os
import random
import uuid
import glob
import shutil
import cv2
import socket
import pathlib
import sys
import tir.technologies.core.enumerations as enum
from functools import reduce
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup, Tag
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from tir.technologies.core import base
from tir.technologies.core.log import Log, nump
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
from io import StringIO
from tir.technologies.core.base_database import BaseDatabase

def count_time(func):
    """
    Decorator to count the time spent in a function.
    """
    def wrapper(*args, **kwargs):
        starttime = time.time()
        result = func(*args, **kwargs)
        endtime = time.time()
        logger().debug(f"Time spent in {func.__name__}: {endtime - starttime}")
        return result
    return wrapper

class WebappInternal(Base):
    """
    Internal implementation of Protheus Webapp class.

    This class contains all the methods defined to run Selenium Interface Tests on Protheus Webapp.

    Internal methods should have the **[Internal]** tag and should not be accessible to the user.

    :param config_path: The path to the config file. - **Default:** "" (empty string)
    :type config_path: str
    :param autostart: Sets whether TIR should open browser and execute from the start. - **Default:** True
    :type: bool

    Usage:

    >>> # Inside __init__ method in Webapp class of main.py
    >>> def __init__(self, config_path="", autostart=True):
    >>>     self.__webapp = WebappInternal(config_path, autostart)
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
            "SetButton" : ".tmodaldialog,.ui-dialog, wa-dialog",
            "GetCurrentContainer": ".tmodaldialog, wa-dialog, wa-message-box",
            "AllContainers": "body,.tmodaldialog,.ui-dialog,wa-dialog",
            "ClickImage": "wa-dialog, .tmodaldialog",
            "BlockerContainers": ".tmodaldialog,.ui-dialog, wa-dialog",
            "Containers": ".tmodaldialog,.ui-dialog, wa-dialog"
        }

        self.grid_selectors = {
            "new_web_app": ".dict-tgetdados, .dict-tcbrowse, .dict-msbrgetdbase, .dict-tgrid, .dict-brgetddb, .dict-msselbr, .dict-twbrowse, .dict-tsbrowse"
        }

        self.grid_check = []
        self.grid_counters = {}
        self.grid_input = []
        self.down_loop_grid = False
        self.num_exec = NumExec()
        self.restart_counter = 0
        self.used_ids = {}
        self.tss = False
        self.restart_coverage = True

        self.blocker = None
        self.parameters = []
        self.procedures = []
        self.backup_parameters = []
        self.tree_base_element = ()
        self.tmenu_screen = None
        self.grid_memo_field = False
        self.range_multiplier = None
        self.test_suite = []
        self.current_test_suite = self.log.get_file_name('testsuite')
        self.restart_tss = False
        self.last_wa_tab_view_input_id = None
        self.mock_counter = 0
        self.mock_route = ''
        self.registry_endpoint = ''
        self.rac_endpoint = ''
        self.platform_endpoint = ''


        if not Base.driver:
            Base.driver = self.driver

        if not Base.wait:
            Base.wait = self.wait

        if not Base.errors:
            Base.errors = self.errors

        if not self.config.smart_test and self.config.issue:
            self.check_mot_exec()

        if webdriver_exception:
            message = f"Wasn't possible execute Start() method: {webdriver_exception}"
            self.restart_counter = 3
            self.log_error(message)
            self.assertTrue(False, message)

    def SetupTSS( self, initial_program = "", enviroment = ""):
        """
        Prepare the Protheus Webapp TSS for the test case, filling the needed information to access the environment.
        .. note::
            This method use the user and password from config.json.

        :param initial_program: The initial program to load.
        :type initial_program: str
        :param environment: The initial environment to load.
        :type environment: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetupTSS("TSSMANAGER", "SPED")
        """

        self.config.poui_login = False

        self.restart_tss = True

        try:

            logger().info("Starting Setup TSS")
            self.tss = True
            self.service_process_bat_file()

            self.config.initial_program = initial_program
            enviroment = self.config.environment if self.config.environment else enviroment

            self.containers_selectors["SetButton"] = "body"
            self.containers_selectors["GetCurrentContainer"] = "wa-dialog, .tmodaldialog, body"

            if not self.config.skip_environment and not self.config.coverage:
                self.program_screen(initial_program, enviroment)

            if not self.log.program:
                self.log.program = self.get_program_name()

            if self.config.coverage:
                self.open_url_coverage(url=self.config.url, initial_program=initial_program, environment=self.config.environment)

            self.user_screen_tss()
            self.set_log_info_config() if self.config.log_info_config else self.set_log_info_tss()

            if self.config.num_exec:
                if not self.num_exec.post_exec(self.config.url_set_start_exec, 'ErrorSetIniExec'):
                    self.restart_counter = 3
                    self.log_error(f"WARNING: Couldn't possible send num_exec to server please check log.")

        except ValueError as e:
            self.log_error(str(e))
        except Exception as e:
            logger().exception(str(e))

    def user_screen_tss(self):
        """
        [Internal]

        Fills the user login screen of Protheus with the user and password located on config.json.

        Usage:

        >>> # Calling the method
        >>> self.user_screen()
        """
        logger().info("Fill user Screen")
        self.wait_element(term="[name='cUser']", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")

        self.SetValue('cUser', self.config.user, name_attr = True)
        self.SetValue('cPass', self.config.password, name_attr = True)
        self.SetButton("Entrar")

    def Setup(self, initial_program, date='', group='99', branch='01', module='', save_input=True):
        """
        Prepare the Protheus Webapp for the test case, filling the needed information to access the environment.

        :param initial_program: The initial program to load.
        :type initial_program: str
        :param date: The date to fill on the environment screen. - **Default:** "" (empty string)
        :type date: str
        :param group: The group to fill on the environment screen. - **Default:** "99"
        :type group: str
        :param branch: The branch to fill on the environment screen. - **Default:** "01"
        :type branch: str
        :param module: The module to fill on the environment screen. - **Default:** "" (empty string)
        :type module: str
        :param save_input: Boolean if all input info should be saved for later usage. Leave this flag 'True' if you are not sure. **Default:** True
        :type save_input: bool

        Usage:

        >>> # Calling the method:
        >>> oHelper.Setup("SIGAFAT", "18/08/2018", "T1", "D MG 01 ")
        """

        if self.config.smart_test or self.config.debug_log:
            logger().info(f"***System Info*** in Setup():")
            system_info()

        if 'POUILogin' in self.config.json_data and self.config.json_data['POUILogin'] == True:
            self.config.poui_login = True
        else:
            self.config.poui_login = False

        try:
            self.service_process_bat_file()

            if not initial_program:
                self.log_error("Couldn't find The initial program")

            if self.config.smart_erp:
                self.wait_smart_erp_environment()

            if not self.log.program:
                self.log.program = self.get_program_name()

            server_environment = self.config.environment

            if save_input:
                self.config.initial_program = initial_program
                self.config.date = self.date_format(date)
                self.config.group = group
                self.config.branch = branch
                self.config.module = module

            if self.config.coverage:
                self.open_url_coverage(url=self.config.url, initial_program=initial_program,
                                       environment=server_environment)

            if not self.config.valid_language:
                self.config.language = self.get_language()
                self.language = LanguagePack(self.config.language)

           
            if not self.config.skip_environment and not self.config.coverage:
                self.program_screen(initial_program=initial_program, environment=server_environment, poui=self.config.poui_login)

            self.log.webapp_version = self.driver.execute_script("return app.VERSION")

            if not self.config.sso_login:    
                self.user_screen(True) if initial_program.lower() == "sigacfg" else self.user_screen()

                endtime = time.time() + self.config.time_out
                if not self.config.poui_login:
                    if self.webapp_shadowroot():
                        while (time.time() < endtime and (
                        not self.element_exists(term=self.language.database, scrap_type=enum.ScrapType.MIXED,
                                                main_container="body", optional_term='wa-text-view'))):
                            self.update_password()
                    else:
                        while (time.time() < endtime and (
                        not self.element_exists(term=self.language.database, scrap_type=enum.ScrapType.MIXED,
                                                main_container=".twindow", optional_term=".tsay"))):
                            self.update_password()

            self.environment_screen()

            self.close_screen_before_menu()

            if save_input:
                self.set_log_info_config() if self.config.log_info_config else self.set_log_info()

            self.log.country = self.config.country
            self.log.execution_id = self.config.execution_id
            self.log.issue = self.config.issue

        except ValueError as error:
            self.log_error(error)
        except Exception as e:
            logger().exception(str(e))

        if self.config.num_exec:
            if not self.num_exec.post_exec(self.config.url_set_start_exec, 'ErrorSetIniExec'):
                self.restart_counter = 3
                self.log_error(f"WARNING: Couldn't possible send num_exec to server please check log.")

        if self.config.smart_test and self.config.coverage and self.search_stack(
                "setUpClass") and self.restart_coverage:
            self.restart()
            self.restart_coverage = False

    def date_format(self, date):
        """

        :param date:
        :return:
        """
        pattern_1 = '([\d]{2}).?([\d]{2}).?([\d]{4})'
        pattern_2 = '([\d]{2}).?([\d]{2}).?([\d]{2})'

        d = self.config.data_delimiter

        formatted_date = re.sub(pattern_1, rf'\1{d}\2{d}\3', date)

        if not re.match(pattern_1, formatted_date):
            formatted_date = re.sub(pattern_2, rf'\1{d}\2{d}\3', date)

        return formatted_date

    def merge_date_mask(self, base_date, date):

        d = self.config.data_delimiter
        pattern_1 = (r"\d{2}*\d{2}*\d{4}").replace("*", d)
        pattern_2 = (r"\d{2}*\d{2}*\d{2}").replace("*", d)

        match1 = re.match(pattern_1, base_date)
        match2 = re.match(pattern_2, base_date)


        if match1:
            return date
        elif match2:
            split_date = date.split(d)
            return f"{split_date[0]}{d}{split_date[1]}{d}{split_date[-1][-2:]}"

    def close_screen_before_menu(self):

        logger().debug('Closing screen before the menu')

        term = '.dict-tmenu' if self.webapp_shadowroot() else '.tmenu'

        endtime = time.time() + self.config.time_out
        while (time.time() < endtime and (
                not self.element_exists(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body"))):
            self.close_warning_screen()
            self.close_coin_screen()
            self.close_modal()

    def service_process_bat_file(self):
        """
        [Internal]
        This method creates a batfile in the root path to kill the process and its children.
        """
        if self.config.smart_test:
            if sys.platform == 'win32':
                with open("firefox_task_kill.bat", "w", ) as firefox_task_kill:
                    firefox_task_kill.write(f"taskkill /f /PID {self.driver.service.process.pid} /T")

    def program_screen(self, initial_program="", environment="", poui=False):
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

        program_screen = []

        if not environment:
            environment = self.config.environment

        if self.config.coverage:
            self.open_url_coverage(url=self.config.url, initial_program=initial_program,
                                   environment=environment)

        self.config.poui_login = poui
        endtime = time.time() + 10

        while time.time() < endtime and not program_screen:
            start_program_term = '#selectStartProg'
            program_screen = self.web_scrap(term=start_program_term, scrap_type=enum.ScrapType.CSS_SELECTOR,
                                    main_container=self.containers_selectors["AllContainers"],
                                    check_help=False, check_error=False)


        if program_screen:
            self.filling_initial_program(initial_program)
            self.filling_server_environment(environment)

            if self.webapp_shadowroot():
                self.wait_until_to(expected_condition = "element_to_be_clickable", element=".startParameters", locator = By.CSS_SELECTOR)
                parameters_screen = self.driver.find_element(By.CSS_SELECTOR, ".startParameters")
                buttons = self.find_shadow_element('wa-button', parameters_screen)
                button = next(iter(list(filter(lambda x: 'ok' in x.text.lower().strip(), buttons))), None)
            else:
                button = self.driver.find_element(By.CSS_SELECTOR, ".button-ok")

            self.click(button)

    def filling_initial_program(self, initial_program):
        """
        [Internal]
        """

        if self.webapp_shadowroot():
            start_program = '#selectStartProg'
        else:
            start_program = '#inputStartProg'

        logger().info(f'Filling Initial Program: "{initial_program}"')

        self.fill_select_element(term=start_program, user_value=initial_program)
        
    def filling_server_environment(self, environment):
        """
        [Internal]
        """

        if self.webapp_shadowroot():
            input_environment = '#selectEnv'
        else:
            input_environment = '#inputEnv'

        logger().info(f'Filling Server Environment: "{environment}"')

        self.fill_select_element(term=input_environment, user_value=environment)
       
    def fill_select_element(self, term, user_value):

        self.wait_element(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
      
        element_value = ''
        try_counter = 0	

        endtime = time.time() + self.config.time_out
        while (time.time() < endtime and (element_value != user_value.strip())):

            soup = self.get_current_DOM()

            soup_element = next(iter(soup.select(term)), None)
            if soup_element is None:
                self.restart_counter += 1
                message = f"Couldn't find '{term}' element."
                self.log_error(message)
                raise ValueError(message)

            element = lambda: self.soup_to_selenium(soup_element)

            self.set_element_focus(element())
            self.click(element())
            self.try_send_keys(element, user_value, try_counter)
            try_counter += 1

            if try_counter > 4:
                try_counter = 0
            
            if self.webapp_shadowroot():
                element_value = self.get_web_value(next(iter(self.find_shadow_element('input', element())))).strip() if self.find_shadow_element('input', element()) else None
            else:
                element_value = self.get_web_value(element())

        if (element_value.strip() != user_value.strip()):
            self.restart_counter += 1
            message = f"Couldn't fill '{term}' element."
            self.log_error(message)
            raise ValueError(message)

    def user_screen(self, admin_user=False):
        """
        [Internal]

        Fills the user login screen of Protheus with the user and password located on config.json.

        Usage:

        >>> # Calling the method
        >>> self.user_screen()
        """

        logger().debug('Filling user screen')

        user_text = self.config.user_cfg if admin_user and self.config.user_cfg else self.config.user
        password_text = self.config.password_cfg if admin_user and self.config.password_cfg else self.config.password

        shadow_root = not self.config.poui_login

        if self.config.smart_test and admin_user and not self.config.user_cfg:
            user_text = "admin"
            password_text = "1234"

        if self.webapp_shadowroot(shadow_root=shadow_root):
            get_user = '[name=cGetUser]'
            get_password = '[name=cGetPsw]'
        else:
            get_user = "[name='cGetUser'] > input"
            get_password = "[name='cGetPsw'] > input"

        if self.config.poui_login:
            self.twebview_context = True
            if not self.wait_element_timeout(term=".po-page-login-info-field .po-input",
                                             scrap_type=enum.ScrapType.CSS_SELECTOR, timeout=self.config.time_out * 3,
                                             main_container='body', twebview=True):
                self.reload_user_screen()

        elif not self.wait_element_timeout(term=get_user,
                                           scrap_type=enum.ScrapType.CSS_SELECTOR, timeout=self.config.time_out * 3,
                                           main_container='body'):
            self.reload_user_screen()

        self.set_multilanguage()

        try_counter = 0
        user_value = ''
        endtime = time.time() + self.config.time_out
        while (time.time() < endtime and (user_value.strip() != user_text.strip())):

            if self.config.poui_login:
                soup = self.get_current_DOM(twebview=True)
            else:
                soup = self.get_current_DOM()

            logger().info("Filling User")

            try:
                if self.config.poui_login:
                    user_element = next(iter(soup.select(".po-page-login-info-field .po-input")), None)
                else:
                    user_element = next(iter(soup.select(get_user)), None)

                if user_element is None:
                    self.restart_counter += 1
                    message = "Couldn't find User input element."
                    self.log_error(message)
                    raise ValueError(message)

            except AttributeError as e:
                self.log_error(str(e))
                raise AttributeError(e)

            if self.webapp_shadowroot():
                user = lambda: self.soup_to_selenium(user_element)
            else:
                if try_counter == 0:
                    user = lambda: self.soup_to_selenium(user_element)
                else:
                    user = lambda: self.soup_to_selenium(user_element.parent)

            self.set_element_focus(user())
            self.wait_until_to(expected_condition="element_to_be_clickable", element=user_element, locator=By.XPATH,
                               timeout=True)
            self.double_click(user())
            self.send_keys(user(), user_text)
            self.send_keys(user(), Keys.ENTER)

            if self.webapp_shadowroot(shadow_root=shadow_root):
                user_value = self.get_web_value(
                    self.driver.execute_script("return arguments[0].shadowRoot.querySelector('input')", user()))
            else:
                user_value = self.get_web_value(user())

            if not user_value:
                user_value = ''

            try_counter += 1 if (try_counter < 1) else -1

        if (user_value.strip() != user_text.strip()):
            self.restart_counter += 1
            message = "Couldn't fill User input element."
            self.log_error(message)
            raise ValueError(message)

        try_counter = 0
        password_value = ''
        endtime = time.time() + self.config.time_out
        while (time.time() < endtime and not password_value and self.config.password != ''):

            if self.config.poui_login:
                soup = self.get_current_DOM(twebview=True)
            else:
                soup = self.get_current_DOM()

            logger().info("Filling Password")
            if self.config.poui_login:
                password_element = next(iter(soup.select(".po-input-icon-right")), None)
            else:
                password_element = next(iter(soup.select(get_password)), None)

            if password_element is None:
                self.restart_counter += 1
                message = "Couldn't find User input element."
                self.log_error(message)
                raise ValueError(message)

            if self.webapp_shadowroot():
                password = lambda: self.soup_to_selenium(password_element)
            else:
                if try_counter == 0:
                    password = lambda: self.soup_to_selenium(password_element)
                else:
                    password = lambda: self.soup_to_selenium(password_element.parent)

            self.set_element_focus(password())
            self.wait_until_to(expected_condition="element_to_be_clickable", element=password_element, locator=By.XPATH,
                               timeout=True)
            self.click(password())
            self.send_keys(password(), Keys.HOME)
            self.send_keys(password(), password_text)

            if not self.config.poui_login:
                self.send_keys(password(), Keys.ENTER)
            else:
                self.send_keys(password(), Keys.TAB)

            password_value = self.get_web_value(password())

            if not password_value:
                password_value = ''

            self.wait_blocker()
            try_counter += 1 if (try_counter < 1) else -1

        if not password_value and self.config.password != '':
            self.restart_counter += 1
            message = "Couldn't fill User input element."
            self.log_error(message)
            raise ValueError(message)

        if self.webapp_shadowroot(shadow_root=shadow_root):
            wa_buttons = self.driver.execute_script(
                "return document.querySelectorAll('wa-button')")
            button_element = next(
                iter(list(filter(lambda x: self.language.enter.lower().strip() in x.text.lower().strip(), wa_buttons))),
                None)
        else:
            button_element = next(iter(list(filter(lambda x: self.language.enter in x.text, soup.select("button")))),
                                  None)

        if button_element is None:
            self.restart_counter += 1
            message = "Couldn't find Enter button."
            self.log_error(message)
            raise ValueError(message)

        if self.webapp_shadowroot(shadow_root=shadow_root):
            button = lambda: button_element
        else:
            button = lambda: self.driver.find_element(By.XPATH, xpath_soup(button_element))

        if self.config.poui_login:
            self.switch_to_iframe()

        self.send_action(self.click, button)

    def reload_user_screen(self):
        """
        [Internal]

        Refresh the page - retry load user_screen
        """

        logger().debug('Reloading user screen')

        server_environment = self.config.environment

        self.restart_browser()

        if self.config.coverage:
            self.driver.get(f"{self.config.url}/?StartProg=CASIGAADV&A={self.config.initial_program}&Env={self.config.environment}")

        if not self.config.skip_environment and not self.config.coverage:
            self.program_screen(self.config.initial_program, environment=server_environment)

        self.wait_element_timeout(term="[name='cGetUser']",
         scrap_type=enum.ScrapType.CSS_SELECTOR, timeout = self.config.time_out , main_container='body')


    def close_ballon_last_login(self):

        bs4_close_button = lambda: next(iter(self.get_current_DOM().select('[style*=ballon_close]')), None)

        if bs4_close_button():
            endtime = time.time() + self.config.time_out
            while time.time() < endtime and self.element_is_displayed(bs4_close_button()):
                button = self.soup_to_selenium(bs4_close_button())
                self.click(button)

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

        if change_env:
            label = self.language.confirm
            container = "body"
        else:
            label = self.language.confirm_in_environment_screen
            container = ".twindow"

        shadow_root = not self.config.poui_login

        self.filling_date(shadow_root=shadow_root, container=container)

        self.filling_group(shadow_root=shadow_root, container=container)

        self.filling_branch(shadow_root=shadow_root, container=container)

        self.filling_environment(shadow_root=shadow_root, container=container)

        if self.config.poui_login:
            buttons = self.filter_displayed_elements(
                self.web_scrap(label, scrap_type=enum.ScrapType.MIXED, optional_term="button", main_container="body",
                               twebview=True),
                True, twebview=True)
        else:
            optional_term = "wa-button" if self.webapp_shadowroot(shadow_root=shadow_root) else "button"
            if self.webapp_shadowroot(shadow_root=shadow_root):
                buttons = self.web_scrap(term=f"[caption*={label}]", scrap_type=enum.ScrapType.CSS_SELECTOR,
                                         main_container='body', optional_term=optional_term)
            else:
                buttons = self.web_scrap(label, scrap_type=enum.ScrapType.MIXED, optional_term=optional_term, second_term='button', main_container="body")

            buttons = list(filter(lambda x: self.element_is_displayed(x), buttons ))

        if len(buttons) > 1:
            button_element = buttons.pop()
        else:
            button_element = next(iter(buttons), None) if buttons else None

        button = lambda: self.soup_to_selenium(button_element)

        if not change_env and not button:
            self.restart_counter += 1
            message = f"Couldn't find {label} button."
            self.log_error(message)
            raise ValueError(message)

        if self.config.poui_login:
            self.switch_to_iframe()

        click = 1
        if self.config.poui_login:
            num_of_trying = 0
            max_num_of_trying = 5

            self.switch_to_iframe()
            logger().info('Clicking on Button')

            self.wait_blocker()
            while max_num_of_trying >= num_of_trying:
                try:
                    self.click(button(), enum.ClickType(click))
                    time.sleep(1)
                except:
                    logger().info('Button click completed')
                    break
                num_of_trying += 1
        else:
            endtime = time.time() + self.config.time_out
            while time.time() < endtime and self.element_is_displayed(button()):
                logger().info('Clicking on Button')
                self.wait_blocker()
                self.click(button(), enum.ClickType(click))
                time.sleep(2)
                click += 1
                if click == 4:
                    click = 1

        if not self.config.poui_login:
            if self.webapp_shadowroot(shadow_root=shadow_root):
                self.wait_element_timeout(term=self.language.database, scrap_type=enum.ScrapType.MIXED, timeout = 120, optional_term='wa-text-view', main_container="body", presence=False)
            else:
                self.wait_element(term=self.language.database, scrap_type=enum.ScrapType.MIXED, presence=False,
                                  optional_term="input", main_container=container)
        else:
            self.driver.switch_to.default_content()
            self.config.poui_login = False

    def filling_date(self, shadow_root=None, container=None):
        """
        [Internal]
        """
        d = self.config.data_delimiter
        if not self.config.date:
            self.config.date = datetime.today().strftime(f'%d{d}%m{d}%Y')

        click_type = 1
        send_type = 1
        base_date_value = ''
        group_bs = None
        datepicker_main = None

        endtime = time.time() + self.config.time_out / 2
        while (time.time() < endtime and (base_date_value.strip() != self.config.date.strip())):

            if self.config.poui_login:
                base_dates = self.web_scrap(term=".po-datepicker", main_container='body',
                                            scrap_type=enum.ScrapType.CSS_SELECTOR, twebview=True)
            else:
                if self.webapp_shadowroot(shadow_root=shadow_root):
                    base_dates = self.web_scrap(term="[name='dDataBase'], [name='__dInfoData']",
                                                scrap_type=enum.ScrapType.CSS_SELECTOR,
                                                main_container='body',
                                                optional_term='wa-text-input')
                    if not group_bs:
                        group_bs = self.group_element(shadow_root, container)
                        if group_bs:
                            group_element = lambda: self.soup_to_selenium(group_bs)
                            group_value = self.get_web_value(group_element())
                else:
                    base_dates = self.web_scrap(term="[name='dDataBase'] input, [name='__dInfoData'] input",
                                                scrap_type=enum.ScrapType.CSS_SELECTOR, label=True,
                                                main_container=container)

            if base_dates:
                if len(base_dates) > 1:
                    base_date = base_dates.pop()
                else:
                    base_date = next(iter(base_dates), None)

                if base_date:
                    if self.webapp_shadowroot() and not self.config.poui_login:
                        date = lambda: next(iter(self.find_shadow_element('input', self.soup_to_selenium(base_date))),
                                            None)
                        datepicker_is_valid =lambda: True
                    else:
                        date = lambda: self.soup_to_selenium(base_date)
                        datepicker_main = base_date.find_parent('po-datepicker')
                        if datepicker_main:
                            datepicker_element = self.soup_to_selenium(datepicker_main)
                            datepicker_is_valid = lambda: self.poui_datepicker_is_valid(datepicker_element)

                    if self.config.poui_login:
                        self.switch_to_iframe()

                    logger().info(f'Filling Date: "{self.config.date}"')

                    self.wait_blocker()
                    for i in range(3):
                        self.click(date(), click_type=enum.ClickType(click_type))
                        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.HOME).key_up(Keys.CONTROL).perform()
                        ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys(
                            Keys.END).key_up(Keys.CONTROL).key_up(Keys.SHIFT).perform()

                        self.try_send_keys(date, self.config.date, try_counter=send_type)

                        base_date_value = self.merge_date_mask(self.config.date, self.get_web_value(date()))
                        if self.config.poui_login:
                            ActionChains(self.driver).send_keys(Keys.TAB * 2).perform()

                        time.sleep(1)
                        send_type += 1
                        if send_type > 3:
                            send_type = 1

                        if base_date_value.strip() == self.config.date.strip() and datepicker_is_valid():
                            break

                        if not self.is_active_element(date()) and click_type == 3:
                            self.filling_group(shadow_root, container, group_value)

                click_type += 1
                if click_type > 3:
                    click_type = 1


    def poui_datepicker_is_valid(self, datepicker):
        """

        :param datepicker: beautiful soup datepicker tag component
        :type datepicker: BeautifulSoup

        :return: True when valid else False
        """
        try:
            datepicker_class = datepicker.get_attribute("class").split()
            return "ng-valid" in datepicker_class
        except (AttributeError, TypeError) as e:
            logger().debug(f'Something wrong with Datepicker, please check it: {e}')
            return False


    def filling_group(self, shadow_root=None, container=None, group_value=''):
        """
        [Internal]
        """

        click_type = 1
        group_current_value = ''
        if group_value:
            group_value = group_value
        else:
            group_value = self.config.group

        endtime = time.time() + self.config.time_out / 2
        while (time.time() < endtime and (group_current_value.strip() != group_value.strip())):

            group_element = self.group_element(shadow_root, container)

            if group_element:
                group = lambda: self.soup_to_selenium(group_element)

                if self.config.poui_login:
                    self.switch_to_iframe()

                logger().info(f'Filling Group: "{group_value}"')
                self.wait_blocker()
                self.click(group(), click_type=enum.ClickType(click_type))
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.HOME).key_up(Keys.CONTROL).perform()
                ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys(
                    Keys.END).key_up(Keys.CONTROL).key_up(Keys.SHIFT).perform()
                self.send_keys(group(), group_value)
                group_current_value = self.get_web_value(group())
                if self.config.poui_login:
                    ActionChains(self.driver).send_keys(Keys.TAB).perform()

                time.sleep(1)
                click_type += 1
                if click_type > 3:
                    click_type = 1

        if not self.config.group:
            poui_iframe = True if self.config.poui_login else False
            group_content =  self.get_web_value(self.soup_to_selenium(self.group_element(shadow_root, container), twebview=poui_iframe))
            if group_content:
                self.config.group = group_content
            else:
                self.log_error(f'Please, fill group parameter in Setup() method')

    def group_element(self, shadow_root, container):

        if self.config.poui_login:
            group_elements = self.web_scrap(term=self.language.group, main_container='body',
                                            scrap_type=enum.ScrapType.TEXT, twebview=True)

            if group_elements:
                group_element = next(iter(group_elements))
                group_element = group_element.find_parent('pro-company-lookup')
                return next(iter(group_element.select('input')), None)
        else:
            if self.webapp_shadowroot(shadow_root=shadow_root):
                group_elements = self.web_scrap(term="[name='cGroup'], [name='__cGroup']",
                                                scrap_type=enum.ScrapType.CSS_SELECTOR,
                                                main_container='body',
                                                optional_term='wa-text-input')
            else:
                group_elements = self.web_scrap(term="[name='cGroup'] input, [name='__cGroup'] input",
                                                scrap_type=enum.ScrapType.CSS_SELECTOR, label=True,
                                                main_container=container)

            if group_elements:
                if len(group_elements) > 1:
                    return group_elements.pop()
                else:
                    return next(iter(group_elements), None)

    def filling_branch(self, shadow_root=None, container=None):
        """
        [Internal]
        """

        click_type = 1
        branch_value = ''
        endtime = time.time() + self.config.time_out / 2
        while (time.time() < endtime and (branch_value.strip() != self.config.branch.strip())):

            if self.config.poui_login:
                branch_elements = self.web_scrap(term=self.language.branch, main_container='body',
                                                 scrap_type=enum.ScrapType.TEXT, twebview=True)

                if branch_elements:
                    branch_element = next(iter(branch_elements))
                    branch_element = branch_element.find_parent('pro-branch-lookup')
                    branch_element = next(iter(branch_element.select('input')), None)
            else:
                if self.webapp_shadowroot(shadow_root=shadow_root):
                    branch_elements = self.web_scrap(term="[name='cFil'], [name='__cFil']",
                                                     scrap_type=enum.ScrapType.CSS_SELECTOR,
                                                     main_container='body',
                                                     optional_term='wa-text-input')
                else:
                    branch_elements = self.web_scrap(term="[name='cFil'] input, [name='__cFil'] input",
                                                     scrap_type=enum.ScrapType.CSS_SELECTOR, label=True,
                                                     main_container=container)

                if branch_elements:
                    if len(branch_elements) > 1:
                        branch_element = branch_elements.pop()
                    else:
                        branch_element = next(iter(branch_elements), None)

            if branch_element:
                branch = lambda: self.soup_to_selenium(branch_element)

                if self.config.poui_login:
                    self.switch_to_iframe()

                logger().info(f'Filling Branch: "{self.config.branch}"')
                self.wait_blocker()
                self.click(branch(), click_type=enum.ClickType(click_type))
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.HOME).key_up(Keys.CONTROL).perform()
                ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys(
                    Keys.END).key_up(Keys.CONTROL).key_up(Keys.SHIFT).perform()
                self.send_keys(branch(), self.config.branch)
                branch_value = self.get_web_value(branch())
                if self.config.poui_login:
                    ActionChains(self.driver).send_keys(Keys.TAB).perform()

                time.sleep(1)
                click_type += 1
                if click_type > 3:
                    click_type = 1

    def filling_environment(self, shadow_root=None, container=None):
        """
        [Internal]
        """

        click_type = 1
        env_value = ''
        environment_element = None
        enable = True
        endtime = time.time() + self.config.time_out / 2
        while (time.time() < endtime and env_value.strip() != self.config.module.strip() and enable):

            if self.config.poui_login:
                environment_elements = self.web_scrap(term=self.language.environment, main_container='body',
                                                      scrap_type=enum.ScrapType.TEXT, twebview=True)

                if environment_elements:
                    environment_element = next(iter(environment_elements))
                    environment_element = environment_element.find_parent('pro-system-module-lookup')
                    environment_element = next(iter(environment_element.select('input')), None)
            else:
                if self.webapp_shadowroot(shadow_root=shadow_root):
                    environment_elements = self.web_scrap(term="[name='cAmb']", scrap_type=enum.ScrapType.CSS_SELECTOR,
                                                          main_container='body',
                                                          optional_term='wa-text-input')
                else:
                    environment_elements = self.web_scrap(term="[name='cAmb'] input",
                                                          scrap_type=enum.ScrapType.CSS_SELECTOR, label=True,
                                                          main_container=container)

                if environment_elements:
                    if len(environment_elements) > 1:
                        environment_element = environment_elements.pop()
                    else:
                        environment_element = next(iter(environment_elements), None)

            if environment_element:
                env = lambda: self.soup_to_selenium(environment_element)

                if self.config.poui_login:
                    self.switch_to_iframe()
                    enable = env().is_enabled()
                else:
                    enable = ("disabled" not in environment_element.parent.attrs[
                        "class"] and env().is_enabled()) and not env().get_attribute('disabled')

                if enable:
                    if self.config.poui_login:
                        self.switch_to_iframe()

                    logger().info(f'Filling Environment: "{self.config.module}"')
                    self.wait_blocker()
                    self.click(env(), click_type=enum.ClickType(click_type))
                    ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.HOME).key_up(
                        Keys.CONTROL).perform()
                    ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys(
                        Keys.END).key_up(Keys.CONTROL).key_up(Keys.SHIFT).perform()
                    self.send_keys(env(), self.config.module)
                    env_value = self.get_web_value(env())
                    if self.config.poui_login:
                        ActionChains(self.driver).send_keys(Keys.TAB).perform()
                    time.sleep(1)
                    self.close_warning_screen()

                    time.sleep(1)
                    click_type += 1
                    if click_type > 3:
                        click_type = 1

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
            if self.webapp_shadowroot():
                if type(element) == Tag:
                    element = self.soup_to_selenium(element)
                element.click()
            else:
                self.click(self.driver.find_element(By.XPATH, xpath_soup(element)))
            self.environment_screen(True)
        else:
            self.log_error("Change Environment method did not find the element to perform the click or the element was not visible on the screen.")

        self.wait_blocker()
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

            if self.webapp_shadowroot():
                selector="wa-button"
                class_selector=".dict-tbutton"
            else:
                selector="button"
                class_selector=".tpanel > .tpanel > .tbutton"

            if self.wait_element_timeout(term=self.language.change_environment, scrap_type=enum.ScrapType.MIXED, timeout = 1, optional_term=selector, main_container="body"):
                return next(iter(self.web_scrap(term=self.language.change_environment, scrap_type=enum.ScrapType.MIXED, optional_term=selector, main_container="body")), None)
            elif self.wait_element_timeout(term=class_selector, scrap_type=enum.ScrapType.CSS_SELECTOR, timeout = 1, main_container="body"):
                tbuttons = self.filter_displayed_elements(self.web_scrap(term=class_selector, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body"), True)
                if self.webapp_shadowroot():
                    element = next(iter(list(filter(lambda x: 'TOTVS' in x.get('caption'), tbuttons))), None)
                else:
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
        dialog_term = "wa-dialog" if self.webapp_shadowroot() else ".tmodaldialog"
        button_term = ".dict-tbrowsebutton" if self.webapp_shadowroot() else ".tbrowsebutton"
        soup = self.get_current_DOM()
        modals = self.zindex_sort(soup.select(dialog_term), True)
        if modals and self.element_exists(term=f"{dialog_term} {button_term}", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body", check_error = False):
            buttons = modals[0].select(button_term)
            if buttons:
                if self.webapp_shadowroot():
                    regex = r"(<[^>]*>)?"
                    close_button = list(filter(lambda x: x.get('caption') and re.sub(regex, '', x['caption']).strip() == self.language.close ,buttons))
                else:
                    close_button = list(filter(lambda x: x.text == self.language.close, buttons))
                close_button = next(iter(close_button),None)
                time.sleep(0.5)
                selenium_close_button = lambda: self.driver.find_element(By.XPATH, xpath_soup(close_button))
                if close_button:
                    try:
                        self.wait_until_to( expected_condition = "element_to_be_clickable", element = close_button , locator = By.XPATH)
                        self.click(selenium_close_button())
                    except:
                        pass
    
    def check_screen_element(self, term="", selector=None, scraptype=enum.ScrapType.MIXED, check_error=True, twebview=False):
        """
        [Internal]

        This method checks if the screen element is displayed.
        """

        element_exists = True if self.element_exists(term=term, scrap_type=scraptype, optional_term=selector, main_container="body", check_error=check_error, twebview=twebview) else False
        
        logger().debug(f'Checking screen element: "{term}": {element_exists}')

        return element_exists
    
    def coin_screen_selectors(self):
        """
        [Internal]

        This method returns the selectors for the coin screen.
        """
        return self.get_screen_selectors("coin")

    def warning_screen_selectors(self):
        """
        [Internal]

        This method returns the selectors for the warning screen.
        """
        return self.get_screen_selectors("warning")

    def news_screen_selectors(self):
        """
        [Internal]

        This method returns the selectors for the news screen.
        """
        return self.get_screen_selectors("news")
    
    def browse_screen_selectors(self):
        """
        [Internal]

        This method returns the selectors for the browse screen.
        """
        return self.get_screen_selectors("browse")

    def get_screen_selectors(self, screen_type):
        """
        [Internal]

        This method returns the selectors for different screens based on the screen type.
        """

        selectors = {
            "coin": {
                "shadowroot": "wa-dialog > wa-panel > wa-text-view",
                "default": ".tmodaldialog > .tpanel > .tsay"
            },
            "warning": {
                "shadowroot": "wa-dialog",
                "default": ".ui-dialog > .ui-dialog-titlebar"
            },
            "news": {
                "shadowroot": "wa-dialog> .dict-tpanel > .dict-tsay",
                "default": ".tmodaldialog > .tpanel > .tsay"
            },
            "browse": {
                "shadowroot": "[style*='fwskin_seekbar_ico']"
            }
        }

        if self.webapp_shadowroot():
            return selectors[screen_type]["shadowroot"]
        else:
            return selectors[screen_type]["default"]
        
    def check_browse_screen(self):
        """
        [Internal]

        Checks if the browse screen is displayed.
        """

        selector = self.browse_screen_selectors()

        return self.check_screen_element(term=selector, scraptype=enum.ScrapType.CSS_SELECTOR)

    def check_coin_screen(self):
        """
        [Internal]

        Checks if the coin screen is displayed.
        """

        selector = self.coin_screen_selectors()

        return self.check_screen_element(term=self.language.coins, selector=selector)
    
    def check_warning_screen(self):
        """
        [Internal]

        Checks if the warning screen is displayed.
        """

        selector = self.warning_screen_selectors()

        return self.check_screen_element(term=self.language.warning, selector=selector)
    
    def check_news_screen(self):
        """
        [Internal]

        Checks if the news screen is displayed.
        """
        selector = self.news_screen_selectors()

        news = self.check_screen_element(term=self.language.news, selector=selector, check_error=False)
        text_inside_iframe = self.check_screen_element(term=self.language.news, selector='header', check_error=False, twebview=True)
        element_on_screen = news or text_inside_iframe
        return element_on_screen
    
    def check_screen(self):
        """
        [Internal]

        Checks if any of the screens (warning, coin, news) are displayed.
        """

        return any([self.check_warning_screen(), self.check_coin_screen(), self.check_news_screen(), self.check_browse_screen()])

    def close_coin_screen(self):
        """
        [Internal]

        Closes the coin screen.

        Usage:

        >>> # Calling the method:
        >>> self.close_coin_screen()
        """

        logger().debug('Closing coin screen!')

        selector = self.coin_screen_selectors()

        soup = self.get_current_DOM()
        modals = self.zindex_sort(soup.select(selector), True)
        if modals and self.check_coin_screen():
            self.SetButton(self.language.shortconfirm)

    def close_coin_screen_after_routine(self):
        """
        [internal]
        This method is responsible for closing the "coin screen" that opens after searching for the routine
        """
        if self.webapp_shadowroot():
            dialog_term = 'wa-tab-page > wa-dialog'
            workspace_term = 'wa-tab-page > wa-dialog'
            coin_term = f'wa-dialog > .dict-tpanel > [caption ={self.language.coins}]'
        else:
            dialog_term = '.tmodaldialog'
            workspace_term = '.workspace-container'
            coin_term = '.tmodaldialog > .tpanel > .tsay'

        self.wait_element_timeout(term=workspace_term, scrap_type=enum.ScrapType.CSS_SELECTOR,
            timeout = self.config.time_out, main_container="body", check_error = False)

        tmodaldialog_list = []

        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not tmodaldialog_list):
            try:
                soup = self.get_current_DOM()
                tmodaldialog_list = soup.select(dialog_term)

                self.wait_element_timeout(term=self.language.coins, scrap_type=enum.ScrapType.MIXED,
                 optional_term=coin_term, timeout=10, main_container = "body", check_error = False)

                tmodal_coin_screen = self.web_scrap(term=self.language.coins, scrap_type=enum.ScrapType.MIXED,
                    optional_term=coin_term, main_container="body", check_error = False, check_help = False)

                if tmodal_coin_screen:
                    tmodal_coin_screen = next(iter(tmodal_coin_screen), None)

                if tmodal_coin_screen and tmodal_coin_screen in tmodaldialog_list:
                    tmodaldialog_list.remove(tmodal_coin_screen.parent.parent)

                self.close_coin_screen()

                if self.check_screen():
                    return

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

        logger().debug('Closing warning screen!')

        selector = self.warning_screen_selectors()

        time.sleep(1)
        soup = self.get_current_DOM()
        modals = self.zindex_sort(soup.select(selector), True)
        if modals and self.check_warning_screen():
            self.set_button_x()


    def close_warning_screen_after_routine(self):
        """
        [internal]
        This method is responsible for closing the "warning screen" that opens after searching for the routine
        """
        if self.webapp_shadowroot():
            dialog_term = f'wa-dialog [title={self.language.warning}]'
            title_term = f'wa-dialog [title={self.language.warning}]'

        else:
            dialog_term = '.ui-dialog'
            title_term = '.ui-dialog-titlebar'

        uidialog_list = []

        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not uidialog_list):
            try:
                soup = self.get_current_DOM()
                uidialog_list = soup.select(dialog_term)

                tmodal_warning_screen = self.web_scrap(term=self.language.warning, scrap_type=enum.ScrapType.MIXED,
                    optional_term=title_term, main_container="body", check_error = False, check_help = False)

                if tmodal_warning_screen:
                    tmodal_warning_screen = next(iter(tmodal_warning_screen), None)

                if tmodal_warning_screen and tmodal_warning_screen in uidialog_list:
                    uidialog_list.remove(tmodal_warning_screen.parent.parent)

                self.close_warning_screen()

                if self.check_screen():
                    return

            except Exception as e:
                logger().exception(str(e))

    def close_news_screen(self):
        """
        [Internal]

        Closes the news do programa screen.

        Usage:

        >>> # Calling the method:
        >>> self.close_news_screen()
        """

        logger().debug('Closing news screen!')

        selector = self.news_screen_selectors()

        soup = self.get_current_DOM()
        modals = self.zindex_sort(soup.select(".tmodaldialog, wa-dialog"), True)
        if modals and self.check_news_screen():
            self.SetButton(self.language.close)

    def close_news_screen_after_routine(self):
        """
        [internal]
        This method is responsible for closing the "news screen" that opens after searching for the routine
        """

        tmodaldialog_list = []

        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not tmodaldialog_list):
            try:
                soup = self.get_current_DOM()
                tmodaldialog_list = soup.select('.tmodaldialog')

                self.wait_element_timeout(term=self.language.news, scrap_type=enum.ScrapType.MIXED,
                 optional_term=".tsay", timeout=10, main_container = "body", check_error = False)

                tmodal_news_screen = self.web_scrap(term=self.language.news, scrap_type=enum.ScrapType.MIXED,
                    optional_term=".tmodaldialog > .tpanel > .tsay", main_container="body", check_error = False, check_help = False)

                if tmodal_news_screen:
                    tmodal_news_screen = next(iter(tmodal_news_screen), None)

                if tmodal_news_screen and tmodal_news_screen in tmodaldialog_list:
                    tmodaldialog_list.remove(tmodal_news_screen.parent.parent)

                self.close_news_screen()

                if self.check_screen():
                    return

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

        logger().info('Getting log info')

        if self.webapp_shadowroot():
            term_dialog = 'wa-dialog'
        else:
            term_dialog = '.tmodaldialog'

        self.SetLateralMenu(self.language.menu_about, save_input=False)
        self.wait_element(term=term_dialog, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        self.wait_until_to(expected_condition = "presence_of_all_elements_located", element = term_dialog, locator= By.CSS_SELECTOR)

        soup = self.get_current_DOM()
        if self.webapp_shadowroot():
            labels = list(soup.select("wa-dialog .dict-tpanel .dict-tsay"))
            release_element = next(iter(filter(lambda x: x.attrs['caption'].startswith(self.language.release), labels)), None)
            database_element = next(iter(filter(lambda x: x.attrs['caption'].startswith(self.language.topdatabase), labels)), None)
            lib_element = next(iter(filter(lambda x: x.attrs['caption'].startswith(self.language.libversion), labels)), None)
            build_element = next(iter(filter(lambda x: x.attrs['caption'].startswith(self.language.build), labels)), None)

        else:
            labels = list(soup.select(".tmodaldialog .tpanel .tsay"))
            release_element = next(iter(filter(lambda x: x.text.startswith(self.language.release), labels)), None)
            database_element = next(iter(filter(lambda x: x.text.startswith(self.language.topdatabase), labels)), None)
            lib_element = next(iter(filter(lambda x: x.text.startswith(self.language.libversion), labels)), None)
            build_element = next(iter(filter(lambda x: x.text.startswith(self.language.build), labels)), None)

        if release_element:
            release = release_element.text.split(":")[1].strip() if release_element.text else release_element.attrs['caption'].split(":")[1].strip()
            self.log.release = release
            self.log.version = release.split(".")[0]

        if database_element:
            self.log.database = database_element.text.split(":")[1].strip() if database_element.text else database_element.attrs['caption'].split(":")[1].strip()

        if build_element:
            self.log.build_version = build_element.text.split(":")[1].strip() if build_element.text else build_element.attrs['caption'].split(":")[1].strip()

        if lib_element:
            self.log.lib_version = lib_element.text.split(":")[1].strip() if lib_element.text else lib_element.attrs['caption'].split(":")[1].strip()

        self.SetButton(self.language.close)

        if self.webapp_shadowroot():
            self.wait_element(term=self.language.close, scrap_type=enum.ScrapType.MIXED,
                            optional_term='wa-button, button, .thbutton', presence=False)

    def set_log_info_tss(self):

        self.log.country = self.config.country
        self.log.execution_id = self.config.execution_id
        self.log.issue = self.config.issue

        label_element = None

        self.SetButton("Sobre...")

        soup = self.get_current_DOM()
        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not label_element):
            soup = self.get_current_DOM()
            if self.webapp_shadowroot():
                container = self.get_current_shadow_root_container()
                if container.has_attr('title') and "Sobre o TSS..." in container.get('title'):
                    element_header = self.driver.execute_script("return arguments[0].shadowRoot.querySelector('wa-dialog-header')",self.soup_to_selenium(container))
                    if element_header:
                        label_element = element_header
                else:
                    label_element = soup.find_all("label", string="Versão do TSS:")

        if not label_element:
            raise ValueError("SetupTss fail about screen not found")

        if self.webapp_shadowroot():
            shadowroot_labels = self.driver.execute_script("return arguments[0].querySelectorAll('wa-text-view')",self.soup_to_selenium(container))
            labels = list(map(lambda x: x.text, shadowroot_labels))
        else:
            labels = list(map(lambda x: x.text, soup.select("label")))
        label = labels[labels.index("Versão do TSS:")+1]
        self.log.release = next(iter(re.findall(r"[\d.]*\d+", label)), None)

        if self.webapp_shadowroot():
            self.driver.execute_script("return arguments[0].shadowRoot.querySelector('button').click()",element_header)
        else:
            self.SetButton('x')

    def set_log_info_config(self):
        """
        [Internal]
        """

        if self.config.release:
            self.log.release = self.config.release
            self.log.version = self.config.release.split('.')[0]

        if self.config.top_database:
            self.log.database = self.config.top_database

        if self.config.build_version:
            self.log.build_version = self.config.build_version

        if self.config.lib_version:
            self.log.lib_version = self.config.lib_version


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

    def Program(self, program_name):
        """
        Method that sets the program in the initial menu search field.

        .. note::
            Only used when the Initial Program is the module Ex: SIGAFAT.

        :param program_name: The program name
        :type program_name: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.Program("MATA020")
        """
        self.config.routine_type = 'Program'
        self.config.routine = program_name

        if self.config.log_info_config:
            self.set_log_info_config()

        if self.config.new_log:
            if not self.log.release:
                self.log_error_newlog()

        if not self.log.program:
            self.log.program = program_name
        self.set_program(program_name)


    def set_program(self, program):
        """
        [Internal]

        Method that sets the program in the initial menu search field.

        :param program: The program name
        :type program: str

        Usage:

        >>> # Calling the method:
        >>> self.set_program("MATA020")
        """

        cget_term = '[name=cGet]'
        try:
            logger().info(f"Setting program: {program}")

            self.escape_to_main_menu()

            self.wait_element(term=cget_term, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")

            soup = self.get_current_DOM()
            tget = next(iter(soup.select(cget_term)), None)
            if tget:
                if self.webapp_shadowroot():
                    tget_img = next(iter(tget.select(".button-image")), None)
                    s_tget_img = lambda: self.soup_to_selenium(tget_img)

                    s_tget = lambda: self.soup_to_selenium(tget)
                    tget_input = self.find_child_element('input', s_tget())[0]
                else:
                    tget_input = next(iter(tget.select("input")), None)
                    tget_img = next(iter(tget.select("img")), None)
                    if tget_img is None or not self.element_is_displayed(tget_img):
                        self.log_error("Couldn't find Program field.")
                    s_tget = lambda : self.driver.find_element(By.XPATH, xpath_soup(tget_input))
                    s_tget_img = lambda : self.driver.find_element(By.XPATH, xpath_soup(tget_img))
                    self.wait_until_to( expected_condition = "element_to_be_clickable", element = tget_input, locator = By.XPATH )

                self.double_click(s_tget())
                self.set_element_focus(s_tget())
                self.send_keys(s_tget(), Keys.HOME)
                ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()

                if self.webapp_shadowroot():
                    self.find_child_element('input', s_tget())
                else:
                    self.wait_until_to( expected_condition = "element_to_be_clickable", element = tget_input, locator = By.XPATH )

                self.send_keys(s_tget(), program)
                current_value = self.get_web_value(s_tget()).strip()

                endtime = time.time() + self.config.time_out
                while(time.time() < endtime and current_value != program):
                    self.send_keys(s_tget(), Keys.BACK_SPACE)
                    if not self.webapp_shadowroot():
                        self.wait_until_to( expected_condition = "element_to_be_clickable", element = tget_input, locator = By.XPATH, timeout=True)

                    self.send_keys(s_tget(), program)
                    current_value = self.get_web_value(s_tget()).strip()

                if current_value.strip() != program.strip():
                    self.log_error(f"Couldn't fill program input - current value:  {current_value} - Program: {program}")
                self.set_element_focus(s_tget_img())

                if self.webapp_shadowroot():
                    self.find_child_element('input', s_tget())
                else:
                    self.wait_until_to( expected_condition = "element_to_be_clickable", element = tget_input, locator = By.XPATH )

                self.wait_until_to( expected_condition = "element_to_be_clickable", element = tget_img, locator = By.XPATH )
                self.send_action(self.click, s_tget_img)
                self.wait_element_is_not_displayed(tget_img)
                self.close_news_screen()

            if self.config.initial_program.lower() == 'sigaadv':
                self.close_warning_screen_after_routine()
                self.close_coin_screen_after_routine()
                self.close_news_screen_after_routine()

        except AssertionError as error:
            logger().exception(f"Warning set program raise AssertionError: {str(error)}")
            raise error
        except Exception as e:
            logger().exception(str(e))

    def escape_to_main_menu(self):
        """

        """

        endtime = time.time() + self.config.time_out /2
        while time.time() < endtime and self.check_layers('wa-dialog') > 1:
            if not self.webapp_shadowroot():
                ActionChains(self.driver).key_down(Keys.ESCAPE).perform()
            elif self.check_layers('wa-dialog') > 1:
                logger().info('Escape to menu')
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

            if any([self.check_warning_screen(), self.check_coin_screen(), self.check_news_screen()]):
                if self.check_layers('wa-dialog') > 1:
                    logger().info('Found layers after Escape to menu')
                    self.close_screen_before_menu()
            # wait trasitions between screens to avoid errors in layers number
            self.wait_element_timeout(term='wa-dialog', scrap_type=enum.ScrapType.CSS_SELECTOR,
                                      position=2, timeout=6, main_container='body')

    def check_layers(self, term):
        """
        [Internal]
        """

        soup = self.get_current_DOM()

        return len(soup.select(term))

    def standard_search_field(self, term, name_attr=False,send_key=False):
        """
        [Internal]

        Do the standard query(F3)
        this method
        1.Search the field
        2.Search icon "lookup"
        3.Click()

        :param term: The term that must be searched.
        :type term: str
        :param name_attr: If true searchs element by name.
        :type name_attr: bool
        :param send_key: Try open standard search field send key F3 (no click).
        :type send_key: bool

        Usage:

        >>> # To search using a label name:
        >>> self.standard_search_field(name_label)
        >>> #------------------------------------------------------------------------
        >>> # To search using the name of input:
        >>> self.standard_search_field(field='A1_EST',name_attr=True)
        >>> #------------------------------------------------------------------------
        >>> # To search using the name of input and do action with a key:
        >>> oHelper.F3(field='A1_EST',name_attr=True,send_key=True)
        """
        endtime = self.config.time_out + time.time()

        try:
            #wait element
            if name_attr:
                self.wait_element(term=f"[name$='{term}']", scrap_type=enum.ScrapType.CSS_SELECTOR)
            else:
                self.wait_element(term)
            # find element
            element = self.get_field(term,name_attr).find_parent() if not self.webapp_shadowroot() else self.get_field(term,name_attr)
            if not(element):
                raise Exception("Couldn't find element")

            logger().debug("Field successfully found")
            if(send_key):
                input_field = lambda: self.driver.find_element(By.XPATH, xpath_soup(element))
                self.set_element_focus(input_field())
                container = self.get_current_container()
                self.send_keys(input_field(), Keys.F3)
            else:
                icon = next(iter(element.select("img[src*=fwskin_icon_lookup], img[src*=btpesq_mdi], [style*=fwskin_icon_lookup]")),None)
                icon_s = self.soup_to_selenium(icon)
                container = self.get_current_container()
                self.click(icon_s)

            container_end = self.get_current_container()
            if (container['id']  == container_end['id']):
                input_field = lambda: self.driver.find_element(By.XPATH, xpath_soup(element))
                self.set_element_focus(input_field())
                self.send_keys(input_field(), Keys.F3)

            while( time.time() < endtime and container['id']  == container_end['id']):
                container_end = self.get_current_container()
                time.sleep(0.01)

            if time.time() > endtime:
                logger().debug("Timeout: new container not found.")
            else:
                logger().debug("Success")

        except Exception as e:
            logger().exception(str(e))

    def SearchBrowse(self, term, key=None, identifier=None, index=False, column=None):
        """
        Searchs a term on Protheus Webapp.

        It will search using the default search key, but if a **key** is provided
        it will search using the chosen key.

        It will search using the first search box on the screen, but if an **identifier**
        is provided, it will search on the chosen search box.

        :param term: The term that must be searched.
        :type term: str
        :param key: The search key to be chosen on the search dropdown. - **Default:** None
        :type key: str
        :param identifier: The identifier of the search box. If none is provided, it defaults to the first of the screen. - **Default:** None
        :type identifier: str
        :param index: Whether the key is an index or not. - **Default:** False
        :type index: bool

        Usage:

        >>> # To search using the first search box and default search key:
        >>> oHelper.SearchBrowse("D MG 001")
        >>> #------------------------------------------------------------------------
        >>> # To search using the first search box and a chosen key:
        >>> oHelper.SearchBrowse("D MG 001", key="Branch+id")
        >>> #------------------------------------------------------------------------
        >>> # To search using a chosen search box and the default search key:
        >>> oHelper.SearchBrowse("D MG 001", identifier="Products")
        >>> #------------------------------------------------------------------------
        >>> # To search using a chosen search box and a chosen search key:
        >>> oHelper.SearchBrowse("D MG 001", key="Branch+id", identifier="Products")
        >>> #------------------------------------------------------------------------
        >>> # To search using the first search box and a chosen column:
        >>> oHelper.SearchBrowse("D MG 001", column="Branch+id")
        >>> #------------------------------------------------------------------------
        """

        self.wait_blocker()

        logger().info(f"Searching: {term}")
        if index and isinstance(key, int):
            key -= 1
        browse_elements = self.get_search_browse_elements(identifier)
        if key:
            self.search_browse_key(key, browse_elements, index)
        elif column:
            self.search_browse_column(column, browse_elements, index)
        self.fill_search_browse(term, browse_elements)


    def get_search_browse_elements(self, panel_name=None):
        """
        [Internal]

        Returns a tuple with the search browse elements in this order:
        Key Dropdown, Input, Icon.

        :param panel_name: The identifier of the search box. If none is provided, it defaults to the first of the screen. - **Default:** None
        :type panel_name: str

        :return: Tuple with the Key Dropdown, Input and Icon elements of a search box
        :rtype: Tuple of Beautiful Soup objects.

        Usage:

        >>> # Calling the method:
        >>> search_elements = self.get_search_browse_elements("Products")
        """
        if self.webapp_shadowroot():
            dialog_term = 'wa-tab-page > wa-dialog'
        else:
            dialog_term = '.tmodaldialog'

        success = False
        container = None
        elements_soup = None

        self.wait_element_timeout(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR, timeout = self.config.time_out)
        endtime = time.time() + self.config.time_out

        while (time.time() < endtime and not success):
            soup = self.get_current_DOM()
            search_index = self.get_panel_name_index(panel_name) if panel_name else 0
            containers = self.zindex_sort(soup.select(dialog_term), reverse=True)
            container = next(iter(containers), None)

            if container:
                elements_soup = container.select("[style*='fwskin_seekbar_ico']")

            if elements_soup:
                if elements_soup and len(elements_soup) -1 >= search_index:
                    if self.webapp_shadowroot():
                        browse_div = elements_soup[search_index].find_parent()
                    else:
                        browse_div = elements_soup[search_index].find_parent().find_parent()
                    success = True

        if not elements_soup:
            self.log_error("Couldn't find search browse.")

        if not container:
            self.log_error("Couldn't find container of element.")

        if not success:
            self.log_error("Get search browse elements couldn't find browser div")

        if self.webapp_shadowroot():
            browse_tget = browse_div.select(".dict-tget")[0]
            browse_key = browse_div.select(".dict-tbutton")[0]
            browse_input = browse_tget
            browse_icon = browse_tget.select(".button-image")[0]
        else:
            browse_tget = browse_div.select(".tget")[0]
            browse_key = browse_div.select(".tbutton button")[0]
            browse_input = browse_tget.select("input")[0]
            browse_icon = browse_tget.select("img")[0]

        return (browse_key, browse_input, browse_icon)


    def search_browse_key(self, search_key, search_elements, index=False):
        """
        [Internal]

        Chooses the search key to be used during the search.

        :param search_key: The search key to be chosen on the search dropdown
        :type search_key: str
        :param search_elements: Tuple of Search elements
        :type search_elements: Tuple of Beautiful Soup objects
        :param index: Whether the key is an index or not.
        :type index: bool

        Usage:

        >>> #Preparing the tuple:
        >>> search_elements = self.get_search_browse_elements("Products")
        >>> # Calling the method:
        >>> self.search_browse_key("Branch+Id", search_elements)

        """

        if self.webapp_shadowroot():
            main_container = 'wa-dialog'
            radio_term = '.dict-tradmenu'
        else:
            main_container = '.tmodaldialog,.ui-dialog'
            radio_term = '.tradiobuttonitem input'

        tradiobuttonitens = None

        success = False
        if index and not isinstance(search_key, int):
            self.log_error("If index parameter is True, key must be a number!")

        sel_browse_key = lambda: self.driver.find_element(By.XPATH, xpath_soup(search_elements[0]))

        self.wait_element(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container=main_container)
        self.wait_until_to( expected_condition = "element_to_be_clickable", element = search_elements[0], locator = By.XPATH)
        self.set_element_focus(sel_browse_key())
        self.driver.switch_to.default_content()
        menu_tab = lambda: self.element_exists(term=radio_term, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        endtime = time.time() + self.config.time_out
        while time.time() < endtime and not menu_tab():
            self.click(sel_browse_key())

        if not index:
            if self.webapp_shadowroot():
                search_key = re.sub(r"(\s)?(\.+$)?", '', search_key.strip()).lower()
            else:
                search_key = re.sub(r"\.+$", '', search_key.strip()).lower()

            endtime = time.time() + self.config.time_out
            while time.time() < endtime and not tradiobuttonitens:
                soup = self.get_current_DOM()
                radio_menu = next(iter(soup.select(radio_term)), None) if self.webapp_shadowroot() else soup.select(radio_term)

                if radio_menu:
                    if self.webapp_shadowroot():
                        tradiobuttonitens = self.find_child_element('div', radio_menu)
                        tradiobuttonitens_ends_dots = list(filter(lambda x: re.search(r"\.\.$", x.text), tradiobuttonitens))
                        tradiobuttonitens_not_ends_dots = list(
                            filter(lambda x: not re.search(r"\.\.$", x.text), tradiobuttonitens))
                    else:
                        tradiobuttonitens_ends_dots = list(
                            filter(lambda x: re.search(r"\.\.$", x.next.text), radio_menu))
                        tradiobuttonitens_not_ends_dots = list(
                            filter(lambda x: not re.search(r"(\.\.)$", x.next.text), radio_menu))

                    if tradiobuttonitens_not_ends_dots:
                        if self.webapp_shadowroot():
                            radio = next(iter(list(filter(lambda x: search_key in re.sub(r"(\s)?(\.+$)?", '', x.text).lower() , tradiobuttonitens_not_ends_dots))), None)
                            if radio:
                                radio.find_element(By.TAG_NAME, 'input').click()
                                success = True
                        else:
                            radio = next(iter(list(filter(lambda x: search_key in re.sub(r"\.+$", '', x.next.text.strip()).lower() , tradiobuttonitens_not_ends_dots))), None)
                            if radio:
                                self.wait_until_to( expected_condition = "element_to_be_clickable", element = radio, locator = By.XPATH )
                                self.click(self.soup_to_selenium(radio))
                                success = True

                    if tradiobuttonitens_ends_dots and not success and self.config.initial_program.lower() != "sigaadv":
                        for element in tradiobuttonitens_ends_dots:
                            if self.webapp_shadowroot():
                                selenium_input = element.find_element(By.TAG_NAME, 'input')
                                self.click(selenium_input)
                            else:
                                self.wait_until_to( expected_condition = "element_to_be_clickable", element = element, locator = By.XPATH )
                                selenium_input = lambda : self.soup_to_selenium(element)
                                self.click(selenium_input())
                            time.sleep(1)

                            try_get_tooltip = 0
                            while (not success and try_get_tooltip < 3):
                                soup = self.get_current_DOM()
                                radio_menu = next(iter(soup.select(radio_term)),None) if self.webapp_shadowroot() else soup.select(radio_term)
                                success = "title" in radio_menu.attrs and  search_key in re.sub(' ', '',  radio_menu['title']).lower()
                                if not success:
                                    success = self.check_element_tooltip(element, search_key, contains=True)
                                try_get_tooltip += 1

                            if success:
                                break
                            elif self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
                                self.driver.switch_to.default_content()
                                soup = self.get_current_DOM()
                                if self.webapp_shadowroot():
                                    remove_focus = soup.select('body')[0]
                                    ActionChains(self.driver).move_to_element(self.soup_to_selenium(remove_focus)).perform()
                            else:
                                pass
                    if tradiobuttonitens_ends_dots and not success and self.config.initial_program.lower() == "sigaadv":
                        for element in tradiobuttonitens_ends_dots:

                            old_value = self.search_browse_key_input_value(search_elements[1])

                            if tradiobuttonitens.index(element) == 0:
                                self.wait_until_to( expected_condition = "element_to_be_clickable", element = tradiobuttonitens_ends_dots[1], locator = By.XPATH )
                                self.click(self.soup_to_selenium(tradiobuttonitens_ends_dots[1]))

                                while(old_value == self.search_browse_key_input_value(search_elements[1])):
                                    time.sleep(0.1)
                                old_value = self.search_browse_key_input_value(search_elements[1])

                                if not self.driver.find_elements(By.CSS_SELECTOR, ".tradiobuttonitem input"):
                                    self.get_current_DOM()
                                    self.set_element_focus(sel_browse_key())
                                    self.click(sel_browse_key())
                                    self.driver.switch_to.default_content()


                            if self.webapp_shadowroot():
                                selenium_input = element.find_element(By.TAG_NAME, 'input')
                                self.click(selenium_input)
                            else:
                                self.wait_until_to( expected_condition = "element_to_be_clickable", element = element, locator = By.XPATH )
                                self.click(self.soup_to_selenium(element))

                            while(old_value == self.search_browse_key_input_value(search_elements[1])):
                                time.sleep(0.1)

                            input_value = re.sub(' ', '', self.search_browse_key_input_value(search_elements[1]).strip().lower())
                            search_key = re.sub(' ', '', search_key.lower().strip())

                            if self.webapp_shadowroot() and not input_value:
                                selenium_element = self.soup_to_selenium(search_elements[1])
                                input_value =  re.sub(' ', '', selenium_element.get_attribute('placeholder').strip().lower())

                            success = search_key in input_value

                            if success:
                                break
                            else:
                                pass

            if not success:
                self.log_error(f"Couldn't search the key: {search_key} on screen.")

        else:
            endtime = time.time() + self.config.time_out
            while time.time() < endtime and not tradiobuttonitens:
                soup = self.get_current_DOM()
                if self.webapp_shadowroot():
                    waradio = soup.select("wa-radio")
                    if waradio:
                        tradiobuttonitens = self.driver.execute_script("return arguments[0].shadowRoot.querySelectorAll('input')", self.soup_to_selenium(next(iter(waradio))))
                else:
                    tradiobuttonitens = soup.select(".tradiobuttonitem input")

                if tradiobuttonitens:
                    if len(tradiobuttonitens) < search_key + 1:
                        self.log_error("Key index out of range.")
                    trb_input = tradiobuttonitens[search_key]
                    if self.webapp_shadowroot():
                        if trb_input:
                            trb_input.click()
                    else:
                        sel_input = lambda: self.driver.find_element(By.XPATH, xpath_soup(trb_input))
                        self.wait_until_to( expected_condition = "element_to_be_clickable", element = trb_input, locator = By.XPATH )
                        self.click(sel_input())

        while time.time() < endtime and menu_tab():
            bs_radio_menu = self.web_scrap(term=radio_term, scrap_type=enum.ScrapType.CSS_SELECTOR,
                                           main_container='body')
            bs_radio_menu = next(iter(bs_radio_menu))
            self.send_keys(self.soup_to_selenium(bs_radio_menu), Keys.ESCAPE)
            time.sleep(1)

    def search_browse_column(self, search_column, search_elements, index=False):
        """
        [Internal]

        Chooses the search key to be used during the search.

        :param search_column: The search Column to be chosen on the search dropdown
        :type search_column: str
        :param search_elements: Tuple of Search elements
        :type search_elements: Tuple of Beautiful Soup objects
        :param index: Whether the key is an index or not.
        :type index: bool

        Usage:

        >>> #Preparing the tuple:
        >>> search_elements = self.get_search_browse_elements("Products")
        >>> # Calling the method:
        >>> self.search_browse_key("Filial*", search_elements)
        """
        if self.webapp_shadowroot():
            main_container = 'wa-dialog'
            menupopup = 'wa-menu-popup.dict-tmenu'
            checkbox_term = "wa-checkbox"
        else:
            main_container = '.tmodaldialog,.ui-dialog'
            menupopup = '.tmenupopup.activationOwner'
            checkbox_term = "span"


        if index and not isinstance(search_column, int):
            self.log_error("If index parameter is True, column must be a number!")
        sel_browse_column = lambda: self.driver.find_element(By.XPATH, xpath_soup(search_elements[0]))
        self.wait_element(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container=main_container)
        self.wait_until_to( expected_condition = "element_to_be_clickable", element = search_elements[0], locator = By.XPATH)
        self.set_element_focus(sel_browse_column())
        self.click(sel_browse_column())

        if self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
            self.tmenu_out_iframe = True

        self.wait_element_timeout(menupopup, scrap_type=enum.ScrapType.CSS_SELECTOR, timeout=5.0, step=0.1, presence=True, position=0)
        tmenupopup = next(iter(self.web_scrap(menupopup, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container = "body")), None)

        if not tmenupopup:
            if self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
                self.tmenu_out_iframe = False
            self.log_error("SearchBrowse - Column: couldn't find the new menupopup")

        if self.webapp_shadowroot():
            div_columns = tmenupopup.select('.dict-tfolder')[0]
            column_button = self.find_child_element('wa-tab-button', div_columns)[1]
        else:
            column_button = self.soup_to_selenium(tmenupopup.select('a')[1])

        self.click(column_button)

        spans = tmenupopup.select(checkbox_term)

        if ',' in search_column:
            search_column_itens = search_column.split(',')
            filtered_column_itens = list(map(lambda x: x.strip(), search_column_itens))
            for item in filtered_column_itens:
                if self.webapp_shadowroot():
                    span = next(iter(list(filter(lambda x: x.attrs['caption'].lower().replace(" ","") == item.lower().replace(" ",""), spans))), None)
                    self.send_action(action=self.click, element=lambda: self.soup_to_selenium(span), click_type=3)
                else:
                    span = next(iter(list(filter(lambda x: x.text.lower().strip() == item.lower(),spans))), None)
                    if not span:
                        span = next(iter(list(filter(lambda x: x.text.lower().replace(" ","") == search_column.lower().replace(" ","") ,spans))), None)
                    self.click(self.soup_to_selenium(span))
        else:
            if self.webapp_shadowroot():
                span = next(iter(list(filter(lambda x: x.attrs['caption'].lower().replace(" ","") == search_column.lower().replace(" ","") ,spans))), None)
                self.send_action(action=self.click, element=lambda: self.soup_to_selenium(span), click_type=3)
            else:
                span = next(iter(list(filter(lambda x: x.text.lower().strip() == search_column.lower().strip() ,spans))), None)
                if not span:
                    span = next(iter(list(filter(lambda x: x.text.lower().replace(" ","") == search_column.lower().replace(" ","") ,spans))), None)
                self.click(self.soup_to_selenium(span))

        if self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
            self.tmenu_out_iframe = False


    def fill_search_browse(self, term, search_elements):
        """
        [Internal]

        Fills search input method and presses the search button.

        :param term: The term to be searched
        :type term: str
        :param search_elements: Tuple of Search elements
        :type search_elements: Tuple of Beautiful Soup objects

        Usage:

        >>> #Preparing the tuple:
        >>> search_elements = self.get_search_browse_elements("Products")
        >>> # Calling the method:
        >>> self.fill_search_browse("D MG 01", search_elements)
        """
        self.wait_blocker()

        sel_browse_input = lambda: self.driver.find_element(By.XPATH, xpath_soup(search_elements[1]))
        sel_browse_icon = lambda: self.driver.find_element(By.XPATH, xpath_soup(search_elements[2]))

        if self.webapp_shadowroot():
            input_lenght = ''
            endtime = time.time() + self.config.time_out
            while time.time() < endtime and not input_lenght:
                try:
                    input_lenght = self.driver.execute_script('return arguments[0]._maxLength', sel_browse_input())
                except:
                    pass

            if len(term.strip()) > input_lenght:
                self.log_error(f"Browse term length exceeded input lenght: {input_lenght}")

        current_value = self.get_element_value(sel_browse_input())

        endtime = time.time() + self.config.time_out
        while (time.time() < endtime and current_value.rstrip() != term.strip()):
            try:
                self.wait_blocker()
                logger().info(f'Filling: {term}')
                self.wait_until_to( expected_condition = "element_to_be_clickable", element = search_elements[2], locator = By.XPATH, timeout=True)
                self.click(sel_browse_input())
                self.set_element_focus(sel_browse_input())
                self.send_keys(sel_browse_input(), Keys.DELETE)
                self.wait_until_to( expected_condition = "element_to_be_clickable", element = search_elements[1], locator = By.XPATH, timeout=True)
                sel_browse_input().clear() if not self.webapp_shadowroot() else self.find_child_element('input', sel_browse_input())[0].clear
                self.set_element_focus(sel_browse_input())
                self.wait_until_to( expected_condition = "element_to_be_clickable", element = search_elements[1], locator = By.XPATH, timeout=True)
                sel_browse_input().send_keys(term.strip())
                current_value = self.get_element_value(sel_browse_input())
                time.sleep(1)
            except StaleElementReferenceException:
                    self.get_search_browse_elements()
            except:
                pass
        if current_value.rstrip() != term.strip():
            self.log_error(f"Couldn't search f{search_elements}  current value is {current_value.rstrip()}")
        self.send_keys(sel_browse_input(), Keys.ENTER)
        self.wait_blocker()
        self.double_click(sel_browse_icon())
        return True


    def search_browse_key_input_value(self, browse_input ):
        """
        [Internal]

        Get the search browse input value
        """
        self.get_current_DOM()
        input_value = self.soup_to_selenium(browse_input).get_attribute('value')
        self.driver.switch_to.default_content()
        return input_value

    def wait_blocker(self):
        """
        [Internal]

        Wait blocker disappear

        """

        twebview = True if self.config.poui_login else False

        logger().debug("Waiting blocker to continue...")
        soup = None
        result = True
        endtime = time.time() + self.config.time_out / 2

        while (time.time() < endtime and result):
            blocker_container = None
            blocker = None
            soup = lambda: self.get_current_DOM(twebview=twebview)
            blocker_container = lambda: self.blocker_containers(soup())

            try:
                if blocker_container():
                    if self.webapp_shadowroot():
                        blocker_container_soup = blocker_container()
                        blocker_container = self.soup_to_selenium(blocker_container())
                        blocker = blocker_container.get_property('blocked') if blocker_container and hasattr(
                            blocker_container, 'get_property') else None
                    else:
                        blocker = soup().select('.ajax-blocker') if len(soup().select('.ajax-blocker')) > 0 else \
                            'blocked' in blocker_container.attrs['class'] if blocker_container and hasattr(
                                blocker_container, 'attrs') else None
            except:
                pass

            logger().debug(f'Blocker status: {blocker}')

            if blocker:
                result = True
            else:
                self.blocker = None
                return False

        if time.time() > endtime:
            self.check_blocked_container(blocker_container_soup)

        return result

    def blocker_containers(self, soup):
        """
        Return The container index by z-index and filter if it is displayed

        :param soup: soup object
        :return: The container index by z-index and filter if it is displayed
        """

        try:
            containers = self.zindex_sort(soup.select(self.containers_selectors["BlockerContainers"]), True)

            if containers:
                containers_filtered = list(filter(lambda x: self.element_is_displayed(x), containers))
                if containers_filtered:
                    return next(iter(containers_filtered), None)
                else:
                    return None
            else:
                return None

        except AttributeError as e:
            logger().exception(f"Warning: wait_blocker > blocker_containers Exeception (AttributeError)\n {str(e)}")
        except Exception as e:
            logger().exception(f"Warning: wait_blocker > blocker_containers Exeception {str(e)}")

    def check_blocked_container(self, blocker_container_soup):
        """

        :return:
        """

        try:

            if hasattr(blocker_container_soup, 'attrs'):
                blocker_container_soup_info = str(blocker_container_soup.attrs)

                if hasattr(blocker_container_soup, 'id'):
                    blocker_container_soup_info += f" ID: {str(blocker_container_soup.attrs['id'])}"

                if hasattr(blocker_container_soup, 'title'):
                    blocker_container_soup_info += f" TITLE: {str(blocker_container_soup.attrs['title'])}"

            else:
                blocker_container_soup_info = blocker_container_soup[:1000]

            logger().debug(f'wait_blocker timeout | blocker container: {str(blocker_container_soup_info)}')

            soup = lambda: self.get_current_DOM()

            containers = soup().find_all(['.tmodaldialog','.ui-dialog', 'wa-dialog'])

            for container in containers:
                blocked = hasattr(container, 'attrs') and 'blocked' in container.attrs

                logger().debug(
                    f"Container ID: {container.attrs['id']} Container title:  {container.attrs['title']} Blocked: {blocked}")
                if blocked:
                    self.blocker = blocked
        except:
            pass

    def get_panel_name_index(self, panel_name):
        """
        [Internal]

        Gets the index of search box element based on the panel name associated with it.

        :param panel_name:
        :type panel_name:

        :return: The index of the search box starting with 0
        :rtype: int

        Usage:

        >>> # Calling the method:
        >>> index = self.get_panel_name_index("Products")
        """
        soup = self.get_current_DOM()
        panels = soup.select(".tmodaldialog > .tpanelcss > .tpanelcss")
        tsays = list(map(lambda x: x.select(".tsay"), panels))
        label = next(iter(list(filter(lambda x: x.text.lower() == panel_name.lower(), tsays)), None))
        return tsays.index(label)

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
        active_tab = []
        if self.webapp_shadowroot():
            term=".dict-tget, .dict-tcombobox, .dict-tmultiget"
            label_term = ".dict-tsay, label, wa-button"
        else:
            term=".tget, .tcombobox, .tmultiget"
            label_term = "label"

        position-=1

        if not input_field:
            term=".tsay, .dict-tsay"

        try:
            while( time.time() < endtime and not label ):
                container = self.get_current_container()
                regex = r"(<[^>]*>)?([\?\*\.\:]+)?"
                labels = container.select(label_term)
                labels_displayed = list(filter(lambda x: self.element_is_displayed(x) ,labels))
                view_filtred = list(filter(lambda x: re.search(r"^{}([^a-zA-Z0-9]+)?$".format(re.escape(field)),x.text) ,labels_displayed))

                if self.webapp_shadowroot():
                    if not view_filtred:
                        field =  re.sub(regex, '', field).lower().strip()
                        view_filtred = list(filter(lambda x: x.get('caption') and re.sub(regex, '', x['caption']).lower().strip().startswith(field) ,labels))
                        if len(view_filtred) > 1:
                            view_filtred = list(filter(lambda x: x.get('caption') and re.sub(regex, '', x['caption']).lower().strip() == (field) ,labels))
                    labels_list_filtered = list(filter(lambda x: 'th' not in self.element_name(x.parent) , view_filtred))
                else:
                    labels_list_filtered = list(filter(lambda x: 'th' not in self.element_name(x.parent.parent) , view_filtred))

                if labels_list_filtered and len(labels_list_filtered) -1 >= position:
                    label = labels_list_filtered[position]

            if not label:
                self.log_error(f"Label: '{field}'' wasn't found.")

            self.wait_until_to( expected_condition = "element_to_be_clickable", element = label, locator = By.XPATH, timeout=True)

            container_size = self.get_element_size(container['id'])
            # The safe values add to postion of element
            width_safe, height_safe = self.width_height(container_size)

            label_s  = lambda:self.soup_to_selenium(label)
            if self.webapp_shadowroot():
                xy_label = lambda: label_s().location
            else:
                xy_label = lambda: self.driver.execute_script('return arguments[0].getPosition()', label_s())

            if input_field:
                active_tab = self.filter_active_tabs(container)

                if active_tab :
                    active_childs = list(filter(lambda x: 'active' in x.attrs , active_tab.find_all_next('wa-tab-page'))) if active_tab else None
                    if active_childs:
                        if len(active_childs) == 0 and active_tab and active_tab.name == 'wa-panel':
                           active_childs = [active_tab]
                        labels_in_tab = next(iter(active_childs), None)
                        if labels_in_tab != None and labels_in_tab.contents != None:
                            label_class = list(filter(lambda x: x.get('class')[0] == 'dict-tsay' , labels_in_tab.contents))
                            if label_class:
                                if len(label_class) > 0:
                                    is_label_in_tab = list(filter(lambda x: x.get('caption') and re.sub(regex, '', x['caption']).lower().strip() == (field) ,labels_in_tab))
                                    label_tab = len(is_label_in_tab) > 0
                                else:
                                    label_tab = True
                            else:
                                label_tab = True
                        if active_childs and label_tab:
                            active_tab = next(iter(active_childs), None)
                            active_tab_labels = active_tab.select(label_term)
                            filtered_labels = list(filter(lambda x: re.search(r"^{}([^a-zA-Z0-9]+)?$".format(re.escape(field)),x.text) ,active_tab_labels))
                            if not filtered_labels:
                                filtered_labels = list(filter(lambda x: x.get('caption') and re.sub(regex, '', x['caption']).lower().strip().startswith(field) ,active_tab_labels))
                                if len(filtered_labels) > 1:
                                    filtered_labels = list(filter(lambda x: x.get('caption') and re.sub(regex, '', x['caption']).lower().strip() == (field) ,active_tab_labels))
                            if not filtered_labels:
                                active_tab = None


            list_in_range = self.web_scrap(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR) if not active_tab else active_tab.select(term)
            list_in_range = list(filter(lambda x: self.element_is_displayed(x), list_in_range))
            if self.search_stack('SetValue') and list_in_range:
                list_in_range = self.filter_not_read_only(list_in_range)

            if not input_field:
                if self.webapp_shadowroot():
                    list_in_range = list(filter(lambda x: x.previousSibling and field.strip().lower() == re.sub(regex, '', x.previousSibling.get('caption')).strip().lower(), list_in_range))
                else:
                    list_in_range = list(filter(lambda x: field.strip().lower() != x.text.strip().lower(), list_in_range))

            position_list = list(map(lambda x:(x[0], self.get_position_from_bs_element(x[1])), enumerate(list_in_range)))
            position_list = self.filter_by_direction(xy_label(), width_safe, height_safe, position_list, direction)
            distance      = self.get_distance_by_direction(xy_label(), position_list, direction)
            if distance:
                elem          = min(distance, key = lambda x: abs(x[1]))
                elem          = list_in_range[elem[0]]

            if not elem:
                self.log_error(f"Label '{field}' wasn't found")
            return elem

        except AssertionError as error:
            raise error
        except Exception as error:
            logger().exception(str(error))


    def filter_not_read_only(self, list_objects):
        '''
        [Internal]

        Return: Objects List not read only
        '''
        list_objects = list(filter(lambda x: not self.soup_to_selenium(x).get_attribute("readonly"), list_objects))
        list_objects = list(filter(lambda x: 'readonly' not in self.soup_to_selenium(x).get_attribute("class") or 'readonly focus' in self.soup_to_selenium(x).get_attribute("class"), list_objects))
        return list_objects


    def find_active_parents(self, bs4_element):
        active_parents = []
        if bs4_element.parents:
            active_parents = list(filter(lambda x: x.get('active') == '', bs4_element.parents))
        return next(iter(active_parents), None)


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
        if self.webapp_shadowroot():
            position = selenium_element.location
        else:
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

    def filter_by_direction(self, xy_label, width_safe, height_safe, position_list, direction=None):
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

        elif direction.lower() == 'left':
            return list(filter(
                lambda xy_elem: (xy_elem[1]['x'] + width_safe <= xy_label['x']) and (xy_elem[1]['y'] + height_safe  >= xy_label['y']), position_list))



    def get_distance_by_direction(self, xy_label, position_list, direction=None):

        if not direction:
            get_distance = self.get_distance

        elif direction.lower() == 'right' or direction.lower() == 'left':
            get_distance = self.get_distance_x

        elif direction.lower() == 'down':
            get_distance = self.get_distance_y

        return list(map(lambda x: (x[0], get_distance(xy_label, x[1])), position_list))

    def SetValue(self, field, value, grid=False, grid_number=1, ignore_case=True, row=None, name_attr=False, position = 1, check_value=None, grid_memo_field=False, range_multiplier=None, direction=None, duplicate_fields=[]):
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
        :param position: Position should be used to select an especific element when there is more than one of same
        :type name_attr: int
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
        >>> # Calling method to input value in cases that have duplicate fields:
        >>> oHelper.SetValue('Tipo Entrada' , '073', grid=True, grid_number=2, name_attr=True)
        >>> self.oHelper.SetValue('Tipo Entrada' , '073', grid=True, grid_number=2, name_attr=True, duplicate_fields=['tipo entrada', 10])
        >>> oHelper.LoadGrid()
        """

        check_value = self.check_value(check_value)

        if grid_memo_field:
            self.grid_memo_field = True

        if range_multiplier:
            self.range_multiplier = range_multiplier

        if grid:
            self.input_grid_appender(field, value, grid_number - 1, row = row, check_value = check_value, duplicate_fields=duplicate_fields, position=position, ignore_case=ignore_case)
        elif isinstance(value, bool):
            self.click_check_radio_button(field, value, name_attr, position, direction)
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

    def input_value(self, field, value, ignore_case=True, name_attr=False, position=1, check_value=True, direction=None):
        """
        [Internal]

        Sets value of an input element.
        Returns True if succeeded, False if it failed.

        :param field: The field name or label to receive the value
        :type field: str
        :param value: The value to be set on the field
        :type value: str
        :param ignore_case: Boolean if case should be ignored or not. - **Default:** True
        :type ignore_case: bool
        :param name_attr: Boolean if search by Name attribute must be forced. - **Default:** False
        :type name_attr: bool
        :param check_value: Boolean ignore input check - **Default:** True
        :type name_attr: bool
        :returns: True if succeeded, False if it failed.
        :rtype: bool

        Usage:

        >>> # Calling the method
        >>> self.input_value("A1_COD", "000001")
        """

        self.wait_blocker()

        field = re.sub(r"([\s\?:\*\.]+)?$", "", field).strip()

        main_element = None

        if name_attr:
            self.wait_element(term=f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR)
        else:
            self.wait_element(field)

        success = False
        try_counter = 0
        endtime = time.time() + self.config.time_out

        while(time.time() < endtime and not success):

            logger().info(f"Looking for element: {field}")

            element = self.get_field(field, name_attr, position, direction=direction)

            if self.last_wa_tab_view_input_id != self.current_wa_tab_view_id() and self.check_element_tab_view(element=element):
                self.last_wa_tab_view_input_id = self.current_wa_tab_view_id()

            if element:
                input_field = lambda : self.soup_to_selenium(element)
                self.scroll_to_element(input_field())
                logger().info(f"Element: {field} Found!")

            logger().info(f"Filling element: {field}")

            if not element or not self.element_is_displayed(element):
                continue

            main_element = element
            multiget = "dict-tmultiget"

            if multiget in element.attrs['class'] if element.get('class') else None:
                textarea = next(iter(self.find_shadow_element('textarea', self.soup_to_selenium(element))), None)
                if not textarea:
                    input_field = lambda : self.soup_to_selenium(element)
                else:
                    input_field = lambda : textarea
            else:
                input_field = lambda : self.soup_to_selenium(element)

            if input_field:
                valtype=''

                if 'type' in element.attrs:
                    valtype = self.value_type(element.attrs["type"])

                unmasked_value = self.remove_mask(value, valtype, input_field())
                main_value = unmasked_value if value != unmasked_value and self.check_mask(input_field()) else value

                if self.check_combobox(element):
                    interface_value = self.return_selected_combo_value(element)
                else:
                    interface_value = self.get_web_value(input_field())

                current_value = interface_value.strip()
                get_max_lenght = lambda: self.driver.execute_script('return arguments[0]._maxLength', input_field())
                interface_value_size = get_max_lenght() if input_field().tag_name != 'textarea' else len(value) + 1
                user_value_size = len(value)

                if valtype == 'D' and user_value_size > interface_value_size:
                    main_value_bkp = main_value
                    main_value = value[0:6] + value[8:10]

                if self.element_name(element) == "input":
                    valtype = self.value_type(element.attrs["type"])

                self.scroll_to_element(input_field())

                try:
                    #Action for Combobox elements
                    if self.check_combobox(element):
                        self.set_element_focus(input_field())
                        main_element = element.parent
                        self.try_element_to_be_clickable(main_element)
                        if main_value == '':
                           self.select_combo(element, main_value, index=True)
                        else:
                            self.select_combo(element, main_value)
                        if self.config.browser.lower() == 'chrome':
                            self.set_element_focus(input_field())
                            ActionChains(self.driver).send_keys(Keys.ENTER).perform()

                        current_value = self.return_selected_combo_value(element).strip()
                    #Action for Input elements
                    else:
                        self.wait_until_to( expected_condition = "visibility_of", element = input_field, timeout=True)
                        self.wait_until_to( expected_condition = "element_to_be_clickable", element = element, locator = By.XPATH, timeout=True)
                        self.double_click(input_field())

                        #if Character input
                        if valtype != 'N':
                            self.set_element_focus(input_field())
                            self.wait_until_to( expected_condition = "element_to_be_clickable", element = element, locator = By.XPATH, timeout=True)
                            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.HOME).key_up(Keys.CONTROL).perform()
                            ActionChains(self.driver).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys(
                                Keys.END).key_up(Keys.CONTROL).key_up(Keys.SHIFT).perform()
                            time.sleep(0.1)
                            if main_value == '':
                                ActionChains(self.driver).move_to_element(input_field()).send_keys(" ").perform()
                            else:
                                self.wait_blocker()
                                self.wait_until_to( expected_condition = "element_to_be_clickable", element = element, locator = By.XPATH, timeout=True)
                                ActionChains(self.driver).move_to_element(input_field()).send_keys(main_value).perform()
                                if valtype == 'D' and user_value_size > interface_value_size:
                                    main_value = main_value_bkp
                        #if Number input
                        else:
                            tries = 0
                            try_counter = 1
                            while(tries < 3):
                                self.set_element_focus(input_field())
                                self.wait_until_to( expected_condition = "element_to_be_clickable", element = element, locator = By.XPATH, timeout=True)
                                self.try_send_keys(input_field, main_value, try_counter)
                                current_number_value = self.get_web_value(input_field())
                                if re.sub('[\s,\.:]', '', self.remove_mask(current_number_value, valtype)).strip() == re.sub('[\s,\.:]', '', main_value).strip():
                                    break
                                tries+=1
                                try_counter+=1


                        if self.check_mask(input_field()):
                            current_value = self.remove_mask(self.get_web_value(input_field()).strip(), valtype)
                            if re.findall(r"\s", current_value):
                                current_value = re.sub(r"\s", "", current_value)
                        else:
                            current_value = self.get_web_value(input_field()).strip()

                        if current_value != "" and current_value.encode('latin-1', 'ignore'):
                            logger().info(f"Current field value: {current_value}")

                        if user_value_size < interface_value_size and self.is_active_element(input_field()):
                            self.send_keys(input_field(), Keys.ENTER)

                        if not check_value:
                            return

                    if self.check_combobox(element):
                        current_value = current_value[0:len(str(value))]

                    if re.match(r"^●+$", current_value):
                        success = len(current_value) == len(str(value).strip())
                    elif ignore_case:
                        replace = r'[\s,\.:]'
                        success = re.sub(replace, '', current_value).lower() == re.sub(replace, '', main_value).lower()
                    else:
                        success = current_value == main_value.replace(",", "").strip()
                except:
                    continue

        if "disabled" in element.attrs:
            self.log_error(self.create_message(['', field],enum.MessageType.DISABLED))

        if not success:
            self.log_error(f"Could not input value {value} in field {field}")
        else:
            self.wait_until_to( expected_condition = "element_to_be_clickable", element = main_element, locator = By.XPATH )

    def check_element_tab_view(self, element):
        """
        [Internal]
        """

        element_tab_view = element.find_parent('wa-tab-view')
        if element_tab_view:
            if len(element_tab_view) == 1:
                element_tab_view = next(iter(element_tab_view))
            
            if hasattr(element_tab_view, "attrs"):
                element_tab_view_id = element_tab_view.attrs['id']
                return element_tab_view_id == self.current_wa_tab_view_id()
    
    def current_wa_tab_view_id(self):
        """
        [Internal]
        """

        selector = "wa-tab-view"

        wa_tab_view = self.get_container_selector(selector=selector)

        if isinstance(wa_tab_view, list) and len(wa_tab_view) == 1:
            wa_tab_view = next(iter(wa_tab_view))
        
        return wa_tab_view.attrs['id'] if hasattr(wa_tab_view, "attrs") else None

    def check_combobox(self, element):
        """

        :param element:
        :return: Return True if the field is a combobox
        """

        if self.webapp_shadowroot():
            attr_class = 'dict-tcombobox'
        else:
            attr_class = 'tcombobox'

        return ((hasattr(element, "attrs") and "class" in element.attrs and attr_class in element.attrs["class"]) or
                (hasattr(element.find_parent(), "attrs") and "class" in element.find_parent().attrs and attr_class in
                 element.find_parent().attrs["class"]))

    def value_type(self, field_type):

        if field_type == 'string':
            return_type = 'C'
        elif field_type == 'number':
            return_type = 'N'
        elif field_type == 'date':
            return_type = 'D'

        return return_type

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

        while(time.time() < endtime and not element):
            if re.match(r"\w+(_)", field) or name_attr:
                element_list = self.web_scrap(f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR)
                if element_list and len(element_list) -1 >= position:
                    element = element_list[position]
            else:
                if self.webapp_shadowroot():
                    element = self.web_scrap(field, scrap_type=enum.ScrapType.TEXT, label=True, input_field=input_field, direction=direction, position=position)
                else:
                    element = next(iter(self.web_scrap(field, scrap_type=enum.ScrapType.TEXT, label=True, input_field=input_field, direction=direction, position=position)), None)

        if element:
            if not self.webapp_shadowroot():
                element_children = next((x for x in element.contents if self.element_name(x) in ["input", "select"]), None)
            else:
                element_children = None
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

        web_value = None

        if element.tag_name == "div":
            element_children = element.find_element(By.CSS_SELECTOR, "div > * ")
            if element_children is not None:
                element = element_children

        if element.tag_name == "label" or element.tag_name == "wa-text-view":
            web_value = element.get_attribute("text")
            if not web_value:
                web_value = element.text.strip()
        elif element.tag_name == "select" or element.tag_name == "wa-combobox":
            if self.webapp_shadowroot():
                is_selected = next(iter(list(filter(lambda x: x.is_selected(), self.find_shadow_element('option', element)))), None)
                if is_selected:
                    web_value = is_selected.text
            else:
                current_select = 0 if element.get_attribute('value') == '' else int(element.get_attribute('value'))
                selected_element = element.find_elements(By.CSS_SELECTOR, "option")[current_select]
                web_value = selected_element.text
        else:
            web_value = element.get_attribute("value")

        logger().debug(f"Current value: {web_value}")
        return web_value

    def CheckResult(self, field, user_value, grid=False, line=1, grid_number=1, name_attr=False, input_field=True,
                    direction=None, grid_memo_field=False, position=1, ignore_case=True):
        """
        Checks if a field has the value the user expects.

        :param field: The field or label of a field that must be checked.
        :type field: str
        :param user_value: The value that the field is expected to contain.
        :type user_value: str
        :param grid: Boolean if this is a grid field or not. - **Default:** False
        :type grid: bool
        :param line: Grid line that contains the column field to be checked.- **Default:** 1
        :type line: int
        :param grid_number: Grid number of which grid should be checked when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int
        :param name_attr: Boolean if search by Name attribute must be forced. - **Default:** False
        :type name_attr: bool
        :param input_field: False if the desired field is not an input type
        :type bool
        :param direction: Desired direction to search for the element, currently accepts right and down
        :type str
        :param grid_memo_field: Boolean if this is a memo grid field. - **Default:** False
        :type grid_memo_field: bool

        Usage:

        >>> # Calling method to check a value of a field:
        >>> oHelper.CheckResult("A1_COD", "000001")
        >>> #-----------------------------------------
        >>> # Calling method to check a field that is on the second line of a grid:
        >>> oHelper.CheckResult("Client", "000001", grid=True, line=2)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Calling method to check a field that is on the second grid of the screen:
        >>> oHelper.CheckResult("Order", "000001", grid=True, line=1, grid_number=2)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Call method to check a field value that is not an input field and is on the right:
        >>> oHelper.CheckResult("Saldo Titulo", "100.000,00", input_field=False, direction='right')
        >>> oHelper.LoadGrid()

        """
        self.wait_blocker()

        if grid_memo_field:
            self.grid_memo_field = True
        if grid:
            self.check_grid_appender(line - 1, field, user_value, grid_number - 1, position, ignore_case)
        elif isinstance(user_value, bool):
            current_value = self.result_checkbox(field, user_value, position)
            self.log_result(field, user_value, current_value)
        else:
            endtime = time.time() + self.config.time_out
            current_value = ''
            while (time.time() < endtime and not current_value):
                field = re.sub(r"(\:*)(\?*)", "", field).strip()
                if name_attr:
                    self.wait_element(term=f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR,
                                      position=position - 1)
                else:
                    self.wait_element(field, position=position - 1)

                element = self.get_field(field, name_attr=name_attr, input_field=input_field, direction=direction,
                                         position=position)
                if not element:
                    self.log_error(f"Couldn't find element: {field}")

                if self.webapp_shadowroot():
                    field_element = lambda : self.soup_to_selenium(element)
                else:
                    field_element = lambda: self.driver.find_element(By.XPATH, xpath_soup(element))

                self.set_element_focus(field_element())
                self.scroll_to_element(field_element())

                if self.get_web_value(field_element()):
                    current_value = self.get_web_value(field_element()).strip()

            logger().info(f"Value for Field {field} is: {current_value}")

            # Remove mask if present.
            if self.check_mask(field_element()):
                current_value = self.remove_mask(current_value).replace(',', '')
                user_value = self.remove_mask(user_value).replace(',', '')
            # If user value is string, Slice string to match user_value's length
            if type(current_value) is str:
                current_value = current_value[0:len(str(user_value))]

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

    def GetValue(self, field, grid=False, line=1, grid_number=1, grid_memo_field=False, position=0):
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
        :param position: Position which duplicated element is located. - **Default:** 1
        :type position: int

        Usage:

        >>> # Calling the method:
        >>> current_value = oHelper.GetValue("A1_COD")
        """
        endtime = time.time() + self.config.time_out
        element = None
        x3_dictionaries = None

        if grid_memo_field:
            self.grid_memo_field = True

        if not grid:
            while ( (time.time() < endtime) and (not element) and (not hasattr(element, "name")) and (not hasattr(element, "parent"))):
                element = self.get_field(field)
                if ( hasattr(element, "name") and hasattr(element, "parent") ):
                    selenium_element = lambda: self.driver.find_element(By.XPATH, xpath_soup(element))
                    value = self.get_web_value(selenium_element())
        else:
            field_array = [line-1, field, "", grid_number-1, position, True]

            if re.match(r"\w+(_)", field_array[1]):
                x3_dictionaries = self.get_x3_dictionaries([field_array[1].strip()])
            value = self.check_grid(field_array, x3_dictionaries, get_value=True, position=position)

        logger().info(f"Current value: {value}")

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

        server_environment = self.config.environment

        if self.config.appserver_service:
            try:
                self.sc_query(self.config.appserver_service)
            except Exception as err:
                logger().debug(f'sc_query exception: {err}')

        try:
            self.restart_browser()
        except WebDriverException as e:
            webdriver_exception = e

        # logger().debug('screenshot after restart driver_refresh.')
        # self.log.take_screenshot_log(self.driver, 'restart', stack_item=self.log.get_testcase_stack())
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
                self.program_screen(self.config.initial_program, environment=server_environment)

            self.wait_user_screen()
            if 'POUILogin' in self.config.json_data and self.config.json_data['POUILogin'] == True:
                self.config.poui_login = True

            if self.restart_tss:
                self.user_screen_tss()
                self.restart_tss = False
                return

            self.user_screen()
            self.environment_screen()

            endtime = time.time() + self.config.time_out
            while(time.time() < endtime and not self.element_exists(term=".tmenu, .dict-tmenu", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")):
                self.close_warning_screen()
                self.close_modal()

            self.set_log_info_config() if self.config.log_info_config else self.set_log_info()

            self.log.country = self.config.country
            self.log.execution_id = self.config.execution_id
            self.log.issue = self.config.issue


            if self.config.routine:
                if self.config.routine_type == 'SetLateralMenu':
                    self.SetLateralMenu(self.config.routine, save_input=False)
                elif self.config.routine_type == 'Program':
                    self.set_program(self.config.routine)

    def wait_user_screen(self):

        term = "[name=cGetUser], [name=cUser]" if self.webapp_shadowroot() else "[name='cGetUser'] > input, [name=cUser]"
        element = None
        endtime = time.time() + self.config.time_out
        while time.time() < endtime and not element:

            if 'POUILogin' in self.config.json_data and self.config.json_data['POUILogin'] == True:
                soup = self.get_current_DOM(twebview=True)
                element = next(iter(soup.select(".po-page-login-info-field .po-input")), None)
            else:
                soup = self.get_current_DOM()
                element = next(iter(soup.select(term)), None)

    def driver_refresh(self):
        """
        [Internal]

        Refresh the driver.

        Usage:

        >>> # Calling the method:
        >>> self.driver_refresh()
        """

        if self.config.appserver_service:
            try:
                self.sc_query(self.config.appserver_service)
            except Exception as err:
                logger().debug(f'sc_query exception: {err}')

        if self.config.smart_test or self.config.debug_log:
            logger().info("Driver Refresh")

        self.driver.refresh()

        if self.config.appserver_service:
            try:
                self.sc_query(self.config.appserver_service)
            except Exception as err:
                logger().debug(f'sc_query exception: {err}')

        self.wait_blocker()
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.F5).key_up(Keys.CONTROL).perform()

    def Finish(self):
        """
        Exit the protheus Webapp.

        Usage:

        >>> # Calling the method.
        >>> oHelper.Finish()
        """
        element = None

        if self.config.coverage:
           self.get_coverage()
        else:
            endtime = time.time() + self.config.time_out
            while( time.time() < endtime and not element ):

                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('q').key_up(Keys.CONTROL).perform()
                element = self.element_exists(self.language.finish, scrap_type=enum.ScrapType.MIXED, optional_term='wa-button, button, .thbutton', main_container='.tmodaldialog,.ui-dialog, wa-dialog, body')
                if element:
                    self.SetButton(self.language.finish)

                self.wait_element_timeout(term=self.language.finish, scrap_type=enum.ScrapType.MIXED, optional_term="wa-button, button, .thbutton", timeout=5, step=0.5, main_container=".tmodaldialog,.ui-dialog, wa-dialog, body")

            if not element:
                logger().warning("Warning method finish use driver.refresh. element not found")

    @count_time
    def get_coverage(self):
        
        timeout = 1800
        optional_term = "wa-button" if self.webapp_shadowroot() else "button, .thbutton"
        current_layers = 0
        coverage_finished = False
        element = None
        new_modal = False
        coverage_exceed_timeout = False
            
        endtime = time.time() + timeout

        logger().debug("Startin coverage.")

        while not coverage_finished:

            if time.time() > endtime:

                if coverage_exceed_timeout:
                    logger().debug("Coverage exceed timeout.")
                    break
                
                logger().debug("Coverage exceed default timeout. adding more time.")
                endtime = time.time() + timeout
                coverage_exceed_timeout = True

            if not element:
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('q').key_up(Keys.CONTROL).perform()
                element = self.wait_element_timeout(term=self.language.finish, scrap_type=enum.ScrapType.MIXED,
                                                    optional_term=optional_term, timeout=5, step=1, main_container="body", check_error=False)
                
            if element and not new_modal:
                current_layers = self.check_layers('wa-dialog')
                self.SetButton(self.language.finish)
                new_modal = current_layers + 1 == self.check_layers('wa-dialog')
                logger().debug("Waiting for coverage to finish.")

            if new_modal:
                coverage_finished = current_layers >= self.check_layers('wa-dialog')
            
            if coverage_finished:
                logger().debug("Coverage finished.")
                
            time.sleep(1)

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

        if self.config.coverage:
            self.get_coverage()
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

    def web_scrap(self, term, scrap_type=enum.ScrapType.TEXT, optional_term=None, label=False, main_container=None,
                      check_error=True, check_help=True, input_field=True, direction=None, position=1, twebview=False,
                      second_term=None, match_case=False):
        """
        [Internal]

        Returns a BeautifulSoup or selenium object list based on the search parameters.

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

        :return: List of BeautifulSoup4 or Selenium elements based on search parameters.
        :rtype: List of BeautifulSoup4 or Selenium objects

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

        self.twebview_context = twebview

        self.base_container = "wa-dialog" if self.webapp_shadowroot() else ".tmodaldialog"

        try:
            endtime = time.time() + self.config.time_out
            container =  None
            while(time.time() < endtime and container is None):
                soup = self.get_current_DOM(twebview=twebview)

                if check_error:
                    self.search_for_errors(check_help)

                if self.config.log_file:
                    with open(f"{term + str(scrap_type) + str(optional_term) + str(label) + str(main_container) + str(random.randint(1, 101)) }.txt", "w") as text_file:
                        text_file.write(f" HTML CONTENT: {str(soup)}")

                container_selector = self.base_container
                if (main_container is not None):
                    container_selector = main_container

                containers = self.zindex_sort(soup.select(container_selector), reverse=True)

                if container_selector == 'wa-text-view':
                    return self.filter_label_element(term, container=soup, position=position, twebview=twebview) if self.filter_label_element(term, container=soup, position=position, twebview=twebview) else []

                if self.base_container in container_selector:
                    container = self.containers_filter(containers)

                if self.webapp_shadowroot() and main_container == 'wa-tgrid':
                    wa_tgrid_label = None
                    while(time.time() < endtime and wa_tgrid_label is None):
                        for container in containers:
                            labels = self.driver.execute_script("return arguments[0].shadowRoot.querySelectorAll('label')", self.soup_to_selenium(container))
                            labels_not_none = list(filter(lambda x: x is not None, labels))
                            if len(labels_not_none) > 0:
                                labels_displayed = list(filter(lambda x: x.is_displayed(), labels_not_none))
                                wa_tgrid_label = list(filter(lambda x: term.lower() in x.text.lower(), labels_displayed))
                                if wa_tgrid_label:
                                    return wa_tgrid_label

                else:
                    container = next(iter(containers), None) if isinstance(containers, list) else container

            if container is None:
                raise Exception(f"Web Scrap couldn't find container - term: {term}")

            if (scrap_type == enum.ScrapType.TEXT):
                if label:
                    return self.find_label_element(term, container, input_field=input_field, direction=direction, position=position)
                elif not re.match(r"\w+(_)", term):
                    return self.filter_label_element(term, container, position=position, twebview=twebview) if self.filter_label_element(term, container, position=position, twebview=twebview) else []
                else:
                    return list(filter(lambda x: term.lower() in x.text.lower(), container.select("div > *")))
            elif (scrap_type == enum.ScrapType.CSS_SELECTOR):
                if self.webapp_shadowroot():
                    self.scroll_to_container(container, term)
                return list(filter(lambda x: self.element_is_displayed(x, twebview=twebview), container.select(term)))
            elif (scrap_type == enum.ScrapType.MIXED and optional_term is not None):
                if self.webapp_shadowroot() and not twebview:
                    return self.selenium_web_scrap(term, container, optional_term, second_term, match_case)
                else:
                    return list(filter(lambda x: term.lower() in x.text.lower(), container.select(optional_term)))
            elif (scrap_type == enum.ScrapType.SCRIPT):
                script_result = self.driver.execute_script(term)
                return script_result if isinstance(script_result, list) else []
            else:
                return []
        except AssertionError:
            raise
        except Exception as e:
            logger().exception(str(e))

    def scroll_to_container(self, container, term):
        """

        :param container:
        :param term:
        :return:
        """
        scroll_container = container.select(term)

        if scroll_container:
            if isinstance(scroll_container, list):
                self.scroll_to_element(self.soup_to_selenium(container.select(term)[0]))
            else:
                self.scroll_to_element(self.soup_to_selenium(container.select(term)))

    def selenium_web_scrap(self, term, container, optional_term, second_term=None, match_case=False):
        """
        [Internal]
        Return selenium web element
        """
        regx_sub = r"[\n?\s?]"
        elements = []
        element = []
        try:
            if second_term:
                labels_list = list(map(
                    lambda x: self.driver.execute_script(
                        f"return arguments[0].shadowRoot.querySelectorAll('label, span, wa-dialog-header, wa-tree-node, {second_term}')",
                        self.soup_to_selenium(x)),
                    container.select(optional_term)))

                if len(list(filter(lambda x: x is not None and x, labels_list))) == 0:
                    labels_list = list(map(
                        lambda x: self.driver.execute_script(
                            f"return arguments[0].querySelectorAll('label, span, wa-dialog-header, {second_term}')",
                            self.soup_to_selenium(x)),
                        container.select(optional_term)))
            else:
                labels_list = list(map(
                    lambda x: self.driver.execute_script(
                        f"return arguments[0].shadowRoot.querySelectorAll('label, span, wa-dialog-header, wa-tree-node')",
                        self.soup_to_selenium(x)),
                    container.select(optional_term)))

            if len(labels_list) == 0:
                labels_list = [self.driver.execute_script(
                    f"return arguments[0].shadowRoot.querySelectorAll('label, span, wa-dialog-header, wa-tree-node')",
                    self.soup_to_selenium(container))]

            for labels in labels_list:
                labels_not_none = list(filter(lambda x: x is not None and x, labels))
                if len(labels_not_none) > 0:
                    labels_displayed = list(filter(lambda x: x.is_displayed(), labels_not_none))
                    if '.dict-tfolder' in optional_term:
                        if container.select('.dict-tfolder') and self.search_navigation_bar(container.select('.dict-tfolder')):
                            labels_displayed = labels_not_none
                    if labels_displayed:
                        element = list(filter(lambda x: term.lower() in x.text.lower().replace('\n', ''), labels_displayed))

                        if (len(element) > 1) or match_case and element:
                            element = next(iter(list(filter(lambda x: term.lower().strip() == x.text.lower().replace('\n', ''), element))),None)
                        else:
                            element = next(iter(element), None)
                        if not element and match_case == False:
                            element = next(iter(list(filter(lambda x: term.lower() in x.get_attribute('textContent').lower().replace('\n', '').replace('\t', ''), labels_displayed))),
                                       None)
                        if not element and len(labels_not_none) >= 1 and match_case == False:
                            element = list(filter(lambda x: re.sub(regx_sub,'', term).lower() in re.sub(regx_sub,'', x.text).lower(), labels_displayed))
                        if element:
                            elements.append(element)
            if elements:
                return elements

            if not element:
                header = self.find_shadow_element('wa-dialog-header', self.soup_to_selenium(container))
                if header:
                    if match_case:
                        element = next(iter(list(filter(
                            lambda x: term.lower() == x.get_attribute('textContent').lower().replace('\n', '').replace(
                                '\t', ''), header))), None)
                    else:
                        element = next(iter(list(filter(lambda x: term.lower() in x.get_attribute('textContent').lower().replace('\n', '').replace('\t',''), header))), None)
                    if element:
                        return [element]
        except:
            return None


    def search_navigation_bar(self, container):
        """
        [Internal]
        Searches for navigation buttons into bs4 object.

        :return: selenium object or None
        :rtype: navigation selenium object

        Usage:
        >>> # Calling the method:
        >>> self.search_navigation_bar(container)
        """
        if container and isinstance(container, list):
            container = next(iter(container), None)
            container = self.soup_to_selenium(container)
        if container:
            tab_bar = self.driver.execute_script(f"return arguments[0].shadowRoot.querySelector('wa-tab-bar').shadowRoot.querySelector('.navigation')", container)
        return tab_bar


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
            if self.webapp_shadowroot():
                selector = "wa-dialog"
            else:
                selector = ".tmodaldialog, .ui-dialog"
            top_layer = next(iter(self.zindex_sort(soup.select(selector), True)), None)

        except AttributeError as e:
            self.log_error(f"Search for erros couldn't find DOM\n Exception: {str(e)}")

        if not top_layer:
            return None

        if self.webapp_shadowroot():
            icon_alert = next(iter(top_layer.select("wa-image[src*='fwskin_info_ico.png']")), None)
        else:
            icon_alert = next(iter(top_layer.select("img[src*='fwskin_info_ico.png']")), None)

        if self.webapp_shadowroot():
            icon_error_log = next(iter(top_layer.select("wa-image[src*='openclosing.png']")), None)
        else:
            icon_error_log = next(iter(top_layer.select("img[src*='openclosing.png']")), None)

        if (not icon_alert or not check_help) and not icon_error_log:
            return None

        if icon_alert:
            if self.webapp_shadowroot():
                label = reduce(lambda x,y: f"{x} {y}", map(lambda x: x.get('caption').strip(), top_layer.select(".dict-tsay")))
            else:
                label = reduce(lambda x,y: f"{x} {y}", map(lambda x: x.text.strip(), top_layer.select(".tsay label")))
            if self.language.messages.error_msg_required in label:
                message = self.language.messages.error_msg_required
            elif "help:" in label.lower() and self.language.problem in label:
                message = label
            else:
                return None

        elif icon_error_log:
            if self.webapp_shadowroot():
                label = reduce(lambda x,y: f"{x} {y}", map(lambda x: x.get('caption').strip(), top_layer.select(".dict-tbutton")))
                textarea = next(iter(top_layer.select(".dict-tmultiget")), None)
                textarea_value = textarea.get('contexttext')
            else:
                label = reduce(lambda x,y: f"{x} {y}", map(lambda x: x.text.strip(), top_layer.select(".tsay label")))
                textarea = next(iter(top_layer.select("textarea")), None)
                textarea_value = self.driver.execute_script(f"return arguments[0].value", self.driver.find_element(By.XPATH, xpath_soup(textarea)))

            error_paragraphs = re.split(r'\n\s*\n', textarea_value.strip())
            error_message = f"Error Log: {error_paragraphs[0]} - {error_paragraphs[1]}" if len(error_paragraphs) > 2 else label
            message = error_message.replace("\n", " ")

            if self.webapp_shadowroot():
                button = next(iter(filter(lambda x: self.language.details.lower() in x.get('caption').lower().replace('<u>', '').replace('</u>',''),top_layer.select("wa-button"))), None)
                self.driver.execute_script(f"return arguments[0].click()", self.soup_to_selenium(button))
            else:
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

    def element_exists(self, term, scrap_type=enum.ScrapType.TEXT, position=0, optional_term="", main_container="", check_error=True, twebview=False, second_term=None):
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

        if not main_container:
            main_container = ".tmodaldialog,.ui-dialog, wa-text-input, wa-dialog, body"

        element_list = []
        containers = None
        self.twebview_context = twebview

        self.base_container = "wa-dialog" if self.webapp_shadowroot() else ".tmodaldialog"

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
                soup = self.get_current_DOM(twebview=twebview)

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
                    element_list = list(filter(lambda x: x.is_displayed(), container_element.find_elements(by, selector)))
                    if not element_list:
                        self.driver.execute_script("return arguments[0].scrollIntoView(true);", self.soup_to_selenium(container))
                        element_list = list(filter(lambda x: x.is_displayed(), container_element.find_elements(by, selector)))
            except:
                pass
        else:
            if scrap_type == enum.ScrapType.MIXED:
                selector = optional_term
            else:
                selector = "div"

        if not element_list:
            element_list = self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container, check_error=check_error, second_term=second_term, twebview=twebview)
            if not element_list and f"wa-dialog[title*={self.language.warning}]" in term:
                return container_element.get_attribute('title') == self.language.warning
            if not element_list:
                return None

        if position == 0:
            return len(element_list) > 0
        else:
            return len(element_list) >= position

    def SetLateralMenu(self, menu_itens, save_input=True, click_menu_functional=False):
        """
        Navigates through the lateral menu using provided menu path.
        e.g. "MenuItem1 > MenuItem2 > MenuItem3"

        :param menu_itens: String with the path to the menu.
        :type menu_itens: str
        :param save_input: Boolean if all input info should be saved for later usage. Leave this flag 'True' if you are not sure. **Default:** True
        :type save_input: bool

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetLateralMenu("Updates > Registers > Products > Groups")
        """

        submenu = ""
        wait_screen = True if menu_itens != self.language.menu_about else False
        used_ids = []

        if self.config.log_info_config:
            self.set_log_info_config()

        if self.config.new_log:
            if not self.check_release_newlog() and wait_screen:
                self.log_error_newlog()

        if save_input:
            self.config.routine_type = 'SetLateralMenu'
            self.config.routine = menu_itens

        if self.webapp_shadowroot():
            menu_term = ".dict-tmenu"
            menu_itens_term = ".dict-tmenuitem"
            term = f"[caption^='{self.language.news}']"
            optional_term_news = ""
            scrap_type = enum.ScrapType.CSS_SELECTOR
        else:
            menu_term = ".tmenu"
            menu_itens_term = ".tmenuitem"
            term = self.language.news
            optional_term_news = ".tmodaldialog > .tpanel > .tsay"
            scrap_type = enum.ScrapType.MIXED

        logger().info(f"Navigating lateral menu: {menu_itens}")

        endtime = time.time() + self.config.time_out
        menu_itens = list(map(str.strip, menu_itens.split(">")))

        self.escape_to_main_menu()

        self.wait_element(term=menu_term, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")

        soup = self.get_current_DOM()

        menu_xpath = soup.select(menu_term)
        menu = menu_xpath[0]
        child = menu
        count = 0
        last_index = len(menu_itens) - 1

        try:
            for index, menuitem in enumerate(menu_itens):
                logger().info(f'Menu item: "{menuitem}"')
                self.wait_blocker()
                self.wait_until_to(expected_condition="element_to_be_clickable", element=menu_term,
                                   locator=By.CSS_SELECTOR)
                self.wait_until_to(expected_condition="presence_of_all_elements_located",
                                   element=f'{menu_term} {menu_itens_term}', locator=By.CSS_SELECTOR)
                menu_item_presence = self.wait_element_timeout(term=menuitem, scrap_type=enum.ScrapType.MIXED,
                                                               timeout=self.config.time_out,
                                                               optional_term=menu_itens_term,
                                                               main_container="body, wa-dialog")

                if not menu_item_presence and submenu:
                    submenu().click()

                subMenuElements = self.get_current_DOM().select(menu_itens_term)


                while not subMenuElements or len(subMenuElements) < self.children_element_count(f"#{child.attrs['id']}",
                                                                                                menu_itens_term):
                    menu = self.get_current_DOM().select(f"#{child.attrs['id']}")[0]
                    subMenuElements = menu.select(menu_itens_term)
                    if time.time() > endtime and (
                            not subMenuElements or len(subMenuElements) < self.children_element_count(menu_term,
                                                                                                      menu_itens_term)):
                        self.restart_counter += 1
                        self.log_error(f"Couldn't find lateral menu")

                regex = r"(<[^>]*>)?"
                if self.webapp_shadowroot():
                    child = list(filter(
                        lambda x: hasattr(x, 'caption') and re.sub(regex, '', x['caption'].lower().strip()).startswith(
                            menuitem.lower().strip()), subMenuElements))
                else:
                    child = list(filter(lambda x: x.text.startswith(menuitem), subMenuElements))

                child = list(filter(lambda x: x.attrs['id'] not in used_ids, child))

                child = next(iter(child), None)

                if hasattr(child, 'attrs'):
                    used_ids.append(child.attrs['id'])

                self.scroll_to_element(self.soup_to_selenium(child))

                if not child or not self.element_is_displayed(child):
                    self.restart_counter += 1
                    self.log_error(f"Couldn't find menu item: {menuitem}")

                try:
                    self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(child))))
                    submenu = lambda: self.driver.find_element(By.XPATH, xpath_soup(child))
                except:
                    logger().info(f'not child xpath')
                    self.wait.until(EC.element_to_be_clickable((By.ID, child['id'])))
                    submenu = lambda: self.driver.find_element(By.ID, child['id'])

                if subMenuElements and submenu():
                    self.expanded_menu(child)
                    self.scroll_to_element(submenu())
                    self.wait_until_to(expected_condition="element_to_be_clickable", element=child, locator=By.XPATH)
                    self.wait_blocker()
                    expanded = lambda: 'expanded' in submenu().get_attribute('class')
                    item_exist = lambda: self.element_exists(term=menuitem, scrap_type=enum.ScrapType.MIXED,
                                                             optional_term=menu_itens_term,
                                                             main_container="body, wa-dialog")
                    tmodal = lambda: self.get_current_DOM().select('.tmodaldialog')

                    endtime = time.time() + self.config.time_out

                    clicked_menu = False

                    while time.time() < endtime and (index != last_index and not expanded()) or (
                            index == last_index and item_exist() and not tmodal()) and not clicked_menu:
                        if click_menu_functional:
                            clicked_menu = True
                        ActionChains(self.driver).move_to_element(submenu()).click().perform()
                        time.sleep(2)

                    if count < len(menu_itens) - 1:
                        if not self.webapp_shadowroot():  
                            self.wait_element(term=menu_itens[count], scrap_type=enum.ScrapType.MIXED,
                                              optional_term=menu_itens_term, main_container="body")
                            menu = self.get_current_DOM().select(f"#{child.attrs['id']}")[0]
                else:
                    self.restart_counter += 1
                    self.log_error(f"Error - Menu Item does not exist: {menuitem}")
                count += 1

            used_ids = []
            if not self.webapp_shadowroot():
                if not re.search("\([0-9]\)$", child.text):
                    self.slm_click_last_item(f"#{child.attrs['id']} > label")

                start_time = time.time()
                child_is_displayed = True

                child_attrs = f"#{child.attrs['id']} > label"

                child_object = next(iter(
                    self.web_scrap(term=child_attrs, scrap_type=enum.ScrapType.CSS_SELECTOR,
                                   main_container="body")), None)

                counter_child = 1
                if menuitem != self.language.menu_about.split('>')[1].strip():
                    while (time.time() < endtime) and (child_is_displayed and counter_child <= 3):
                        time.sleep(1)

                        try:
                            if child_object:
                                child_element = lambda: self.soup_to_selenium(child_object)

                                if hasattr(child_element(), 'is_displayed'):
                                    child_is_displayed = child_element().is_displayed()

                                    elapsed_time = time.time() - start_time
                                    self.wait_blocker()
                                    time.sleep(1)

                                    if elapsed_time >= 20 and not click_menu_functional:
                                        start_time = time.time()
                                        logger().info(f'Trying an additional click in last menu item: "{menuitem}"')
                                        if not re.search("\([0-9]\)$", child.text):
                                            self.slm_click_last_item(f"#{child.attrs['id']} > label")
                            else:
                                counter_child += 1
                        except:
                            counter_child += 1

            if wait_screen and self.config.initial_program.lower() == 'sigaadv':
                self.close_warning_screen_after_routine()
                self.close_coin_screen_after_routine()
                self.close_news_screen_after_routine()

            self.wait_blocker()
            if self.element_exists(term=term, scrap_type=scrap_type,
                                   main_container="body", optional_term=optional_term_news):
                self.close_news_screen()

        except AssertionError as error:
            raise error
        except Exception as error:
            logger().exception(str(error))
            self.restart_counter += 1

    def expanded_menu(self, element):
        if self.webapp_shadowroot():
            tmenu_term = '.dict-tmenu'
        else:
            tmenu_term = '.tmenu'

        expanded = lambda: True if "expanded" in self.get_current_DOM().select(f"#{element.attrs['id']}")[0].attrs['class'] else False

        endtime = time.time() + self.config.time_out
        while time.time() < endtime and expanded():
            self.wait_blocker()
            self.wait_element(term=tmenu_term, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
            if self.webapp_shadowroot():
                span = self.find_child_element('span', element)
                parent_menu = next(iter(span), None)
            else:
                label_expanded = next(iter(element.select('label')), None)
                parent_menu = self.driver.find_element(By.XPATH, xpath_soup(label_expanded))
            self.scroll_to_element(parent_menu)
            self.wait_blocker()
            ActionChains(self.driver).move_to_element(parent_menu).click().perform()
            self.wait_element(term=tmenu_term, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")


    def tmenuitem_element(self, menu):
        subMenuElements = menu.select(".tmenuitem")
        subMenuElements = list(filter(lambda x: self.element_is_displayed(x), subMenuElements))


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


    def slm_click_last_item(self, sub_menu_child_label):
        """
        [Internal]

        SetLateralMenu, this method retry click in the last sub item
        """
        try:
            child_label = next(iter(self.web_scrap(term=sub_menu_child_label,
                scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")), None)
            child_label_s = self.soup_to_selenium(child_label)
            child_label_s.click()
        except Exception as e:
            if self.config.smart_test or self.config.debug_log:
                logger().warning(f"Warning SetLateralMenu click last item method exception: {str(e)} ")


    def SetButton(self, button, sub_item="", position=1, check_error=True):
        """
        Method that clicks on a button on the screen.

        :param button: Button to be clicked.
        :type button: str
        :param sub_item: Sub item to be clicked inside the first button. - **Default:** "" (empty string)
        :type sub_item: str
        :param position: Position which element is located. - **Default:** 1
        :type position: int

        > ⚠️ **Warning:**
        > If there are a sequence of similar buttons. Example:
        `self.oHelper.SetButton("Salvar")`
        `self.oHelper.SetButton("Salvar")`
        We recomend insert some wait of elements method between them, like WaitShow, WaitHide... etc.
        This way you ensure the correct element be selected in correct screen.

        Usage:

        >>> # Calling the method to click on a regular button:
        >>> oHelper.SetButton("Add")
        >>> #-------------------------------------------------
        >>> # Calling the method to click on a sub item inside a button.
        >>> oHelper.SetButton("Other Actions", "Process")
        >>> #-------------------------------------------------
        >>> # Calling the method to click on a sub item inside a button, this form is an alternative.
        >>> oHelper.SetButton("Other Actions", "Process, Process_02, Process_03")
        """
        logger().info(f"Clicking on {button}")

        initial_program = ['sigaadv', 'sigamdi']

        self.wait_blocker()
        container = self.get_current_container()

        if self.webapp_shadowroot():
            term_button="wa-button"
        else:
            term_button="button, .thbutton"

        if container  and 'id' in container.attrs:
            id_container = container.attrs['id']

        try:
            restore_zoom = False
            soup_element  = ""
            if (button.lower().strip() == "x"):
                self.set_button_x(position, check_error)
                return
            elif (button.strip() == "?"):
                self.set_button_character(term=button, position=position, check_error=check_error)
                return
            else:
                self.wait_element_timeout(term=button, scrap_type=enum.ScrapType.MIXED, optional_term=term_button, timeout=10, step=0.1, check_error=check_error)
                position -= 1

            layers = 0
            if button in [self.language.confirm, self.language.save]:
                layers = len(self.driver.find_elements(By.CSS_SELECTOR, ".tmodaldialog"))

            success = False
            endtime = time.time() + self.config.time_out
            starttime = time.time()

            if self.config.smart_test or self.config.debug_log:
                logger().debug(f"***System Info*** Before Clicking on button:{button}")
                system_info()

            regex = r"(<[^>]*>)?"
            filtered_button = []
            next_button = None
            while(time.time() < endtime and not soup_element):
                if self.webapp_shadowroot():
                    self.wait_element_timeout(term=button, scrap_type=enum.ScrapType.MIXED, optional_term=term_button, timeout=10, step=0.1, check_error=check_error)
                    self.containers_selectors["GetCurrentContainer"] = "wa-dialog, wa-message-box,.tmodaldialog, body"
                    soup = self.get_current_container()
                    soup_objects = soup.select(term_button)

                    if soup_objects and not filtered_button:
                        filtered_button = list(filter(lambda x: hasattr(x,'caption') and button.lower() in re.sub(regex,'',x['caption'].lower()) and self.element_is_displayed(x), soup_objects ))

                        if not filtered_button:
                            filtered_button = self.return_soup_by_selenium(elements=soup_objects, term=button, selectors='label, span')

                    if self.webapp_shadowroot():
                        if not soup_objects:
                            footer = self.find_shadow_element('footer', self.soup_to_selenium(soup), get_all=False)
                            if footer:
                                buttons = self.find_shadow_element("wa-button", footer)
                                if not buttons:
                                    buttons = footer.find_elements(By.CSS_SELECTOR, "wa-button")
                                if buttons:
                                    filtered_button = list(filter(lambda x: x.text.strip().replace('\n', '') == button.strip().replace(' \n ', ''), buttons))

                    if filtered_button and len(filtered_button) - 1 >= position:
                        parents_actives = list(filter(lambda x: self.filter_active_tabs(x), filtered_button ))
                        if parents_actives:
                            filtered_button = parents_actives
                        next_button = filtered_button[position]
                    else:
                        filtered_button = list(filter(lambda x: (hasattr(x,'caption') and button.lower() in re.sub(regex,'',x['caption'].lower())) and 'focus' in x.get('class'), soup_objects ))

                    if not filtered_button:
                        filtered_button = self.web_scrap(term=button, scrap_type=enum.ScrapType.MIXED, optional_term="wa-button", main_container = self.containers_selectors["SetButton"])

                    if next_button:
                        id_parent_element = next_button['id'] if hasattr(next_button, 'id') and type(next_button) == Tag else None
                        soup_element = self.soup_to_selenium(next_button) if type(next_button) == Tag else next_button
                        self.scroll_to_element(soup_element)
                        soup_element = soup_element if self.element_is_displayed(soup_element) else None
                        if soup_element == None:
                            bodySoup = self.get_current_DOM().select('body')
                            self.driver.execute_script("arguments[0].style.cssText+='transform: scale(0.8)';", self.soup_to_selenium(bodySoup[0]))
                            soup_element = soup_element if self.element_is_displayed(soup_element) else None
                            restore_zoom = True

                else:
                    soup_objects = self.web_scrap(term=button, scrap_type=enum.ScrapType.MIXED, optional_term="button, .thbutton", main_container = self.containers_selectors["SetButton"], check_error=check_error)

                    if isinstance(soup_objects, list):
                        soup_objects = list(filter(lambda x: self.element_is_displayed(x), soup_objects ))

                    if soup_objects and len(soup_objects) - 1 >= position:
                        self.wait_until_to( expected_condition = "element_to_be_clickable", element = soup_objects[position], locator = By.XPATH, timeout=True)
                        soup_element = lambda : self.soup_to_selenium(soup_objects[position])
                        parent_element = self.soup_to_selenium(soup_objects[0].parent)
                        id_parent_element = parent_element.get_attribute('id')

            if self.config.smart_test:
                logger().debug(f"Clicking on Button {button} Time Spent: {time.time() - starttime} seconds")

            if not soup_element:
                other_action = self.web_scrap(term=self.language.other_actions, scrap_type=enum.ScrapType.MIXED, optional_term=term_button, check_error=check_error)
                if (other_action is None or not hasattr(other_action, "name") and not hasattr(other_action, "parent")):
                    self.log_error(f"Couldn't find element: {button}")

                other_action_element = lambda : self.soup_to_selenium(next(iter(other_action)))

                self.scroll_to_element(other_action_element())
                self.click(other_action_element())

                success = self.click_sub_menu(button if button.lower() != self.language.other_actions.lower() else sub_item)
                if success:
                    return
                else:
                    self.log_error(f"Element {button} not found!")

            if soup_element:
                if self.webapp_shadowroot():
                    self.scroll_to_element(soup_element)
                    self.set_element_focus(soup_element)
                    self.send_action(action=self.click, element=lambda: soup_element)
                    if button.lower() == self.language.other_actions.lower():
                        popup_item = lambda: self.wait_element_timeout(term=".tmenupopupitem, wa-menu-popup", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body", check_error=False)
                        while time.time() < endtime and not popup_item():
                            self.click(soup_element)
                    if restore_zoom:
                        bodySoup = self.get_current_DOM().select('body')
                        self.driver.execute_script("arguments[0].style.cssText+='transform: scale(1)';", self.soup_to_selenium(bodySoup[0]))
                        soup_element = soup_element if self.element_is_displayed(soup_element) else None

                else:
                    self.scroll_to_element(soup_element())
                    self.set_element_focus(soup_element())
                    self.wait_until_to( expected_condition = "element_to_be_clickable", element = soup_objects[position], locator = By.XPATH )
                    if button.lower() == self.language.other_actions.lower() and self.config.initial_program.lower() in initial_program:
                        self.click(soup_element())
                    else:
                        self.send_action(self.click, soup_element)
                    self.wait_element_is_not_focused(soup_element)

            if sub_item and ',' not in sub_item:
                logger().info(f"Clicking on {sub_item}")
                if self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
                    self.tmenu_out_iframe = True

                soup_objects_filtered = None
                while (time.time() < endtime and not soup_objects_filtered):
                    if button == self.language.other_actions:
                        self.wait_element_timeout(term=".tmenupopupitem, wa-menu-popup", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body", check_error=False)

                    soup_objects = self.web_scrap(term=sub_item, scrap_type=enum.ScrapType.MIXED,
                                                  optional_term=".tmenupopupitem, wa-menu-popup", main_container="body",
                                                  check_error=check_error, second_term='wa-menu-popup-item')
                    if soup_objects:
                        soup_objects_filtered = self.filter_is_displayed(soup_objects)

                if soup_objects_filtered:
                    if self.webapp_shadowroot():
                        EC.element_to_be_clickable(soup_objects_filtered[0])
                    else:
                        contents = list(map(lambda x: x.contents, soup_objects_filtered))
                        soup_objects_filtered = next(iter(
                            list(filter(lambda x: x[0].text.strip().lower() == sub_item.strip().lower(), contents))),
                            None)
                        soup_element = lambda: self.soup_to_selenium(soup_objects_filtered[0])
                        self.wait_until_to(expected_condition="element_to_be_clickable",
                                           element=soup_objects_filtered[0],
                                           locator=By.XPATH)

                    self.click(soup_element()) if not self.webapp_shadowroot() else self.click(soup_objects_filtered[0])
                    self.tmenu_out_iframe = False
                else:

                    result = False
                    self.tmenu_out_iframe = False

                    soup_objects = self.web_scrap(term=button, scrap_type=enum.ScrapType.MIXED, optional_term=term_button, main_container = self.containers_selectors["SetButton"], check_error=check_error)

                    if isinstance(soup_objects, list):
                        soup_objects = list(filter(lambda x: self.element_is_displayed(x), soup_objects ))

                    if soup_objects and len(soup_objects) - 1 >= position:
                        if  type(soup_objects[position]) == Tag:
                            soup_element = lambda : self.soup_to_selenium(soup_objects[position])
                        else:
                            soup_element = lambda : soup_objects[position]
                    else:
                        self.log_error(f"Couldn't find element {button}")

                    self.scroll_to_element(soup_element())#posiciona o scroll baseado na height do elemento a ser clicado.
                    self.set_element_focus(soup_element())
                    if not self.webapp_shadowroot():
                        self.wait_until_to( expected_condition = "element_to_be_clickable", element = soup_objects[position], locator = By.XPATH )
                    self.send_action(self.click, soup_element)

                    result  = self.click_sub_menu(sub_item)

                    if not result:
                        self.log_error(f"Couldn't find element {sub_item}")
                    else:
                        return

            elif ',' in sub_item:
                list_sub_itens = sub_item.split(',')
                filtered_sub_itens = list(map(lambda x: x.strip(), list_sub_itens))
                sucess = self.click_sub_menu(filtered_sub_itens)
                if not sucess:
                    self.log_error(f"Couldn't find element {sub_item}")

            buttons = [self.language.Ok, self.language.confirm, self.language.finish,self.language.save, self.language.exit, self.language.next, "x"]

            buttons_filtered = list(map(lambda x: x.lower(), buttons))

            if button.lower() in buttons_filtered:

                if self.used_ids:
                    self.used_ids = self.pop_dict_itens(self.used_ids, id_container)

                elif self.grid_counters:
                    self.grid_counters = {}

            if button == self.language.save and id_parent_element in self.get_enchoice_button_ids(layers):
                self.wait_element_timeout(term="", scrap_type=enum.ScrapType.MIXED, optional_term="[style*='fwskin_seekbar_ico']", timeout=10, step=0.1, check_error=False, main_container="body")
                self.wait_element_timeout(term="", scrap_type=enum.ScrapType.MIXED, presence=False, optional_term="[style*='fwskin_seekbar_ico']", timeout=10, step=0.1, check_error=False, main_container="body")
            elif not self.webapp_shadowroot() and button == self.language.confirm and id_parent_element in self.get_enchoice_button_ids(layers):
                self.wait_element_timeout(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=layers + 1, main_container="body", timeout=10, step=0.1, check_error=False)

        except ValueError as error:
            logger().exception(str(error))
            logger().exception(f"Button {button} could not be located.")
        except AssertionError:
            raise
        except Exception as error:
            logger().exception(str(error))

        if self.config.smart_test or self.config.debug_log:
            logger().debug(f"***System Info*** After Clicking on button:")
            system_info()
    
    def set_button_character(self, term, position=1, check_error=True):
        """
        [Internal]
        """

        position -= 1
        button = None

        self.wait_element(term=term, position=position, check_error=check_error, main_container=self.containers_selectors["AllContainers"])

        endtime = time.time() + self.config.time_out

        while time.time() < endtime and not button:
            
            container = self.get_current_container()

            buttons = container.select('button')

            buttons_displayed = list(filter(lambda x: self.element_is_displayed(x), buttons))

            filtered_button = list(filter(lambda x: x.text.strip().lower() == term.strip().lower(), buttons_displayed))

            if filtered_button and len(filtered_button) - 1 >= position:
                button = filtered_button[position]
            
            element = self.soup_to_selenium(button)

            self.scroll_to_element(element)
            self.wait_until_to(expected_condition="element_to_be_clickable", element=button, locator=By.XPATH)
            self.click(element)

    def set_button_x(self, position=1, check_error=True):
        endtime = self.config.time_out/2
        if self.webapp_shadowroot():
            term_button = f"wa-dialog[title*={self.language.warning}], wa-button[icon*='fwskin_delete_ico'], wa-button[style*='fwskin_delete_ico'], wa-image[src*='fwskin_modal_close.png'], wa-dialog"
        else:
            term_button = ".ui-button.ui-dialog-titlebar-close[title='Close'], img[src*='fwskin_delete_ico.png'], img[src*='fwskin_modal_close.png']"

        position -= 1
        wait_button = self.wait_element_timeout(term=term_button, scrap_type=enum.ScrapType.CSS_SELECTOR, timeout=endtime, position=position, check_error=check_error)

        if wait_button:
            soup = self.get_current_container()
            if hasattr(soup, 'attrs') and 'title' in soup.attrs and f'{self.language.warning}' in soup.attrs['title']:
                soup = self.get_current_DOM()
        else:
            soup = self.get_current_DOM()

        close_list = soup.select(term_button)
        if not close_list:
            soup = self.get_current_DOM()
            close_list = soup.select(term_button)

        if not close_list:
            self.log_error(f"Element not found")
        if len(close_list) < position + 1:
            self.log_error(f"Element x position: {position} not found")
        if position == 0:
            element_soup = close_list.pop()
        else:
            element_soup = close_list.pop(position)
        element_selenium = self.soup_to_selenium(element_soup)
        if self.webapp_shadowroot():
            header = self.find_shadow_element('wa-dialog-header', element_selenium, get_all=False)
            x_button = self.find_shadow_element("button[class~=button-close]", header, get_all=False)
            if x_button:
                element_selenium = x_button

        self.scroll_to_element(element_selenium)
        self.wait_until_to(expected_condition="element_to_be_clickable", element=element_soup, locator=By.XPATH)

        self.send_action(action=self.click, element=lambda : element_selenium)


    def click_sub_menu(self, filtered_sub_itens):
        """
        [Internal]

        Clicks on the sub menu of buttons. Returns True if succeeded.
        Internal method of SetButton.

        :param filtered_sub_itens: The menu item that should be clicked.
        :type filtered_sub_itens: str

        :return: Boolean if click was successful.
        :rtype: bool

        Usage:

        >>> # Calling the method:
        >>> self.click_sub_menu("Process")
        """

        regex = r"(<[^>]*>)?"


        selector = '.dict-tmenuitem' if self.webapp_shadowroot() else '.tmenupopup.active'
        if self.driver.execute_script("return app.VERSION").split('-')[0] >= "4.6.4":
            self.driver.switch_to.default_content()

        content = self.driver.page_source
        soup = BeautifulSoup(content,"html.parser")

        if isinstance(filtered_sub_itens, list):
            sub_item = filtered_sub_itens[len(filtered_sub_itens) - 1]
            if self.webapp_shadowroot():
                parent_id = next(filter(lambda x: re.sub(regex, '', x.get('caption')).strip() == filtered_sub_itens[-2], soup.select(selector)), None)
                if parent_id:
                    parent_id = parent_id.get('id')
                    menu_id = next(filter(lambda x: re.sub(regex, '', x.get('caption')).strip() == sub_item and x.parent.get('id') == parent_id, soup.select(selector)), None)
                    if menu_id:
                        menu_id = menu_id.get('id')
            else:
                menu_id = self.zindex_sort(soup.select(selector), True)[0].attrs["id"]
        else:
            if self.webapp_shadowroot():
                menu_id = next(filter(lambda x: re.sub(regex, '', x.get('caption')).strip() == filtered_sub_itens, soup.select(selector)), None)
                if menu_id:
                    menu_id= menu_id.get('id')
            else:
                menu_id = self.zindex_sort(soup.select(selector), True)[0].attrs["id"]

        menu = self.driver.find_element(By.ID, menu_id)

        if self.webapp_shadowroot():
            class_selector = '.dict-tmenuitem'
            item = menu
        else:
            class_selector = ".tmenupopupitem"
            menu_itens = menu.find_elements(By.CSS_SELECTOR, class_selector)

            result = self.find_sub_menu_text(sub_item, menu_itens)

            item = ""
            if result[1]:
                item = self.find_sub_menu_child(sub_item, result[1])
            elif result[0]:
                item = result[0]

            else:
                return False

        if item:
            self.scroll_to_element(item)
            time.sleep(0.5)
            self.click(item)
            return True
        else:
            return False

    def find_sub_menu_child(self, sub_item, containers):
        """
        [Internal]

        Finds the menu item inside child menu layers.

        :param sub_item: The menu item that should be clicked.
        :type sub_item: str
        :param containers: The menu itens of the current layer that have children.
        :type containers: List of Beautiful Soup objects

        :return: The item that was found. If None was found, it returns an empty string.
        :rtype: Selenium object

        Usage:

        >>> # Calling the method:
        >>> item = self.find_sub_menu_child("Process", container_list)
        """
        item = ""
        for child in containers:

            child_id = child.get_attribute("id")
            old_class = self.driver.execute_script("return document.querySelector('#{}').className".format(child_id))
            new_class = old_class + " highlighted expanded, highlight expanded"
            self.driver.execute_script("document.querySelector('#{}').className = '{}'".format(child_id, new_class))

            child_itens = child.find_elements(By.CSS_SELECTOR, ".tmenupopupitem")
            result = self.find_sub_menu_text(sub_item, child_itens)

            if not result[0] and result[1]:
                item = self.find_sub_menu_child(sub_item, result[1])
            else:
                item = result[0]
                if item:
                    break
                self.driver.execute_script("document.querySelector('#{}').className = '{}'".format(child_id, old_class))

        return item

    def find_sub_menu_text(self, menu_item, current_itens):
        """
        [Internal]

        Returns a tuple containing a possible match of a menu item among the current itens.
        If none was found it will be an empty string.

        The second position will contain the itens that have children itens.
        If none has children itens, it will be an empty list.

        :param menu_item: The menu item that should be clicked.
        :type menu_item: str
        :param current_item: The menu itens in the current layer.
        :type current_item: List of Selenium objects.

        :return: Tuple containing a possible match of a menu item and the itens that have children itens.
        :rtype: Tuple (selenium object, list of selenium objects)

        Usage:

        >>> # Calling the method:
        >>> result = self.find_sub_menu_text(item, child_itens)
        """
        submenu = ""
        containers = []
        for child in current_itens:
            if "container" in child.get_attribute("class"):
                containers.append(child)
            elif child.text.lower().rstrip() == menu_item.lower().rstrip():
                submenu = child

        return (submenu, containers)

    def SetBranch(self, branch):
        """
        Chooses the branch on the branch selection screen.

        :param branch: The branch that would be chosen.
        :type branch: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetBranch("D MG 01 ")
        """
        logger().info(f"Setting branch: {branch}.")

        if self.webapp_shadowroot():
            term = '.dict-tpanel'
        else:
            term = "[style*='fwskin_seekbar_ico']"
        self.wait_element(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR, position=2, main_container="body")
        Ret = self.fill_search_browse(branch, self.get_search_browse_elements())
        if Ret:
            self.SetButton('OK')

    def WaitHide(self, string, timeout=None, throw_error=True, match_case=False):
        """
        Search string that was sent and wait hide the element.

        :param string: String that will hold the wait.
        :type string: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitHide("Processing")
        """
        logger().info("Waiting Hide...")

        if not timeout:
            timeout = 1200

        endtime = time.time() + timeout
        while(time.time() < endtime):

            element = None
            element = self.web_scrap(term=string, scrap_type=enum.ScrapType.MIXED,
                                     optional_term=".tsay, .tgroupbox, wa-text-view",
                                     main_container=self.containers_selectors["AllContainers"],
                                     check_help=False, match_case=match_case)

            if not element:
                return
            if endtime - time.time() < 1180:
                time.sleep(0.5)

        if not throw_error:
            return False
        else:
            self.log_error(f"Element {string} not found")

    def WaitShow(self, string, timeout=None, throw_error=True, match_case=False):
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

            element = self.web_scrap(term=string, scrap_type=enum.ScrapType.MIXED,
                                     optional_term=".tsay, .tgroupbox, wa-text-view",
                                     main_container=self.containers_selectors["AllContainers"],
                                     check_help=False, match_case=match_case)

            if element:
                logger().info(f"Text found! ")
                return True

            if endtime - time.time() < 1180:
                time.sleep(0.5)

        if not throw_error:
            return False
        else:
            self.log_error(f"Element {string} not found")

    def WaitProcessing(self, itens, timeout=None, match_case=False):
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

        self.WaitShow(itens, timeout, throw_error = False, match_case=match_case)

        self.WaitHide(itens, timeout, throw_error = False, match_case=match_case)


    def SetTabEDAPP(self, table):
        """
        Chooses the table on the generic query (EDAPP).

        :param table: The table that would be chosen.
        :type table: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetTabEDAPP("AAB")
        """
        try:
            logger().debug('Filling EDAPP...')
            table       = table.lower().strip()
            column_item = None

            self.wait_element(term=f"[name$='cPesq']", scrap_type=enum.ScrapType.CSS_SELECTOR)
            field   = self.get_field("cPesq", name_attr=True)
            element = lambda: self.driver.find_element(By.XPATH, xpath_soup(field))
            endtime = time.time() + self.config.time_out / 2
            while time.time() < endtime and not column_item:
                self.click(element(), click_type=enum.ClickType.ACTIONCHAINS)
                self.send_keys(element(), table)
                self.send_keys(element(), Keys.ENTER)
                self.wait_blocker()
                rows = self.get_grid_content(0, '.dict-twbrowse')
                for row in rows:
                    columns     = self.driver.execute_script("return arguments[0].querySelectorAll('td')", row)
                    column_item = next(iter(filter(lambda x: x.text.lower().strip() == table, columns)),None)
                    if column_item:
                        self.send_action(action=self.click, element=lambda: row)
                        break
            self.SetButton("Ok")
        except:
            logger().exception("Search field could not be located.")

    def ClickFolder(self, folder_name, position):
        """
        Clicks on folder elements on the screen.

        :param folder_name: Which folder item should be clicked.
        :type folder_name: str
        :param position: In case of two or more folders with the same name in the screen, you could choose by position in order
        :type position: int

        Usage:

        >>> # Calling the method:
        >>> oHelper.ClickFolder("Folder1")
        >>> # Second folder named as Folder1 in the same screen
        >>> oHelper.ClickFolder("Folder1", position=2)
        """

        logger().info(f"Clicking on folder: {folder_name}")

        self.wait_blocker()

        if self.webapp_shadowroot():
            term = '.dict-tfolder, wa-tab-page'
            bt_term = ".dict-tfolder"
        else:
            term = '.tfolder.twidget, .button-bar a'
            bt_term = ".button-bar a"

        element = ""
        position -= 1

        if self.current_wa_tab_view_id() == self.last_wa_tab_view_input_id:
            self.displayed_label_on_screen(label=folder_name, selector='wa-tab-button')

        self.wait_element(term=folder_name, scrap_type=enum.ScrapType.MIXED, optional_term=term, second_term='wa-tab-button')

        endtime  = time.time() + self.config.time_out
        half_config_timeout = time.time() + self.config.time_out / 2


        while(time.time() < endtime and not element):
            if self.webapp_shadowroot():
                panels_filtered = self.web_scrap(term=folder_name, scrap_type=enum.ScrapType.MIXED, optional_term=bt_term ,main_container = self.containers_selectors["GetCurrentContainer"], second_term='wa-tab-button')
            else:
                panels = self.web_scrap(term=bt_term, scrap_type=enum.ScrapType.CSS_SELECTOR,main_container = self.containers_selectors["GetCurrentContainer"])
                panels_filtered = self.filter_is_displayed(list(filter(lambda x: x.text == folder_name, panels)))

                if time.time() >= half_config_timeout:
                    panels_filtered = list(filter(lambda x: x.text == folder_name, panels))

            if panels_filtered:
                if self.webapp_shadowroot():
                    self.scroll_to_element(panels_filtered[position])

                if position > 0:
                    panel = panels_filtered[position] if position < len(panels_filtered) else None
                else:
                    while isinstance(panels_filtered, list):
                        panels_filtered = next(iter(panels_filtered), None)
                    panel = panels_filtered

                element = self.soup_to_selenium(panel) if panel and not self.webapp_shadowroot() else panel

                if element:
                    self.scroll_to_element(element)#posiciona o scroll baseado na height do elemento a ser clicado.
                    self.set_element_focus(element)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click()", element)

        if not element:
            self.log_error("Couldn't find panel item.")

    def displayed_label_on_screen(self, label, selector):

        selector_list = self.get_container_selector(selector)
        element_is_displayed = False

        filtered_label = self.filter_label_by_selector(label=label, selector=selector_list)

        if filtered_label:
            element_is_displayed = self.element_is_displayed(filtered_label)

            if not element_is_displayed:
                active_element = next(iter(filter(lambda x: 'active' in x.attrs, selector_list)), None)
                element = lambda: self.soup_to_selenium(active_element)
                self.scroll_to_element(element=element())
            
    def filter_label_by_selector(self, label, selector):

        label = label.lower().strip()

        return next(iter(list(filter(lambda x: x.text.lower().strip() == label or x.attrs.get('caption', '').lower().strip() == label, selector))), None)

    def ClickBox(self, fields="", content_list="", select_all=False, grid_number=1, itens=False):
        """
        Clicks on Checkbox elements of a grid.

        :param fields: Comma divided string with values that must be checked, combine with content_list.
        :type fields: str
        :param content_list: Comma divided string with values that must be checked. - **Default:** "" (empty string)
        :type content_list: str
        :param select_all: Boolean if all options should be selected. - **Default:** False
        :type select_all: bool
        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int
        :param itens: Bool parameter that click in all itens based in the field and content reference.
        :type itens: bool

        Usage:

        >>> # Calling the method to select a specific checkbox:
        >>> oHelper.ClickBox("Branch", "D MG 01 ")
        >>> #--------------------------------------------------
        >>> # Calling the method to select multiple checkboxes:
        >>> oHelper.ClickBox("Branch", "D MG 01 , D RJ 02")
        >>> #--------------------------------------------------
        >>> # Calling the method to select all checkboxes:
        >>> oHelper.ClickBox("Branch", select_all=True)
        >>> #--------------------------------------------------
        >>> # Calling the method to performe click based in 2 fields and contens:
        >>> test_helper.ClickBox('Numero da SC, Item da SC', 'COM068, 0001')
        >>> #--------------------------------------------------
        >>> # Calling the method to click in all itens with this reference:
        >>> test_helper.ClickBox('Numero da SC', 'COM068', itens=True)
        """

        logger().info(f"ClickBox - Clicking on {content_list}")
        self.wait_blocker()
        grid_number -= 1
        if not select_all:
            fields = list(map(lambda x: x.strip(), fields.split(',')))
            content_list = list(map(lambda x: x.strip(), content_list.split(',')))

            if len(fields) == 2 and len(content_list) == 2 and not select_all:
                self.click_box_dataframe(*fields, *content_list, grid_number=grid_number)
            elif len(fields) == 1 and len(content_list) == 2 and not select_all:
                self.click_box_dataframe(first_column=fields, first_content=content_list[0], second_content=content_list[1], grid_number=grid_number)
            elif len(fields) == 1 and not select_all:
                self.click_box_dataframe(first_column=fields[0], first_content=content_list[0], grid_number=grid_number, itens=itens)


        if select_all:
            optional_term = "wa-button" if self.webapp_shadowroot() else "label span"
            self.wait_element_timeout(term=self.language.invert_selection, scrap_type=enum.ScrapType.MIXED, optional_term=optional_term)

            grid = self.get_grid(grid_number)

            is_select_all_button = self.element_exists(term=self.language.invert_selection, scrap_type=enum.ScrapType.MIXED, optional_term=optional_term)

            if select_all and is_select_all_button:
                self.wait_element(term=self.language.invert_selection, scrap_type=enum.ScrapType.MIXED, optional_term=optional_term)
                if self.webapp_shadowroot():
                    element = next(iter(self.web_scrap(term=self.language.invert_selection, scrap_type=enum.ScrapType.MIXED, optional_term=optional_term)), None)
                else:
                    element = next(iter(self.web_scrap(term="label.tcheckbox input", scrap_type=enum.ScrapType.CSS_SELECTOR)), None)

                if element:
                    box = lambda: element if self.webapp_shadowroot() else lambda: self.driver.find_element(By.XPATH, xpath_soup(element))
                    self.click(box())

            elif select_all and not is_select_all_button:
                success = False
                endtime = time.time() + self.config.time_out
                while time.time() < endtime and not success:
                    try:
                        th = self.find_shadow_element('th', self.soup_to_selenium(grid)) if self.webapp_shadowroot() else next(
                            iter(grid.select('th')))

                        if th:
                            if self.webapp_shadowroot():
                                first_cell = self.find_shadow_element('tr td div', self.soup_to_selenium(grid))
                                if first_cell:
                                    current_box = lambda: next(iter(first_cell)).get_attribute('style')
                                    before_box = current_box()
                                    endtime = time.time() + self.config.time_out
                                    while time.time() < endtime and current_box() == before_box:
                                        th_element = next(iter(th))
                                        th_element.click()
                                        success = current_box() != before_box
                                else:
                                    logger().debug('ClickBox not first_cell condition')
                                    th_element = next(iter(th))
                                    th_element.click()
                                    success = True # not maped yet
                            else:
                                th_element = self.soup_to_selenium(th)
                                th_element.click()
                                success = True # not maped yet
                    except:
                        pass
                if not success:
                    self.log_error("Couldn't find ClickBox item")

    def performing_click(self, element_bs4, class_grid, click_type=1):

        if not self.webapp_shadowroot():
            self.wait_until_to(expected_condition="element_to_be_clickable", element=element_bs4, locator=By.XPATH)
            element = lambda: self.soup_to_selenium(element_bs4)
        else:
            element = lambda: element_bs4

        self.set_element_focus(element())
        self.scroll_to_element(element())

        time.sleep(1)
        try:
            if click_type == 1:
                ActionChains(self.driver).move_to_element(element()).click(element()).perform()
                event = "var evt = document.createEvent('MouseEvents');\
                    evt.initMouseEvent('dblclick',true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0,null);\
                    arguments[0].dispatchEvent(evt);"
                self.driver.execute_script(event, element())
            elif click_type == 2:
                self.double_click(element(), click_type=enum.ClickType.ACTIONCHAINS)
            elif click_type == 3:
                element().click()
                ActionChains(self.driver).move_to_element(element()).send_keys(Keys.ENTER).perform()
            elif click_type == 4:
                self.send_action(action=self.double_click, element=element, wait_change=False)
        except:
            pass

    def click_box_dataframe(self, first_column=None, second_column=None, first_content=None, second_content=None, grid_number=0, itens=False):

        index_number = []
        count = 0

        endtime = time.time() + self.config.time_out
        while time.time() < endtime and len(index_number) < 1 and count <= 3:

            try:
                df, grid = self.grid_dataframe(grid_number=grid_number)

                last_df = df

                class_grid = next(iter(grid.attrs['class']))

                if not df.empty:
                    if first_column and second_column:
                        index_number = df.loc[(df[first_column] == first_content) & (df[second_column] == second_content)].index.array
                    elif first_column and (first_content and second_content):
                        index_number = df.loc[(df[first_column[0]] == first_content) | (df[first_column[0]] == second_content)].index.array
                    elif itens:
                        index_number = df.loc[(df[first_column] == first_content)].index.array
                    elif first_column and first_content:
                        first_column = next(iter(list(filter(lambda x: first_column.lower().strip() in x.lower().strip(), df.columns))), None)
                        first_column_values = df[first_column].values
                        first_column_formatted_values = list(map(lambda x: x.replace(' ', ''), first_column_values))
                        content = next(iter(list(filter(lambda x: x == first_content.replace(' ', ''), first_column_formatted_values))), None)
                        if content:
                            index_number.append(first_column_formatted_values.index(content))
                            if len(index_number) > 0:
                                index_number = [index_number[0]]
                    else:
                        index_number.append(0)

                    if len(index_number) < 1 and count <= 3:
                        first_element_focus = next(iter(grid.select('tbody > tr > td')), None)
                        if self.webapp_shadowroot():
                            if not first_element_focus:
                                first_element_focus = self.driver.execute_script("return arguments[0].shadowRoot.querySelector('tbody tr td')", self.soup_to_selenium(grid))
                        if first_element_focus:
                            if self.webapp_shadowroot():
                                first_element_focus.click()
                            else:
                                self.wait_until_to(expected_condition="element_to_be_clickable", element=first_element_focus, locator=By.XPATH)
                                self.soup_to_selenium(first_element_focus).click()
                        ActionChains(self.driver).key_down(Keys.PAGE_DOWN).perform()
                        self.wait_blocker()
                        df, grid = self.grid_dataframe(grid_number=grid_number)
                        if df.equals(last_df):
                            count +=1

            except Exception as e:
                logger().exception(f"Content doesn't found on the screen! {str(e)}")

        if len(index_number) < 1:
            logger().exception(f"Content doesn't found on the screen! {first_content}")
            self.log_error(f"Content doesn't found on the screen! {first_content}")

        if self.webapp_shadowroot():
            sel_grid  = self.soup_to_selenium(grid)
            tr = self.find_shadow_element('tbody > tr', sel_grid)
        else:
            tr = grid.select('tbody > tr')

        if hasattr(index_number, '__iter__'):
            for index in index_number:

                if len(tr) < index:
                    self.log_error(f"Couldn't check box element in line: {index+1}")

                element_td = next(iter(tr[index].find_elements(By.CSS_SELECTOR, 'td'))) if self.webapp_shadowroot() else next(iter(tr[index].select('td')))
                self.wait_blocker()
                self.performing_additional_click(element_td, tr, index, class_grid, grid_number)
        else:
            index = index_number
            element_td = next(iter(tr[index].select('td')))
            self.wait_blocker()
            self.performing_additional_click(element_td, tr, index, class_grid, grid_number)

    def performing_additional_click(self, element_bs4, tr, index, class_grid, grid_number):
        try:
            if element_bs4:
                success = False
                td = next(
                    iter(tr[index].find_elements(By.CSS_SELECTOR, 'td > div'))) if self.webapp_shadowroot() else next(
                    iter(tr[index].select('td')))

                if hasattr(td, 'style') or self.webapp_shadowroot():
                    last_box_state = td.get_attribute('style') if self.webapp_shadowroot() else td.attrs['style']
                    logger().debug(f'Before: {last_box_state}')
                    click_type = 1
                    endtime = time.time() + self.config.time_out
                    while time.time() < endtime and not success:

                        soup = self.get_current_DOM()

                        term = "wa-dialog" if self.webapp_shadowroot() else ".tmodaldialog"
                        tmodal_list = soup.select(term)
                        tmodal_layer = len(tmodal_list) if tmodal_list else 0

                        self.set_grid_focus(grid_number)
                        self.performing_click(element_bs4, class_grid, click_type)
                        self.wait_blocker()
                        time.sleep(2)

                        tmodal = self.element_exists(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR,
                                                     main_container="body", check_error=False,
                                                     position=tmodal_layer + 1)
                        if tmodal:
                            return

                        grid = self.get_grid(grid_number=grid_number)

                        if self.webapp_shadowroot():
                            sel_grid = self.soup_to_selenium(grid)
                            tr = self.find_shadow_element('tbody > tr', sel_grid)

                            if len(tr) - 1 >= index:
                                td = next(iter(tr[index].find_elements(By.CSS_SELECTOR, 'td > div')))
                            else:
                                tr = next(iter(tr))
                                td = next(iter(tr.find_elements(By.CSS_SELECTOR, 'td > div')))
                            new_box_state = td.get_attribute('style')
                        else:
                            tr = grid.select('tbody > tr')
                            td = next(iter(tr[index].select('td')))
                            new_box_state = td.attrs['style']
                        logger().debug(f'After: {new_box_state}')
                        success = last_box_state != new_box_state
                        click_type += 1
                        if click_type > 4:
                            click_type = 1
                else:
                    logger().debug(f"Couldn't check box element td: {str(td)}")
        except Exception as error:
            self.log_error(f"Couldn't check box element: {str(error)}")

    def set_grid_focus(self, grid_number=0):
        """
        [Internal]
        """
        count = 0
        df, grid = self.grid_dataframe(grid_number=grid_number)
        sel_grid  = self.soup_to_selenium(grid)
        success = lambda: 'focus' in sel_grid.get_attribute('class')
        while count < 3 and not success():
            self.wait_blocker()
            sel_grid.click()
            count += 1


    def grid_dataframe(self, grid_number=0):
        """
        [Internal]
        """
        term = self.grid_selectors["new_web_app"] if self.webapp_shadowroot() else ".tgetdados,.tgrid,.tcbrowse,.tmsselbr"

        self.wait_element(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR)

        grid = self.get_grid(grid_number=grid_number)

        if self.webapp_shadowroot():
            shadow_grid = self.soup_to_selenium(grid)
            shadow_table = next(iter(self.find_shadow_element('table', shadow_grid)),None)
            shadow_html = shadow_table.get_attribute('outerHTML')
            df = (next(iter(pd.read_html(StringIO(shadow_html)))))
        else:
            df = (next(iter(pd.read_html(StringIO(grid)))))

        converters = {c: lambda x: str(x) for c in df.columns}

        if self.webapp_shadowroot():
            df, grid = (next(iter(pd.read_html(StringIO(shadow_html), converters=converters)), None), grid)
        else:
            df, grid = (next(iter(pd.read_html(StringIO(grid), converters=converters)), None), grid)

        if not df.empty:
            df = df.fillna('Not Value')
            return (df, grid)

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

    def ScrollGrid(self, column, match_value, grid_number=1):
        """
        Scrolls Grid until a matching column is found.

        :param field: The column to be matched.
        :type field: str
        :param match_value: The value to be matched in defined column.
        :type match_value: str
        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method to scroll to a column match:
        >>> oHelper.ScrollGrid(column="Branch",match_value="D MG 01 ")
        >>> #--------------------------------------------------
        >>> # Calling the method to scroll to a column match of the second grid:
        >>> oHelper.ScrollGrid(column="Branch", match_value="D MG 01 ", grid_number=2)
        """
        grid_number -= 1
        td_element = None
        actions = ActionChains(self.driver)

        self.wait_element_timeout(term = column, scrap_type = enum.ScrapType.TEXT, timeout = self.config.time_out , optional_term = 'label')
        endtime = time.time() + self.config.time_out

        grid = self.get_grid(grid_number)
        if self.webapp_shadowroot():
            rows = self.driver.execute_script("return arguments[0].shadowRoot.querySelectorAll('tbody tr')", self.soup_to_selenium(grid))
            get_current = self.get_selected_row(rows)
            column_enumeration = self.driver.execute_script("return arguments[0].shadowRoot.querySelectorAll('thead th')", self.soup_to_selenium(grid))
            chosen_column = next(iter(list(filter(lambda x: column.lower() in x.text.lower(), column_enumeration))), None)
            column_index = chosen_column.get_attribute('id') if chosen_column else self.log_error("Couldn't find chosen column.")
            current_td = f'td[id="{column_index}"]'

            current = get_current
            td = self.driver.execute_script(f"return arguments[0].shadowRoot.querySelectorAll('{current_td}')",self.soup_to_selenium(grid))
        else:
            get_current = lambda: self.selected_row(grid_number)
            column_enumeration = list(enumerate(grid.select("thead label")))
            chosen_column = next(iter(list(filter(lambda x: column in x[1].text, column_enumeration))), None)
            column_index = chosen_column[0] if chosen_column else self.log_error("Couldn't find chosen column.")

            current = get_current()
            td = lambda: next(iter(current.select(f"td[id='{column_index}']")), None)

            frozen_table = next(iter(grid.select('table.frozen-table')),None)
            if (not self.click_grid_td(td()) and not frozen_table):
                self.log_error(" Couldn't click on column, td class or tr is not selected ")

        while( time.time() < endtime and  not td_element ):

            grid = self.get_grid(grid_number)
            if self.webapp_shadowroot():
                current = get_current
                td_list = self.driver.execute_script(f"return arguments[0].shadowRoot.querySelectorAll('{current_td}')",self.soup_to_selenium(grid))
            else:
                current = get_current()
                td_list = grid.select(f"td[id='{column_index}']")

            td_element_not_filtered = next(iter(td_list), None)
            td_list_filtered  = list(filter(lambda x: x.text.strip() == match_value and self.element_is_displayed(x) ,td_list))
            td_element = next(iter(td_list_filtered), None)

            if self.webapp_shadowroot():
                if not td_element:
                    td_element_not_filtered.click()
                    actions.key_down(Keys.PAGE_DOWN).perform()

            else:
                if not td_element and next(self.scroll_grid_check_elements_change(xpath_soup(td_element_not_filtered))):
                    actions.key_down(Keys.PAGE_DOWN).perform()
                    self.wait_element_is_not_displayed(td().parent)

        if not td_element:
            self.log_error("Scroll Grid couldn't find the element")
        else:
            td_element.click()

        if not self.webapp_shadowroot() and frozen_table:
            self.soup_to_selenium(td_element.next_sibling).click()

            self.click(self.soup_to_selenium(td_element))

    def click_grid_td(self, td_soup):
        """
         Click on a td element and checks if is selected

        :param td: The column to be matched.
        :type td: bs4 element

        >>> # Calling the method to click on td and check if is selected:
        >>> oHelper.click_grid_td(td)
        """
        success = None
        endtime = time.time() + 10

        while ( not success and time.time() < endtime ):
            try:
                td_selenium = lambda: self.soup_to_selenium(td_soup)
                tr_selenium_class = lambda: self.soup_to_selenium(td_soup.parent).get_attribute('class')
                td_is_selected = lambda: True if 'selected' in td_selenium().get_attribute('class') or 'selected' in tr_selenium_class() else False
                self.set_element_focus(td_selenium())
                td_selenium().click()
                if not td_is_selected():
                    self.wait_until_to( expected_condition = "visibility_of", element = td_selenium, timeout=True)
                    self.wait_until_to(expected_condition="element_to_be_clickable", element = td_selenium, locator = By.XPATH, timeout=True)

                    success = td_is_selected()
                else:
                    success = td_is_selected()
            except:
                pass
        return success

    def scroll_grid_check_elements_change(self, xpath):
        """
        [Internal]
        Used to check PG_DOWN correct execute.

        """
        elements_set = set()
        elements_set.add(xpath)
        yield True if xpath else False
        while(True):
            old_lenght = len(elements_set)
            elements_set.add(xpath)
            yield True if len(elements_set) > old_lenght and xpath  else False


    def selected_row(self, grid_number = 0):
        """
        [Internal]

        Returns the selected row in the grid.

        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method to return the selected row:
        >>> oHelper.selected_row(grid_number = 0)

        """
        row_selected = None
        grid = self.get_grid(grid_number)
        if grid:
            row = next(iter(grid.select('tbody tr.selected-row')), None)
            column = next(iter(grid.select('td.selected-cell')), None)
            row_selected = column.parent  if column else row

        return row_selected

    def wait_selected_row(self, grid_number = 0, column_index = 0, text = "default-text", time_out = 5):
        """
        [Internal]

        This method expects the selected line to be the line with the text value entered.

        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 0
        :type grid_number: int
        :param column_index: The column index
        :type column_index: int
        :param text: The value of column to be matched
        :type text: string

        Usage:

        >>> # Calling the method to wait the selected row:
        >>> oHelper.wait_selected_row(grid_number = 0, column_index = 0, text= "value" )
        """
        success = False
        endtime = time.time() + time_out
        while( time.time() < endtime and not success):
            current = self.selected_row(grid_number)
            td = next(iter(current.select(f"td[id='{column_index}']")), None)
            success = td.text in text

    def get_grid(self, grid_number=0, grid_element = None, grid_list=False):
        """
        [Internal]
        Gets a grid BeautifulSoup object from the screen.

        :param grid_number: The number of the grid on the screen.
        :type: int
        :param grid_element: Grid class name in HTML ex: ".tgrid".
        :type: str
        :return: Grid BeautifulSoup object
        :rtype: BeautifulSoup object
        :param grid_list: Return all grids.
        :type grid_list: bool

        Usage:

        >>> # Calling the method:
        >>> my_grid = self.get_grid()
        """

        endtime = time.time() + self.config.time_out
        grids = None
        term = self.grid_selectors["new_web_app"] if self.webapp_shadowroot() else ".tgetdados,.tgrid,.tcbrowse,.tmsselbr"
        while(time.time() < endtime and not grids):
            if not grid_element:
                grids = self.web_scrap(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR)
            else:
                grids = self.web_scrap(term= grid_element, scrap_type=enum.ScrapType.CSS_SELECTOR)

            if self.webapp_shadowroot():
                grids = self.filter_active_tabs(grids)

            if grids:
                grids = list(filter(lambda x: self.element_is_displayed(x), grids))

                if grids:
                    if grid_list:
                        return grids
                    elif len(grids) - 1 >= grid_number:
                        return grids[grid_number]

        if not grids:
            self.log_error("Couldn't find grid.")

    def check_mask(self, element):
        """
        [Internal]

        Checks whether the element has a mask or not.

        :param element: The element that must be checked.
        :type element: Selenium object

        :return: Boolean if element has a mask or not.
        :rtype: bool

        Usage:

        >>> # Calling the method:
        >>> self.check_mask(my_element)
        """
        reg = (r"^[1-9.\/-:\+]+|(@. )[1-9.\/-:\+]+")
        mask = element.get_attribute("picture")
        if mask is None:
            child = element.find_elements(By.CSS_SELECTOR, "input")
            if child:
                mask = child[0].get_attribute("picture")

        return (mask != "" and mask is not None and (re.findall(reg, mask)))

    def remove_mask(self, string, valtype=None, element=None):
        """
        [Internal]

        Removes special characters from received string.

        :param string: The string that would have its characters removed.
        :type string: str

        :return: The string with its special characters removed.
        :rtype: str

        Usage:

        >>> # Calling the method:
        >>> value_without_mask = self.remove_mask("111-111.111")
        >>> # value_without_mask == "111111111"
        """
        if type(string) is str:
            if valtype == 'N':
                if element:
                    pattern = (r'\,')
                    if re.findall(pattern, element.get_attribute('picture')):
                        string = re.sub('\.', '', string)
                return string
            else:
                caracter = (r'[.\/+-]')
                if string[0:4] != 'http':
                    match = re.findall(caracter, string)
                    if match:
                        string = re.sub(caracter, '', string)

                return string

    def SetKey(self, key, grid=False, grid_number=1, additional_key="", wait_show = "", step = 3, wait_change=False):
        """
        Press the desired key on the keyboard on the focused element.

        .. warning::
            If this methods is the first to be called, we strongly recommend using some wait methods like WaitShow().

        .. warning::
            Before using this method, set focus on any element.

        Supported keys: F1 to F12, CTRL+Key, ALT+Key, Up, Down, Left, Right, ESC, Enter and Delete ...

        :param key: Key that would be pressed
        :type key: str
        :param grid: Boolean if action must be applied on a grid. (Usually with DOWN key)
        :type grid: bool
        :param grid_number: Grid number of which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int
		:param additional_key: Key additional that would be pressed.
        :type additional_key: str
        :param wait_show: String that will hold the wait after press a key.
        :type wait_show: str
        :param step: The amount of time each step should wait. - **Default:** 3
        :type step: float
        :param wait_change: Bool when False it skips the wait for html changes.
        :type wait_change: Bool

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetKey("ENTER")
        >>> #--------------------------------------
        >>> # Calling the method on a grid:
        >>> oHelper.SetKey("DOWN", grid=True)
        >>> #--------------------------------------
        >>> # Calling the method on the second grid on the screen:
        >>> oHelper.SetKey("DOWN", grid=True, grid_number=2)
        >>> #--------------------------------------
        >>> # Call the method with WaitShow when you expect a new window or text to appear on the screen:
        >>> oHelper.SetKey( key = "F12", wait_show="Parametros", step = 3 )
        >>> #--------------------------------------
        >>> # Calling the method with special keys (using parameter additional_key):
        >>> oHelper.SetKey(key="CTRL", additional_key="A")
        """
        self.wait_blocker()
        logger().info(f"Key pressed: {key + '+' + additional_key if additional_key != '' else key }")

        #JavaScript function to return focused element if DIV/Input OR empty if other element is focused

        script = """
        var getActiveElement = () => {
	        if(document.activeElement.tagName.toLowerCase() == "input" || document.activeElement.tagName.toLowerCase() == "div"){
		        if(document.activeElement.attributes["id"]){
			        return document.activeElement.attributes["id"].value
		        }else if(document.activeElement.parentElement.attributes["id"]){
			        return document.activeElement.parentElement.attributes["id"].value
		        }
            }
	        return ""
        }

        return getActiveElement()
        """
        key = key.upper()
        endtime = time.time() + self.config.time_out
        hotkey = ["CTRL","ALT","SHIFT"]
        grid_number-=1
        tries = 0
        success = False

        try:
            if key in hotkey and not additional_key:
                self.log_error("Additional key is empty")

            if key == "DOWN" and grid:
                grid_number = 0 if grid_number is None else grid_number
                self.grid_input.append(["", "", grid_number, True])
                return

            while(time.time() < endtime and not success):
                logger().debug(f"Trying press key")
                if key not in hotkey and self.supported_keys(key):
                    if grid:
                        if key != "DOWN":
                            self.LoadGrid()
                        grids = self.get_grid(grid_list=True)
                        if grids and key == "DELETE":
                            rows = list(map(lambda x: self.driver.execute_script(
                                "return arguments[0].shadowRoot.querySelectorAll('tbody tr')",
                                self.soup_to_selenium(x)), grids))
                            rows = self.flatten_list(rows)
                            rows_before = list(map(lambda x: x.get_attribute('style'), rows))
                        success = self.send_action(action=ActionChains(self.driver).key_down(self.supported_keys(key)).perform, wait_change=wait_change)
                        if key == "DELETE" and grids and rows_before:
                            rows_after = list(map(lambda x: x.get_attribute('style'), rows))
                            if rows_after == rows_before:
                                self.send_action(
                                    action=ActionChains(self.driver).key_down(self.supported_keys(key)).perform,
                                    wait_change=False)
                    elif tries > 0:
                        ActionChains(self.driver).key_down(self.supported_keys(key)).perform()
                        tries = 0
                    else:
                        time.sleep(2)
                        Id = self.driver.execute_script(script)
                        if Id:
                            element = lambda: self.driver.find_element(By.ID, Id)
                            self.set_element_focus(element())
                            success = self.send_action(ActionChains(self.driver).move_to_element(element()).send_keys(
                                self.supported_keys(key)).perform, wait_change=wait_change)
                            tries += 1
                        else:
                            success = self.send_action(action=ActionChains(self.driver).send_keys(self.supported_keys(key)).perform, wait_change=wait_change)

                elif additional_key:
                    success = self.send_action(action=ActionChains(self.driver).key_down(self.supported_keys(key)).send_keys(additional_key.lower()).key_up(self.supported_keys(key)).perform, wait_change=wait_change)

                if wait_show:
                    success = self.WaitShow(wait_show, timeout=step, throw_error = False)


        except WebDriverException as e:
            self.log_error(f"SetKey - Screen is not load: {e}")
        except Exception as error:
            logger().exception(str(error))

    def flatten_list(self, matrix):
        flattened_list = []
        for element in matrix:
            if isinstance(element, list):
                flattened_list.extend(self.flatten_list(element))
            else:
                flattened_list.append(element)
        return flattened_list

    def supported_keys(self, key = ""):
        """
        [Internal]
        """
        try:
            supported_keys = {
                "F1" : Keys.F1,
                "F2" : Keys.F2,
                "F3" : Keys.F3,
                "F4" : Keys.F4,
                "F5" : Keys.F5,
                "F6" : Keys.F6,
                "F7" : Keys.F7,
                "F8" : Keys.F8,
                "F9" : Keys.F9,
                "F10" : Keys.F10,
                "F11" : Keys.F11,
                "F12" : Keys.F12,
                "UP" : Keys.UP,
                "DOWN" : Keys.DOWN,
                "LEFT" : Keys.LEFT,
                "RIGHT" : Keys.RIGHT,
                "DELETE" : Keys.DELETE,
                "ENTER" : Keys.ENTER,
                "ESC" : Keys.ESCAPE,
                "CTRL" : Keys.CONTROL,
                "ALT" : Keys.ALT,
                "NUMPAD0" : Keys.NUMPAD0,
                "NUMPAD1" : Keys.NUMPAD1,
                "NUMPAD2" : Keys.NUMPAD2,
                "NUMPAD3" : Keys.NUMPAD3,
                "NUMPAD4" : Keys.NUMPAD4,
                "NUMPAD5" : Keys.NUMPAD5,
                "NUMPAD6" : Keys.NUMPAD6,
                "NUMPAD7" : Keys.NUMPAD7,
                "NUMPAD8" : Keys.NUMPAD8,
                "NUMPAD9" : Keys.NUMPAD9,
                "MULTIPLY" : Keys.MULTIPLY,
                "ADD" : Keys.ADD,
                "SEPARATOR" : Keys.SEPARATOR,
                "SUBTRACT" : Keys.SUBTRACT,
                "DECIMAL" : Keys.DECIMAL,
                "DIVIDE" : Keys.DIVIDE,
                "META" : Keys.META,
                "COMMAND" : Keys.COMMAND,
                "NULL" : Keys.NULL,
                "CANCEL" : Keys.CANCEL,
                "HELP" : Keys.HELP,
                "BACKSPACE" : Keys.BACKSPACE,
                "TAB" : Keys.TAB,
                "CLEAR" : Keys.CLEAR,
                "RETURN" : Keys.RETURN,
                "SHIFT" : Keys.SHIFT,
                "PAUSE" : Keys.PAUSE,
                "ESCAPE" : Keys.ESCAPE,
                "SPACE" : Keys.SPACE,
                "END" : Keys.END,
                "HOME" : Keys.HOME,
                "INSERT" : Keys.INSERT,
                "SEMICOLON" : Keys.SEMICOLON,
                "EQUALS" : Keys.EQUALS,
                "ARROW_LEFT" : Keys.ARROW_LEFT,
                "ARROW_UP" : Keys.ARROW_UP,
                "ARROW_RIGHT" : Keys.ARROW_RIGHT,
                "ARROW_DOWN" : Keys.ARROW_DOWN,
                "BACK_SPACE" : Keys.BACK_SPACE,
                "LEFT_SHIFT" : Keys.LEFT_SHIFT,
                "LEFT_CONTROL" : Keys.LEFT_CONTROL,
                "LEFT_ALT" : Keys.LEFT_ALT,
                "PAGE_UP" : Keys.PAGE_UP ,
                "PAGE_DOWN" : Keys.PAGE_DOWN

            }

            return supported_keys[key.upper()]

        except KeyError:
            self.log_error("Key is not supported")

    def SetFocus(self, field, grid_cell, row_number, position):
        """
        Sets the current focus on the desired field.

        :param field: The field that must receive the focus.
        :type field: str
        :param grid_cell: Indicates if the element that deserve focus is on a grid.
        :type grid_cell: bool
        :param row_number: Number of row in case of multiples rows.
        :type row_number: int
        :param position: Position which element is located. - **Default:** 1
        :type position: int

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetFocus("A1_COD")
        >>> oHelper.SetFocus("A1_COD", grid_cell = True)
        """

        logger().debug(f"Setting focus on element {field}.")

        if grid_cell:
            if self.webapp_shadowroot():
                self.wait_element(term=field, scrap_type=enum.ScrapType.MIXED,
                                  optional_term='.dict-tgetdados, .dict-tcbrowse, .dict-msbrgetdbase,.dict-tgrid,.dict-brgetddb',
                                  main_container="body")
            else:
                self.wait_element(field)

            self.ClickGridCell(field, row_number)
            time.sleep(1)
            ActionChains(self.driver).key_down(Keys.ENTER).perform()
            time.sleep(1)
        else:

            label = False if re.match(r"\w+(_)", field) else True

            if label:
                container = self.get_current_container()
                labels = container.select('label')

                label_text_filtered = re.sub(r"[:;*?]", "", field)
                label_filtered = next(iter(list(filter(
                    lambda x: re.sub(r"[:;*?]", "", x.text) == label_text_filtered, labels))), None)

                if label_filtered and not self.element_is_displayed(label_filtered):
                    self.scroll_to_element(self.soup_to_selenium(label_filtered))

            element = ''
            endtime = time.time() + self.config.time_out
            while time.time() < endtime and not element:
                element = self.web_scrap(field, scrap_type=enum.ScrapType.TEXT, optional_term="label",
                                         main_container=self.containers_selectors["Containers"], label=label,
                                         position=position)
                if isinstance(element, list):
                    element = next(iter(element), None)

                if not element:
                    element = next(iter(self.web_scrap(f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR,
                                                       main_container=self.containers_selectors["Containers"],
                                                       label=label, position=position)), None)
            if element:
                if self.webapp_shadowroot():
                    element = self.soup_to_selenium(element)
                    input_element = next(iter(self.find_shadow_element('input', element)), None)
                    if input_element:
                        element = input_element

                element = element if self.webapp_shadowroot() else self.soup_to_selenium(element)

                if element and not self.element_is_displayed(element):
                    self.scroll_to_element(element)
            try:
                self.set_element_focus(element)
                if self.switch_to_active_element() != element:
                    self.click(element, click_type=enum.ClickType.SELENIUM)
            except Exception as e:
                logger().exception(f"Warning: SetFocus: '{field}' - Exception {str(e)}")

    def click_check_radio_button(self, field, value, name_attr = False, position = 1, direction=None):
        """
        [Internal]
        Identify and click on check or radio button.

        :param field: The field that would receive the input.
        :type field: str
        :param value: The value that must be on the checkbox or grid.
        :type value: bool

        :return: The element that changed value.
        :rtype: Selenium object

        Usage:

        >>> # Calling the method:
        >>> element = self.check_checkbox("CheckBox1", True)
        """
        logger().info(f'Clicking in "{self.returns_printable_string(field)}"')

        position -= 1
        field = field.strip()
        element_list = []

        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not element_list):
            if re.match(r"\w+(_)", field):
                self.wait_element(term=f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR)
                element_list = self.web_scrap(term=f"[name$='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR, position=position)
            else:
                if self.webapp_shadowroot():
                    self.wait_element(field, scrap_type=enum.ScrapType.MIXED, second_term='label', optional_term="wa-radio, wa-checkbox")
                    element_list = self.web_scrap(term=field, scrap_type=enum.ScrapType.MIXED, second_term='label', optional_term="wa-radio, wa-checkbox", position=position)
                else:
                    self.wait_element(field, scrap_type=enum.ScrapType.MIXED, optional_term="label")
                    element_list = self.web_scrap(term=field, scrap_type=enum.ScrapType.MIXED, optional_term=".tradiobutton .tradiobuttonitem label, .tcheckbox input", position=position)


        if not element_list:
            self.log_error(f"Couldn't find {field} radio element")

        if element_list and len(element_list) -1 >= position:
            element = element_list[position]

        if self.webapp_shadowroot():
            if isinstance(element, list):
                element = next(iter(element), None)

            if re.match(r"\w+(_)", field) and element.name == 'wa-text-input':
                container = self.get_current_container()
                active_tab = self.filter_active_tabs(container)

                box_elements = self.web_scrap(term="wa-radio, wa-checkbox", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
                box_elements = list(filter(lambda x: self.element_is_displayed(x), box_elements))

                container_size = self.get_element_size(container['id'])

                # The safe values add to postion of element
                width_safe, height_safe = self.width_height(container_size)
                label_s = lambda: self.soup_to_selenium(element)
                if self.webapp_shadowroot():
                    xy_label = label_s().location
                else:
                    xy_label = self.driver.execute_script('return arguments[0].getPosition()', label_s())

                position_list = list(map(lambda x:(x[0], self.get_position_from_bs_element(x[1])), enumerate(box_elements)))
                position_list = self.filter_by_direction(xy_label, width_safe, height_safe, position_list, direction)
                distance      = self.get_distance_by_direction(xy_label, position_list, direction)
                if distance:
                    elem = min(distance, key = lambda x: abs(x[1]))
                    element = box_elements[elem[0]]

                    element = self.soup_to_selenium(element)
                    elem_value = lambda: element.get_attribute('checked')
                    chck = lambda: False if not elem_value() else True
                    while time.time() < endtime and chck() != value:
                        self.send_action(action=self.click, element=lambda: element)
            elif element:
                self.scroll_to_element(element)

                self.double_click(element)
        else:
            if 'input' not in element and element:
                input_element = next(iter(element.find_parent().select("input")), None)

            if not input_element:
                self.log_error(f"Couldn't find {field} input element")

            xpath_input = lambda: self.driver.find_element(By.XPATH, xpath_soup(input_element))

            self.scroll_to_element(xpath_input())

            self.click(xpath_input())

    def result_checkbox(self, field, value):
        """
        [Internal]

        Checks expected value of a Checkbox element.

        :param field: The field whose value would be checked.
        :type field: str
        :param value: The expected value of the radio button.
        :type value: bool

        :return: Boolean if expected value was found on the element or not.
        :rtype: bool

        Usage:

        >>> # Calling the method:
        >>> assertion_value = self.result_checkbox("CheckBox1", True)
        """
        result = False
        time.sleep(1)
        lista = self.driver.find_elements(By.CSS_SELECTOR, ".tcheckbox.twidget")
        for line in lista:
            if line.is_displayed() and line.get_attribute('name').split('->')[1] == field:
                if "CHECKED" in line.get_attribute('class').upper():
                    result = True
        return result

    def clear_grid(self):
        """
        [Internal]

        Empties the global grid list variables.

        Usage:

        >>> # Calling the method:
        >>> self.clear_grid()
        """
        self.grid_input = []
        self.grid_check = []

    def input_grid_appender(self, column, value, grid_number=0, new=False, row=None, check_value = True, duplicate_fields=[], position=0, ignore_case=True):
        """
        [Internal]

        Adds a value to the input queue of a grid.

        :param column: The column of the grid that would receive the input.
        :type column: str
        :param value: The value that would be inputted.
        :type value: str
        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 0
        :type grid_number: int
        :param new: Boolean value if this is a new line that should be added. - **Default:** 1
        :type new: bool
        :param row: Row number that will be filled
        :type row: int

        Usage:

        >>> # Calling the method:
        >>> self.input_grid_appender("A1_COD", "000001", 0)
        >>> # ---------------------------------------------
        >>> # Calling the method for a new line:
        >>> self.input_grid_appender("", "", 0, True)
        """
        if row is not None:
            row -= 1

        self.grid_input.append([column, value, grid_number, new, row, check_value, duplicate_fields, position, ignore_case])

    def check_grid_appender(self, line, column, value=None, grid_number=0, position=1, ignore_case=True):
        """
        [Internal]

        Adds a value to the check queue of a grid.

        :param line: The line of the grid that would be checked.
        :type line: int
        :param column: The column of the grid that would be checked.
        :type column: str
        :param value: The value that is expected.
        :type value: str
        :param grid_number: Which grid should be used when there are multiple grids on the same screen. - **Default:** 0
        :type grid_number: int

        Usage:

        >>> # Calling the method:
        >>> self.check_grid_appender(0,"A1_COD", "000001", 0)
        """
        self.grid_check.append([line, column, value, grid_number, position, ignore_case])

    def LoadGrid(self):
        """
        This method is responsible for running all actions of the input and check queues
        of a grid. After running, the queues would be empty.

        Must be called after SetValue and CheckResult calls that has the grid parameter set to True.

        Usage:

        >>> # After SetValue:
        >>> oHelper.SetValue("A1_COD", "000001", grid=True)
        >>> oHelper.LoadGrid()
        >>> #--------------------------------------
        >>> # After CheckResult:
        >>> oHelper.CheckResult("A1_COD", "000001", grid=True, line=1)
        >>> oHelper.LoadGrid()
        """

        x3_dictionaries = self.create_x3_tuple()

        duplicate_fields=[]

        initial_layer = 0
        if self.grid_input:
            selector = ".dict-tgetdados, .dict-tgrid, .dict-tcbrowse, .dict-msbrgetdbase,.dict-brgetddb, .dict-twbrowse"
            self.wait_element(term=selector, scrap_type=enum.ScrapType.CSS_SELECTOR)

            soup = self.get_current_DOM()
            container_soup = next(iter(soup.select('body')))
            container_element = self.driver.find_element(By.XPATH, xpath_soup(container_soup))
            dialog_selector = 'wa-dialog'
            find_element_method = By.CSS_SELECTOR
            initial_layer = len(container_element.find_elements(find_element_method, dialog_selector))

        for field in self.grid_input:
            if field[3] and field[0] == "":
                self.new_grid_line(field)
            else:
                self.wait_blocker()
                logger().info(f"Filling grid field: {field[0]}")
                if len(field[6]) > 0:
                    duplicate_fields=field[6]
                self.fill_grid(field, x3_dictionaries, initial_layer, duplicate_fields)

        for field in self.grid_check:
            logger().info(f"Checking grid field value: {field[1]}")
            self.check_grid(field, x3_dictionaries, position=field[4])

        self.clear_grid()

    def create_x3_tuple(self):
        """
        [Internal]

        Returns a tuple of dictionaries of field information based on all fields in the grid queues.

        :return: A tuple containing the needed x3 information.
        :rtype: Tuple of Dictionaries

        Usage:

        >>> # Calling the method:
        >>> x3_dictionaries = self.create_x3_tuple()
        """
        x3_dictionaries = ()
        inputs = list(map(lambda x: x[0], self.grid_input))
        checks = list(map(lambda x: x[1], self.grid_check))
        fields = list(filter(lambda x: "_" in x, inputs + checks))
        if fields:
            x3_dictionaries = self.get_x3_dictionaries(fields)
        return x3_dictionaries


    def fill_grid(self, field, x3_dictionaries, initial_layer, duplicate_fields=[]):
        """
        [Internal]

        Fills the grid cell with the passed parameters.

        :param field: An item from the grid's input queue
        :type field: List of values
        :param x3_dictionaries: Tuple of dictionaries containing information extracted from x3.
        :type x3_dictionaries: Tuple of dictionaries
        :param initial_layer: The initial layer of elements of Protheus Webapp
        :type initial_layer: int

        Usage:

        >>> # Calling the method:
        >>> self.fill_grid(["A1_COD", "000001", 0, False], x3_dictionaries, 0)
        """

        field_to_label = {}
        field_to_valtype = {}
        field_to_len = {}

        current_value = ""
        column_name = ""
        rows = ""
        headers = ""
        columns = ""

        grids = None
        try_counter = 1
        grid_reload = True
        check_value = field[5]
        grid_class=[]

        if (field[1] == True):
            field_one = 'is a boolean value'
        elif (field[1] == False):
            field_one = ''
        elif (isinstance(field[1], str)):
            field_one = self.remove_mask(field[1]).strip()

        if x3_dictionaries:
            field_to_label = x3_dictionaries[2]
            field_to_valtype = x3_dictionaries[0]
            field_to_len = x3_dictionaries[1]

        if "_" in field[0]:
            try:
                column_name = field_to_label[field[0]].lower().strip()
            except:
                self.log_error("Couldn't find column '" + field[0] + "' in sx3 file. Try with the field label.")
        else:
            column_name = field[0].lower().strip()

        try:
            endtime = time.time() + self.config.time_out + 300
            while (current_value != field_one and time.time() < endtime):
                current_value = re.sub('[\,\.]', '', self.remove_mask(current_value).strip())
                field_one = re.sub('[\,\.]', '', self.remove_mask(field_one).strip())
                if current_value.isnumeric() and field_one.isnumeric():
                   if float(current_value) == float(field_one):
                        break
                if field[8] and current_value.lower() == field_one.lower():
                    break
                endtime_row = time.time() + self.config.time_out
                while (time.time() < endtime_row and grid_reload):
                    logger().debug('Grid loading...')
                    if not field[4]:
                        grid_reload = False

                    container = self.get_current_shadow_root_container()
                    if container:
                        try:
                            container_id = self.soup_to_selenium(container).get_attribute("id") if self.soup_to_selenium(
                                container) else None
                        except Exception as err:
                            container_id = None
                            logger().exception(str(err))
                            pass
    
                        grids = container.select(".dict-tgetdados, .dict-tgrid, .dict-tcbrowse, .dict-msbrgetdbase, .dict-brgetddb, .dict-twbrowse")
                        grids = self.filter_active_tabs(grids)
                        grids = self.filter_displayed_elements(grids)

                    if grids:
                        headers = self.get_headers_from_grids(grids, column_name=column_name, position=field[7], duplicate_fields=duplicate_fields)

                        if not column_name in headers[field[2]]:
                            field[2] = self.return_header_index(column_name, headers)
                            column_name = next(iter(filter(lambda x: re.sub(' ', '', column_name) in re.sub(' ', '', x), headers[field[2]].keys())),'')

                        if field[2] is not None and field[2] + 1 > len(grids):
                            grid_reload = True
                        else:
                            grid_id = grids[field[2]].attrs["id"]
                            if grid_id not in self.grid_counters:
                                self.grid_counters[grid_id] = 0

                            down_loop = 0
                            rows = self.driver.execute_script(
                                "return arguments[0].shadowRoot.querySelectorAll('tbody tr')",
                                self.soup_to_selenium(grids[field[2]]))
    
                    else:
                        grid_reload = True

                    if (field[4] is not None) and not (field[4] > len(rows) - 1 or field[4] < 0):
                        grid_reload = False

                if (field[4] is not None) and (field[4] > len(rows) - 1 or field[4] < 0):
                    self.log_error(f"Couldn't select the specified row: {field[4] + 1}")

                if grids:
                    if field[2] + 1 > len(grids):
                        self.log_error(
                            f'{self.language.messages.grid_number_error} Grid number: {field[2] + 1} Grids in the screen: {len(grids)}')
                else:
                    self.log_error("Grid element doesn't appear in DOM")

                row = rows[field[4]] if field[4] is not None else self.get_selected_row(rows) if self.get_selected_row(rows) else (
                    next(iter(rows), None))

                if row:
                    row_id = row.get_attribute("id")
                    while (int(row_id) < self.grid_counters[grid_id]) and (down_loop < 2) and self.down_loop_grid and field[
                        4] is None and time.time() < endtime:
                        self.new_grid_line(field, False)
                        row = self.get_selected_row(self.get_current_DOM().select(f"#{grid_id} tbody tr"))
                        down_loop += 1
                    self.down_loop_grid = False
                    columns = self.driver.execute_script("return arguments[0].querySelectorAll('td')", row)
                    if columns:
                        if column_name in headers[field[2]]:
                            logger().debug('Column found!')
                            column_number = headers[field[2]][column_name]

                            current_value = columns[column_number].text.strip()
                            current_value = self.remove_mask(current_value).strip()
    
                            selenium_column = lambda: columns[column_number]

                            term = "wa-multi-get" if self.grid_memo_field else "wa-dialog"

                            soup = self.get_current_DOM()
                            tmodal_list = soup.select(term)
                            tmodal_layer = len(tmodal_list) if tmodal_list else 0

                            self.scroll_to_element(selenium_column())
                            self.click(selenium_column(), click_type=enum.ClickType.ACTIONCHAINS)
                            self.set_element_focus(selenium_column())

                            endtime_selected_cell = time.time() + self.config.time_out / 3
                            while time.time() < endtime_selected_cell and not self.selected_cell(selenium_column()):
                                logger().debug('Trying to select cell in grid!')
                                self.scroll_to_element(selenium_column())
                                self.click(selenium_column(), click_type=enum.ClickType.ACTIONCHAINS)
                                self.set_element_focus(selenium_column())

                            endtime_open_cell = time.time() + self.config.time_out / 3
                            while (time.time() < endtime_open_cell and not self.wait_element_timeout(term='wa-dialog',
                                                                                                     scrap_type=enum.ScrapType.CSS_SELECTOR,
                                                                                                     position=tmodal_layer + 1,
                                                                                                     timeout=5,
                                                                                                     main_container='body')):
                                grid_class = grids[field[2]].attrs['class']
                                logger().debug('Trying open cell in grid!')
                                if not 'dict-msbrgetdbase' in grid_class:
                                    self.scroll_to_element(selenium_column())
                                    self.set_element_focus(selenium_column())
                                try:
                                    ActionChains(self.driver).move_to_element(selenium_column()).send_keys(Keys.ENTER).perform()
                                except WebDriverException:
                                    try:
                                        self.send_keys(selenium_column(), Keys.ENTER)
                                    except WebDriverException:
                                        pass
                                except:
                                    pass
                                self.wait_blocker()

                                if (field[1] == True):
                                    field_one = ''
                                    break

                            if (field[1] == True): break  # if boolean field finish here.

                            new_container_selector = ".dict-tget.focus, .dict-msbrgetdbase.focus, wa-dialog, .dict-tgrid, .dict-brgetddb, .dict-tget, .dict-tmultiget, .dict-tcombobox"

                            soup = self.get_current_DOM()
                            new_container = self.zindex_sort(soup.select(new_container_selector), True)[0]

                            endtime_child = time.time() + self.config.time_out
                            child = None
                            while time.time() < endtime_child and not child:
                                try:
                                    child = self.driver.execute_script(
                                        "return arguments[0].shadowRoot.querySelector('input, textarea')",
                                        self.soup_to_selenium(new_container))
                                except Exception as err:
                                    logger().info(f'fillgrid child error: {str(err)}')
                                    pass

                            child_type = "input"
                            option_text = ""
                            if not child or 'dict-tcombobox' in new_container['class']:
                                child = self.driver.execute_script(
                                    "return arguments[0].shadowRoot.querySelector('select')",
                                    self.soup_to_selenium(new_container))
                                child_type = "select"

                            if isinstance(child, list):
                                child = next(iter(child), None)

                            if child_type == "input":

                                selenium_input = lambda: child
                                EC.visibility_of(child)

                                valtype = self.value_type(new_container.get("type"))

                                lenfield = len(self.get_element_value(selenium_input()))
                                user_value = field[1]
                                check_mask = self.check_mask(selenium_input())

                                if check_mask or valtype == 'N':
                                    if (check_mask and check_mask[0].startswith('@D') and user_value == ''):
                                        user_value = '00000000'
                                    user_value = self.remove_mask(user_value)

                                    self.wait_until_to(expected_condition="visibility_of", element=selenium_input,
                                                    timeout=True)
                                    self.set_element_focus(selenium_input())
                                    self.click(selenium_input())

                                endtime_container = time.time() + self.config.time_out
                                while time.time() < endtime_container and 'class' not in self.get_current_container().next.attrs:
                                    logger().info('Waiting container attributes')

                                if 'tget' in self.get_current_container().next.attrs['class'] or 'tmultiget' in \
                                        self.get_current_container().next.attrs['class'] \
                                        or 'dict-tget' in self.get_current_container().next.attrs['class']:
                                    bsoup_element = self.get_current_container().next
                                    self.wait_until_to(expected_condition="element_to_be_clickable", element=bsoup_element,
                                                    locator=By.XPATH, timeout=True)
                                    logger().debug(f"Sending keys: {user_value}")

                                    selenium_input().send_keys(Keys.HOME)
                                    ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
                                    ActionChains(self.driver).move_to_element(selenium_input()).send_keys(user_value).perform()

                                    self.wait_blocker()
                                    if self.grid_memo_field:
                                        self.SetButton('Ok')
                                        check_value = False
                                        self.grid_memo_field = False

                                    modal_open = self.wait_element_timeout(term='wa-dialog', scrap_type=enum.ScrapType.CSS_SELECTOR, position= tmodal_layer + 1, timeout=5, presence=True, main_container='body', check_error=False)

                                    endtime_container = time.time() + self.config.time_out
                                    while time.time() < endtime_container and 'id' not in self.get_current_container().attrs:
                                        logger().info('Waiting container attributes')

                                    if (("_" in field[0] and field_to_len != {} and int(field_to_len[field[0]]) > len(
                                            field[1])) or lenfield > len(field[1])) and modal_open:
                                        if (("_" in field[0] and field_to_valtype != {} and field_to_valtype[
                                            field[0]] != "N") or valtype != "N"):
                                            self.send_keys(selenium_input(), Keys.ENTER)
                                        else:
                                            if not (re.match(r"[0-9]+,[0-9]+", user_value)):
                                                self.send_keys(selenium_input(), Keys.ENTER)
                                            else:
                                                self.wait_element_timeout(term=".tmodaldialog.twidget, wa-dialog",
                                                                        scrap_type=enum.ScrapType.CSS_SELECTOR,
                                                                        position=initial_layer + 1, presence=False,
                                                                        main_container="body")
                                                if self.element_exists(term=".tmodaldialog.twidget, wa-dialog",
                                                                    scrap_type=enum.ScrapType.CSS_SELECTOR,
                                                                    position=initial_layer + 1, main_container="body"):
                                                    self.wait_until_to(expected_condition="element_to_be_clickable",
                                                                    element=bsoup_element, locator=By.XPATH,
                                                                    timeout=True)
                                                    self.send_keys(selenium_input(), Keys.ENTER)

                                    elif lenfield == len(field[1]) and self.get_current_container().attrs[
                                        'id'] != container_id:
                                        try:
                                            self.send_keys(selenium_input(), Keys.ENTER)
                                        except:
                                            pass

                                    element_exist = self.wait_element_timeout(term='wa-dialog', scrap_type=enum.ScrapType.CSS_SELECTOR, position= tmodal_layer + 1, timeout=10, presence=False, main_container='body', check_error=False)
                                    if element_exist:
                                        current_value = self.get_element_text(selenium_column())
                                        if current_value == None:
                                            current_value = ''
                                    else:
                                        containers = self.get_current_DOM().select(self.containers_selectors["GetCurrentContainer"])
                                        if isinstance(child, list) and child.parent.parent in containers:
                                            containers.remove(child.parent.parent)
                                        container_current = next(iter(self.zindex_sort(containers, True)))
                                        if container_current.attrs['id'] != container_id:
                                            logger().debug(
                                                "Consider using the waithide and setkey('ESC') method because the input can remain selected.")
                                            return
                            else:
                                if child:
                                    if self.webapp_shadowroot():
                                        option_list = child.find_elements(By.TAG_NAME, 'option')
                                        option_text_list = list(filter(lambda x: field[1] == x[0:len(field[1])], map(lambda x: x.text, option_list)))
                                        option_value_dict = dict(map(lambda x: (x.get_attribute('value'), x.text), option_list))
                                        option_value = self.get_element_value(child)
                                    else:
                                        option_text_list = list(filter(lambda x: field[1] == x[0:len(field[1])], map(lambda x: x.text, child.select('option'))))
                                        option_value_dict = dict(map(lambda x: (x.attrs["value"], x.text), child.select('option')))
                                        option_value = self.get_element_value(self.driver.find_element(By.XPATH, xpath_soup(child)))
                                    option_text = next(iter(option_text_list), None)
                                    if not option_text:
                                        self.log_error("Couldn't find option")
                                    if (option_text != option_value_dict[option_value]):
                                        self.select_combo(new_container, field[1])

                                        if self.config.browser.lower() == 'chrome':
                                            self.set_element_focus(self.soup_to_selenium(new_container))
                                            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                                        if field[1] in option_text[0:len(field[1])]:
                                            current_value = field[1]
                                    else:
                                        if self.webapp_shadowroot():
                                            self.send_keys(child, Keys.TAB)
                                        else:
                                            self.send_keys(self.driver.find_element(By.XPATH, xpath_soup(child)), Keys.ENTER)
                                        current_value = field[1]

                if not check_value:
                    break
            if (check_value and self.remove_mask(current_value).strip().replace(',', '') != field_one.replace(',', '') and (self.remove_mask(current_value).strip().replace(',', '').isnumeric() and field_one.replace(',', '').isnumeric() and float(current_value) != float(field_one))):
                self.search_for_errors()
                self.check_grid_error(grids, headers, column_name, rows, columns, field)
                self.log_error(
                    f"Current value: {current_value} | Couldn't fill input: {field_one} value in Column: '{column_name}' of Grid: '{headers[field[2]].keys()}'.")

        except Exception as e:
            logger().exception(f"fill grid error: {str(e)}")
            self.log_error(f'fill grid error: {str(e)}')


    def selected_cell(self, element):
        """
        [Internal]
        """
        return element.get_attribute('class') == 'selected-cell'

    def get_selenium_column_element(self, xpath):
        """
        [Internal]

        Tries to get the selenium element out of a grid column.
        Workaround method to be used instead of a lambda function on fill_grid method.

        :param xpath: The xpath to the column.
        :type xpath: str

        Usage:

        >>> #  Calling the method:
        >>> self.get_selenium_column_element(xpath)
        """
        try:
            return self.driver.find_element(By.XPATH, xpath)
        except:
            return False

    def try_recover_lost_line(self, field, grid_id, row, headers, field_to_label):
        """
        [Internal]

        Tries to recover the position if a new line is lost.

        Workaround method to keep trying to get the right row fill_grid method.

        :param field: An item from the grid's input queue
        :type field: List of values
        :param grid_id: The grid's ID
        :type grid_id: str
        :param row: The current row
        :type row: Beautiful Soup object
        :param headers: List of dictionaries with each grid's headers
        :type headers: List of Dictionaries
        :param field_to_label: Dictionary from the x3 containing the field to label relationship.
        :type field_to_label: Dict

        Usage:

        >>> # Calling the method:
        >>> self.try_recover_lost_line(field, grid_id, row, headers, field_to_label)
        """
        ret = None
        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not ret):
            if self.config.debug_log:
                logger().debug("Recovering lost line")
            while ( time.time() < endtime and int(row.attrs["id"]) < self.grid_counters[grid_id]):
                self.new_grid_line(field, False)
                row = self.get_selected_row(self.get_current_DOM().select(f"#{grid_id} tbody tr"))

            columns = row.select("td")
            if columns:
                if "_" in field[0]:
                    column_name = field_to_label[field[0]]
                else:
                    column_name = field[0]

                column_name = column_name.lower()

                if column_name not in headers[field[2]]:
                    self.log_error(f"{self.language.messages.grid_column_error} Coluna: '{column_name}' Grid: '{headers[field[2]].keys()}'")

                column_number = headers[field[2]][column_name]
                xpath = xpath_soup(columns[column_number])
                ret = self.get_selenium_column_element(xpath)

        return ret

    def check_grid(self, field, x3_dictionaries, get_value=False, position=0):
        """
        [Internal]

        Checks the grid cell with the passed parameters.

        :param field: An item from the grid's check queue
        :type field: List of values
        :param x3_dictionaries: Tuple of dictionaries containing information extracted from x3.
        :type x3_dictionaries: Tuple of dictionaries
        :param get_value: Boolean value if check_grid should return its value.
        :type get_value: bool

        :return: If get_value flag is True, it will return the captured value.
        :return type: str

        Usage:

        >>> # Calling the method:
        >>> self.check_grid([0, "A1_COD", "000001", 0], x3_dictionaries, False)
        """
        text = ""
        column_name = ""

        field_to_label = {}

        grids = None
        columns = None
        headers = None
        rows = None
        obscured_row = None
        down_count = 0
        success = False
        text = ''
        tries = 0

        endtime = time.time() + self.config.time_out
        if x3_dictionaries:
            field_to_label = x3_dictionaries[2]

        while(self.element_exists(term=".tmodaldialog .ui-dialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=3, main_container="body") and time.time() < endtime):
            if self.config.debug_log:
                logger().debug("Waiting for container to be active")
            time.sleep(1)

        while(time.time() < endtime and not success):

            containers = self.web_scrap(term=".tmodaldialog, wa-dialog", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
            container = next(iter(self.zindex_sort(containers, True)), None)

            if container:
                grid_term = self.grid_selectors['new_web_app'] if self.webapp_shadowroot() else ".tgetdados, .tgrid, .tcbrowse"

                grids = container.select(grid_term)

                if grids:
                    if self.webapp_shadowroot():
                        grids = self.filter_active_tabs(grids)

                    grids = self.filter_displayed_elements(grids)

            if grids:

                headers = self.get_headers_from_grids(grids, column_name=field[1], position=position)
                column_name = ""

                if field[3] > len(grids):
                    self.log_error(self.language.messages.grid_number_error)

                if self.webapp_shadowroot():
                    grid = self.soup_to_selenium(grids[field[3]])
                    rows = self.find_shadow_element('tbody tr', grid)
                else:
                    rows = grids[field[3]].select("tbody tr")

                if rows:
                    if field[0] > len(rows) - 1:
                        grid_lenght = self.lenght_grid_lines(grids[field[3]])
                        if get_value:
                            return ''
                        elif grid_lenght > field[0]:
                            obscured_row, down_count = self.get_obscure_gridline(grids[field[3]], field[0])
                        else:
                            self.log_error(self.language.messages.grid_line_error)

                    field_element = next(iter(field), None)

                    if field_element != None and len(rows) - 1 >= field_element or obscured_row:
                        if self.webapp_shadowroot():
                            if obscured_row:
                                columns = obscured_row.find_elements(By.CSS_SELECTOR, 'td')
                            else:
                                columns = rows[field_element].find_elements(By.CSS_SELECTOR, 'td')
                        else:
                            columns = rows[field_element].select("td")

                if columns and rows:

                    if "_" in field[1]:
                        column_name = field_to_label[field[1]].lower()
                    else:
                        column_name = field[1].lower()

                    if column_name in headers[field[3]]:
                        column_number = headers[field[3]][column_name]
                        if self.grid_memo_field:
                            text = self.check_grid_memo(columns[column_number])
                            self.grid_memo_field = False
                        else:
                            text = columns[column_number].text.strip()
                        if column_name == '' and text == '':
                            icon = next(iter(columns[column_number].find_elements(By.TAG_NAME, 'div')),None)
                            if icon:
                                text = self.get_status_color(icon)
                        success = True

                    if success and get_value:
                        if text:
                            return text
                        if tries <= 2: # if not found any text using GetValue try twice more
                            success = False
                            tries += 1

        for i in range(down_count):
            ActionChains(self.driver).key_down(Keys.PAGE_UP).perform()

        field_name = f"({field[0]}, {column_name})"
        logger().info(f"Collected value: {text}")

        if field[5]:
            self.log_result(field_name, field[2].lower(), text.lower())
        else:
            self.log_result(field_name, field[2], text)
        if not success:
            self.check_grid_error(grids, headers, column_name, rows, columns, field)


    def get_status_color(self, sl_object):
        colors = {
            "branco":   "White",
            "verde":    "Green",
            "amarelo":  "Yellow",
            "vermelho": "Red",
            "azul":     "Blue"
        }
        style = sl_object.get_attribute('style')
        status = next(iter(list(filter(lambda x: x in style, colors))), None)
        if status:
            return colors[status]


    def get_obscure_gridline(self, grid, row_num=0):
        """
        [Internal]
        :param grid:
        :param row_num:
        :return obscured row based in row number:
        """
        grid_lines = None
        row_list = []

        if self.webapp_shadowroot():
            grid_lines = lambda: self.find_shadow_element('tbody tr', self.soup_to_selenium(grid))
            before_texts = list(filter(lambda x: hasattr(x, 'text'), grid_lines()))
            before_texts = list(map(lambda x: x.text, before_texts))
            after_texts = []
            down_count = 0
            if grid_lines():
                self.send_action(action=self.click, element=lambda: next(iter(grid_lines())), click_type=3)
                endtime = time.time() + self.config.time_out
                while endtime > time.time() and next(reversed(after_texts), None) != next(reversed(before_texts), None):

                    after_texts = list(map(lambda x: x.text, grid_lines()))

                    for i in after_texts:
                        if i not in before_texts:
                            before_texts.append(i)

                    if len(before_texts) > row_num:
                        row_list = list(filter(lambda x: x.text == before_texts[row_num], grid_lines()))
                        break

                    ActionChains(self.driver).key_down(Keys.PAGE_DOWN).perform()
                    down_count += 1
                    self.wait_blocker()

                    after_texts = list(map(lambda x: x.text, grid_lines()))

            return next(iter(row_list), None), down_count


    def check_grid_memo(self, element):
        """
        [Internal]
        :param element:
        :return:
        """
        term = ".dict-tmultiget" if self.webapp_shadowroot() else "textarea"
        self.soup_to_selenium(element).click() if type(element) == Tag else element.click()

        ActionChains(self.driver).key_down(Keys.ENTER).perform()
        container = self.get_current_container()
        textarea = next(iter(container.select(term)), None)

        if self.webapp_shadowroot() and textarea:
            textarea = next(iter(self.find_shadow_element('textarea', self.soup_to_selenium(textarea))))
            content = self.driver.execute_script(f"return arguments[0].value",textarea).strip()
        else:
            content = self.driver.execute_script(f"return arguments[0].value",self.driver.find_element(By.XPATH, xpath_soup(textarea))).strip()

        self.SetButton('Ok')

        return content

    def check_grid_error(self, grid, headers, column_name, rows, columns, field):
        """
        [Internal]

        """
        error = False

        if not grid:
            self.log_error("Couldn't find grids.")
            error = True

        if not error and column_name not in headers[field[3]]:
            self.log_error(f"{self.language.messages.grid_column_error} Coluna: '{column_name}' Grid: '{headers[field[3]].keys()}'")
            error = True

        if not error and not columns:
            self.log_error("Couldn't find columns.")

        if not error and not rows:
            self.log_error("Couldn't find rows.")
            error = True

        return


    def new_grid_line(self, field, add_grid_line_counter=True):
        """
        [Internal]

        Creates a new line on the grid.

        :param field: An item from the grid's input queue
        :type field: List of values
        :param add_grid_line_counter: Boolean if counter should be incremented when method is called. - **Default:** True
        :type add_grid_line_counter: bool

        Usage:

        >>> # Calling the method:
        >>> self.new_grid_line(["", "", 0, True])
        """
        grids = ''
        endtime = time.time() + self.config.time_out
        self.down_loop_grid = True
        logger().debug('New grid line')
        while(not grids and time.time() < endtime):
            soup = self.get_current_DOM()

            containers = self.get_current_container()
            if containers:
                containers = self.zindex_sort(containers, True)
                container = next(iter(containers), None) if isinstance(containers, list) else containers
                if container:
                    term = self.grid_selectors['new_web_app'] if self.webapp_shadowroot() else ".tgetdados, .tgrid"
                    grids = self.filter_displayed_elements(container.select(term))
                    grids = self.filter_active_tabs(grids) if self.webapp_shadowroot() else grids

            time.sleep(1)

        if grids:
            if field[2] > len(grids):
                self.log_error(self.language.messages.grid_number_error)

            if self.webapp_shadowroot():
                shadowroot_tr = lambda: self.find_shadow_element('tbody tr', self.soup_to_selenium(grids[field[2]]))

            rows = shadowroot_tr() if self.webapp_shadowroot() else grids[field[2]].select("tbody tr")
            row = self.get_selected_row(rows)
            if row:
                columns = self.find_shadow_element('td', self.soup_to_selenium(grids[field[2]])) if self.webapp_shadowroot() else row.select("td")
                if columns:
                    second_column = lambda: (
                    columns[1]) if self.webapp_shadowroot() else self.driver.find_element(By.XPATH,
                        xpath_soup(columns[1]))
                    self.driver.execute_script("$('.horizontal-scroll').scrollLeft(-400000);")
                    self.set_element_focus(second_column())

                    try:
                        ActionChains(self.driver).move_to_element(second_column()).send_keys(Keys.DOWN).perform()
                    except MoveTargetOutOfBoundsException:
                        ActionChains(self.driver).send_keys(Keys.DOWN).perform()

                    term = self.grid_selectors['new_web_app'] if self.webapp_shadowroot() else ".tgetdados tbody tr, .tgrid tbody tr"
                    endtime = time.time() + self.config.time_out
                    while (time.time() < endtime and not (
                    self.element_exists(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR, position=len(rows) + 1, main_container=self.containers_selectors["GetCurrentContainer"]) or len(shadowroot_tr()) > 1)):
                        if self.config.debug_log:
                            logger().debug("Waiting for the new line to show")
                        time.sleep(1)

                    if (add_grid_line_counter):
                        self.add_grid_row_counter(grids[field[2]])
                else:
                    self.log_error("Couldn't find columns.")
            else:
                self.log_error("Couldn't find rows.")
        else:
            self.log_error("Couldn't find grids.")

    def ClickGridCell(self, column, row_number=1, grid_number=1):
        """
        Clicks on a Cell of a Grid.

        :param column: The column that should be clicked.
        :type column: str
        :param row_number: Grid line that contains the column field to be checked.- **Default:** 1
        :type row_number: int
        :param grid_number: Grid number of which grid should be checked when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method:
        >>> oHelper.ClickGridCell("Product", 1)
        """
        success = False
        grids = None
        row_number -= 1
        grid_number -= 1
        column_name = ""
        column = column.strip()
        column_element_old_class = None
        columns =  None
        rows = None
        same_location = False
        term = self.grid_selectors['new_web_app'] if self.webapp_shadowroot() else ".tgetdados, .tgrid, .tcbrowse"
        click_attempts = 0

        logger().info(f"Clicking on grid cell: {column}")

        self.wait_blocker()
        self.wait_element(
            term=term,
            scrap_type=enum.ScrapType.CSS_SELECTOR)

        endtime = time.time() + self.config.time_out

        if re.match(r"\w+(_)", column):
            column_name = self.get_x3_dictionaries([column])[2][column].lower()
        else:
            column_name = column.lower()

        while(not success and time.time() < endtime):

            if self.webapp_shadowroot():
                containers = self.get_current_container()
            else:
                self.wait_element_timeout(term=column_name, scrap_type=enum.ScrapType.TEXT,
                                          timeout=self.config.time_out,
                                          optional_term='label')
                containers = self.web_scrap(term=".tmodaldialog,.ui-dialog", scrap_type=enum.ScrapType.CSS_SELECTOR,
                                            main_container="body")

            container = next(iter(self.zindex_sort(containers, True)), None) if isinstance(containers, list) else containers
            if container:
                grids = self.filter_displayed_elements(container.select(term))

                if grids:
                    if len(grids) > 1:

                        if self.webapp_shadowroot():
                            grids = self.filter_active_tabs(grids)
                        else:
                            grids, same_location = self.filter_non_obscured(grids, grid_number)
                            if same_location:
                                grid_number = 0

                    grids = list(filter(lambda x:x.select("tbody tr"), grids)) if list(filter(lambda x:x.select("tbody tr"), grids)) else grids
                    headers = self.get_headers_from_grids(grids)
                    if grid_number < len(grids):
                        if self.webapp_shadowroot():
                            rows = self.driver.execute_script(
                                "return arguments[0].shadowRoot.querySelectorAll('tbody tr')",
                                self.soup_to_selenium(grids[grid_number]))

                            if not rows and len(headers) < len(grids):
                                grids = list(filter(lambda x: self.get_headers_from_grids(x), grids))
                                rows = self.driver.execute_script(
                                    "return arguments[0].shadowRoot.querySelectorAll('tbody tr')",
                                    self.soup_to_selenium(grids[grid_number]))
                        else:
                            rows = grids[grid_number].select("tbody tr")

                    if rows:
                        if row_number < len(rows):
                            if self.webapp_shadowroot():
                                columns = self.driver.execute_script("return arguments[0].querySelectorAll('td')", rows[row_number])
                            else:
                                columns = rows[row_number].select("td")

                    if columns:
                        if len(headers) > grid_number and column_name in headers[grid_number]:
                            column_number = headers[grid_number][column_name]
                            if self.webapp_shadowroot():
                                column_element = lambda: columns[column_number]
                            else:
                                column_element = lambda : self.driver.find_element(By.XPATH, xpath_soup(columns[column_number]))

                            if column_element_old_class == None:
                                column_element_old_class = column_element().get_attribute("class")

                            if self.webapp_shadowroot():
                                self.wait_until_to(expected_condition="visibility_of", element=column_element)
                            else:
                                self.wait_until_to(expected_condition="element_to_be_clickable", element = columns[column_number], locator = By.XPATH, timeout=True)

                            endtime_click = time.time() + self.config.time_out/2
                            while time.time() < endtime_click and column_element_old_class == column_element().get_attribute("class"):
                                self.scroll_to_element(column_element())
                                self.send_action(action=self.click, element=column_element, click_type=3, wait_change=False) if self.webapp_shadowroot() else self.click(column_element())
                                click_attempts += 1
                                if column_number == 0 and click_attempts > 3 or 'selected' in column_element().get_attribute(
                                        "class") and click_attempts > 3:
                                    break

                            self.wait_element_is_focused(element_selenium = column_element, time_out = 2)

                            if column_element_old_class != column_element().get_attribute("class") or 'selected' in column_element().get_attribute("class") :
                                if self.webapp_shadowroot():
                                    self.wait_until_to(expected_condition="visibility_of", element=column_element)
                                else:
                                    self.wait_until_to(expected_condition="element_to_be_clickable",
                                                       element=columns[column_number], locator=By.XPATH, timeout=True)
                                self.wait_blocker()
                                success = True
                            elif grids[grid_number] and "tcbrowse" in grids[grid_number].attrs['class']:
                                time.sleep(0.5)
                                success = True

        if not success:
            logger().debug(f"Couldn't Click on grid cell \ngrids:{grids}\nrows: {rows} ")
            self.log_error(f"Couldn't Click on \n Column: '{column}' Grid number: {grid_number+1}")


    def filter_non_obscured(self, elements, grid_number):

        same_position = []

        main_element = self.soup_to_selenium(elements[grid_number])
        x, y = main_element.location['x'], main_element.location['y']

        for element in elements:
            selenium_element = self.soup_to_selenium(element)

            if x == selenium_element.location['x'] and y == selenium_element.location['y'] and \
                    not main_element == selenium_element:
                same_position.append(element)

        if same_position:
            same_position.append(elements[grid_number])
            return [next(iter(list(self.zindex_sort(same_position, reverse=True))))], True

        return elements, False


    def filter_active_tabs(self, object):
        """

        :param object:
        :return: return the object if parent wa-tab-page is active else []
        """
        if not object:
            return []

        if isinstance(object, list):
            filtered_object = list(
                filter(lambda x: hasattr(x.find_parent('wa-tab-page'), 'attrs') if x else None, object))

            if filtered_object:
                activated_objects = list(filter(lambda x: 'active' in x.find_parent('wa-tab-page').attrs, object))
                activated_tabs = list(map(lambda x: x.find_parent('wa-tab-page'), activated_objects))
                for i, j in enumerate(activated_tabs[:-1]):
                    if j != activated_tabs[i+1]:
                        parents_folders = list(filter(lambda x: 'data-advpl' and "caption" in x.attrs and x['caption'] and x['data-advpl'] == 'tfolderpage', j.find_parents('wa-tab-page')))
                        prev_siblings = list(map(lambda x: x.find_previous_siblings("wa-tab-page"), parents_folders))
                        next_siblings = list(map(lambda x: x.find_next_siblings("wa-tab-page"), parents_folders))
                        is_same_layer = list(filter(lambda x: activated_tabs[i+1] in prev_siblings[x[0]] or activated_tabs[i+1] in next_siblings[x[0]], enumerate(parents_folders)))
                        if is_same_layer:
                            activated_objects.pop(i)
                return activated_objects
            else:
                filtered_object = next(iter(object))
                if filtered_object.name == 'wa-tgrid':
                    return [filtered_object]

        elif isinstance(object, Tag):
            if hasattr(object.find_parent('wa-tab-page'), 'attrs'):
                return object if 'active' in object.find_parent('wa-tab-page').attrs else None
            elif hasattr(object, 'opened') and 'opened' in object.attrs:
                panels_object = object.select('.dict-tscrollarea')
                if panels_object:
                    filtered_object = next(iter(panels_object))
                    if filtered_object.contents:
                        return next(iter(filtered_object.contents))


    def ClickGridHeader( self, column = 1, column_name = '', grid_number = 1):
        """
        Clicks on a Cell of a Grid Header.

        :param column: The column index that should be clicked.
        :type column: int
        :param column_name: The column index that should be clicked.
        :type row_number: str
        :param grid_number: Grid number of which grid should be checked when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method:
        >>> oHelper.ClickGridHeader(column = 1 , grid_number =  1)
        >>> oHelper.ClickGridHeader(column_name = 'Código' , grid_number =  1)
        >>> oHelper.ClickGridHeader(column = 1 , grid_number =  2)
        """
        grid_number -= 1
        column -=1 if column > 0 else 0
        header = None
        column_number = None

        self.wait_element(term=f".tgetdados tbody tr, .tgrid tbody tr, .tcbrowse, {self.grid_selectors['new_web_app']}", scrap_type=enum.ScrapType.CSS_SELECTOR)
        grid = self.get_grid(grid_number)
        header = self.get_headers_from_grids(grid)

        if not column_name:

            if self.webapp_shadowroot():
                column_element_selenium = self.find_shadow_element('thead label', self.soup_to_selenium(grid))[column]
                if not column_element_selenium.text:
                    column_element_selenium = self.find_shadow_element('thead th', self.soup_to_selenium(grid))[column]
                self.wait.until(EC.visibility_of((column_element_selenium)))
            else:
                column_element = grid.select('thead label')[column].find_parent('th')
                column_element_selenium = self.soup_to_selenium(column_element)
                self.wait_until_to(expected_condition="element_to_be_clickable", element=column_element,
                                   locator=By.XPATH)

            self.set_element_focus(column_element_selenium)
            column_element_selenium.click()
        else:
            column_name =column_name.lower()

            if column_name in header[grid_number]:
                column_number = header[grid_number][column_name]
            else:
                grid = self.return_grid_by_index(column_name)
                header = self.get_headers_from_grids(grid)
                column_number = header[0][column_name]

            if self.webapp_shadowroot():
                column_element_selenium = self.find_shadow_element('thead label', self.soup_to_selenium(grid))[column_number]
                if column_element_selenium:
                    self.wait.until(EC.visibility_of((column_element_selenium)))
            else:
                column_element = grid.select('thead label')[column_number].find_parent('th')
                column_element_selenium = self.soup_to_selenium(column_element)
                self.wait_until_to(expected_condition="element_to_be_clickable", element=column_element,
                                   locator=By.XPATH)

            if column_element_selenium:
                self.set_element_focus(column_element_selenium)

                self.click(column_element_selenium)

    def return_grid_by_index(self, column_name):
        """
        [Internal]
        """

        grids = self.get_grid(grid_list=True)

        header_index = self.return_header_index(column_name)

        if header_index:
            return grids[header_index]

    def return_header_index(self, column_name=None, headers=None):
        """
        [Internal]
        """

        grids = self.get_grid(grid_list=True)

        if not headers:
            headers = self.get_headers_from_grids(grids)

        if column_name and headers:
            header = next(iter(list(filter(lambda x: column_name.lower() in x, headers))), None)
            if not header: # if not find header, do inverse search with regex in headers keys'
                column_name =  re.sub(' ', '', column_name).lower()
                for hd in headers:
                    header = next(iter(list(filter(lambda x: column_name in re.sub(' ', '', x).lower(), hd.keys()))), None)
                    if header:
                        header = next(iter(list(filter(lambda x: header.lower() in x, headers))), None)
                        break

        if header:
            return headers.index(header)

    def search_column_index(self, grid, column):

        if self.webapp_shadowroot():
            column_enumeration = list(enumerate(self.find_shadow_element('thead label', self.soup_to_selenium(grid))))
            chosen_column = list(filter(lambda x: column.lower().strip() == x[1].text.lower().strip(),
                                        column_enumeration))

        else:
            column_enumeration = list(enumerate(grid.select("thead label")))
            chosen_column = next(iter(list(filter(lambda x: column in x[1].text, column_enumeration))), None)

        if chosen_column:
            column_index = chosen_column[0]
        else:
            self.log_error("Couldn't find chosen column.")

        return column_index

    def get_x3_dictionaries(self, fields):
        """
        [Internal]

        Generates the dictionaries with field comparisons from the x3 file,

        Dictionaries:Field to Type, Field to Size, Field to Title.

        :param fields: List of fields that must be located in x3.
        :type fields: List of str

        :return: The three x3 dictionaries in a Tuple.
        :trype: Tuple of Dictionary

        Usage:

        >>> # Calling the method:
        >>> x3_dictionaries = self.get_x3_dictionaries(field_list)
        """
        prefixes = list(set(map(lambda x:x.split("_")[0] + "_" if "_" in x else "", fields)))
        regex = self.generate_regex_by_prefixes(prefixes)

        #caminho do arquivo csv(SX3)
        path = os.path.join(os.path.dirname(__file__), self.replace_slash(r'core\\data\\sx3.csv'))

        #DataFrame para filtrar somente os dados da tabela informada pelo usuário oriundo do csv.
        data = pd.read_csv(path, sep=';', encoding='latin-1', header=None, on_bad_lines='error',
                        index_col='Campo', names=['Campo', 'Tipo', 'Tamanho', 'Titulo', 'Titulo_Spa', 'Titulo_Eng', None], low_memory=False)
        df = pd.DataFrame(data, columns=['Campo', 'Tipo', 'Tamanho', 'Titulo', 'Titulo_Spa', 'Titulo_Eng', None])
        if not regex:
            df_filtered = df.query("Tipo=='C' or Tipo=='N' or Tipo=='D' ")
        else:
            df_filtered = df.filter(regex=regex, axis=0)

        if self.config.language == "es-es":
            df_filtered.Titulo = df_filtered.loc[:,('Titulo_Spa')].str.strip()
        elif self.config.language == "en-us":
            df_filtered.Titulo = df_filtered.loc[:,('Titulo_Eng')].str.strip()
        else:
            df_filtered.Titulo = df_filtered.loc[:,('Titulo')].str.strip()

        df_filtered.index = df_filtered.index.map(lambda x: x.strip())

        dict_ = df_filtered.to_dict()

        return (dict_['Tipo'], dict_['Tamanho'], dict_['Titulo'])

    def generate_regex_by_prefixes(self, prefixes):
        """
        [Internal]

        Returns a regex string created by combining all field prefixes.

        :param prefixes: Prefixes of fields to be combined in a regex.
        :type prefixes: List of str

        Usage:

        >>> # Calling the method:
        >>> regex = self.generate_regex_by_prefixes(field_prefixes)
        """
        filtered_prefixes = list(filter(lambda x: x != "", prefixes))
        regex = ""
        for prefix in filtered_prefixes:
            regex += "^" + prefix + "|"

        return regex[:-1]

    def get_headers_from_grids(self, grids, column_name='', position=0, duplicate_fields=[]):
        """
        [Internal]

        Returns the headers of each grid in *grids* parameter.

        :param grids: The grids to extract the headers.
        :type grids: List of BeautifulSoup objects

        :return: List of Dictionaries with each header value and index.
        :rtype: List of Dict

        Usage:

        >>> # Calling the method:
        >>> headers = self.get_headers_from_grids(grids)
        """

        headers = []
        labels = None
        index = []
        labels_list= []

        if isinstance(grids, list):
            for item in grids:
                labels = self.driver.execute_script("return arguments[0].shadowRoot.querySelectorAll('thead tr label')",
                                                                    self.soup_to_selenium(item))
                if labels:
                    keys = list(map(lambda x: x.text.strip().lower(), labels))
                    labels_list.append(keys)
                    values = list(map(lambda x: x[0], enumerate(labels)))
                    headers.append(dict(zip(keys, values)))

        elif self.webapp_shadowroot():
            labels = self.driver.execute_script("return arguments[0].shadowRoot.querySelectorAll('thead tr label')",
                                       self.soup_to_selenium(grids))

            if labels:
                keys = list(map(lambda x: x.text.strip().lower(), labels))
                labels_list.append(keys)
                values = list(map(lambda x: x[0], enumerate(labels)))
                headers.append(dict(zip(keys, values)))

        if column_name or column_name == '':
            if duplicate_fields:
                duplicated_key = str(duplicate_fields[0]).lower()
                duplicated_value = duplicate_fields[1]-1 if duplicate_fields[1] > 0 else 0
            else:
                duplicated_key = column_name.lower()
                duplicated_value = position-1 if position > 0 else 0

            for labels in labels_list:
                for idx, value in enumerate(labels):
                    if value == duplicated_key:
                        index.append(idx)
                if len(index) > 1:
                    for header in headers:
                        if duplicated_key in header:
                            header[duplicated_key] = duplicated_value if duplicate_fields else index[duplicated_value]
                index = []

        return headers

    def add_grid_row_counter(self, grid):
        """
        [Internal]

        Adds the counter of rows to the global dictionary.

        :param grid: The grid whose rows are being controlled.
        :type grid: BeautifulSoup object.

        Usage:

        >>> # Calling the method:
        >>> self.add_grid_row_counter(grid)
        """
        grid_id = grid.attrs["id"]

        if grid_id not in self.grid_counters:
            self.grid_counters[grid_id] = 0
        else:
            self.grid_counters[grid_id]+=1

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

    def wait_element(self, term, scrap_type=enum.ScrapType.TEXT, presence=True, position=0, optional_term=None, main_container=".tmodaldialog,.ui-dialog,wa-dialog", check_error=True, twebview=False, second_term=None):
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

        self.twebview_context = twebview

        endtime = time.time() + self.config.time_out
        if self.config.debug_log:
            logger().debug("Waiting for element")

        if presence:
            while (not self.element_exists(term, scrap_type, position, optional_term, main_container, check_error, twebview, second_term) and time.time() < endtime):
                time.sleep(0.1)
        else:
            while (self.element_exists(term, scrap_type, position, optional_term, main_container, check_error, twebview) and time.time() < endtime):
                time.sleep(0.1)

        if time.time() > endtime:
            if term == "[name='cGetUser']":
                self.close_resolution_screen()
            else:
                if self.webapp_shadowroot():
                    class_term = "wa-dialog"
                else:
                    class_term = ".ui-button.ui-dialog-titlebar-close[title='Close']"
                if  class_term in term:
                    return False
                self.restart_counter += 1
                logger().debug(f'wait_element doesn\'t found term: {term}')
                if presence:
                    self.log_error(f"Element '{term}' not found!")
                else:
                    self.log_error(f"Unexpected element '{term}' found!")

        presence_endtime = time.time() + 10
        if presence:

            if self.config.debug_log:
                logger().debug("Element found! Waiting for element to be displayed.")

            element = next(iter(self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container, check_error=check_error, twebview=twebview, second_term=second_term)), None)

            if element is not None:

                sel_element = lambda: self.soup_to_selenium(element) if type(element) == Tag else element
                if self.webapp_shadowroot():
                    self.scroll_to_element(sel_element())
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


    def wait_element_timeout(self, term, scrap_type=enum.ScrapType.TEXT, timeout=5.0, step=0.1, presence=True, position=0, optional_term=None, main_container=".tmodaldialog,.ui-dialog, wa-dialog, body", check_error=True, twebview=False):
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
        self.twebview_context = twebview

        element = None
        success = False
        if presence:
            endtime = time.time() + timeout
            while time.time() < endtime:
                time.sleep(step)
                if self.element_exists(term, scrap_type, position, optional_term, main_container, check_error, twebview):
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

            element = self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container, check_error=check_error, twebview=twebview, position=position)

            if element:
                element = next(iter(element), None)
                if type(element) == Tag:
                    sel_element = lambda: self.driver.find_element(By.XPATH, xpath_soup(element))


                while(time.time() < endtime and not self.element_is_displayed(element)):
                    try:
                        time.sleep(0.1)

                        if self.config.poui_login:
                            self.switch_to_iframe()

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
        if self.webapp_shadowroot():
            filtered_rows = list(filter(lambda x: self.driver.execute_script("return arguments[0].querySelector('td.selected-cell')", x),rows))
            if filtered_rows:
                return next(iter(filtered_rows), None)

            filtered_rows =list(filter(lambda x: self.driver.execute_script("return arguments[0].querySelector('.selected-row')", x),rows))
            if filtered_rows:
                return next(iter(filtered_rows), None)

        else:
            filtered_rows = list(filter(lambda x: len(x.select("td.selected-cell")), rows))
            if filtered_rows:
                return next(iter(filtered_rows))
            else:
                filtered_rows = list(filter(lambda x: "selected-row" == self.soup_to_selenium(x).get_attribute('class'), rows))
                if filtered_rows:
                    return next(iter(list(filter(lambda x: "selected-row" == self.soup_to_selenium(x).get_attribute('class'), rows))), None)
        return next(reversed(rows), None)


    def SetFilePath(self, value, button = ""):
        """
        Fills the path screen with the desired path

        .. warning::
            Necessary informed the button name or the program will select the current button name.

        :param value: Path to be inputted.
        :type value: str
        :param button: Name button from path screen.
        :type button: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetFilePath(r"C:\\folder")
        >>> oHelper.SetFilePath(r"C:\\folder","save")
        """
        if self.webapp_shadowroot():
            self.wait_element(self.language.file_name, enum.ScrapType.MIXED, optional_term='wa-file-picker')
            soup = self.get_current_DOM()
            containers_soup = next(iter(soup.select('wa-file-picker')), None)
            element = self.driver.execute_script(f"return arguments[0].shadowRoot.getElementById('txtPath')", self.soup_to_selenium(containers_soup))
            if element:
                self.driver.execute_script("document.querySelector('wa-file-picker').shadowRoot.querySelector('#{}').value='';".format(element.get_attribute("id")))

                self.send_keys(element, self.replace_slash(value))
                elements = self.find_shadow_element('button, wa-button', self.soup_to_selenium(containers_soup))
                possible_buttons = button.upper() + '_' + self.language.open.upper() + '_' + self.language.save.upper()
                if elements:
                    elements = list(filter(lambda x: x.text.strip().upper() in possible_buttons, elements))
        else:
            self.wait_element(self.language.file_name)
            element = self.driver.find_element(By.CSS_SELECTOR, ".filepath input")

            if element:
                self.driver.execute_script("document.querySelector('#{}').value='';".format(element.get_attribute("id")))
                self.send_keys(element, self.replace_slash(value))
                elements = self.driver.find_elements(By.CSS_SELECTOR, ".tremoteopensave button")

        if elements:
            for line in elements:
                if button != "":
                    if line.text.strip().upper() == button.upper():
                        self.click(line)
                        break
                if line.text.strip().upper() == self.language.open.upper():
                    self.click(line)
                    break
                if line.text.strip().upper() == self.language.save.upper():
                    self.click(line)
                    break

                self.log_error(f"Button: {button} not found")

    def MessageBoxClick(self, button_text):
        """
        Clicks on desired button inside a Messagebox element.

        :param button_text: Desired button to click.
        :type button_text: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.MessageBoxClick("Ok")
        """
        regx_sub = r"[\n?\s?]"
        if self.webapp_shadowroot():
            box_term = "wa-message-box"
            self.wait_element(term=box_term, main_container='body', scrap_type = enum.ScrapType.CSS_SELECTOR)
        else:
            box_term = ".messagebox-container"
            self.wait_element(box_term, enum.ScrapType.CSS_SELECTOR)

        content = self.driver.page_source
        soup = BeautifulSoup(content,"html.parser")
        container = soup.select(box_term)
        if container:
            buttons = self.find_shadow_element('wa-button', self.soup_to_selenium(container[0])) if self.webapp_shadowroot() else container[0].select(".ui-button")
            button = list(filter(lambda x: re.sub(regx_sub,'', x.text).lower() == button_text.lower(), buttons))
            if button:
                selenium_button = button[0] if self.webapp_shadowroot() else self.driver.find_element(By.XPATH, xpath_soup(button[0]))
                self.click(selenium_button)


    def get_enchoice_button_ids(self, layer):
        """
        [Internal]

        If current layer level has an enchoice, returns all buttons' ids.

        :param layer: Current layer level that the application is.
        :type layer: int

        :return: List with enchoice's buttons' ids.
        :rtype: List of str

        Usage:

        >>> # Calling the method:
        >>> self.get_enchoice_button_ids(current_layer)
        """
        try:
            soup = self.get_current_DOM()
            current_layer = self.zindex_sort(soup.select(".tmodaldialog"), False)[layer - 1]
            buttons = list(filter(lambda x: x.text.strip() != "", current_layer.select(".tpanel button")))
            return list(map(lambda x: x.parent.attrs["id"], buttons))
        except Exception as error:
            return []

    def CheckView(self, text, element_type="help"):
        """
        Checks if a certain text is present in the screen at the time and takes an action.

        "help" - alerts with messages of errors.

        :param text: Text to be checked.
        :type text: str
        :param element_type: Type of element. - **Default:** "help"
        :type element_type: str

        Usage:

        >>> # Calling the method.
        >>> oHelper.CheckView("Processing")
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field that is on the second grid of the screen:
        >>> oHelper.CheckView("Text",element_type=text-view)
        >>> #-----------------------------------------
        """
        if element_type == "help":
            logger().info(f"Checking text on screen: {text}")
            if self.webapp_shadowroot():
                term = '.dict-tsay'
            else:
                term = '.tsay'

            self.wait_element_timeout(term=text, scrap_type=enum.ScrapType.MIXED, timeout=2.5, step=0.5, optional_term=term, check_error=False)
            if self.webapp_shadowroot():
                if not self.element_exists(term=text, scrap_type=enum.ScrapType.MIXED, optional_term=term, main_container="wa-text-view", check_error=False):
                    self.errors.append(f"{self.language.messages.text_not_found}({text})")
            else:
                if not self.element_exists(term=text, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay", check_error=False):
                    self.errors.append(f"{self.language.messages.text_not_found}({text})")

        if element_type == "message-box":
            logger().info(f"Checking text on screen: {text}")

            term = 'wa-message-box'

            self.wait_element_timeout(term=text, scrap_type=enum.ScrapType.TEXT, timeout=2.5, step=0.5, optional_term=term, check_error=False)
            if not self.element_exists(term=text, scrap_type=enum.ScrapType.TEXT, main_container=term, check_error=False):
                self.errors.append(f"{self.language.messages.text_not_found}({text})")

        if element_type == "text-view":
            logger().info(f"Checking text on screen: {text}")

            term = 'wa-text-view'

            self.wait_element_timeout(term=text, scrap_type=enum.ScrapType.TEXT, timeout=2.5, step=0.5, optional_term=term, check_error=False)
            if not self.element_exists(term=text, scrap_type=enum.ScrapType.TEXT, main_container=term, check_error=False):
                self.errors.append(f"{self.language.messages.text_not_found}({text})")


    def try_send_keys(self, element_function, key, try_counter=1):
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

        action_send_keys = None
        is_active_element  = lambda : self.is_active_element(element_function())

        logger().debug(f"Trying to send keys to element using technique {try_counter}")
        self.wait_until_to( expected_condition = "visibility_of", element = element_function )

        if try_counter == 1:
            element_function().send_keys(Keys.HOME)
            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
            if is_active_element():
                element_function().send_keys(key)
        elif try_counter == 2:
            ActionChains(self.driver).send_keys(Keys.HOME).perform()
            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
            action_send_keys = ActionChains(self.driver).move_to_element(element_function()).send_keys(key)
        elif try_counter == 3:
            element_function().send_keys(Keys.HOME)
            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.DOWN).key_up(Keys.SHIFT).perform()
            action_send_keys = ActionChains(self.driver).move_to_element(element_function()).send_keys(key)
        else:
            element_function().send_keys(Keys.HOME)
            ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.END).key_up(Keys.SHIFT).perform()
            action_send_keys = ActionChains(self.driver).move_to_element(element_function()).send_keys(key)

        if action_send_keys and is_active_element():
            action_send_keys.perform()

    def is_active_element(self, element):
        """
        [Internal]

        Return true if an element is active status

        :param element: Element to analyse
        :type element: Selenium object

        :return: A list containing a BeautifulSoup object next to the label
        :rtype: List of BeautifulSoup objects
        """

        is_active = self.switch_to_active_element() == element

        if is_active:
            return is_active
        else :
            shadow_input = self.find_shadow_element('input, textarea', self.switch_to_active_element(), get_all=False)
            return shadow_input == element



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
                elements = self.filter_label_element(label_text, container, position)
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

        if self.blocker:
            message += f' Blocker: {self.blocker}'
            self.blocker = None

        if self.config.smart_test:
            self.log.log_exec_file()

        self.clear_grid()
        logger().warning(f"Warning log_error {message}")

        if self.config.smart_test or self.config.debug_log:
            logger().debug(f"***System Info*** in log_error():")
            system_info()

        stack_item = self.log.get_testcase_stack()
        test_number = f"{stack_item.split('_')[-1]} -" if stack_item else ""
        log_message = f"{test_number} {message}"
        self.message = log_message
        self.expected = False
        self.log.seconds = self.log.set_seconds(self.log.initial_time)
        self.log.initial_time = datetime.today()
        self.log.testcase_seconds = self.log.set_seconds(self.log.testcase_initial_time)
        self.log.ct_method, self.log.ct_number = self.log.ident_test()

        if self.config.new_log:
            self.execution_flow()

        proceed_action = lambda: ((stack_item != "setUpClass") or (stack_item == "setUpClass" and self.restart_counter == 3))

        if self.config.screenshot and proceed_action() and stack_item not in self.log.test_case_log and self.driver:
            self.log.take_screenshot_log(self.driver, stack_item, test_number)
            time.sleep(1)

        if new_log_line and proceed_action():
            self.log.new_line(False, log_message)
        if proceed_action() and self.log.has_csv_condition():
            self.log.generate_log()
        if not self.config.skip_restart and len(self.log.list_of_testcases()) >= 1 and self.config.initial_program != '':
            self.restart()
        elif self.config.coverage and self.config.initial_program != '':
            self.restart()
        else:
            try:
                if self.driver:
                    self.driver.close()
            except Exception as e:
                logger().exception(f"Warning Log Error Close {str(e)}")

        if self.restart_counter > 2:

            if self.config.num_exec and stack_item == "setUpClass" or stack_item == "tearDownClass" and self.log.checks_empty_line():
                if not self.num_exec.post_exec(self.config.url_set_end_exec, 'ErrorSetFimExec'):
                    self.restart_counter = 3
                    self.log_error(f"WARNING: Couldn't possible send num_exec to server please check log.")

                if self.config.check_dump:
                    self.check_dmp_file()

            if (stack_item == "setUpClass") :
                try:
                    if self.driver:
                        self.driver.close()
                except Exception as e:
                    logger().exception(f"Warning Log Error Close {str(e)}")

        if stack_item != "setUpClass":
            self.restart_counter = 0

        if proceed_action() or not self.check_release_newlog():
            if self.restart_counter >= 3:
                self.restart_counter = 0
            self.assertTrue(False, log_message)

    def ClickIcon(self, icon_text, position=1):
        """
        Clicks on an Icon button based on its tooltip text or Alt attribute title.

        :param icon_text: The tooltip/title text.
        :type icon_text: str
        :param position: Position which element is located. - **Default:** 1
        :type position: int

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickIcon("Add")
        >>> oHelper.ClickIcon("Edit")
        """
        icon = ""
        success = False
        filtered_buttons = None
        position -= 1

        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and not icon and not success):
            if self.webapp_shadowroot():
                selector = "wa-toolbar, .dict-tbtnbmp2, .dict-tbtnbmp"
            else:
                selector = ".ttoolbar, .tbtnbmp"

            self.wait_element(term=selector, scrap_type=enum.ScrapType.CSS_SELECTOR)
            soup = self.get_current_DOM()
            if self.webapp_shadowroot():
                container = next(iter(self.zindex_sort(soup.select("wa-dialog"))), None)
            else:
                container = next(iter(self.zindex_sort(soup.select(".tmodaldialog"))), None)
            container = container if container else soup
            if self.webapp_shadowroot():
                tbtnbmp_img = self.on_screen_enabled(container.select(selector))
            else:
                tbtnbmp_img = self.on_screen_enabled(container.select(".tbtnbmp > img"))
            tbtnbmp_img_str = " ".join(str(x) for x in tbtnbmp_img) if tbtnbmp_img else ''

            if icon_text not in tbtnbmp_img_str:
                container = self.get_current_container()
                if self.webapp_shadowroot():
                    tbtnbmp_img = self.on_screen_enabled(container.select("wa-toolbar,.dict-tbtnbmp2"))
                else:
                    tbtnbmp_img = self.on_screen_enabled(container.select(".tbtnbmp > img"))

            if tbtnbmp_img and len(tbtnbmp_img) -1 >= position:
                if self.webapp_shadowroot():
                    icon = list(filter(lambda x: icon_text == x.get("title"), tbtnbmp_img))
                    if icon and isinstance(icon, list):
                        icon = list(filter(lambda x: icon_text == x.get("title"), tbtnbmp_img))[position]
                else:
                    icon = list(filter(lambda x: icon_text == self.soup_to_selenium(x).get_attribute("alt"), tbtnbmp_img))[position]

            if not icon:

                if self.webapp_shadowroot():
                    buttons = self.on_screen_enabled(container.select('wa-button'))
                else:
                    buttons = self.on_screen_enabled(container.select("button[style]"))

                logger().info("Searching for Icon")
                if buttons:
                    filtered_buttons = list(filter(lambda x: "title" in x.attrs and icon_text.lower().strip() in x['title'].lower().strip(), buttons))
                    if not filtered_buttons:
                        filtered_buttons = self.filter_by_tooltip_value(buttons, icon_text)
                    if filtered_buttons and len(filtered_buttons) -1 >= position:
                        icon = next(iter(filtered_buttons), None)

            if icon:
                element = lambda: self.soup_to_selenium(icon)
                self.set_element_focus(element())
                success = self.click(element())

        if not icon:
            self.log_error(f"Couldn't find Icon: {icon_text}.")
        if not success:
            self.log_error(f"Couldn't click Icon: {icon_text}.")

    def AddParameter(self, parameter, branch, portuguese_value, english_value="", spanish_value=""):
        """
        Adds a parameter to the queue of parameters to be set by SetParameters method.

        :param parameter: The parameter name.
        :type parameter: str
        :param branch: The branch to be filled in parameter edit screen.
        :type branch: str
        :param portuguese_value: The value for a portuguese repository.
        :type portuguese_value: str
        :param english_value: The value for an english repository.
        :type english_value: str
        :param spanish_value: The value for a spanish repository.
        :type spanish_value: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.AddParameter("MV_MVCSA1", "", ".F.", ".F.", ".F.")
        """

        logger().info(f"AddParameter: {parameter}")

        if 'POUILogin' in self.config.json_data and self.config.json_data['POUILogin'] == True:
            twebview = True
        else:
            twebview = False

        if(self.config.smart_test or self.config.parameter_url):

            if self.tmenu_screen is None:
                self.tmenu_screen = self.check_tmenu_screen()

            value = self.parameter_url_value( self.config.language.lower(),
                {'pt-br': portuguese_value, 'en-us': english_value, 'es-es': spanish_value})

            logger().debug(f"Adding parameter url...")

            self.driver.get(f"""{self.config.url}/?StartProg=u_AddParameter&a={parameter}&a={
                branch}&a={value}&Env={self.config.environment}""")

            logger().debug(f"Parameter Url added")

            endtime = time.time() + self.config.time_out
            halftime = time.time() + 30

            while (time.time() < endtime and not self.element_exists(term="[name='cGetUser'] > input, [name='cGetUser'], [name='login']",
                                    scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body', twebview=twebview)):

                logger().info(f"Start while timeout: {parameter}")
                tmessagebox = self.web_scrap(".tmessagebox", scrap_type=enum.ScrapType.CSS_SELECTOR,
                    optional_term=None, label=False, main_container="body")
                if( tmessagebox ):
                    self.restart_counter = 3
                    self.log_error(f" AddParameter error: {tmessagebox[0].text}")

                if ( not tmessagebox and time.time() >= halftime):
                    halftime = time.time() + 30
                    logger().info(f"Enter if tmessagebox: {parameter}")
                    self.driver.get(f"""{self.config.url}/?StartProg=u_AddParameter&a={parameter}&a={
                        branch}&a={value}&Env={self.config.environment}""")
        else:
            self.parameters.append([parameter.strip(), branch, portuguese_value, english_value, spanish_value])


    def SetParameters(self):
        """
        Sets the parameters in CFG screen. The parameters must be passed with calls for **AddParameter** method.

        Usage:

        >>> # Adding Parameter:
        >>> oHelper.AddParameter("MV_MVCSA1", "", ".F.", ".F.", ".F.")
        >>> # Calling the method:
        >>> oHelper.SetParameters()
        """

        if(self.config.smart_test or self.config.parameter_url):
            self.parameter_url(restore_backup=False)
        else:
            self.parameter_screen(restore_backup=False)

    def RestoreParameters(self):
        """
        Restores parameters to previous value in CFG screen. Should be used after a **SetParameters** call.

        Usage:

        >>> # Adding Parameter:
        >>> oHelper.AddParameter("MV_MVCSA1", "", ".F.", ".F.", ".F.")
        >>> # Calling the method:
        >>> oHelper.SetParameters()
        """
        if(self.config.smart_test or self.config.parameter_url):
            self.tmenu_screen = self.check_tmenu_screen()
            self.parameter_url(restore_backup=True)
        else:
            self.parameter_screen(restore_backup=True)

    def parameter_url(self, restore_backup=False):
        """
        [Internal]

        Internal method of set and restore parameters.

        :param restore_backup: Boolean if method should restore the parameters.
        :type restore_backup: bool

        Usage:

        >>> # Calling the method:
        >>> self.parameter_url(restore_backup=False)
        """
        try_counter = False

        if 'POUILogin' in self.config.json_data and self.config.json_data['POUILogin'] == True:
            twebview = True
        else:
            twebview = False

        endtime = time.time() + self.config.time_out
        halftime = ((endtime - time.time()) / 2)
        function_to_call = "u_SetParam" if restore_backup is False else "u_RestorePar"
        if restore_backup == True and self.parameters:
            return

        time.sleep(3)
        self.driver.get(f"""{self.config.url}/?StartProg={function_to_call}&a={self.config.group}&a={
                self.config.branch}&a={self.config.user}&a={self.config.password}&Env={self.config.environment}""")

        while ( time.time() < endtime and not self.wait_element_timeout(term="[name='cGetUser'] > input, [name='cGetUser'], [name='login']", timeout = 1,
            scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body', twebview=twebview)):

            logger().info("Start while timeout: parameter_url")
            tmessagebox = self.web_scrap(".tmessagebox", scrap_type=enum.ScrapType.CSS_SELECTOR,
                optional_term=None, label=False, main_container="body")
            if( tmessagebox ):
                method = "SetParameters" if restore_backup is False else "RestoreParameters"
                self.restart_counter = 3
                self.log_error(f" {method} error: {tmessagebox[0].text}")

            if ( not tmessagebox and ((endtime) - time.time() < halftime) and not try_counter):
                logger().info(f"parameter_url: {function_to_call} again")
                self.driver.get(f"""{self.config.url}/?StartProg={function_to_call}&a={self.config.group}&a={
                        self.config.branch}&a={self.config.user}&a={self.config.password}&Env={self.config.environment}""")
                try_counter = True


        time.sleep(3)
        logger().info(f"Finish parameter_url while")
        self.driver.get(self.config.url)
        self.Setup(self.config.initial_program, self.config.date, self.config.group,
            self.config.branch, save_input=not self.config.autostart)


        if not self.tmenu_screen:
            if ">" in self.config.routine:
                self.SetLateralMenu(self.config.routine, save_input=False)
            else:
                self.Program(self.config.routine)

        self.tmenu_screen = None

    def parameter_screen(self, restore_backup):
        """
        [Internal]

        Internal method of SetParameters and RestoreParameters.

        :param restore_backup: Boolean if method should restore the parameters.
        :type restore_backup: bool

        Usage:

        >>> # Calling the method:
        >>> self.parameter_screen(restore_backup=False)
        """
        label_param = None
        exception = None
        stack = None
        img_param = []

        self.tmenu_screen = self.check_tmenu_screen()

        try:
            self.driver_refresh()
        except Exception as error:
            exception = error

        if not exception:
            if self.config.browser.lower() == "chrome":
                try:
                    self.wait_until_to( expected_condition = "alert_is_present" )
                    self.driver.switch_to_alert().accept()
                except:
                    pass

            self.Setup("SIGACFG", self.config.date, self.config.group, self.config.branch, save_input=False)
            self.SetLateralMenu(self.config.parameter_menu if self.config.parameter_menu else self.language.parameter_menu, save_input=False)

            self.wait_element(term=".ttoolbar, wa-toolbar, wa-panel", scrap_type=enum.ScrapType.CSS_SELECTOR)
            self.wait_element_timeout(term="img[src*=bmpserv1]", scrap_type=enum.ScrapType.CSS_SELECTOR, timeout=5.0, step=0.5)

            endtime = time.time() + self.config.time_out

            while(time.time() < endtime and not label_param):

                container = self.get_current_container()
                if self.webapp_shadowroot():
                    bs_tree = container.select('wa-tree')
                    if bs_tree:
                        shadow_tree_node = self.find_shadow_element('wa-tree-node',
                                                                    self.soup_to_selenium(next(iter(bs_tree))))
                        if shadow_tree_node:
                            label_serv1 = next(iter(shadow_tree_node), None)
                else:
                    img_serv1 = next(iter(container.select("img[src*='bmpserv1']")), None )
                    label_serv1 = next(iter(img_serv1.parent.select('label')), None)

                if label_serv1:
                    self.ClickTree(label_serv1.text.strip())
                    self.wait_element_timeout(term="img[src*=bmpparam]", scrap_type=enum.ScrapType.CSS_SELECTOR, timeout=5.0, step=0.5)
                    container = self.get_current_container()

                    if self.webapp_shadowroot():
                        bs_tree_2 = container.select('wa-tree')
                        if bs_tree_2:
                            tree_nodes = self.find_shadow_element('wa-tree-node', self.soup_to_selenium(next(iter(bs_tree_2))))
                            if len(tree_nodes) > 1 :
                                img_param = tree_nodes[1]
                    else:
                        img_param = next(iter(container.select("img[src*='bmpparam']")), None )

                    if img_param:
                        label_param = img_param if self.webapp_shadowroot() else next(iter(img_param.parent.select('label')), None)

                        self.ClickTree(label_param.text.strip())

            if not label_param:
                self.log_error(f"Couldn't find Icon")

            self.ClickIcon(self.language.search)

            self.fill_parameters(restore_backup=restore_backup)
            self.parameters = []
            self.ClickIcon(self.language.exit)
            time.sleep(1)

            if self.config.coverage:
                self.driver_refresh()
            else:
                self.Finish()

            self.Setup(self.config.initial_program, self.config.date, self.config.group, self.config.branch, save_input=not self.config.autostart)

            if not self.tmenu_screen:
                if ">" in self.config.routine:
                    self.SetLateralMenu(self.config.routine, save_input=False)
                else:
                    self.Program(self.config.routine)
        else:
            stack = next(iter(list(map(lambda x: x.function, filter(lambda x: re.search('tearDownClass', x.function), inspect.stack())))), None)
            if(stack and not stack.lower()  == "teardownclass"):
                self.restart_counter += 1
                self.log_error(f"Wasn't possible execute parameter_screen() method Exception: {exception}")

    def check_tmenu_screen(self):
        """
        [Internal]
        """

        try:
            return self.element_is_displayed(
                next(iter(self.web_scrap(term=".tmenu, .dict-tmenu", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")),
                     None))
        except:
            return False

    def parameter_url_value(self, language, values = {'pt-br': '', 'en-us': '','es-es': '' }):
        """
        [Internal]

        Internal method of AddParameters to filter the values.

        :param language: The language of config file.
        :type language: str
        :param values: The values organized by language.
        :type values: dict[str, str]

        Usage:

        >>> # Calling the method:
        >>> self.parameter_url_value(language = self.config.language.lower(), values = {'pt-br': portuguese_value })
        """
        value = values[language]

        if not value:
            for vl in values.values():
                if vl:
                    value = vl

        value = value.replace("=","/\\")
        value = value.replace("|","\\/")
        value = value.replace("+","[2B]")

        return value

    def fill_parameters(self, restore_backup):
        """
        [Internal]

        Internal method of fill_parameters.
        Searches and edits all parameters in the queue.

        :param restore_backup: Boolean if method should restore the parameters.
        :type restore_backup: bool

        Usage:

        >>> # Calling the method:
        >>> self.fill_parameters(restore_backup=False)
        """
        parameter_list = self.backup_parameters if restore_backup else self.parameters
        for parameter in parameter_list:
            self.SetValue(self.language.search_by, parameter[0])
            self.used_ids = []
            self.SetButton(self.language.search2)
            self.ClickIcon(self.language.edit)

            if not restore_backup:
                current_branch = self.GetValue("X6_FIL")
                current_pt_value = self.GetValue("X6_CONTEUD")
                current_en_value = self.GetValue("X6_CONTENG")
                current_spa_value = self.GetValue("X6_CONTSPA")

                self.backup_parameters.append([parameter[0], current_branch.strip(), current_pt_value.strip(), current_en_value.strip(), current_spa_value.strip()])

            self.SetValue("X6_FIL", parameter[1]) if parameter[1] else None
            self.SetValue("X6_CONTEUD", parameter[2]) if parameter[2] else None
            self.SetValue("X6_CONTENG", parameter[3]) if parameter[3] else None
            self.SetValue("X6_CONTSPA", parameter[4]) if parameter[4] else None

            self.SetButton(self.language.save)
            if self.WaitShow(self.language.warning, timeout=5, throw_error=False):
                self.SetButton(self.language.continue_string)

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
        return list(filter(lambda x: self.check_element_tooltip(x, expected_text), element_list))

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
        expected_text = re.sub(' ', '', expected_text.lower())
        element_function = False

        if self.webapp_shadowroot():
            tooltip_term = 'wa-tooltip'
            if type(element) == Tag:
                element = self.soup_to_selenium(element)
            if self.find_shadow_element('button', element):
                element_function = lambda: next(iter(self.find_shadow_element('button', element)))
            elif element:
                element_function = lambda: element
            try:
                ActionChains(self.driver).move_to_element(element_function().find_element(By.TAG_NAME, "input")).perform()
            except:
                ActionChains(self.driver).move_to_element(element_function()).perform()
        else:
            tooltip_term = '.ttooltip'
            element_function = lambda: self.driver.find_element(By.XPATH, xpath_soup(element))
            self.driver.execute_script(f"$(arguments[0]).mouseover()", element_function())

        time.sleep(2)
        tooltips = self.driver.find_elements(By.CSS_SELECTOR, tooltip_term)
        if not tooltips:
            tooltips = self.get_current_DOM().select(tooltip_term)
        if tooltips:
            has_text = (len(list(filter(lambda x: expected_text in re.sub(' ', '', x.text.lower()), tooltips))) > 0 if contains else (tooltips[0].text.lower() == expected_text.lower()))
        if element_function:
            self.driver.execute_script(f"$(arguments[0]).mouseout()", element_function())
        return has_text

    def WaitFieldValue(self, field, expected_value):
        """
        Wait until field has expected value.
        Recommended for Trigger fields.

        :param field: The desired field.
        :type field: str
        :param expected_value: The expected value.
        :type expected_value: str

        Usage:

        >>> # Calling method:
        >>> self.WaitFieldValue("CN0_DESCRI", "MY DESCRIPTION")
        """
        logger().info(f"Waiting for field {field} value to be: {expected_value}")
        field = re.sub(r"(\:*)(\?*)", "", field).strip()
        self.wait_element(field)

        field_soup = self.get_field(field)

        if not field_soup:
            self.log_error(f"Couldn't find field {field}")

        field_element = lambda: self.driver.find_element(By.XPATH, xpath_soup(field_soup))

        success = False
        endtime = time.time() + 60

        while(time.time() < endtime and not success):
            if ((field_element().text.strip() == expected_value) or
                (field_element().get_attribute("value").strip() == expected_value)):
                success = True
            time.sleep(0.5)

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
        self.log.initial_time = datetime.today()

        if self.config.smart_test:
            self.log.log_exec_file()

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


    def ClickCheckBox(self, label_box_name, position=1, double_click=False):
        """
        Clicks on a Label in box on the screen.

        :param label_box_name: The label box name
        :type label_box_name: str
        :param position: index label box on interface
        :type position: int
        :param double_click: True if a double click in element is necessary.
        :type double_click: bool

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickCheckBox("Search",1)
        """

        img = None

        success = False

        logger().info(f"ClickCheckBox - Clicking on {label_box_name}")
        if position > 0:

            self.wait_element(label_box_name)

            endtime = time.time() + self.config.time_out
            while time.time() < endtime and not success:
                label_box = self.get_checkbox_label(label_box_name, position)
                if label_box:
                    checked_status =lambda: ((hasattr(self.get_checkbox_label(label_box_name, position), 'attrs') and
                                             'checked' in self.get_checkbox_label(label_box_name, position).attrs)  or \
                                             (self.soup_to_selenium(label_box).get_attribute('checked')))
                    if 'tcheckbox' or 'dict-tcheckbox' in label_box.get_attribute_list('class'):
                        label_box_element  = lambda: self.soup_to_selenium(label_box)
                        check_before_click = checked_status()

                        if self.webapp_shadowroot():
                            label_box_element =  lambda: next(iter(self.find_shadow_element('input', self.soup_to_selenium(label_box))), None)

                        if double_click:
                            success = self.send_action(action=self.double_click, element=label_box_element)
                        else:
                            self.send_action(action=self.click, element=label_box_element)
                            check_after_click = checked_status()
                            success = check_after_click != check_before_click

                    if not success:
                        label_box = label_box.parent
                        if label_box.find_next('img'):
                            if hasattr(label_box.find_next('img'), 'src'):
                                img = label_box.find_next('img').attrs['src'].split('/')[-1] if \
                                label_box.find_next('img').attrs['src'] else None

                        if 'tcheckbox' in label_box.get_attribute_list('class') or img == 'lbno_mdi.png':
                            label_box_element = lambda: self.soup_to_selenium(label_box)
                            self.wait_until_to(expected_condition="element_to_be_clickable", element=label_box,
                                            locator=By.XPATH)
                            if double_click:
                                success = self.send_action(action=self.double_click , element=label_box_element)
                            else:
                                success = self.send_action(action=self.click, element=label_box_element)

            if not success:
                self.log_error("Checkbox index is invalid.")

    def get_checkbox_label(self, label_box_name, position):
        '''Get checkbox from label name

        :param label_box_name: String
        :param position: int
        :return: BS object
        '''
        label_box = None
        container = self.get_current_container()
        if not container:
            self.log_error("Couldn't locate container.")

        labels_boxs = container.select("span, wa-checkbox")
        label_box_name = label_box_name.lower().strip()
        if self.webapp_shadowroot():
            filtered_labels_boxs = list(
                filter(lambda x: label_box_name in x.get('caption').lower().strip(), labels_boxs))
        else:
            filtered_labels_boxs = list(filter(lambda x: label_box_name in x.text.lower().strip(), labels_boxs))
        if not filtered_labels_boxs:
            filtered_labels_boxs = list(filter(lambda x: label_box_name.lower() in x.parent.text.lower(), labels_boxs))

        if position <= len(filtered_labels_boxs):
            position -= 1
            label_box = filtered_labels_boxs[position].parent if not self.webapp_shadowroot() else filtered_labels_boxs[
                position]

        return label_box

    def ClickLabel(self, label_name, position=0):
        """
        Clicks on a Label on the screen.

        :param label_name: The label name
        :type label_name: str

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickLabel("Search")
        """
        bs_label = ''
        label = ''
        filtered_labels = []
        self.wait_blocker()
        self.wait_element(label_name)
        logger().info(f"Clicking on {label_name}")
        endtime = time.time() + self.config.time_out
        while(not label and time.time() < endtime):
            container = self.get_current_container()
            if not container:
                self.log_error("Couldn't locate container.")

            if self.webapp_shadowroot():

                labels = container.select("wa-text-view, wa-checkbox, .dict-tradmenu")
                for element in labels:
                    if "class" in element.attrs and 'dict-tradmenu' in element['class']:
                        radio_labels = self.driver.execute_script(f"return arguments[0].shadowRoot.querySelectorAll('label')",
                                                   self.soup_to_selenium(element))
                        filtered_radio = list(
                            filter(lambda x: label_name.lower().strip() == x.text.lower().strip(),
                                   radio_labels))
                        if filtered_radio:
                            [filtered_labels.append(i) for i in filtered_radio]

                    elif element.get('caption') and label_name.lower() == element.get('caption').lower():
                        filtered_labels.append(element)

                if filtered_labels:
                    if len(filtered_labels) > position:
                        label = filtered_labels[position]

                    if type(label) == Tag:
                        label = self.driver.execute_script(f"return arguments[0].shadowRoot.querySelector('label')", self.soup_to_selenium(label))
                else:
                    label = next(iter(self.web_scrap(term=label_name)))

                if position > len(filtered_labels):
                    return self.log_error(f"Element position not found")

            else:
                labels = container.select("label")
                filtered_labels = list(filter(lambda x: label_name.lower() in x.text.lower(), labels))
                filtered_labels = list(filter(lambda x: EC.element_to_be_clickable((By.XPATH, xpath_soup(x))), filtered_labels))
                label = next(iter(filtered_labels), None)

        if not label:
            return self.log_error("Couldn't find any labels.")

        if type(label) == Tag:
            bs_label = self.soup_to_selenium(label)

        if self.webapp_shadowroot():
            label_element = bs_label if bs_label else label
            time.sleep(2)
            self.scroll_to_element(label_element)
            self.set_element_focus(label_element)
            self.send_action(action=self.click, element=lambda: label_element)
        else:
            time.sleep(2)
            label_element = bs_label if bs_label else label
            self.scroll_to_element(label_element)
            self.wait_until_to(expected_condition="element_to_be_clickable", element = label, locator = By.XPATH )
            self.set_element_focus(label_element)
            self.wait_until_to(expected_condition="element_to_be_clickable", element = label, locator = By.XPATH )
            self.click(label_element)

    def get_current_container(self):
        """
        [Internal]

        An internal method designed to get the current container.
        Returns the BeautifulSoup object that represents this container or NONE if nothing is found.

        :return: The container object
        :rtype: BeautifulSoup object

        Usage:

        >>> # Calling the method:
        >>> container = self.get_current_container()
        """
        soup = self.get_current_DOM()
        containers = self.zindex_sort(soup.select(self.containers_selectors["GetCurrentContainer"]), True)
        return next(iter(containers), None)

    def get_current_shadow_root_container(self):
        """
        [Internal]

        An internal method designed to get the current container.
        Returns the BeautifulSoup object that represents this container or NONE if nothing is found.

        :return: The container object
        :rtype: BeautifulSoup object

        Usage:

        >>> # Calling the method:
        >>> container = self.get_current_container()
        """
        soup = self.get_current_DOM()
        containers = self.zindex_sort(soup.select("wa-dialog"), True)
        return next(iter(containers), None)

    def get_all_containers(self):
        """
        [Internal]

        An internal method designed to get all containers.
        Returns the List of BeautifulSoup object that represents this containers or NONE if nothing is found.

        :return: List containers object
        :rtype: List BeautifulSoup object

        Usage:

        >>> # Calling the method:
        >>> container = self.get_all_containers()
        """
        soup = self.get_current_DOM()
        containers = soup.select(self.containers_selectors["AllContainers"])
        return containers

    def ClickTree(self, treepath, right_click=False, position=1, tree_number=0):
        """
        Clicks on TreeView component.

        :param treepath: String that contains the access path for the item separate by ">" .
        :type string: str
        :param right_click: Clicks with the right button of the mouse in the last element of the tree.
        :type string: bool
        :param tree_number: Tree position for cases where there is more than one tree on exibits.
        :type string: int

        Usage:

        >>> # Calling the method:
        >>> oHelper.ClickTree("element 1 > element 2 > element 3")
        >>> # Right Click example:
        >>> oHelper.ClickTree("element 1 > element 2 > element 3", right_click=True)
        """
        self.click_tree(treepath, right_click, position, tree_number)

    def click_tree(self, treepath, right_click, position, tree_number):
        """
        [Internal]
        Take treenode and label to filter and click in the toggler element to expand the TreeView.
        """

        logger().info(f"Clicking on Tree: {treepath}")

        hierarchy = None

        position -= 1
        tree_number = tree_number-1 if tree_number > 0 else 0

        labels = list(map(str.strip, re.split(r'(?<!-)>', treepath)))
        labels = list(filter(None, labels))
        dialog_layers = self.check_layers('wa-dialog')

        for row, label in enumerate(labels):

            label = re.sub(r'[ ]{2,}', ' ', label).strip()

            self.wait_blocker()

            last_item = True if row == len(labels) - 1 else False

            success = False

            try_counter = 0

            label_filtered = label.lower().strip()

            try:
                if self.tree_base_element and label_filtered == self.tree_base_element[0]:
                    self.scroll_to_element(self.tree_base_element[1])
            except:
                pass

            endtime = time.time() + self.config.time_out

            while ((time.time() < endtime) and (try_counter < 3 and not success)):

                tree_node = self.find_tree_bs(label_filtered, tree_number)

                if self.webapp_shadowroot():
                    tree_node_filtered = list(filter(lambda x: not x.get_attribute('hidden'), tree_node))
                else:
                    tree_node_filtered = list(
                        filter(lambda x: not x.find_parents(class_='hidden'), tree_node))

                elements = list(
                    filter(lambda x: label_filtered in x.text.lower().strip() and self.element_is_displayed(x),
                           tree_node_filtered))

                if elements:

                    if position:
                        elements = elements[position] if len(elements) >= position + 1 else next(iter(elements))
                        if hierarchy:
                            elements = elements if elements.attrs['hierarchy'].startswith(hierarchy) and elements.attrs[
                                'hierarchy'] != hierarchy else None
                    else:
                        elements = list(filter(lambda x: self.element_is_displayed(x), elements))

                        if hierarchy:
                            if not self.webapp_shadowroot():
                                elements = list(filter(lambda x: x.attrs['hierarchy'].startswith(hierarchy) and x.attrs[
                                    'hierarchy'] != hierarchy, elements))

                    for element in elements:
                        if not success:
                            if self.webapp_shadowroot():
                                element_class = self.driver.execute_script(
                                    f"return arguments[0].shadowRoot.querySelectorAll('.toggler, .lastchild, .data, label')",
                                    element)
                                if not element_class:
                                    element_class = self.driver.execute_script(
                                        f"return arguments[0].shadowRoot.querySelectorAll('.icon')", element)
                                if not element_class:
                                    if element.get_attribute('icon') != None:
                                        element_class = [element]
                            else:
                                element_class = next(iter(element.select(".toggler, .lastchild, .data")), None)

                                if "data" in element_class.get_attribute_list("class"):
                                    element_class = element_class.select("img, span")

                            for element_class_item in element_class:
                                if not success:
                                    try:
                                        if self.webapp_shadowroot(): # exclusive shadow_root condition
                                            element_click = lambda: element_class_item
                                        else:
                                            element_click = lambda: self.soup_to_selenium(element_class_item)

                                        if last_item:
                                            self.wait_blocker()
                                            if self.webapp_shadowroot():
                                                element_is_closed = lambda: element.get_attribute('closed') == 'true' or element.get_attribute('closed') == ''
                                                treenode_selected = lambda: self.treenode_selected(label_filtered, tree_number)
                                                click_try = 0
                                                is_element_acessible = lambda: not element_is_closed() if self.check_toggler(label_filtered, element) else treenode_selected()

                                                while click_try < 3 and not is_element_acessible():
                                                    self.scroll_to_element(element_click())
                                                    element_click().click()
                                                    click_try += 1

                                                success = self.check_hierarchy(label_filtered, False)
                                                
                                                if not success:
                                                    success = True if is_element_acessible() else False

                                                    # If dialog layers show up through last click
                                                    if not success and dialog_layers < self.check_layers('wa-dialog'):
                                                        success = True

                                                if success and right_click:
                                                    last_zindex = self.return_last_zindex()
                                                    current_zindex = last_zindex
                                                    
                                                    endtime_right_click = time.time() + self.config.time_out / 3
                                                    while time.time() < endtime_right_click and last_zindex <= current_zindex:
                                                        if self.webapp_shadowroot():
                                                            self.click(element_click(), enum.ClickType.SELENIUM,
                                                                    right_click)
                                                            current_zindex = self.return_last_zindex()
                                                        else:
                                                            self.send_action(action=self.click, element=element_click, right_click=right_click)
                                            else:
                                                self.scroll_to_element(element_click())
                                                element_click().click()
                                                if self.check_toggler(label_filtered, element):
                                                    success = self.check_hierarchy(label_filtered)
                                                    if success and right_click:
                                                        self.send_action(action=self.click, element=element_click, right_click=right_click)
                                                else:
                                                    if right_click:
                                                        self.send_action(action=self.click, element=element_click,
                                                                         right_click=right_click)
                                                    success = self.clicktree_status_selected(label_filtered)
                                        else:
                                            if self.webapp_shadowroot():
                                                self.tree_base_element = label_filtered, element_class_item
                                                element_is_closed = lambda: element.get_attribute('closed') == 'true' or element.get_attribute('closed') == '' or not self.treenode_selected(label_filtered, tree_number)
                                                self.scroll_to_element(element_click())

                                                click_try = 0
                                                while click_try < 3 and element_is_closed():
                                                    if element.get_attribute(
                                                            'closed') == 'true' or element.get_attribute(
                                                            'closed') == '':
                                                        element_click().click()
                                                    try:
                                                        element_closed_click = self.driver.execute_script(
                                                        f"return arguments[0].shadowRoot.querySelector('.toggler, .lastchild, .data')",
                                                        element_click())
                                                    except:
                                                        element_closed_click = None

                                                    if element_closed_click:
                                                        element_closed_click.click()

                                                    click_try += 1
                                            else:
                                                self.tree_base_element = label_filtered, self.soup_to_selenium(element_class_item)
                                                self.scroll_to_element(element_click())
                                                element_click().click()
                                            success = self.check_hierarchy(label_filtered)

                                        try_counter += 1
                                    except:
                                        pass

                                if not success:
                                    try:
                                        element_click = lambda: self.soup_to_selenium(element_class_item.parent)
                                        self.scroll_to_element(element_click())
                                        element_click().click()
                                        success = self.clicktree_status_selected(label_filtered) if last_item and not self.check_toggler(label_filtered) else self.check_hierarchy(label_filtered)
                                    except:
                                        pass

            if not last_item:
                treenode_selected = self.treenode_selected(label_filtered, tree_number)
                if treenode_selected:
                    if self.webapp_shadowroot():
                        hierarchy = treenode_selected.get_attribute('hierarchy')
                    else:
                        hierarchy = treenode_selected.attrs['hierarchy']

        if not success:
            self.log_error(f"Couldn't click on tree element {label}.")

    def find_tree_bs(self, label, tree_number):
        """
        [Internal]

        Search the label string in current container and return a treenode element.
        """

        tree_node = ""

        if self.webapp_shadowroot():
            self.wait_element(term=label, scrap_type=enum.ScrapType.MIXED, optional_term=".dict-ttree")
        else:
            self.wait_element(term=label, scrap_type=enum.ScrapType.MIXED, optional_term=".ttreenode, .data")

        endtime = time.time() + self.config.time_out

        while (time.time() < endtime and not tree_node):

            container = self.get_current_container()

            if self.webapp_shadowroot():
                tree = container.select("wa-tree")
                if len(tree) >= tree_number:
                    tree = tree[tree_number]
                    tree_node = self.driver.execute_script(f"return arguments[0].shadowRoot.querySelectorAll('wa-tree-node')", self.soup_to_selenium(tree))
            else:
                tree_node = container.select(".ttreenode")

        if not tree_node:
            self.log_error("Couldn't find tree element.")

        return(tree_node)

    def clicktree_status_selected(self, label_filtered, check_expanded=False):
        """
        [Internal]
        """
        success = None

        treenode_selected = self.treenode_selected(label_filtered)

        if not check_expanded:
            if treenode_selected:
                return True
            else:
                return False
        else:
            if self.webapp_shadowroot():
                tree_selected = self.find_shadow_element('span[class~=toggler]', treenode_selected, get_all=False)
                if self.find_shadow_element('span[class~=toggler]', treenode_selected, get_all=False):
                    return not treenode_selected.get_attribute('closed')
            else:
                tree_selected = next(iter(list(filter(lambda x: label_filtered == x.text.lower().strip(), treenode_selected))), None)
                if tree_selected.find_all_next("span"):
                    if "toggler" in next(iter(tree_selected.find_all_next("span"))).attrs['class']:
                        return "expanded" in next(iter(tree_selected.find_all_next("span")), None).attrs['class']
                else:
                    return False

    def check_toggler(self, label_filtered, element):
        """
        [Internal]
        """

        if self.webapp_shadowroot:
            return self.check_toggler_shadow(element)

        element_id = element.get_attribute_list('id')
        tree_selected = self.treenode_selected(label_filtered)

        if tree_selected:
            if tree_selected.find_all_next("span"):
                first_span = next(iter(tree_selected.find_all_next("span"))).find_parent('tr')
                if first_span:
                    if next(iter(element_id)) == next(iter(first_span.get_attribute_list('id'))):
                        try:
                            return "toggler" in next(iter(tree_selected.find_all_next("span")), None).attrs['class']
                        except:
                            return False
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False
        
    def check_toggler_shadow(self, element):
        """
        [Internal]
        """
        
        return True if self.find_shadow_element('span[class~=toggler]', element, get_all=False) else False


    def treenode_selected(self, label_filtered, tree_number=0):
        """
        [Internal]
        Returns a tree node selected by label
        """

        ttreenode = self.treenode(tree_number)

        if self.webapp_shadowroot():
            treenode_selected = list(filter(lambda x: "selected" in x.get_attribute('class') or x.get_attribute('selected'), ttreenode))
        else:
            treenode_selected = list(filter(lambda x: "selected" in x.attrs['class'], ttreenode))

        return next(iter(list(filter(lambda x: label_filtered == x.text.lower().strip(), treenode_selected))), None)

    def treenode(self, tree_number=0):
        """

        :return: treenode bs4 object
        """

        container = self.get_current_container()
        tr = []

        if self.webapp_shadowroot():
            bs_tree_node = container.select('wa-tree')
            if bs_tree_node and len(bs_tree_node) > tree_number:
                tr = self.driver.execute_script(f"return arguments[0].shadowRoot.querySelectorAll('wa-tree-node')", self.soup_to_selenium(bs_tree_node[tree_number]))
            return tr
        else:
            tr = container.select("tr")
            tr_class = list(filter(lambda x: "class" in x.attrs, tr))
            return list(filter(lambda x: "ttreenode" in x.attrs['class'], tr_class))

    def check_hierarchy(self, label, check_expanded=True):
        """

        :param label:
        :return: True or False
        """

        counter = 1

        node_check = None

        if self.webapp_shadowroot():
            while (counter <= 3 and not node_check):
                treenode_parent_id = self.treenode_selected(label)
                if treenode_parent_id:
                    treenode_parent_id = treenode_parent_id.get_attribute('id')
                    treenode = list(filter(lambda x: self.element_is_displayed(x), self.treenode()))
                    node_check = next(iter(list(filter(lambda x: treenode_parent_id == x.get_attribute('parentid'),
                                                       treenode))), None)
                counter += 1
        else:
            while (counter <= 3 and not node_check):

                treenode_parent_id = self.treenode_selected(label).attrs['id']

                treenode = list(filter(lambda x: self.element_is_displayed(x), self.treenode()))

                node_check = next(iter(list(filter(lambda x: treenode_parent_id == x.attrs['parentid'], treenode))), None)

                counter += 1

        return True if node_check else self.clicktree_status_selected(label, check_expanded)

    def GridTree(self, column, tree_path, right_click=False):
        """
        Clicks on Grid TreeView component.

        :param treepath: String that contains the access path for the item separate by ">" .
        :type string: str
        :param right_click: Clicks with the right button of the mouse in the last element of the tree.
        :type string: bool

        Usage:

        >>> # Calling the method:
        >>> oHelper.GridTree("element 1 > element 2 > element 3")
        >>> # Right GridTree example:
        >>> oHelper.GridTree("element 1 > element 2 > element 3", right_click=True)

        """

        endtime = time.time() + self.config.time_out

        tree_list = list(map(str.strip, tree_path.split(">")))
        last_item = tree_list.pop()

        grid_selectors = '.dict-tcbrowse' if self.webapp_shadowroot() else '.tcbrowse'

        while (time.time() < endtime and tree_list):

            len_grid_lines = self.expand_treeGrid(column, tree_list[0])

            grid = self.get_grid(grid_element=grid_selectors)

            self.wait_blocker()

            if self.lenght_grid_lines(grid) > len_grid_lines:
                tree_list.remove(tree_list[0])
            else:
                len_grid_lines = self.expand_treeGrid(column, tree_list[0])
                tree_list.remove(tree_list[0])

        grid = self.get_grid(grid_element=grid_selectors)
        column_index = self.search_column_index(grid, column)

        div = self.search_grid_by_text(grid, last_item, column_index)

        if div:
            if self.webapp_shadowroot():
                time.sleep(2)
                self.click((div), enum.ClickType.SELENIUM, right_click)
            else:
                self.wait_until_to(expected_condition="element_to_be_clickable", element=div, locator=By.XPATH)
                div_s = self.soup_to_selenium(div)
                time.sleep(2)
                self.click((div_s), enum.ClickType.SELENIUM, right_click)

    def expand_treeGrid(self, column, item):
        """
        [Internal]

        Search for a column and expand the tree
        Returns len of grid lines

        """

        grid_selectors = '.dict-tcbrowse' if self.webapp_shadowroot() else '.tcbrowse'

        grid = self.get_grid(grid_element = grid_selectors)
        column_index = self.search_column_index(grid, column)
        len_grid_lines = self.lenght_grid_lines(grid)
        div = self.search_grid_by_text(grid, item, column_index)

        if div:
            if self.webapp_shadowroot():
                div.click()
                ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                self.wait_gridTree(len_grid_lines, timeout=10)
            else:
                line = div.parent.parent
                td = next(iter(line.select('td')), None)
                self.expand_tree_grid_line(td)
                self.wait_gridTree(len_grid_lines)

        return len_grid_lines

    def expand_tree_grid_line(self, element_soup):
        """
        [Internal]
        Click on a column and send the ENTER key

        """
        self.wait_until_to(expected_condition="element_to_be_clickable", element = element_soup, locator = By.XPATH )
        element_selenium = lambda: self.soup_to_selenium(element_soup)
        element_selenium().click()
        self.wait_blocker()
        self.wait_until_to(expected_condition="element_to_be_clickable", element = element_soup, locator = By.XPATH )
        ActionChains(self.driver).send_keys(Keys.ENTER).perform()

    def wait_gridTree(self, n_lines, timeout=None):
        """
        [Internal]
        Wait until the GridTree line count increases or decreases.

        """

        timeout = self.config.time_out if not timeout else timeout

        grid_selectors = '.dict-tcbrowse' if self.webapp_shadowroot() else '.tcbrowse'

        endtime = time.time() + timeout
        grid = self.get_grid(grid_element=grid_selectors)

        while (time.time() < endtime and n_lines == self.lenght_grid_lines(grid) ):
            grid = self.get_grid(grid_element=grid_selectors)


    def search_grid_by_text(self, grid, text, column_index):
        """
        [Internal]
        Searches for text in grid columns
        Returns the div containing the text

        """
        if self.webapp_shadowroot():
            columns_list = self.find_shadow_element('td', self.soup_to_selenium(grid))
            element = next(iter(list(filter(lambda x: text.strip() == x.text.strip(), columns_list))), None)
            if element:
                return element

        else:
            columns_list = grid.select('td')

            columns_list_filtered = list(filter(lambda x: int(x.attrs['id']) == column_index  ,columns_list))
            div_list = list(map(lambda x: next(iter(x.select('div')), None)  ,columns_list_filtered))
            div = next(iter(list(filter(lambda x: (text.strip() == x.text.strip() and x.parent.parent.attrs['id'] != '0', div_list))), None))
            return div

    def lenght_grid_lines(self, grid):
        """
        [Internal]
        Returns the leght of grid.

        """

        grid_lines = None

        if self.webapp_shadowroot():

            grid_lines = lambda: self.find_shadow_element('tbody tr', self.soup_to_selenium(grid))
            before_texts = list(filter(lambda x: hasattr(x, 'text'), grid_lines()))
            before_texts = list(map(lambda x: x.text, before_texts))
            after_texts = []
            down_count = 0
            if grid_lines():
                self.send_action(action=self.click, element=lambda: next(iter(grid_lines())), click_type=3)
                ActionChains(self.driver).key_down(Keys.SHIFT).key_down(Keys.HOME).perform()
                endtime = time.time() + self.config.time_out
                while endtime > time.time() and next(reversed(after_texts), None) != next(reversed(before_texts), None):

                    after_texts = list(map(lambda x: x.text, grid_lines()))
                    for i in after_texts:
                        if i not in before_texts:
                            before_texts.append(i)

                    ActionChains(self.driver).key_down(Keys.PAGE_DOWN).perform()
                    down_count += 1
                    self.wait_blocker()

                    after_texts = list(map(lambda x: x.text, grid_lines()))

                ActionChains(self.driver).key_down(Keys.SHIFT).key_down(Keys.HOME).perform()

                return len(before_texts)
        else:
            return len(grid.select("tbody tr"))

        return len(grid_lines)

    def TearDown(self):
        """
        Closes the webdriver and ends the test case.

        Usage:

        >>> #Calling the method
        >>> self.TearDown()
        """

        if self.config.new_log:
            self.execution_flow()

        if self.config.smart_test:
            self.log.log_exec_file()

        if self.config.log_info_config:
            self.set_log_info_config()

        webdriver_exception = None
        timeout = 1500
        string = self.language.codecoverage #"Aguarde... Coletando informacoes de cobertura de codigo."
        term = '.dict-tmenu' if self.webapp_shadowroot() else '.tmenu'

        if self.config.coverage:
            try:
                self.driver_refresh()
            except WebDriverException as e:
                logger().exception(str(e))
                webdriver_exception = e

            if 'POUILogin' in self.config.json_data and self.config.json_data['POUILogin'] == True:
                self.config.poui_login = True
            else:
                self.config.poui_login = False

            if webdriver_exception:
                message = f"Wasn't possible execute self.driver.refresh() Exception: {next(iter(webdriver_exception.msg.split(':')), None)}"
                logger().debug(message)

            if not webdriver_exception and not self.tss:
                self.user_screen()
                self.environment_screen()
                endtime = time.time() + self.config.time_out
                while (time.time() < endtime and (
                not self.element_exists(term=term, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body"))):
                    self.close_screen_before_menu()
                self.Finish()
            elif not webdriver_exception:
                self.SetupTSS(self.config.initial_program, self.config.environment )
                self.SetButton(self.language.exit)
                self.SetButton(self.language.yes)

        if len(self.log.table_rows[1:]) > 0 and not self.log.has_csv_condition():
            self.log.generate_log()

        if self.config.num_exec:
            if not self.num_exec.post_exec(self.config.url_set_end_exec, 'ErrorSetFimExec'):
                self.restart_counter = 3
                self.log_error(f"WARNING: Couldn't possible send num_exec to server please check log.")

            if self.config.check_dump:
                self.check_dmp_file()

        try:
            self.driver.close()
        except Exception as e:
            logger().exception(f"Warning tearDown Close {str(e)}")

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
            if self.webapp_shadowroot():
                selector = "wa-panel"
            else:
                selector = "div"
            container_class = list(filter(lambda x: "class" in x.attrs, container.select(selector)))
            if list(filter(lambda x: class_remove in x.attrs['class'], container_class)):
                iscorrect = False
            if iscorrect:
                container_filtered.append(container)

        return container_filtered


    def filter_label_element(self, label_text, container, position, twebview=False):
        """
        [Internal]
        Filter and remove a specified character with regex, return only displayed elements if > 1.

        Usage:

        >>> #Calling the method
        >>> elements = self.filter_label_element(label_text, container)
        """

        elements = None
        position -= 1

        shadow_root = not twebview

        if self.webapp_shadowroot(shadow_root=shadow_root):
            sl_term = label_text
            regex = r"(<[^>]*>)?([\?\*\.\:]+)?"
            label_text =  re.sub(regex, '', label_text)

            wa_text_view = container.select('wa-text-view, wa-checkbox, wa-button, wa-tree')
            wa_text_view_filtered = list(filter(lambda x: hasattr(x, 'caption') and x.get('caption') and re.sub(regex, '', x['caption']).lower().strip().startswith(label_text.lower().strip()), wa_text_view))

            if len(wa_text_view_filtered) > 1:
                wa_text_view_filtered = list(filter(lambda x:  hasattr(x, 'caption') and x.get('caption') and re.sub(regex, '', x['caption']).lower().strip() == (label_text.lower().strip()), wa_text_view))

            if not wa_text_view_filtered:
                wa_text_view = container.select('label, span')
                wa_text_view_filtered = list(filter(lambda x: re.sub(regex, '', x.text).lower().strip() == label_text.lower().strip(), wa_text_view))
                if not wa_text_view_filtered:
                   wa_text_view_filtered= self.selenium_web_scrap(term=sl_term, container=container, optional_term='wa-radio, wa-tree, wa-tgrid')

            if wa_text_view_filtered and len(wa_text_view_filtered)-1 >= position:
                return [wa_text_view_filtered[position]]

            if container:
                elements = list(map(lambda x: self.find_first_wa_panel_parent(x),
                                container.find_all(text=re.compile(f"^{re.escape(label_text)}" + r"([\s\?:\*\.]+)?"))))
        else:
            elements = list(map(lambda x: self.find_first_div_parent(x), container.find_all(text=re.compile(f"^{re.escape(label_text)}" + r"([\s\?:\*\.]+)?"))))

        if elements:
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

    def element_is_displayed(self, element=None, twebview=False):
        """
        [Internal]

        """
        if type(element) == Tag:
            element_selenium = self.soup_to_selenium(element, twebview)
        else:
            element_selenium = element

        if isinstance(element, list):
            call_stack = list(filter(lambda x: 'webapp_internal.py' == x.filename.split(self.replace_slash('\\'))[-1], inspect.stack()))
            for n in call_stack: logger().debug(f'element_is_displayed Error: {str(n.function)}')
            element_selenium = next(iter(element),None)

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

        string = ""

        if string_left:
            string = string_left
        elif string_right:
            string = string_right

        labels = self.web_scrap(term=string, scrap_type=enum.ScrapType.MIXED,
                                optional_term=".tsay, .tgroupbox, wa-text-view, label",
                                main_container=self.containers_selectors["GetCurrentContainer"], check_help=False)

        if labels:
            if string:
                label = next(iter(list(filter(lambda x: string.lower() in x.text.lower(), labels))))
                return self.get_text_position(label.text, string_left, string_right)
            else:
                return next(iter(labels)).text

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

    def wait_smart_erp_environment(self):
        """
        [Internal]
        """
        content = False
        endtime = time.time() + self.config.time_out

        logger().debug("Waiting for SmartERP environment assembly")

        while not content and (time.time() < endtime):
            try:
                soup = self.get_current_DOM()

                content = True if next(iter(soup.select("img[src*='resources/images/parametersform.png']")), None) else False
            except AttributeError:
                pass

    def wait_until_to(self, expected_condition = "element_to_be_clickable", element = None, locator = None , timeout=False):
        """
        [Internal]

        This method is responsible for encapsulating "wait.until".
        """

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
        except StaleElementReferenceException as e:
            logger().exception(f"Element is stale, skipping...")
            pass

        if timeout:
            setattr(self.wait, '_timeout', self.config.time_out)


    def CheckHelp(self, text, button, text_help, text_problem, text_solution, verbosity):
        """
        Checks if some help screen is present in the screen at the time and takes an action.

        :param text: Text to be checked.
        :type text: str
        :param text_help: Only the help text will be checked.
        :type text_help: str
        :param text_problem: Only the problem text will be checked.
        :type text_problem: str
        :param text_solution: Only the solution text will be checked.
        :type text_solution: str
        :param button: Button to be clicked.
        :type button: str
        :param verbosity: Check the text with high accuracy.
        :type verbosity: bool

        Usage:

        >>> # Calling method to check all window text.
        >>> oHelper.CheckHelp("TK250CADRE Problema: Essa reclamação já foi informada anteriormente. Solução: Informe uma reclamação que ainda não tenha sido cadastrada nessa tabela.", "Fechar")
        >>> # Calling method to check help text only.
        >>> oHelper.CheckHelp(text_help="TK250CADRE", button="Fechar")
        >>> # Calling method to check problem text only.
        >>> oHelper.CheckHelp(text_problem="Problema: Essa reclamação já foi informada anteriormente.", button="Fechar")
        >>> # Calling method to check problem text only.
        >>> oHelper.CheckHelp(text_solution="Solução: Informe uma reclamação que ainda não tenha sido cadastrada nessa tabela.", button="Fechar")
        >>> # Calling the method to check only the problem text with high precision.
        >>> oHelper.CheckHelp(text_problem="Problema: Essa reclamação já foi informada anteriormente.", button="Fechar", verbosity=True)
        """

        text_help_extracted     = ""
        text_problem_extracted  = ""
        text_solution_extracted = ""
        text_extracted = ""
        regex = r"(<[^>]*>)"
        modal_is_closed = False

        if not button:
            button = self.get_single_button().text

        endtime = time.time() + self.config.time_out
        while(time.time() < endtime and (not text_extracted or not modal_is_closed)):

            logger().info(f"Checking Help on screen: {text}")
            # self.wait_element_timeout(term=text, scrap_type=enum.ScrapType.MIXED, timeout=2.5, step=0.5, optional_term=".tsay", check_error=False)
            if self.webapp_shadowroot():
                label_term = ".dict-tsay"
            else:
                label_term = ".tsay"
            self.wait_element_timeout(term=text_help, scrap_type=enum.ScrapType.MIXED, timeout=2.5, step=0.5,
                                      optional_term=label_term, check_error=False)
            container = self.get_current_container()
            container_filtered = container.select(label_term)
            container_text = ''
            for x in range(len(container_filtered)):
                if self.webapp_shadowroot():
                    container_text += re.sub(regex, ' ',container_filtered[x].get('caption')) + ' '
                else:
                    container_text += container_filtered[x].text + ' '

            try:
                if self.language.checkproblem in container_text:
                    text_help_extracted = container_text[
                                          container_text.index(self.language.checkhelp):container_text.index(
                                              self.language.checkproblem)]
                else:
                    text_help_extracted = container_text[container_text.index(self.language.checkhelp):]

                if self.language.checksolution in container_text:
                    text_problem_extracted = container_text[
                                             container_text.index(self.language.checkproblem):container_text.index(
                                                 self.language.checksolution)]
                else:
                    text_problem_extracted = container_text[container_text.index(self.language.checkproblem):]

                text_solution_extracted = container_text[container_text.index(self.language.checksolution):]
            except:
                pass

            if text_help:
                text = text_help
                text_extracted = text_help_extracted
            elif text_problem:
                text = text_problem
                text_extracted = text_problem_extracted
            elif text_solution:
                text = text_solution
                text_extracted = text_solution_extracted
            else:
                text_extracted = container_text

            if text_extracted:
                self.check_text_container(text, text_extracted, container_text, verbosity)
                self.SetButton(button, check_error=False)
                modal_is_closed = not self.wait_element_timeout(term=text, scrap_type=enum.ScrapType.MIXED, timeout=2, step=0.5,
                                                            optional_term=label_term, main_container=self.containers_selectors["AllContainers"], 
                                                            check_error=False)

        if not text_extracted or not modal_is_closed:
            self.log_error(f"Couldn't find: '{text}', text on display window is: '{container_text}'")

    def check_text_container(self, text_user, text_extracted, container_text, verbosity):
        if verbosity == False:
            if text_user.replace(" ","") in text_extracted.replace(" ",""):
                logger().info(f"Help on screen Checked: {text_user}")
                return
            else:
                logger().info(f"Couldn't find: '{text_user}', text on display window is: '{container_text}'")
        else:
            if text_user in text_extracted:
                logger().info(f"Help on screen Checked: {text_user}")
                return
            else:
                logger().info(f"Couldn't find: '{text_user}', text on display window is: '{container_text}'")

    def get_single_button(self):
        """
        [Internal]
        """
        container = self.get_current_container()
        buttons = container.select("button")
        button_filtered = next(iter(filter(lambda x: x.text != "", buttons)))
        if not button_filtered:
            self.log_error(f"Couldn't find button")
        return button_filtered

    def ClickMenuPopUpItem(self, label, right_click, position = 1):
        """
        Clicks on MenuPopUp Item based in a text

        :param text: Text in MenuPopUp to be clicked.
        :type text: str
        :param right_click: Button to be clicked.
        :type button: bool
        :param position: index item text
        :type position: int

        Usage:

        >>> # Calling the method.
        >>> oHelper.ClickMenuPopUpItem("Label")
        >>> # Calling the method using position.
        >>> oHelper.ClickMenuPopUpItem("Label", position = 2)
        """
        position -= 1

        self.wait_element(term=label, scrap_type=enum.ScrapType.MIXED, main_container="body", optional_term=".tmenupopup, wa-menu-popup-item")

        label = label.lower().strip()

        endtime = time.time() + self.config.time_out

        tmenupopupitem_filtered = ""

        while(time.time() < endtime and not tmenupopupitem_filtered):

            tmenupopupitem = self.tmenupopupitem()

            if tmenupopupitem:

                tmenupopupitem_displayed = list(filter(lambda x: self.element_is_displayed(x), tmenupopupitem))

                tmenupopupitem_filtered = list(filter(lambda x: x.get('caption').lower().replace('<u>', '').replace('</u>','').strip() and x['caption'].lower().replace('<u>', '').replace('</u>','').strip() == label, tmenupopupitem_displayed))
                if not tmenupopupitem_filtered:
                    tmenupopupitem_filtered = list(filter(lambda x: x.text.lower().strip() == label, tmenupopupitem_displayed))

                if tmenupopupitem_filtered and len(tmenupopupitem_filtered) -1 >= position:
                    tmenupopupitem_filtered = tmenupopupitem_filtered[position]

        if not tmenupopupitem_filtered:
            self.log_error(f"Couldn't find tmenupopupitem: {label}")

        tmenupopupitem_element = lambda: self.soup_to_selenium(tmenupopupitem_filtered)

        if right_click:
            self.click(tmenupopupitem_element(), right_click=right_click)
        else:
            self.click(tmenupopupitem_element())

    def tmenupopupitem(self):
        """

        :return:
        """

        soup = self.get_current_DOM()

        body = next(iter(soup.select("body")))

        return body.select(".tmenupopupitem, wa-menu-popup-item")

    def get_release(self):
        """
        Gets the current release of the Protheus.

        :return: The current release of the Protheus.
        :type: str

        Usage:

        >>> # Calling the method:
        >>> self.get_release()
        >>> # Conditional with method:
        >>> # Situation: Have a input that only appears in release greater than or equal to 12.1.023
        >>> if self.get_release() >= '12.1.023':
        >>>     self.click(element)
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

    def on_screen_enabled(self, elements):
        """
        [Internal]

        Returns a list if selenium displayed and enabled methods is True.
        """
        if elements:
            is_displayed = list(filter(lambda x: self.element_is_displayed(x), elements))

            return list(filter(lambda x: self.soup_to_selenium(x).is_enabled(), is_displayed))

    def update_password(self):
        """
        [Internal]
        Update the password in the Protheus password change request screen
        """
        container = self.get_current_container()
        if container and self.element_exists(term=self.language.change_password, scrap_type=enum.ScrapType.MIXED, main_container=".tmodaldialog, wa-dialog", optional_term=".tsay, wa-text-view"):
            user_login = self.GetValue(self.language.user_login)
            if user_login == self.config.user or self.config.user.lower() == "admin":
                self.SetValue(self.language.current_password, self.config.password)
                self.SetValue(self.language.nem_password, self.config.password)
                self.SetValue(self.language.confirm_new_password, self.config.password)
                self.SetButton(self.language.finish)
                self.wait_element(self.language.database, main_container=".twindow")

    def ClickListBox(self, text):
        """
        Clicks on Item based in a text in a window tlistbox

        :param text: Text in windows to be clicked.
        :type text: str

        Usage:

        >>> # Calling the method.
        >>> oHelper.ClickListBox("text")
        """

        self.wait_element(term='.tlistbox, .dict-tlistbox', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container=".tmodaldialog, wa-dialog")
        container = self.get_current_container()
        term = '.dict-tlistbox' if self.webapp_shadowroot() else '.tlistbox'

        tlist = container.select(term)

        if self.webapp_shadowroot():
            list_option = next(iter(list(map(lambda x: self.find_shadow_element('option', self.soup_to_selenium(x)), tlist))))
        else:
            list_option = next(iter(list(filter(lambda x: x.select('option'), tlist))))

        list_option_filtered = list(filter(lambda x: self.element_is_displayed(x), list_option))
        element = next(iter(filter(lambda x: x.text.strip() == text.strip(), list_option_filtered)), None)

        if self.webapp_shadowroot():
            element_selenium = element
        else:
            element_selenium = self.soup_to_selenium(element)
            self.wait_until_to(expected_condition="element_to_be_clickable", element = element, locator = By.XPATH )

        element_selenium.click()

    def ClickImage(self, img_name, double_click=False):
        """
        Clicks in an Image button. They must be used only in case that 'ClickIcon' doesn't  support.
        :param img_name: Image to be clicked.
        :type img_name: src

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickImage("img_name")
        >>> oHelper.ClickImage("img_name",double_click=True)
        """
        if self.webapp_shadowroot():
            term=".dict-tbtnbmp2"
        else:
            term="div.tbtnbmp > img, div.tbitmap > img"

        self.wait_element(term, scrap_type=enum.ScrapType.CSS_SELECTOR, main_container =  self.containers_selectors["ClickImage"])

        success = None
        endtime = time.time() + self.config.time_out

        while(time.time() < endtime and not success):

            img_list = self.web_scrap(term, scrap_type=enum.ScrapType.CSS_SELECTOR , main_container = self.containers_selectors["ClickImage"])
            if self.webapp_shadowroot():
                img_list_filtered = list(filter(lambda x: img_name == x.previous.get('caption'), img_list))
            else:
                img_list_filtered = list(filter(lambda x: img_name == self.img_src_filtered(x),img_list))
            img_soup = next(iter(img_list_filtered), None)

            if img_soup:
                    element_selenium = lambda: self.soup_to_selenium(img_soup)
                    self.set_element_focus(element_selenium())
                    self.wait_until_to(expected_condition="element_to_be_clickable", element = img_soup, locator = By.XPATH, timeout=True)
                    if double_click:
                        success = self.double_click(element_selenium())
                    else:
                        success = self.click(element_selenium())
        return success

    def ClickMenuFunctional(self,menu_name,menu_option):

        regex = r"•."

        if self.webapp_shadowroot():
            class_selector = '.dict-tpanel > .dict-tsay'
        else:
            class_selector = '.tpanel > .tsay'

        endtime = time.time() + self.config.time_out
        soup = self.get_current_DOM()
        class_menu_itens = soup.select(class_selector)

        if self.webapp_shadowroot():
            name_title = next(iter(list(filter(lambda x: x.get('caption') and x['caption'].lower().strip() == menu_name.lower().strip(), class_menu_itens))), None)
            text_name_title = name_title.get('caption')
        else:
            menu_titles = list(filter(lambda x: 'font-size: 16px' in x.attrs['style'], class_menu_itens))
            name_title = next(iter(list(filter(lambda x: menu_name == x.text, menu_titles))), None)
            text_name_title = name_title.string


        while ((time.time() < endtime) and re.sub(regex, '',text_name_title) != menu_option):
            name_title = name_title.nextSibling
            if self.webapp_shadowroot():
                text_name_title = name_title.get('caption')
            else:
                text_name_title = name_title.string

        self.click(self.soup_to_selenium(name_title))

        return

    def img_src_filtered(self, img_soup):

        """
        [Internal]
        Return an image source filtered.
        """

        img_src_string = self.soup_to_selenium(img_soup).get_attribute("src")
        return next(iter(re.findall('[\w\_\-]+\.', img_src_string)), None).replace('.','')

    def try_element_to_be_clickable(self, element):
        """
        Try excpected condition element_to_be_clickable by XPATH or ID
        """
        try:
            self.wait_until_to(expected_condition="element_to_be_clickable", element = element, locator = By.XPATH)
        except:
            if 'id' in element.find_parent('div').attrs:
                self.wait_until_to(expected_condition="element_to_be_clickable", element = element.find_previous("div").attrs['id'], locator = By.ID )
            else:
                pass

    def open_csv(self, csv_file, delimiter, column, header, filter_column, filter_value):
        """
        Returns a dictionary when the file has a header in another way returns a list
        The folder must be entered in the CSVPath parameter in the config.json. Ex:

        .. note::
            This method return data as a string if necessary use some method to convert data like int().

        >>> config.json
        >>> CSVPath : "C:\\temp"

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
            data = pd.read_csv(self.replace_slash(f"{self.config.csv_path}\\{csv_file}"), sep=delimiter, encoding='latin-1', on_bad_lines="error", header=has_header, index_col=False, dtype=str)
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

    def send_action(self, action = None, element = None, value = None, right_click=False, click_type=None, wait_change=True):
        """

        Sends an action to element and compare it object state change.

        :param action: selenium function as a reference like click, actionchains or send_keys.
        :param element: selenium element as a reference
        :param value: send keys value
        :param right_click: True if you want a right click
        :param click_type: ClickType enum. 1-3 types- **Default:** None
        :type click_type: int
        :return: True if there was a change in the object
        """

        twebview = True if self.config.poui_login else False

        soup_before_event = self.get_current_DOM(twebview=twebview)
        soup_after_event = soup_before_event

        parent_classes_before = self.get_active_parent_class(element)
        parent_classes_after = parent_classes_before

        classes_before = ''
        classes_after = classes_before

        if element:
            classes_before = self.get_selenium_attribute(element(), 'class')
            classes_after = classes_before

        self.wait_blocker()
        soup_select = None

        main_click_type = click_type

        click_type = 1 if not main_click_type else click_type

        endtime = time.time() + self.config.time_out
        try:
            while ((time.time() < endtime) and (soup_before_event == soup_after_event) and (parent_classes_before == parent_classes_after) and (classes_before == classes_after) ):
                logger().debug(f"Trying to send action")
                if right_click:
                    soup_select = self.get_soup_select(".tmenupopupitem, wa-menu-popup-item")
                    if not soup_select:
                        action(element(), right_click=right_click)
                        self.wait_blocker()
                elif value:
                    action(element(), value)
                elif element:
                    self.set_element_focus(element())
                    action(click_type=enum.ClickType(click_type), element=element())
                elif action:
                    action()

                if soup_select:
                    soup_after_event = soup_select
                elif soup_select == []:
                    soup_after_event = soup_before_event
                else:
                    soup_after_event = self.get_current_DOM(twebview=twebview)

                parent_classes_after = self.get_active_parent_class(element)

                if element:
                    classes_after = self.get_selenium_attribute(element(), 'class')

                click_type = click_type+1 if not main_click_type else click_type

                if click_type > 3:
                    click_type = 1

                if not wait_change:
                    return True
                time.sleep(1)

        except Exception as e:
            if self.config.smart_test or self.config.debug_log:
                logger().debug(f"Warning Exception send_action {str(e)}")
            return False

        if self.config.smart_test or self.config.debug_log:
            logger().debug(f"send_action method result = {soup_before_event != soup_after_event}")
            logger().debug(f'send_action selenium status: {parent_classes_before != parent_classes_after}')
        return soup_before_event != soup_after_event


    def get_selenium_attribute(self, element, attribute):
        try:
            return element.get_attribute(attribute)
        except StaleElementReferenceException:
            return None


    def get_active_parent_class(self, element=None):
        """
        Returns class list of an element's parent
        """
        try:
            if element:
                parent_sl = element().parent.switch_to.active_element
                if parent_sl:
                    sl_classes = list(map(lambda x: x.get_attribute('class'), self.find_shadow_element('div', parent_sl))) if self.find_shadow_element('div', parent_sl) else None
                    return sl_classes
            return
        except Exception as e:
            if self.config.smart_test or self.config.debug_log:
                logger().exception(f"Warning Exception get_active_parent_class: {str(e)}")


    def image_compare(self, img1, img2):
        """
        Returns differences between 2 images in Gray Scale.

        :param img1: cv2 object.
        :param img2: cv2 object
        :return: Mean Squared Error (Matching error) between the images.
        """
        h, w = img1.shape
        diff = cv2.subtract(img1, img2)
        err = nump.sum(diff**2)
        mse = err/(float(h*w))
        return mse, diff

    def get_soup_select(self, selector):
        """
        Get a soup select object.

        :param selector: Css selector
        :return: Return a soup select object
        """

        twebview = True if self.config.poui_login else False

        soup = self.get_current_DOM(twebview=twebview)

        return soup.select(selector)

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
                self.replace_slash(f'We created a "auto" based in current file in "{self.config.baseline_spool}\\{current_file}". please, if you dont have a base file, make a copy of auto and rename to base then run again.'))
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

        file = re.sub('auto', '', file)

        file_extension = file[-4:].lower()

        full_path = self.replace_slash(f'{self.config.baseline_spool}\\{file}')

        auto_file_path = self.replace_slash(f'{self.config.baseline_spool}\\{next(iter(file.split(".")))}auto{file_extension}')

        if pathlib.Path(f'{auto_file_path}').exists():
            return auto_file_path

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

            emissao = re.search(r'('+self.language.issued+': )(?:(\d{2}-\d{2}-\d{4}))', line)

            dtref = re.search(r'('+self.language.ref_dt+': )(?:(\d{2}-\d{2}-\d{4}))', line)

            hora = re.search(r'('+self.language.time+'\.\.\.: )(?:(\d{2}:\d{2}:\d{2}))', line)

            hora_termino = re.search(r'('+self.language.end_time+': )(?:(\d{2}:\d{2}:\d{2}))', line)

            slash = re.search(r'(/)', line)

            if emissao:
                line = re.sub(emissao.group(0), self.language.issued+': 01-01-2015', line)
            if dtref:
                line = re.sub(dtref.group(0), self.language.ref_dt+': 01-01-2015', line)
            if hora:
                line = re.sub(hora.group(0), self.language.time+'...: 00:00:00', line)
            if hora_termino:
                line = re.sub(hora_termino.group(0), self.language.end_time+': 00:00:00', line)
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
                line = re.sub(width.group(0), 'ss:Width="100"', line)

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

        if self.config.poui_login:

            po_select = None

            endtime = time.time() + self.config.time_out
            while time.time() < endtime and not po_select:

                soup = lambda: self.get_current_DOM(twebview=True)
                po_select = next(iter(soup().select(".po-select-container")), None)

                if po_select:
                    span_label = lambda: next(iter(po_select.select('span')), None)
                    language = self.return_select_language()
                    endtime = time.time() + self.config.time_out
                    while time.time() < endtime and not span_label().text.lower() in language:
                        self.set_language_poui(language, po_select)

                else:
                    po_select = next(iter(soup().select("po-select")), None)

                    if po_select:
                        po_select_object = po_select.select('select')[0]

                        success = False
                        endtime = time.time() + self.config.time_out
                        while time.time() < endtime and not success:

                            languages = self.return_select_language()

                            for language in languages:
                                self.select_combo(po_select_object, language, index=True, shadow_root=False)
                                combo = self.return_combo_object(po_select_object, shadow_root=False)
                                text = combo.all_selected_options[0].text.lower()

                                if text == language:
                                    success = True
                                    break

        elif self.webapp_shadowroot():
            if self.element_exists(term='.dict-tcombobox', scrap_type=enum.ScrapType.CSS_SELECTOR,
                                   main_container="body",
                                   check_error=False):
                tcombobox = next(iter(self.web_scrap(term='.dict-tcombobox', scrap_type=enum.ScrapType.CSS_SELECTOR,
                                                     main_container='body')))
                selects = tcombobox
                languages = self.return_select_language()

                if languages:
                    for language in languages:
                        self.select_combo(selects, language, index=True)

        elif self.element_exists(term='.tcombobox', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body",
                                 check_error=False):

            tcombobox = next(
                iter(self.web_scrap(term='.tcombobox', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body')))
            selects = next(iter(tcombobox.select('select')))

            language = self.return_select_language()

            if language:
                self.select_combo(selects, language, index=True)

    def set_language_poui(self, language, container):

        icon = next(iter(list(filter(lambda x: "class" in x.attrs, container.select('span')))), None)
        if icon:
            icon_element = self.soup_to_selenium(icon)
            icon_element.click()

            container_ul = next(iter(container.select('ul')), None)
            if container_ul:
                item = next(iter(list(filter(lambda x: x.text.lower() in language, container_ul.select('li')))), None)
                element = self.soup_to_selenium(item)
                element.click()

    def return_select_language(self):

        language = None

        config_language = None

        config_language = self.config.language.lower().strip()

        if config_language == 'pt-br':
            language = ['português', 'portugués', 'portuguese']
        elif config_language == 'es-es':
            language = ['espanhol', 'español', 'spanish']
        elif config_language == 'en-us':
            language = ['inglês', 'inglés', 'english']
        elif config_language == 'ru-ru':
            language = ['русс.', 'русс.', 'русский']

        return language

    def get_grid_content(self, grid_number, grid_element):
        """

        :param grid_number:
        :param grid_element:
        :return:
        """

        grid_number -= 1 if grid_number > 0 else 0
        grid_list = []

        self.wait_element(self.grid_selectors['new_web_app']+f', {grid_element}',
                          scrap_type=enum.ScrapType.CSS_SELECTOR)
        grid = self.get_grid(grid_number, grid_element)

        if grid:
            if self.webapp_shadowroot():
                return self.find_shadow_element('tbody tr', self.soup_to_selenium(grid))
            else:
                return grid.select('tbody tr')


    def LengthGridLines(self, grid):
        """
        Returns the length of the grid.
        :return:
        """

        return len(grid)

    def find_child_element(self, term, element):
        """
        Waits and find for shadow elements in a beautiful soup object and returns a list of elements found

        >>> # Calling the method:
        >>> find_element(".dict-tmenuitem", bs4_element)
        """
        elements = []

        endtime = time.time() + self.config.time_out
        while not elements and time.time() < endtime:
            try:
                element_dom = self.soup_to_selenium(self.get_current_DOM()) if not element else self.soup_to_selenium(element)
                elements = self.driver.execute_script(f"return arguments[0].shadowRoot.querySelectorAll('{term}')", element_dom)
                elements = list(filter(lambda x: EC.element_to_be_clickable(x), elements))
            except:
                elements = self.driver.execute_script(f"return arguments[0].shadowRoot.querySelectorAll('{term}')", element)
                elements = list(filter(lambda x: EC.element_to_be_clickable(x), elements))
        if elements:
            return elements
        else:
            message = "Couldn't find child element."
            self.log_error(message)
            raise ValueError(message)


    def find_shadow_element(self, term, objects, get_all=True):

        elements = None
        if get_all:
            script = f"return arguments[0].shadowRoot.querySelectorAll('{term}')"
        else:
            script = f"return arguments[0].shadowRoot.querySelector('{term}')"

        try:
            elements = self.driver.execute_script(script, objects)
        except:
            pass
            
        return elements if elements else None

    def return_soup_by_selenium(self, elements, term, selectors):
        """

        :param elements:
        :param term:
        :return:
        """

        element_list = []

        for element in elements:
            shadow_root = next(iter(self.find_shadow_element(selectors, self.soup_to_selenium(element))), None)

            if shadow_root:
                if term.lower().strip() == shadow_root.text.lower().strip():
                    element_list.append(element)

        return element_list

    def check_dmp_file(self):
        """
        [Internal]
        """

        source_path = self.config.appserver_folder
        destination_path = self.config.destination_folder

        files = glob.glob(str(pathlib.Path(source_path, "*.dmp")))

        if files:
            for file in files:
                if file and self.current_test_suite not in self.test_suite:
                    logger().debug(f'.dmp file found: "{file}" in "{source_path}" moving to: "{destination_path}"')
                    shutil.move(file, destination_path)
                    self.test_suite.append(self.log.get_file_name('testsuite'))

    def restart_browser(self):
        """
        [Internal]
        """

        logger().info("Closing the Browser")
        self.driver.close()
        # self.close_process()
        logger().info("Starting the Browser")
        self.Start()

        try:
            line_parameters_url = f"{self.config.url}/?StartProg={self.config.initial_program}&Env={self.config.environment}"
            logger().debug(f"Get url with line parameters: {line_parameters_url}")
            self.get_url(line_parameters_url)
        except:
            pass

        time.sleep(10)

        logger().debug(f"Get url {self.config.url}")
        self.get_url()

    def close_process(self):
        """
        [Internal]
        """
        logger().debug('Closing process')
        try:
            if self.config.smart_test:
                os.system("taskkill /f /im firefox.exe")
            else:
                self.driver.quit()
            os.system("taskkill /f /im geckodriver.exe")
        except Exception as e:
            logger().debug(f'Close process error: {str(e)}')


    def GetLineNumber(self, values=[], columns=[], grid_number=0):
        """

        :param values: values composition expected in respective columns
        :param columns: reference columns used to get line
        :param grid_number:
        :return:
        """

        grid_number = grid_number-1 if grid_number > 0 else 0

        self.wait_blocker()

        if columns and len(columns) != len(values):
            self.log_error('Number of Values divergent from columns!')
            return

        success = False
        endtime = time.time() + self.config.time_out
        while(time.time() < endtime):

            containers = self.web_scrap(term=".tmodaldialog, wa-dialog", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
            container = next(iter(self.zindex_sort(containers, True)), None)

            if container:
                grid_term = self.grid_selectors['new_web_app']

                grids = container.select(grid_term)

                if grids:
                    grids = self.filter_active_tabs(grids)
                    grids = self.filter_displayed_elements(grids)

            if grids:
                headers = self.get_headers_from_grids(grids)
                values = list(map(lambda x: x.lower().strip() , values))
                columns_numbers = []

                if columns:
                    columns = list(map(lambda x: x.lower().strip(), columns))
                    difference = list(filter(lambda x: x not in list(headers[grid_number].keys()), columns))
                    columns_numbers = list(map(lambda x: headers[grid_number][x], columns))

                    if difference:
                        self.log_error(f"There's no have {difference} in the grid")
                        return

                if grid_number > len(grids):
                    self.log_error(self.language.messages.grid_number_error)

                grid = self.soup_to_selenium(grids[grid_number])
                rows = self.find_shadow_element('tbody tr', grid)

            if rows:
                for row in rows:
                    row_columns = self.driver.execute_script("return arguments[0].querySelectorAll('td')", row )

                    if len(row_columns) < len(columns) or not row_columns:
                        self.log_error(f"There are not number of columns present in the grid")
                        return

                    filtered_columns = [row_columns[x] for x in columns_numbers] if columns_numbers else row_columns
                    if filtered_columns:
                        if columns:
                            filtered_cells = list(filter(lambda x: x[1].text.lower().strip() == values[x[0]], enumerate(filtered_columns)))
                        else:
                            filtered_cells = list(filter(lambda x: x[1].text.lower().strip() in values, enumerate(filtered_columns)))
                        if len(filtered_cells) == len(values):
                            return rows.index(row)


    def AddProcedure(self, procedure, group):
        """
        Install/Desinstall a procedure in CFG to be set by SetProcedures method.

        :param procedure: The procedure to be clicked in edit screen.
        :type branch: str
        :param group: The group name.
        :type parameter: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.AddProcedure("01", "T1")
        """

        logger().info(f"AddProcedure: {procedure}")

        endtime = time.time() + self.config.time_out
        halftime = ((endtime - time.time()) / 2)

        self.procedures.append([procedure.strip(), group])


    def SetProcedures(self, is_procedure_install=True):
        """
        Sets the procedures in CFG screen. The procedures must be passed with calls for **AddProcedure** method.

        Usage:

        :param is_procedure_install: If True will install the procedure.
        :type branch: str

        >>> # Adding procedures:
        >>> oHelper.AddProcedure("19", "T1")
        >>> # Calling the method:
        >>> oHelper.SetProcedures(is_procedure_install=True)
        """

        self.procedure_screen(is_procedure_install)

    def procedure_screen(self, is_procedure_install):
        """
        [Internal]

        Internal method of SetProcedures.

        :type restore_backup: bool

        Usage:

        >>> # Calling the method:
        >>> self.parameter_screen(restore_backup=False)
        """
        procedure_codes = []
        procedure_groups = []
        exception = None
        stack = None
        success = False

        procedure_install = self.language.procedure_install 
        procedure_uninstall = self.language.procedure_uninstall 

        self.tmenu_screen = self.check_tmenu_screen()

        try:
            self.driver_refresh()
        except Exception as error:
            exception = error

        if not exception:
            if self.config.browser.lower() == "chrome":
                try:
                    self.wait_until_to( expected_condition = "alert_is_present" )
                    self.driver.switch_to_alert().accept()
                except:
                    pass

            self.Setup("SIGACFG", self.config.date, self.config.group, self.config.branch, save_input=False)
            self.SetLateralMenu(self.config.procedure_menu if self.config.procedure_menu else self.language.procedure_menu, save_input=False)

            self.wait_element(term=".ttoolbar, wa-toolbar, wa-panel, wa-tgrid", scrap_type=enum.ScrapType.CSS_SELECTOR)
            
            endtime = time.time() + self.config.time_out

            while(time.time() < endtime and not success):

                for procedure in self.procedures:
                    container = self.get_current_container()
                    procedure_codes.append(procedure[0])
                    procedure_groups.append(procedure[1])

                procedure_codes = list(set(procedure_codes))
                procedure_groups = list(set(procedure_groups))

                for group in procedure_groups:
                    self.ClickBox(self.language.code, group)
                    time.sleep(2)
                    ActionChains(self.driver).key_down(Keys.HOME).perform()   

                for code in procedure_codes:
                    self.ClickBox(self.language.code, code, grid_number=2)
                    time.sleep(2)
                    ActionChains(self.driver).key_down(Keys.HOME).perform()                   
                    
                procedure_buttons = container.select('wa-button')

                if is_procedure_install:
                    procedure_install_button = list(filter(lambda x: x.get("title") == procedure_install, procedure_buttons))[0]
                    self.click(self.soup_to_selenium(procedure_install_button))         
                else:
                    procedure_uninstall_button = list(filter(lambda x: x.get("title") == procedure_uninstall, procedure_buttons))[0]
                    self.click(self.soup_to_selenium(procedure_uninstall_button))

                self.SetButton(self.language.yes)            

                container = self.get_current_container()
                procedure_success = list(filter(lambda x: self.language.success in x.get("caption"), container.select("wa-text-view")))                            
                if procedure_success:
                    number_proc_success = procedure_success[0].get("caption").split(":")[1].strip()
                    if int(number_proc_success) == len(procedure_codes):
                        success = True
                        self.SetButton(self.language.close)
                            
            self.procedures = []
            time.sleep(1)

            if self.config.coverage:
                self.driver_refresh()
            else:
                self.Finish()

            self.Setup(self.config.initial_program, self.config.date, self.config.group, self.config.branch, save_input=not self.config.autostart)

            if not self.tmenu_screen:
                if ">" in self.config.routine:
                    self.SetLateralMenu(self.config.routine, save_input=False)
                else:
                    self.Program(self.config.routine)
        else:
            stack = next(iter(list(map(lambda x: x.function, filter(lambda x: re.search('tearDownClass', x.function), inspect.stack())))), None)
            if(stack and not stack.lower()  == "teardownclass"):
                self.restart_counter += 1
                self.log_error(f"Wasn't possible execute parameter_screen() method Exception: {exception}")


    def SetCalendar(self, day='', month='', year='', position=0):
        """
        Set date on Calendar without input field

        :param day: day disered
        :type day: str
        :param month: month disered
        :type month: str
        :param year: year disered
        :type year: str
        """

        logger().info('Setting date on calendar')

        self.wait_blocker()
        success = False

        self.wait_element(term=".dict-mscalend", scrap_type=enum.ScrapType.CSS_SELECTOR)

        endtime = time.time() + self.config.time_out/2
        while time.time() < endtime and not success:
            calendar = self.web_scrap(term=".dict-mscalend", scrap_type=enum.ScrapType.CSS_SELECTOR)
            if calendar:
                calendar = calendar[position]
                elem_calendar = self.soup_to_selenium(calendar)
                # setting year proccess
                if year:
                    year_header = next(iter(self.find_shadow_element('wa-datepicker-year', elem_calendar)))
                    year_select = next(iter(self.find_shadow_element('select', year_header)))
                    year_interface = lambda: self.return_selected_combo_value(year_select, locator=True)
                    self.select_combo(year_select, year, index=True, locator=True)
                # setting month proccess
                if month:
                    if int(month) >= 1 and int(month) <= 12:
                        month = int(month) - 1
                        month_header = next(iter(self.find_shadow_element('wa-datepicker-month', elem_calendar)))
                        month_select = next(iter(self.find_shadow_element('select', month_header)))
                        month_combo = self.return_combo_object(month_select, locator=True)
                        month_combo.select_by_index(str(month))
                    else:
                        return self.log_error(f"Month {month} doesn't exist")
                # setting day proccess
                if day:
                    days_body = next(iter(self.find_shadow_element('wa-datepicker-body', elem_calendar)))
                    days_elements = self.find_shadow_element('wa-datepicker-day', days_body)
                    filtered_day = next(iter(list(filter(lambda x: x.get_attribute('day') == day, days_elements))),None)
                    if filtered_day:
                        click_try = time.time() + 20
                        day_selected = lambda: True if filtered_day.get_attribute(
                            'selected') else False
                        while not day_selected() and time.time() < click_try:
                            self.click(filtered_day)
                        if filtered_day and month_combo and year_interface():
                            success = filtered_day.get_attribute('day') == day and month_combo.options.index(month_combo.first_selected_option) == month and year_interface() == year

    def check_release_newlog(self):
        return self.log.release and self.config.new_log

    def log_error_newlog(self):
        self.log_error('Please check config.json key "Release".It is necessary to generate the log on the dashboard. ex: "Release": "12.1.2310" ')


    def set_schedule(self, schedule_status):
        """Access de Schedule settings and Start run all itens

        """

        exception = None
        service_status = False
        schedule_run = 'Iniciar Todos Serviços' if schedule_status else 'Parar Todos Serviços'
        service_curr_status = 'Iniciado' if schedule_status else 'Parado'
        self.tmenu_screen = self.check_tmenu_screen()

        try:
            self.driver_refresh()
        except Exception as error:
            exception = error

        if not exception:
            if self.config.browser.lower() == "chrome":
                try:
                    self.wait_until_to( expected_condition = "alert_is_present" )
                    self.driver.switch_to_alert().accept()
                except:
                    pass

            #Access Schedule environment
            self.Setup("SIGACFG", self.config.date, self.config.group, self.config.branch, save_input=False)
            self.SetLateralMenu(self.language.schedule_menu, save_input=False)

            #Wait show grid
            self.wait_element_timeout(term=self.grid_selectors["new_web_app"], scrap_type=enum.ScrapType.CSS_SELECTOR,
                                      timeout= self.config.time_out/2,
                                      main_container='body')

            endtime = time.time() + self.config.time_out/2
            while time.time() < endtime and not service_status:
                grid_rows = self.get_grid_content(0, self.grid_selectors["new_web_app"])
                if grid_rows:
                    stoped_itens = list(filter(lambda x: not service_curr_status in x.text, grid_rows))
                    if stoped_itens:
                        self.ClickIcon(schedule_run)
                    self.ClickIcon('Atualizar')
                    service_changed = list(filter(lambda x: service_curr_status in x.text, grid_rows))
                    if service_changed:
                        service_status = True

            logger().info(f"Schedule: {service_curr_status}")
            if not service_status:
                self.log_error("Schedule culdn't start")

            self.driver.get(self.config.url)
            self.Setup(self.config.initial_program, self.config.date, self.config.group,
                       self.config.branch, save_input=not self.config.autostart)

            if not self.tmenu_screen:
                if ">" in self.config.routine:
                    self.SetLateralMenu(self.config.routine, save_input=False)
                else:
                    self.Program(self.config.routine)

            self.tmenu_screen = None


    def get_container_selector(self, selector):

        container = self.get_current_container()

        return container.select(selector)


    def query_execute(self, query, database_driver, dbq_oracle_server, database_server, database_port, database_name, database_user, database_password):
        """Execute a query in a database
        """
        base_database = BaseDatabase()
        try:
            return base_database.query_execute(query, database_driver, dbq_oracle_server, database_server, database_port, database_name, database_user, database_password)
        except Exception as e:
            self.log_error(f"Error in query_execute: {str(e)}")


    def set_mock_route(self, route, sub_route, registry):
        """Set up mock server ip on appserver.ini file
        """
        self.mock_route = route + sub_route
        logger().info(f'"{self.mock_route}" route Was seted')

        if registry:
            if self.config.appserver_folder:
                config = configparser.ConfigParser()
                appserver_file = self.replace_slash(f'{self.config.appserver_folder}\\appserver.ini')

                try:
                    logger().info(f'Reading .ini file...')
                    config.read(appserver_file)

                    if config.has_section(self.config.environment):
                        registry_endpoints = {
                            "fw-tf-registry-endpoint": f"{self.get_route_mock()}/registry",
                            "fw-tf-rac-endpoint": f"{self.get_route_mock()}",
                            "fw-tf-platform-endpoint": f"{self.get_route_mock()}",
                        }

                        for key, value in registry_endpoints.items():
                            if config.has_option(self.config.environment, key):
                                if not self.mock_counter:
                                    if key == "fw-tf-registry-endpoint" and not self.registry_endpoint:
                                        self.registry_endpoint = config.get(self.config.environment, key)
                                    elif key == "fw-tf-rac-endpoint" and not self.rac_endpoint:
                                        self.rac_endpoint = config.get(self.config.environment, key)
                                    elif key == "fw-tf-platform-endpoint" and not self.platform_endpoint:
                                        self.platform_endpoint = config.get(self.config.environment, key)
                                config.set(self.config.environment, key, value)
                            else:
                                config.set(self.config.environment, key, value)

                        with open(appserver_file, "w", encoding="utf-8") as configfile:
                            config.write(configfile)
                            configfile.flush()
                            configfile.close()

                        self.mock_counter += 1

                        logger().info(f'Endpoints has been updated in .ini file!')
                except:
                    logger().info(f"it wasn't possible to read .ini file. Please Check it")


            else:
                logger().info(f"AppServerFolder key not defined. Please check config.json file")


    def get_route_mock(self):
        """Set up mock server ip on appserver.ini file
        """
        url = self.config.server_mock + self.mock_route
        return re.sub(r'(?<!:)//+', '/', url)


    def rest_resgistry(self):
        """restore registry keys on appserver.ini file
        """

        if self.platform_endpoint:
            registry_endpoints = {
                "fw-tf-registry-endpoint": f"{self.registry_endpoint}",
                "fw-tf-rac-endpoint": f"{self.rac_endpoint}",
                "fw-tf-platform-endpoint": f"{self.platform_endpoint}",
            }

            config = configparser.ConfigParser()
            appserver_file = self.replace_slash(f'{self.config.appserver_folder}\\appserver.ini')

            config.read(appserver_file)

            for key, value in registry_endpoints.items():
                if config.has_option(self.config.environment, key):
                    config.set(self.config.environment, key, value)

            with open(appserver_file, "w") as configfile:
                config.write(configfile)
                configfile.close()

            logger().info(f'Endpoints has been restored in .ini file.')

