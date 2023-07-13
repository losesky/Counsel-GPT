# -*- coding: utf-8 -*-
import asyncio
import importlib
import logging
import os
import random
import time
import uuid
import html2text
from datetime import datetime
import os
import time
import gradio as gr
from threading import Thread

from selenium.common import TimeoutException

from configs.model_config import logger
from module.model_func import get_local_doc_qa, set_vector_store
from module.toolkit import truncate_string
from utils.append_to_data import save_as_md
from utils.page_parsing import (wait_element_clickable_by_xp, wait_element_present_by_xp, driver_and_actions, Xclick)



#################################################################################################

MODULE_NAME = 'spider_logger'
logs = logging.getLogger(MODULE_NAME)
logs.setLevel(logging.INFO)
log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log")
log_file = os.path.join(log_path, f"{MODULE_NAME}.log")

class ColoredFormatter(logging.Formatter):
    """自定义 Formatter，用于设置不同级别的日志输出的颜色"""
    def format(self, record):
        record.msg = "{}".format(record.msg)
        return super().format(record)
    
if not logs.hasHandlers():
    # 设置 Handler
    handler = logging.FileHandler(log_file, encoding="utf-8")
    # 设置 Formatter
    formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    # 设置 Handler
    handler.setFormatter(formatter)
    # 添加 Handler
    logs.addHandler(handler)

#################################################################################################
    
def legal_provisions(driver, actions, keywords):
    keyword_xpath = '//*[@id="law_keyword"]'
    wait_element_clickable_by_xp(driver, keyword_xpath).send_keys(keywords)
    
    choices_xp = '//*[@id="t"]'
    choices = wait_element_clickable_by_xp(driver, choices_xp)
    actions.move_to_element(choices).perform()
    fulltxt_xp = '//option[@label="内容"]'
    wait_element_clickable_by_xp(driver, fulltxt_xp).click()
    
    submit_xp = '//input[@class="buttoncx"]'
    wait_element_clickable_by_xp(driver, submit_xp).click()
    return driver, actions


def prepare(spider_url, keywords):
    """
    准备工作
    """
    driver, actions = driver_and_actions(spider_url)
    driver, actions = legal_provisions(driver, actions, keywords)
    return driver, actions


def update_dct_by_content(dct, driver, original_window):
    """
    根据网页内容构建dct
    """
    for window_handle in driver.window_handles:
        if window_handle != original_window:
            driver.switch_to.window(window_handle)
            try:
                title_xp = '//div[@class="content_text"]/div[1]|//div[@class="content_text"]/p[1]'
                content = wait_element_present_by_xp(driver, title_xp, False).text
                content = content.replace("\n", "")
                title = truncate_string(content.strip(), 40)
            except TimeoutException:
                logger.warning(f'Get title error: {driver.current_url}, try...')
                content_xp = '//div[@class="content_text"]'
                try:
                    content = wait_element_present_by_xp(driver, content_xp, False).text
                    content = content.replace("\n", "")
                    title = truncate_string(content.strip(), 40)
                except TimeoutException:
                    logger.error(f'Page data abnormal {driver.current_url} next')
                    driver.close()
                    driver.switch_to.window(original_window)
                    return dct, driver

            stitle_xp = '//span[@class="STitle"]'
            stitle = wait_element_present_by_xp(driver, stitle_xp, False).text

            issuing_authority = stitle.split('【发布单位】')[1].split('【')[0].strip()
            document_number = stitle.split('发布文号】')[1].split('【')[0].strip()
            publication_date = stitle.split('发布日期】')[1].split('【')[0].strip()
            implementation_date = stitle.split('生效日期】')[1].split('【')[0].strip()
            validity = stitle.split('失效日期】')[1].split('【')[0].strip()
            effectiveness_level = stitle.split('文件来源】')[1].strip()
            category = stitle.split('所属类别】')[1].split('【')[0].strip()

            content_xp = '//div[@class="content_text"]'
            html_content = wait_element_present_by_xp(driver, content_xp, False).get_attribute('innerHTML') # type: ignore
            content = html2text.html2text(html_content)

            source = driver.current_url

            data_dict = {
                'title': title,
                'reference_code': str(uuid.uuid4()),
                'issuing_authority': issuing_authority,
                'document_number': document_number,
                'publication_date': publication_date,
                'implementation_date': implementation_date,
                'validity': validity,
                'effectiveness_level': effectiveness_level,
                'category': category,
                'content': content,
                'source': source
            }
            dct.append(data_dict)
            wait_time = random.uniform(1, 5)
            time.sleep(wait_time)
            driver.close()
            driver.switch_to.window(original_window)
    return dct, driver, title


