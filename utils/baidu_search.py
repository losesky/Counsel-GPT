# -*- coding: utf-8 -*-

import sys
from typing import Literal
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

from utils.page_parsing import init_chrome_driver, init_firefox_driver

# 创建一个字典表，定义不允许出现在 src 中的字符串
forbidden_urls = {
    'zhihu.com': None,
    'xiaohongshu.com': None,
    'weibo.com': None,
    'wenku.baidu.com': None,
    'zhidao.baidu.com': None,
    '66law.cn': None,
    '64365.com': None,
    # 添加其他不允许出现的字符串
}

class BaiduSearch():
    """
    Baidu search.
    """

    def __init__(
        self,
        browser: Literal["chrome", "firefox"] = "chrome",
        headless: bool = True,
    ):
        self.browser = browser
        self.headless = headless
        self.baidu_host_url = "https://www.baidu.com"
        self.baidu_search_url = "https://www.baidu.com/s?ie=utf-8&tn=baidu&wd="
        self.ABSTRACT_MAX_LENGTH = 300
        if self.browser == 'firefox':
            self.driver = init_firefox_driver(is_headless=headless)
        else:
            self.driver = init_chrome_driver(is_headless=headless)
        self.driver.maximize_window()
        
    def __del__(self):
        self.driver.quit()
    
    def _parse_soup(self, html):
        return BeautifulSoup(html, 'html.parser')

    def search(self, keyword, num_results=10, debug=0):
        """
        通过关键字进行搜索
        :param keyword: 关键字
        :param num_results： 指定返回的结果个数
        :return: 结果列表
        """
        if not keyword:
            return None

        list_result = []
        page = 1

        # 起始搜索的url
        next_url = self.baidu_search_url + keyword
        # 循环遍历每一页的搜索结果，并返回下一页的url
        while len(list_result) < num_results:
            data, next_url = self.parse_html(next_url, rank_start=len(list_result))
            if data:
                list_result += data
                if debug:
                    print("---searching[{}], finish parsing page {}, results number={}: ".format(keyword, page, len(data)))
                    for d in data:
                        print(str(d))

            if not next_url:
                if debug:
                    print(u"already search the last page。")
                break
            page += 1
        
        if debug:
            print("\n---search [{}] finished. total results number={}！".format(keyword, len(list_result)))
        
        self.driver.quit()
        
        return list_result[: num_results] if len(list_result) > num_results else list_result


    def parse_html(self, url, rank_start=0, debug=0):
        """
        解析处理结果
        :param url: 需要抓取的 url
        :return:  结果列表，下一页的url
        """
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            root = self._parse_soup(self.driver.page_source)
            list_data = []
            div_contents = root.find_all("div", class_="result c-container xpath-log new-pmd")
            for div in div_contents:
                title = ''
                url = ''
                snippet = ''
                try:
                    # 遍历所有找到的结果，取得标题和概要内容（50字以内）
                    if div.h3 and div.h3.a:
                        title = div.h3.a.text.strip()
                        url = div.h3.a['href'].strip()
                        real_url = div["mu"]
                        if real_url is None or any(forbidden_str in real_url for forbidden_str in forbidden_urls):
                            continue
                    if div.find("div", class_="c-gap-top-small"):
                        snippet_div = div.find("div", class_="c-gap-top-small")
                        snippet_spans = snippet_div.find_all("span")
                        if len(snippet_spans) > 2:
                            snippet = snippet_spans[0].text.strip() + '-' + snippet_spans[1].text.strip()
                        else:
                            snippet = div.find("div", class_="c-gap-top-small").text.strip()
                    elif div.find("div", class_="c-gap-top-middle"):
                        snippet_div = div.find("div", class_="c-span-last")
                        snippet_spans = snippet_div.find_all("span")
                        if len(snippet_spans) > 2:
                            snippet = snippet_spans[0].text.strip() + '-' + snippet_spans[1].text.strip()
                        else:
                            snippet = div.find("div", class_="c-gap-top-middle").text.strip()
                except Exception as e:
                    if debug:
                        print("catch exception during parsing page html, e={}".format(e))
                    continue

                if self.ABSTRACT_MAX_LENGTH and len(snippet) > self.ABSTRACT_MAX_LENGTH:
                    snippet = snippet[:self.ABSTRACT_MAX_LENGTH].strip()
                # if real_url:
                rank_start+=1
                list_data.append({"title": title, "snippet": snippet, "link": real_url, "rank": rank_start})


            # 找到下一页按钮
            next_btn = root.find_all("a", class_="n")

            # 已经是最后一页了，没有下一页了，此时只返回数据不再获取下一页的链接
            if len(next_btn) <= 0 or u"上一页" in next_btn[-1].text:
                return list_data, None

            next_url = self.baidu_host_url + next_btn[-1]["href"]
            return list_data, next_url
        except Exception as e:
            if debug:
                print(u"catch exception duration parsing page html, e：{}".format(e))
            return None, None


    def run(self):
        """
        主程序入口，支持命令得带参执行或者手动输入关键字
        :return:
        """
        default_keyword = u"百度搜索"
        num_results = 10
        debug = 0

        prompt = """
        baidusearch: not enough arguments
        [0]keyword: keyword what you want to search
        [1]num_results: number of results
        [2]debug: debug switch, 0-close, 1-open, default-0
        eg: baidusearch NBA
            baidusearch NBA 6
            baidusearch NBA 8 1
        """
        if len(sys.argv) > 3:
            keyword = sys.argv[1]
            try:
                num_results = int(sys.argv[2])
                debug = int(sys.argv[3])
            except:
                pass
        elif len(sys.argv) > 1:
            keyword = sys.argv[1]
        else:
            print(prompt)
            keyword = input("please input keyword: ")
            # sys.exit(1)

        if not keyword:
            keyword = default_keyword

        print("---start search: [{}], expected number of results:[{}].".format(keyword, num_results))
        results = self.search(keyword, num_results=num_results, debug=debug)

        if isinstance(results, list):
            print("search results：(total[{}]items.)".format(len(results)))
            for res in results:
                print("{}. {}\n   {}\n   {}".format(res['rank'], res["title"], res["snippet"], res["link"]))
        else:
            print("start search: [{}] failed.".format(keyword))


if __name__ == '__main__':
    bs = BaiduSearch()
    bs.run()