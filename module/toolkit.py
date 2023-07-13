# -*- coding:utf-8 -*-
from __future__ import annotations
import html
import socket
import gradio as gr
import csv
import json
import os
import re
from pypinyin import lazy_pinyin
import requests
import tiktoken


from configs.model_config import APP_PORT, logger, TEMPLATES_DIR, SYSTEM_PROMPT


def count_token(message):
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        length = len(encoding.encode(message))
        return length
    except Exception as e:
        return 0

def token_message(token_lst=None):
    if token_lst is None:
        token_lst = []
    token_sum = sum(token_lst[1:])
    return ("Token 计数: ") + f"{token_sum} tokens"

def convert_bot_before_marked(chat_message):
    """
    注意不能给输出加缩进, 否则会被marked解析成代码块
    """
    if '<div class="md-message">' in chat_message:
        return chat_message
    else:
        code_block_pattern = re.compile(r"```(.*?)(?:```|$)", re.DOTALL)
        code_blocks = code_block_pattern.findall(chat_message)
        non_code_parts = code_block_pattern.split(chat_message)[::2]
        result = []

        # hr_pattern = r'\n\n<hr class="append-display no-in-raw" />(.*?)'
        # hr_match = re.search(hr_pattern, chat_message, re.DOTALL)
        # clip_hr = chat_message[:hr_match.start()] if hr_match else chat_message
        # raw = f'<div class="raw-message hideM">{escape_markdown(clip_hr)}</div>'
        for non_code, code in zip(non_code_parts, code_blocks + [""]):
            if non_code.strip():
                result.append(non_code)
            if code.strip():
                code = f"\n```{code}\n```"
                result.append(code)
        result = "".join(result)
        md = f'<div class="md-message">{result}\n</div>'
        # return raw + md
        return md

def convert_user_before_marked(chat_message):
    if '<div class="user-message">' in chat_message:
        return chat_message
    else:
        return f'<div class="user-message">{escape_markdown(chat_message)}</div>'

def escape_markdown(text):
    """
    Escape Markdown special characters to HTML-safe equivalents.
    """
    escape_chars = {
        ' ': '&nbsp;',
        '_': '&#95;',
        '*': '&#42;',
        '[': '&#91;',
        ']': '&#93;',
        '(': '&#40;',
        ')': '&#41;',
        '{': '&#123;',
        '}': '&#125;',
        '#': '&#35;',
        '+': '&#43;',
        '-': '&#45;',
        '.': '&#46;',
        '!': '&#33;',
        '`': '&#96;',
        '>': '&#62;',
        '<': '&#60;',
        '|': '&#124;',
        ':': '&#58;',
    }
    return ''.join(escape_chars.get(c, c) for c in text)


def sorted_by_pinyin(list):
    return sorted(list, key=lambda char: lazy_pinyin(char)[0][0])


def get_file_names(dir, plain=False, filetypes=[".json"]):
    # logger.info(f"获取文件名列表，目录为{dir}，文件类型为{filetypes}，是否为纯文本列表{plain}")
    files = []
    try:
        for type in filetypes:
            files += [f for f in os.listdir(dir) if f.endswith(type)]
    except FileNotFoundError:
        files = []
    files = sorted_by_pinyin(files)
    if files == []:
        files = [""]
    logger.debug(f"files are:{files}")
    if plain:
        return files
    else:
        return gr.Dropdown.update(choices=files)

def get_template_content(templates, selection, original_system_prompt):
    # logger.info(f"应用模板中，选择为{selection}，原始系统提示为{original_system_prompt}")
    try:
        return templates[selection]
    except:
        return original_system_prompt
    

def get_template_names(plain=False):
    # logger.info("获取模板文件名列表")
    return get_file_names(TEMPLATES_DIR, plain, filetypes=[".csv", "json"])


def load_template(filename, mode=0):
    # logger.info(f"加载模板文件{filename}，模式为{mode}（0为返回字典和下拉菜单，1为返回下拉菜单，2为返回字典）")
    lines = []
    if filename.endswith(".json"):
        with open(os.path.join(TEMPLATES_DIR, filename), "r", encoding="utf8") as f:
            lines = json.load(f)
        lines = [[i["act"], i["prompt"]] for i in lines]
    else:
        with open(
            os.path.join(TEMPLATES_DIR, filename), "r", encoding="utf8"
        ) as csvfile:
            reader = csv.reader(csvfile)
            lines = list(reader)
        lines = lines[1:]
    if mode == 1:
        return sorted_by_pinyin([row[0] for row in lines])
    elif mode == 2:
        return {row[0]: row[1] for row in lines}
    else:
        choices = sorted_by_pinyin([row[0] for row in lines])
        return {row[0]: row[1] for row in lines}, gr.Dropdown.update(
            choices=choices
        )


def get_system_prompt():
    return SYSTEM_PROMPT