def search_per_index(dct, driver, actions, line_per_page, batch_size, select_vs, sentence_size):
    """
    按页遍历数据
    """
    count = 0
    index = 0
    while True:
        t0 = time.time()
        page = index // line_per_page + 1
        total_line = index + 1
        line = index % line_per_page + 1
        original_window = driver.current_window_handle
        try:
            line_xp = '//div[@id="ssjg"]/div[1]/dl[{}]/dt/a'.format(line)
            Xclick(driver, line_xp)
        except TimeoutException:
            file_dct = asyncio.run(save_as_md(select_vs, dct))
            logs.info(f'准备写入知识库')
            file_status = set_vector_store(select_vs, file_dct, sentence_size)
            logs.info(f"{file_status}")
            logger.info(f'finish patch {total_line} data!')
            return dct, driver, actions
        
        dct, driver, title = update_dct_by_content(dct, driver, original_window)
        actions.pause(0.1).perform()
        logs.info("{} - {}".format(total_line, title))
        
        count += 1
        if count == batch_size:
            file_dct = asyncio.run(save_as_md(select_vs, dct))
            logs.info(f'准备写入知识库')
            file_status = set_vector_store(select_vs, file_dct, sentence_size)
            count = 0
            dct = []
            logs.info(f"{file_status}")

        if line == line_per_page:
            Page_xp = '//div[@class="paginationControl"]/a[text()="下一页"]'
            Xclick(driver, Page_xp)
            logs.info(f'获取第 {page + 1} 页数据')
            wait_time = random.uniform(2, 5)
            time.sleep(wait_time)
            
        t1 = time.time()
        
        index += 1

    return dct, driver, actions


def process_batchs(spider_url, keywords, select_vs, sentence_size, dct=[], line_per_page=5, batch_size=5):
    """
    获取并处理数据 每页5条 每5条记录存储一次
    """
    t0 = time.time()
    driver, actions = prepare(spider_url, keywords)
    t1 = time.time()
    
    logger.info("batch prepare time:{}".format(t1 - t0))

    dct, driver, actions = search_per_index(dct, driver, actions, line_per_page, batch_size, select_vs, sentence_size)

    t2 = time.time()
    logger.info("search time:{}".format(t2 - t1))
    driver.quit()

def syn_crawling(spider_url, keywords, select_vs, sentence_size):
    try:
        if os.path.exists(log_file):
            with open(log_file, 'w') as file:
                file.truncate()
    except PermissionError:
        pass
    if spider_url is None or keywords is None or len(spider_url.strip()) == 0 or len(keywords.strip()) == 0:
        logs.info(f'请输入关键词')
    else:
        logs.info(f'开始获取 "{keywords}" 数据')
        process_batchs(spider_url, keywords, select_vs, sentence_size)
        logs.info(f'获取数据完成，点击清除按钮开启新的抓取')
        
# 获取日志，添加到返回logs_chat格式数据
def read_log_file(logs_chat):
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding="utf-8") as file:
            lines = file.readlines()

        if len(logs_chat) > 0:
            last_read_line = len(logs_chat) - 1
        else:
            last_read_line = 0

        new_lines = lines[last_read_line:]

        for line in new_lines:
            logs_chat.append([None, line.strip()])

    return logs_chat


# 检查日志是否结束
def check_logs_for_completion(logs_chat):
    for log in logs_chat:
        if log[1] is not None and "获取数据完成" in log[1]:
            return True
    return False


# 清除日志内容
def clear_log_file(log_file):
    try:
        if os.path.exists(log_file):
            with open(log_file, 'w') as file:
                file.truncate()
    except PermissionError:
        pass


# 运行爬虫主程序
def run_crawling(spider_url, keywords, logs_chat, select_vs, vs_path, sentence_size):
    # 先清理日志
    clear_log_file(log_file)
    is_running, is_finish = False, False
    local_doc_qa = get_local_doc_qa()
    while True:
        if spider_url is None or keywords is None or len(spider_url.strip()) == 0 or len(keywords.strip()) == 0:
            logs.info(f'请输入关键词')
            
            yield (read_log_file(logs_chat),
                   gr.update(visible=True),
                   gr.update(visible=False),
                   gr.update(choices=local_doc_qa.list_file_from_vector_store(vs_path) if vs_path else []))
            break
        
        # 如果日志已经读取结束，退出循环
        if check_logs_for_completion(logs_chat):
            yield (read_log_file(logs_chat),
                   gr.update(visible=False),
                   gr.update(visible=True),
                   gr.update(choices=local_doc_qa.list_file_from_vector_store(vs_path) if vs_path else []))
            break
        
        time.sleep(3)
        current_time = datetime.now().time()
        print(f'begin run_crawling {current_time}')
        if not is_running and not is_finish:
            is_running = True
            T = Thread(target=syn_crawling, args=(spider_url, keywords, select_vs, sentence_size), name='syn_crawling')
            T.start()

        yield (read_log_file(logs_chat),
               gr.update(visible=False),
               gr.update(visible=False),
               gr.update(choices=local_doc_qa.list_file_from_vector_store(vs_path) if vs_path else []))

# 重置所有内容
def init_all():
    # 先清理日志
    clear_log_file(log_file)
    
    return (gr.update(visible=True), gr.update(visible=False))