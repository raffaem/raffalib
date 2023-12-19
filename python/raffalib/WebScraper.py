#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

import time
import logging
from typing import Optional
from pathlib import Path
import base64

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, NoSuchElementException
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.print_page_options import PrintOptions

from .EWebBrowser import EWebBrowser

class RaffaWebScraper():
    
    def __init__(self,
                 browser_app:EWebBrowser=EWebBrowser.FIREFOX,
                 headless_browser:bool=False,
                 geckodriver_path:Optional[Path]=None,
                 firefox_profile_path:Optional[Path]=None,
                 chromedriver_path:Optional[Path]=None,
                 log_path:Optional[Path]=None,
                 download_path:Optional[Path]=None):

        self.browser = None

        if browser_app == EWebBrowser.FIREFOX:
            logging.info("Initializing Firefox browser")
            options = webdriver.FirefoxOptions()
            if download_path:
                # See: https://stackoverflow.com/a/69974916/1719931
                # See: https://kb.mozillazine.org/About:config_entries
                options.set_preference("browser.download.folderList", 2)
                options.set_preference("browser.download.manager.showWhenStarting", False)
                options.set_preference("browser.download.dir", str(download_path.resolve()))
                #options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")
            if headless_browser:
                options.add_argument('--headless')
            if firefox_profile_path:
                options.profile = webdriver.FirefoxProfile(firefox_profile_path)
            service = webdriver.FirefoxService(executable_path=geckodriver_path, log_path=log_path)
            self.browser = webdriver.Firefox(options=options, service=service)
        elif browser_app == EWebBrowser.CHROME:
            logging.info("Initializing Chrome browser")
            options = webdriver.ChromeOptions()
            if headless_browser:
                options.add_argument('--headless')
            service = webdriver.ChromeService(executable_path=chromedriver_path, log_path=log_path)
            self.browser = webdriver.Chrome(options=options, service=service)
        else:
            raise Exception(f"Unknown value for browser_app={browser_app}")
        self.browser.maximize_window()

    def __del__(self):
        self.close()

    def close(self):
        if self.browser:
            try:
                self.browser.close()
            except ConnectionRefusedError:
                logging.error("Intercepted ConnectionRefusedError. Browser closed manually?")
            self.browser = None

    # BUTTONS

    def my_click(self, locator, timeout, starting_element=None):
        el = self.wait_element_to_be_clickable(locator=locator, timeout=timeout, starting_element=starting_element)
        el.click()
        return el
    
    def my_click_xpath(self, xpath, timeout=5, starting_element=None):
        locator = (By.XPATH, xpath)
        return self.my_click(locator=locator,
                             timeout=timeout,
                             starting_element=starting_element)
    
    def my_click_css(self, css, timeout=5, starting_element=None):
        locator = (By.CSS_SELECTOR, css)
        return self.my_click(locator=locator,
                     timeout=timeout,
                     starting_element=starting_element)

    # WAITS

    # WAITS - CLICKABILITY

    def wait_element_to_be_clickable(self, locator, timeout=5, starting_element=None):
        if not starting_element:
            starting_element = self.browser
        cond = EC.element_to_be_clickable(locator)
        try:
            el = WebDriverWait(starting_element, timeout).until(cond)
        except TimeoutException as e:
            msg = "Timed out waiting for element to be clickable\n"
            msg += f"locator={locator}\n"
            msg += f"timeout={timeout}\n"
            msg += f"starting_element={starting_element}"
            logging.error(msg)
            raise e
        return el

    def wait_element_to_be_clickable_css(self, css, timeout=5, starting_element=None):
        locator = (By.CSS_SELECTOR, css)
        return self.wait_element_to_be_clickable(locator=locator,
                                                 timeout=timeout,
                                                 starting_element=starting_element)

    def wait_element_to_be_clickable_xpath(self, xpath, timeout=5, starting_element=None):
        locator = (By.XPATH, xpath)
        return self.wait_element_to_be_clickable(locator=locator,
                                                 timeout=timeout,
                                                 starting_element=starting_element)

    # WAITS - INVISIBILITY - ALL

    def wait_invisibility_of_all_elements(self, locator, timeout=5):
        try:
            cond_appear = EC.visibility_of_all_elements_located(locator)
            return WebDriverWait(self.browser, timeout).until_not(cond_appear)
        except TimeoutException as e:
            msg = "TimeoutException while waiting for all elements to become invisible:\n"
            msg += f"locator={locator}\n"
            msg += f"timeout={timeout}"
            logging.error(msg)
            raise e
        except UnexpectedAlertPresentException as e:
            msg = "UnexpectedAlertPresentException while waiting for all elements to become invisible:\n"
            msg += f"locator={locator}\n"
            msg += f"timeout={timeout}"
            logging.error(msg)
            raise e

    def wait_invisibility_of_all_elements_xpath(self, xpath, timeout=5):
        locator = (By.XPATH, xpath)
        return self.wait_invisibility_of_all_elements(locator, timeout)

    def wait_invisibility_of_all_elements_css(self, css, timeout=5):
        locator = (By.CSS_SELECTOR, css)
        return self.wait_invisibility_of_all_elements(locator, timeout)

    # WAITS - INVISIBILITY - ANY

    def wait_invisibility_of_any_elements(self, locator, timeout=5):
        try:
            cond_appear = EC.visibility_of_any_elements_located(locator)
            return WebDriverWait(self.browser, timeout).until_not(cond_appear)
        except TimeoutException as e:
            msg = "TimeoutException while waiting for all elements to become invisible:\n"
            msg += f"locator={locator}\n"
            msg += f"timeout={timeout}"
            logging.error(msg)
            raise e
        except UnexpectedAlertPresentException as e:
            msg = "UnexpectedAlertPresentException while waiting for all elements to become invisible:\n"
            msg += f"locator={locator}\n"
            msg += f"timeout={timeout}"
            logging.error(msg)
            raise e

    def wait_invisibility_of_any_elements_xpath(self, xpath, timeout=5):
        locator = (By.XPATH, xpath)
        return self.wait_invisibility_of_any_elements(locator, timeout)

    def wait_invisibility_of_any_elements_css(self, css, timeout=5):
        locator = (By.CSS_SELECTOR, css)
        return self.wait_invisibility_of_any_elements(locator, timeout)

    # WAITS - VISIBILITY - ALL

    def wait_visibility_of_all_elements(self, locator, timeout=5):
        try:
            cond_appear = EC.visibility_of_all_elements_located(locator)
            return WebDriverWait(self.browser, timeout).until(cond_appear)
        except TimeoutException:
            msg = "TimeoutException while waiting for any elements to become visible:\n"
            msg += f"locator={locator}\n"
            msg += f"timeout={timeout}"
            logging.error(msg)
            raise Exception(msg)
        except UnexpectedAlertPresentException:
            msg = "UnexpectedAlertPresentException while waiting for any elements to become visible:\n"
            msg += f"locator={locator}\n"
            msg += f"timeout={timeout}"
            logging.error(msg)
            raise Exception(msg)

    def wait_visibility_of_all_elements_xpath(self, xpath, timeout=5):
        locator = (By.XPATH, xpath)
        return self.wait_visibility_of_all_elements(locator, timeout)

    def wait_visibility_of_all_elements_css(self, css, timeout=5):
        locator = (By.CSS_SELECTOR, css)
        return self.wait_visibility_of_all_elements(locator, timeout)

    # WAITS - VISIBILITY - ANY
    
    def wait_visibility_of_any_elements(self, locator, timeout=5):
        try:
            cond_appear = EC.visibility_of_any_elements_located(locator)
            return WebDriverWait(self.browser, timeout).until(cond_appear)
        except TimeoutException:
            msg = "TimeoutException while waiting for any elements to become visible:\n"
            msg += f"locator={locator}\n"
            msg += f"timeout={timeout}"
            logging.error(msg)
            raise Exception(msg)
        except UnexpectedAlertPresentException:
            msg = "UnexpectedAlertPresentException while waiting for any elements to become visible:\n"
            msg += f"locator={locator}\n"
            msg += f"timeout={timeout}"
            logging.error(msg)
            raise Exception(msg)
    
    def wait_visibility_of_any_elements_xpath(self, xpath, timeout=5):
        locator = (By.XPATH, xpath)
        return self.wait_visibility_of_any_elements(locator, timeout)
    
    def wait_visibility_of_any_elements_css(self, css, timeout=5):
        locator = (By.CSS_SELECTOR, css)
        return self.wait_visibility_of_any_elements(locator, timeout)

    # WAITS - POPUP
    
    def wait_popup(self, locator, timeout_appear=10, timeout_disappear=60*60, fail_if_not_appear=True):
        # Wait for popup to appear
        logging.debug("Waiting for popup to appear")
        try:
            self.wait_visibility_of_any_elements(locator, timeout=timeout_appear)
        except Exception as e:
            if fail_if_not_appear:
                raise e
            else:
                logging.debug("Failed to appear, continuing")
        else:
            logging.debug("Popup appeared")
        # Wait for popup to disappear
        logging.debug("Waiting for popup to disappear")
        self.wait_invisibility_of_any_elements(locator, timeout=timeout_disappear)
        logging.debug("Popup disappeared")
        return True
    
    def wait_popup_css(self, css,
                       timeout_appear=5, timeout_disappear=60*60,
                       fail_if_not_appear=True):
        locator = (By.CSS_SELECTOR, css)
        return self.wait_popup(locator, timeout_appear, timeout_disappear, fail_if_not_appear)
    
    def wait_popup_xpath(self, xpath,
                         timeout_appear=5, timeout_disappear=60*60,
                         fail_if_not_appear=True):
        locator = (By.XPATH, xpath)
        return self.wait_popup(locator, timeout_appear, timeout_disappear, fail_if_not_appear)
    
    # PAGE SCROLL

    def scroll_by(self, value):
        self.browser.execute_script(f"window.scrollBy(0,{value})")
    
    def scroll_down_all(self, max_scrolls=30, scroll_by_value=500, sleep_between_scrolls=2):
        """
        Scroll down the page all the way
        """
        old_page = self.browser.page_source
        for i in range(0,max_scrolls):
            logging.debug("Scrolling loop")
            scroll_by(driver, scroll_by_value)
            time.sleep(sleep_between_scrolls)
            new_page = driver.page_source
            if new_page != old_page:
                old_page = new_page
            else:
                break
        return True

    # INPUT FIELDS
    
    def fill_input_field(self, locator, value):
        try:
            el = self.browser.find_element(locator[0], locator[1])
        except NoSuchElementException:
            raise Exception(f"Cannot find element with XPath '{xpath}'")
        el.clear()
        el.send_keys(value)

    def fill_input_field_css(self, css, value):
        locator = (By.CSS_SELECTOR, css)
        return self.fill_input_field(locator, value)

    def fill_input_field_xpath(self, xpath, value):
        locator = (By.XPATH, xpath)
        return self.fill_input_field(locator, value)

    # SELECT BOXES
    
    def select_box_select_by_visible_text(self, locator, value):
        try:
            select_element = self.browser.find_element(locator[0], locator[1])
        except NoSuchElementException:
            raise Exception(f"Cannot find select box with XPath '{xpath}'")
        select = Select(select_element)
        select.select_by_visible_text(value)

    def select_box_select_by_visible_text_css(self, css, value):
        locator = (By.CSS_SELECTOR, css)
        return self.select_box_select_by_visible_text(locator, value)

    def select_box_select_by_visible_text_xpath(self, xpath, value):
        locator = (By.XPATH, xpath)
        return self.select_box_select_by_visible_text(locator, value)

    # TEXT AREA

    def insert_in_textarea(self, locator, text, timeout_visibility=20):
        el = self.wait_visibility_of_any_elements(locator, timeout_visibility)
        # Select first object found
        assert(len(el)==1)
        el = el[0]
        el.clear()
        el.send_keys(text)
        return el

    def insert_in_textarea_css(self, css, text, timeout_visibility=20):
        locator = (By.CSS_SELECTOR, css)
        return self.insert_in_textarea(locator, text, timeout_visibility)

    def insert_in_textarea_xpath(self, xpath, text, timeout_visibility=20):
        locator = (By.XPATH, xpath)
        return self.insert_in_textarea(locator, text, timeout_visibility)

    # WINDOW INTERACTION

    def get_active_tab(self) -> None:
        cwd = self.browser.current_window_handle
        return self.browser.window_handles.find(cwd)

    def get_tabs_count(self) -> None:
        return len(self.browser.window_handles)

    def goto_tab(self, tab_index:int) -> None:
        self.browser.switch_to.window(self.browser.window_handles[tab_index])

    def print_to(self, filepath:Path, page_width:float, page_height:float) -> None:
        print_options = PrintOptions()
        print_options.page_width = page_width
        print_options.page_height = page_height
        pdf = self.browser.print_page(print_options=print_options)
        pdf_bytes = base64.b64decode(pdf)
        with open(filepath, "wb") as fh:
            fh.write(pdf_bytes)
