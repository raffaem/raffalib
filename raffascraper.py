import time
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, NoSuchElementException
from selenium.webdriver.support.select import Select

def get_browser(browser_app="firefox", headless_browser=False,
                geckodriver_path=None, chromedriver_path=None,
                log_path=None):
    browser = None
    if browser_app == "firefox":
        options = webdriver.FirefoxOptions()
        if headless_browser:
            options.add_argument('--headless')
        service = webdriver.FirefoxService(executable_path=geckodriver_path, log_path=log_path)
        browser = webdriver.Firefox(options=options, service=service)
    elif browser_app == "chrome":
        options = webdriver.ChromeOptions()
        if headless_browser:
            options.add_argument('--headless')
        service = webdriver.ChromeService(executable_path=chromedriver_path, log_path=log_path)
        browser = webdriver.Chrome(options=options, service=service)
    else:
        raise Exception(f"Unknown value for browser_app={browser_app}")
    browser.maximize_window()
    return browser

def my_click(browser, locator, timeout, post_sleep):
    cond = EC.element_to_be_clickable(locator)
    try:
        el = WebDriverWait(browser, timeout).until(cond)
    except TimeoutException:
        raise Exception("Timed out waiting for element to be clickable")
    el.click()
    time.sleep(post_sleep)

def my_click_xpath(browser, xpath, timeout=5, post_sleep=1):
    locator = (By.XPATH, xpath)
    return my_click(browser, locator, timeout, post_sleep)

def my_click_css(browser, css, timeout=5, post_sleep=1):
    locator = (By.CSS_SELECTOR, css)
    return my_click(browser, locator, timeout, post_sleep)

def wait_visibility_of_any_elements(browser, locator, timeout=5):
    try:
        cond_appear = EC.visibility_of_any_elements_located(locator)
        WebDriverWait(browser, timeout).until(cond_appear)
    except TimeoutException:
        msg = f"Timeout exception while waiting for element to appear: ({locator[0], locator[1]})"
        logging.error(msg)
        raise Exception(msg)
    except UnexpectedAlertPresentException:
        msg = f"UnexpectedAlertPresentException while waiting for element to appear: ({locator[0], locator[1]})"
        logging.error(msg)
        raise Exception(msg)

def wait_visibility_of_any_elements_xpath(browser, xpath, timeout=5):
    locator = (By.XPATH, xpath)
    return wait_visibility_of_any_elements(browser, locator, timeout)

def wait_visibility_of_any_elements_css(browser, css, timeout=5):
    locator = (By.CSS_SELECTOR, css)
    return wait_visibility_of_any_elements(browser, locator, timeout)

def wait_popup(browser, locator, timeout_appear=10, timeout_disappear=60*60, fail_if_not_appear=True):
    # <div class="popup__component">
    try:
        # wait for at least one element to appear
        # required to prevent prematurely checking if element
        # has disappeared before it has had a chance to appear
        logging.info("Waiting for popup to appear")
        cond_appear = EC.visibility_of_any_elements_located(locator)
        WebDriverWait(browser, timeout_appear).until(cond_appear)
    except TimeoutException:
        if fail_if_not_appear:
            raise Exception(f"Timeout exception while waiting for popup to appear")
        else:
            pass
    except UnexpectedAlertPresentException:
        raise Exception(f"UnexpectedAlertPresentException while waiting for popup to appear")
    try:
        # wait for all elements to disappear
        logging.info("Waiting for popup to disappear")
        cond_disappear = EC.visibility_of_any_elements_located(locator)
        WebDriverWait(browser, timeout_disappear).until_not(cond_disappear)
    except TimeoutException:
        raise Exception(f"Timeout exception while waiting for popup to disappear")
    except UnexpectedAlertPresentException:
        raise Exception(f"UnexpectedAlertPresentException while waiting for popup to disappear")
    logging.info("Popup disappeared")

def wait_popup_css(browser, css, timeout_appear=5, timeout_disappear=60*60, fail_if_not_appear=True):
    locator = (By.CSS_SELECTOR, css)
    return wait_popup(browser, locator, timeout_appear, timeout_disappear, fail_if_not_appear)

def wait_popup_xpath(browser, xpath, timeout_appear=5, timeout_disappear=60*60, fail_if_not_appear=True):
    locator = (By.XPATH, xpath)
    return wait_popup(browser, locator, timeout_appear, timeout_disappear, fail_if_not_appear)

def scroll_by(driver, value):
    driver.execute_script(f"window.scrollBy(0,{value})")

# Scroll down the page
def scroll_down_all(driver, max_scrolls=30, scroll_by_value=500, sleep_between_scrolls=2):
    old_page = driver.page_source
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

def fill_input_field(browser, xpath, value):
    try:
        el = browser.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        raise Exception(f"Cannot find element with XPath '{xpath}'")
    el.clear()
    el.send_keys(value)

def select_from_select_box(browser, xpath, value):
    try:
        select_element = browser.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        raise Exception(f"Cannot find select box with XPath '{xpath}'")
    select = Select(select_element)
    select.select_by_visible_text(value)
