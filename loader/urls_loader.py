"""Loader that uses Selenium to load a page, then uses unstructured to load the html.
"""
import logging
import random
import time
from typing import List, Literal
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common import TimeoutException
from module.toolkit import shorten_str

from utils.page_parsing import init_chrome_driver, init_firefox_driver
from utils.main_content import MainContent

from langchain.docstore.document import Document
# from langchain.document_loaders.base import BaseLoader

logger = logging.getLogger(__name__)


class SeleniumURLLoader():
    """Loader that uses Selenium and to load a page and unstructured to load the html.
    This is useful for loading pages that require javascript to render.

    Attributes:
        urls (List[str]): List of URLs to load.
        browser (str): The browser to use, either 'chrome' or 'firefox'.
        headless (bool): If True, the browser will run in headless mode.
    """

    def __init__(
        self,
        urls: List[str],
        browser: Literal["chrome", "firefox"] = "chrome",
        headless: bool = True,
        continue_on_failure: bool = True,
    ):
        self.urls = urls
        self.browser = browser
        self.headless = headless
        self.continue_on_failure = continue_on_failure
        self.main_content = MainContent()
        if self.browser == 'firefox':
            self.driver = init_firefox_driver(is_headless=headless)
        else:
            self.driver = init_chrome_driver(is_headless=headless)
        self.driver.maximize_window()
        
    def _parse_soup(self, html):
        return BeautifulSoup(html, 'html.parser')

    def load(self) -> List[Document]:
        """Load the specified URLs using Selenium and create Document instances.

        Returns:
            List[Document]: A list of Document instances with loaded content.
        """
        from unstructured.partition.html import partition_html

        docs: List[Document] = list()
        
        for url in self.urls:
            try:
                self.driver.get(url)
                # 设置 WebDriverWait() 的等待时间，超时则抛出异常
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                soup = self._parse_soup(self.driver.page_source)
                title, content, imgs_array = self.main_content.extract(url, soup)
                elements = partition_html(text=content)
                text = "\n\n".join([str(el) for el in elements])
                text = shorten_str(text, int(6144 / len(self.urls)))
                metadata = {"source": url, "filename" : title, "imgs_array" : imgs_array}
                docs.append(Document(page_content=text, metadata=metadata))
                wait_time = random.uniform(2, 5)
                time.sleep(wait_time)
            except TimeoutException:
                continue
            except Exception as e:
                if self.continue_on_failure:
                    logger.error(f"Error fetching or processing {url}, exception: {e}")
                else:
                    raise e

        self.driver.quit()
        return docs