def retrieve_proxy(proxy=None):
    """
    1, 如果proxy = NONE，设置环境变量，并返回最新设置的代理
    2，如果proxy ！= NONE，更新当前的代理配置，但是不更新环境变量
    """
    global http_proxy, https_proxy
    if proxy is not None:
        http_proxy = proxy
        https_proxy = proxy
        yield http_proxy, https_proxy
    else:
        old_var = os.environ["HTTP_PROXY"], os.environ["HTTPS_PROXY"]
        os.environ["HTTP_PROXY"] = http_proxy
        os.environ["HTTPS_PROXY"] = https_proxy
        yield http_proxy, https_proxy # return new proxy

        # return old proxy
        os.environ["HTTP_PROXY"], os.environ["HTTPS_PROXY"] = old_var
        

def get_geoip():
    try:
        with retrieve_proxy():
            response = requests.get("https://ipapi.co/json/", timeout=5)
        data = response.json()
    except:
        data = {"error": True, "reason": "连接ipapi失败"}
    if "error" in data.keys():
        logger.warning(f"无法获取IP地址信息。\n{data}")
        if data["reason"] == "RateLimited":
            return (
                ("您的IP区域：未知。")
            )
        else:
            return ("获取IP地理位置失败。原因：") + f"{data['reason']}" + ("。你仍然可以使用聊天功能。")
    else:
        country = data["country_name"]
        if country == "China":
            text = "**您的IP区域：中国。请立即检查代理设置，在不受支持的地区使用API可能导致账号被封禁。**"
        else:
            text = ("您的IP区域：") + f"{country}。"
        logger.info(text)
        return text

# 定义一个正则表达式模式，匹配日志行中的格式字符
line_pattern = re.compile(r"\033\[\d+m(.*?)\033\[0m")

# 定义一个替换函数，将匹配到的格式字符替换为富文本颜色
def replace_color(match):
    color_code = match.group(0)
    text = match.group(1)
    if color_code == "\033[32m":
        return "<span style='color: green;'>{}</span>".format(text)
    elif color_code == "\033[33m":
        return "<span style='color: yellow;'>{}</span>".format(text)
    elif color_code == "\033[31m":
        return "<span style='color: red;'>{}</span>".format(text)
    else:
        return text

# 截取一个字符串的前40个汉字或等效长度的字符
def truncate_string(string, length):
    if len(string) <= length:
        return string
    else:
        # 使用切片截取前40个字符
        truncated_string = string[:length]
        # 如果截取的最后一个字符是半个汉字，则去掉该字符
        if len(truncated_string.encode('utf-8')) > length:
            truncated_string = truncated_string[:-1]
        return truncated_string

# 获取当前的域名和端口，构建预览链接地址
def get_current_domain_with_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    port = APP_PORT
    print(f'http://{ip}:{port}')
    return f'http://{ip}:{port}'


# 去掉 HTML 标签和 <details> 内容
def remove_html_tags(text):
    if text is None:
        return None
    message_html = remove_newlines_and_spaces(html.unescape(text).strip())
    if 'user-message' in message_html:
        match = re.search(r'<div class="user-message">(.*?)</div>', message_html)
        if match:
            message = match.group(1)
            return re.sub('<.*?>', '', message)
    elif 'md-message' in message_html:
        match = re.search(r'<div class="md-message">(.*?)</div>', message_html)
        if match:
            message = match.group(1)
            return re.sub('<.*?>', '', message)
    return None

# 去掉 HTML 标签
def remove_all_html_tags(text):
    if text is None:
        return None
    message_html = remove_newlines_and_spaces(html.unescape(text).strip())
    if 'user-message' in message_html:
        match = re.search(r'<div class="user-message">(.*?)</div>', message_html)
        if match:
            message = match.group(1)
            return re.sub('<.*?>', '', message)
    elif 'md-message' in message_html:
        match = re.search(r'<div class="md-message">(.*?)</div>', message_html)
        if match:
            message = match.group(1)
            # Remove <details> tag and its content
            message = re.sub(r'<details.*', '', message, flags=re.DOTALL)
            return re.sub('<.*?>', '', message)
    return None

def remove_newlines_and_spaces(text):
    # 去掉换行符和连续的空格
    text = re.sub(r'\n', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def start_outputing():
    # logger.info("显示取消按钮，隐藏发送按钮")
    return gr.Button.update(visible=False), gr.Button.update(visible=True)


def end_outputing():
    # logger.info("显示发送按钮，隐藏取消按钮")
    return (
        gr.Button.update(visible=True),
        gr.Button.update(visible=False),
    )


def shorten_str(url, max_length):
    if len(url) <= max_length:
        return url
    
    # 计算省略号的长度
    ellipsis_length = 4
    
    # 计算需要保留的部分的长度
    preserved_length = int(max_length / 2) - int(ellipsis_length / 2)
    
    # 截断链接并拼接省略号
    shortened_url = url[:preserved_length] + "..." + url[-preserved_length:]
    
    return shortened_url

