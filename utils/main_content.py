# -*- coding: utf-8 -*-
from io import BytesIO
import logging
import re
import lxml
import lxml.html
import cchardet
from PIL import Image
from lxml.html import HtmlComment
import requests
import base64

REGEXES = {
    'okMaybeItsACandidateRe': re.compile(
        'and|article|artical|body|column|main|shadow', re.I),
    'positiveRe': re.compile(
        ('article|arti|body|content|entry|hentry|main|page|'
         'artical|zoom|arti|context|message|editor|'
         'pagination|post|txt|text|blog|story'), re.I),
    'negativeRe': re.compile(
        ('copyright|combx|comment|com-|contact|foot|footer|footnote|decl|copy|'
         'notice|'
         'masthead|media|meta|outbrain|promo|related|scroll|link|pagebottom|bottom|'
         'other|shoutbox|sidebar|sponsor|shopping|tags|tool|widget'), re.I),
}

# 创建一个字典表，定义不允许出现在 src 中的字符串
forbidden_strings = {
    'activity': None,
    'example': None,
    'logo': None,
    'bg': None,
    'data:image': None,
    # 添加其他不允许出现的字符串
}


class MainContent:
    def __init__(self, ):
        self.non_content_tag = set([
            'head',
            'meta',
            'script',
            'style',
            'object', 'embed',
            'iframe',
            'marquee',
            'select',
        ])
        self.title = ''
        self.p_space = re.compile(r'\s')
        self.p_html = re.compile(r'<html|</html>', re.IGNORECASE | re.DOTALL)
        self.p_content_stop = re.compile(r'正文.*结束|正文下|相关阅读|声明')
        self.p_clean_tree = re.compile(r'author|post-add|copyright')

    def get_title(self, doc):
        title = ''
        title_el = doc.xpath('//title')
        if title_el:
            title = title_el[0].text_content().strip()
        if len(title) < 7:
            tt = doc.xpath('//meta[@name="title"]')
            if tt:
                title = tt[0].get('content', '')
        if len(title) < 7:
            tt = doc.xpath('//*[contains(@id, "title") or contains(@class, "title")]')
            if not tt:
                tt = doc.xpath('//*[contains(@id, "font01") or contains(@class, "font01")]')
            for t in tt:
                ti = t.text_content().strip()
                if ti in title and len(ti) * 2 > len(title):
                    title = ti
                    break
                if len(ti) > 20: continue
                if len(ti) > len(title) or len(ti) > 7:
                    title = ti
        return title

    def shorten_title(self, title):
        spliters = [' - ', '–', '—', '-', '|', '::']
        for s in spliters:
            if s not in title:
                continue
            tts = title.split(s)
            if len(tts) < 2:
                continue
            title = tts[0]
            break
        return title

    def calc_node_weight(self, node):
        weight = 1
        attr = '%s %s %s' % (
            node.get('class', ''),
            node.get('id', ''),
            node.get('style', '')
        )
        if attr:
            mm = REGEXES['negativeRe'].findall(attr)
            weight -= 2 * len(mm)
            mm = REGEXES['positiveRe'].findall(attr)
            weight += 4 * len(mm)
        if node.tag in ['div', 'p', 'table']:
            weight += 2
        return weight

    def get_main_block(self, url, html, short_title=True):
        if isinstance(html, bytes):
            encoding = cchardet.detect(html)['encoding']
            if encoding is None:
                return None, None, []
            html = html.decode(encoding, 'ignore')
        try:
            doc = lxml.html.fromstring(str(html))
            doc.make_links_absolute(base_url=url)
        except lxml.etree.ParserError:
            return None, None, []
        
        self.title = self.get_title(doc)
        if short_title:
            self.title = self.shorten_title(self.title)
        
        body = doc.xpath('//body')
        if not body:
            return self.title, None, []
        
        candidates = []
        nodes = body[0].getchildren()
        imgs_array = []
        img_count = 0  # 计数器，用于跟踪已插入的图片数量
        while nodes:
            node = nodes.pop(0)
            children = node.getchildren()
            tlen = 0
            for child in children:
                if isinstance(child, HtmlComment):
                    continue
                if child.tag in self.non_content_tag or child.tag == 'a' or child.tag == 'textarea' or child.tag == 'video':
                    continue
                attr = '%s%s%s' % (child.get('class', ''), child.get('id', ''), child.get('style'))
                if 'display' in attr and 'none' in attr:
                    continue
                # 对图片进行筛选
                # if child.tag == 'img' and img_count < 3:
                #     src = child.get('src')
                #     if src and not any(forbidden_str in src for forbidden_str in forbidden_strings):
                #         try:
                #             response = requests.get(src, timeout=3)  # 设置超时时间为3秒
                #             if response.status_code == 200:
                #                 image = Image.open(BytesIO(response.content))
                #                 width, height = image.size
                #                 if width > 500 and height > 500:
                #                     imgs_array.append(src)
                #                     img_count += 1
                #         except requests.exceptions.Timeout:
                #             logging.error(f"Timeout when loading image: {src}")
                #             pass
                #         except Exception as e:
                #             logging.error(f"Failed to open image: {src}")
                #             pass
                #     continue
                nodes.append(child)
                weight = 3 if child.tag == 'p' else 1
                text = '' if not child.text else child.text.strip()
                tail = '' if not child.tail else child.tail.strip()
                tlen += (len(text) + len(tail)) * weight
            if tlen < 10:
                continue
            weight = self.calc_node_weight(node)
            candidates.append((node, tlen * weight, imgs_array))
        
        if not candidates:
            return self.title, None, []
        
        candidates.sort(key=lambda a: a[1], reverse=True)
        good = candidates[0][0]
        
        if good.tag in ['p', 'pre', 'code', 'blockquote']:
            for _ in range(5):
                good = good.getparent()
                if good.tag == 'div':
                    break
        
        good = self.clean_etree(good, url)
        
        return self.title, good, candidates[0][2]

    def clean_etree(self, tree, url=''):
        to_drop = []
        drop_left = False
        for node in tree.iterdescendants():
            if drop_left:
                to_drop.append(node)
                continue
            if isinstance(node, HtmlComment):
                to_drop.append(node)
                if self.p_content_stop.search(node.text):
                    drop_left = True
                continue
            if node.tag in self.non_content_tag:
                to_drop.append(node)
                continue
            attr = '%s %s' % (
                node.get('class', ''),
                node.get('id', '')
            )
            if self.p_clean_tree.search(attr):
                to_drop.append(node)
                continue
            aa = node.xpath('.//a')
            if aa:
                text_node = len(self.p_space.sub('', node.text_content()))
                text_aa = 0
                for a in aa:
                    alen = len(self.p_space.sub('', a.text_content()))
                    if alen > 5:
                        text_aa += alen
                if text_aa > text_node * 0.4:
                    to_drop.append(node)
        for node in to_drop:
            try:
                node.drop_tree()
            except:
                pass
        return tree

    def get_text(self, doc):
        lxml.etree.strip_elements(doc, 'script')
        lxml.etree.strip_elements(doc, 'style')
        for ch in doc.iterdescendants():
            if not isinstance(ch.tag, str):
                continue
            if ch.tag in ['div', 'h1', 'h2', 'h3', 'p', 'br', 'table', 'tr', 'dl']:
                if not ch.tail:
                    ch.tail = '\n'
                else:
                    ch.tail = '\n' + ch.tail.strip() + '\n'
            if ch.tag in ['th', 'td']:
                if not ch.text:
                    ch.text = '  '
                else:
                    ch.text += '  '
            if ch.tail:
                ch.tail = ch.tail.strip()
        lines = doc.text_content().split('\n')
        content = []
        for l in lines:
            l = l.strip()
            if not l:
                continue
            content.append(l)
        return '\n'.join(content)

    def extract(self, url, html):
        """
        return (title, content)
        """
        title, node, imgs_array = self.get_main_block(url, html)
        if node is None:
            logging.error(f'no main block got !!!!!{url}')
            return title, '', ''
        content = self.get_text(node)
        return title, content, imgs_array
