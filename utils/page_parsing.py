# -*- coding: utf-8 -*-
import os
import platform

from selenium import webdriver
from selenium.common import TimeoutException, StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from configs.model_config import logger


def init_chrome_driver(is_headless, proxy_host=None, proxy_port=None):
    """
    初始化一个 chrome Driver
    :param is_headless:  是否开启无头模式
    :param proxy_host: 代理服务器主机
    :param proxy_port: 代理服务器端口号
    :return: chrome Driver
    """
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # 设置屏幕器宽高
    chrome_options.add_argument("--window-size=1440,750")
    # 最大化，防止失去焦点
    chrome_options.add_argument("--start-maximized")
    # 消除安全校验 可以直接无提示访问http网站
    chrome_options.add_argument("--allow-running-insecure-content")
    if is_headless:
        chrome_options.add_argument('--headless')

    if proxy_host and proxy_port:
        proxy_string = f"{proxy_host}:{proxy_port}"
        chrome_options.add_argument(f"--proxy-server={proxy_string}")

    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 实例化驱动
    system = platform.system()
    if system == "Windows":
        executable_path = './utils/chromedriver.exe'
    elif system == "Linux":
        executable_path = '/usr/bin/chromedriver'
    else:
        raise Exception("Unsupported system detected")
    driver = webdriver.Chrome(executable_path=executable_path, options=chrome_options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
                """
    })
    return driver


def init_firefox_driver(is_headless, proxy_host=None, proxy_port=None):
    """
    初始化一个 chrome Driver
    :param is_headless:  是否开启无头模式
    :param proxy_host: 代理服务器主机
    :param proxy_port: 代理服务器端口号
    :return: firefox Driver
    """
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.set_preference('javascript.enabled', True)
    firefox_options.add_argument('--no-sandbox')
    firefox_options.add_argument('--disable-dev-shm-usage')
    # 设置屏幕器宽高
    firefox_options.add_argument("--window-size=1440,750")
    # 最大化，防止失去焦点
    firefox_options.add_argument("--start-maximized")
    # 消除安全校验 可以直接无提示访问http网站
    firefox_options.add_argument("--allow-running-insecure-content")
    if is_headless:
        firefox_options.add_argument('--headless')

    if proxy_host and proxy_port:
        proxy_string = f"{proxy_host}:{proxy_port}"
        firefox_options.add_argument(f"--proxy-server={proxy_string}")

    # 实例化驱动
    system = platform.system()
    if system == "Windows":
        executable_path = './utils/geckodriver.exe'
    elif system == "Linux":
        executable_path = '/usr/local/bin/geckodriver'
    else:
        raise Exception("Unsupported system detected")
    # 创建 Firefox WebDriver 实例
    profile = webdriver.FirefoxProfile()
    profile.set_preference("dom.webdriver.enabled", False)
    driver = webdriver.Firefox(executable_path=executable_path, options=firefox_options, firefox_profile=profile)
    # 在 WebDriver 中注入 JavaScript 代码以禁用 navigator.webdriver 属性
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    """)
    return driver


def Xclick(driver, xp):
    try:
        element = wait_element_clickable_by_xp(driver, xp, False)
        if element is None:
            logger.error("element not clickable: %s", xp)
            return
        driver.execute_script("arguments[0].click();", element)
    except TimeoutException as e:
        logger.error("TimeoutException: element not clickable: %s", xp)
        raise e  # 继续抛出异常

def fexp(driver, xpath):
    return driver.find_element('xpath', xpath)


def EC_by_xp(EC_ec, driver, xp, pri=True):
    wait = WebDriverWait(driver, timeout=10)
    while True:
        try:
            element = wait.until(EC_ec((By.XPATH, xp)))
            if pri:
                if isinstance(element, list):
                    # element is a list
                    logger.info("find %d elements! tag: %s", len(element), element[0].tag_name)
                else:
                    # element is not a list
                    logger.info("find element! text: %s, tag: %s", element.text, element.tag_name)
            return element
        except StaleElementReferenceException:
            logger.warning("element is stale, retrying...")


def wait_element_present_by_xp(driver, xp, pri=True):
    return EC_by_xp(EC.presence_of_element_located, driver, xp, pri)


def wait_elements_present_by_xp(driver, xp, pri=True):
    return EC_by_xp(EC.presence_of_all_elements_located, driver, xp, pri)


def wait_element_clickable_by_xp(driver, xp, pri=True):
    try:
        element = EC_by_xp(EC.element_to_be_clickable, driver, xp, pri)
    except TimeoutException as e:
        logger.error("TimeoutException: element not clickable: %s", xp)
        raise e  # 继续抛出异常
    return element


def driver_and_actions(url):
    driver = init_chrome_driver(is_headless=True)
    driver.maximize_window()
    driver.get(url)
    actions = ActionChains(driver)
    logger.info("get driver and actions!")
    return driver, actions


def get_file_path(directory_path, data_file_name):
    file_extension = os.path.splitext(data_file_name)[1][1:]
    directory_path = os.path.join(directory_path, file_extension)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    file_path = os.path.join(directory_path, data_file_name)
    return file_path