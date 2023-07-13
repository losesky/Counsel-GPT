# -*- coding: utf-8 -*-
from datetime import datetime
import io
import time
import jsonlines
import os
from jinja2 import Template
from configs.model_config import KB_TMP_PATH
from module.toolkit import truncate_string

async def append_to_json_file(data_dict, file_path, prefix='data_', max_size=10 * 1024 * 1024):
    # 获取目标目录下以指定前缀开头的所有文件
    file_dir, file_name = os.path.split(file_path)
    file_name, file_ext = os.path.splitext(file_name)
    file_prefix = os.path.join(file_dir, prefix + file_name)
    file_list = [f for f in os.listdir(file_dir) if f.startswith(file_prefix)]

    # 如果目录下没有符合条件的文件，则创建新文件
    if not file_list:
        new_file_path = os.path.join(file_dir, f"{prefix}{file_name}_1{file_ext}")
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.write('')
        file_path = new_file_path
    else:
        # 按照文件名编码的大小排序，找到最大的文件
        file_list = sorted(file_list, key=lambda x: int(x.split('_')[-1].split('.')[0]))
        last_file_path = os.path.join(file_dir, file_list[-1])
        # 判断最大的文件是否已经超过阈值，如果超过则新建文件
        if os.path.getsize(last_file_path) > max_size:
            i = int(file_list[-1].split('_')[-1].split('.')[0]) + 1
            new_file_path = os.path.join(file_dir, f"{prefix}{file_name}_{i}{file_ext}")
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write('')
            file_path = new_file_path
        else:
            file_path = last_file_path

    # 将 dct 追加到之前的 json 文件中
    with jsonlines.open(file_path, mode='a') as writer:
        writer.write_all(data_dict)


async def save_as_html(data_dict):
    for doc in data_dict:
        title = truncate_string(doc['title'].strip(), 40)
        directory_path = os.path.join(KB_TMP_PATH, 'html')
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        content= doc['content']
        template = Template('''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>{{ title }}</title>
</head>
<body>
{{ content }}
</body>
</html>
    ''')
        file_path = os.path.join(directory_path, f'{title}.html')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template.render(title=title, content=content))


async def save_as_md(select_vs, data_dict):
    file_dct = []
    for doc in data_dict:
        current_time = datetime.now().time()
        formatted_time = current_time.strftime(f"%H_%M_%S")
        title = doc['title'][:60].strip()
        directory_path = os.path.join(KB_TMP_PATH, select_vs, "content")
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        template = Template('''
```                             
【发布单位】{{ issuing_authority }}
【发布文号】{{ document_number }}
【发布日期】{{ publication_date }}
【生效日期】{{ implementation_date }}
【失效日期】{{ validity }}
【所属类别】{{ category }}
【文件来源】{{ effectiveness_level }}
``` 

{{ content }}
        ''')
        file_path = os.path.join(directory_path, f'{title}_{formatted_time}.md')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template.render(issuing_authority=doc['issuing_authority'],
                                    document_number=doc['document_number'],
                                    publication_date=doc['publication_date'],
                                    implementation_date=doc['implementation_date'],
                                    validity=doc['validity'],
                                    effectiveness_level=doc['effectiveness_level'],
                                    category=doc['category'],
                                    content=doc['content']))
        file_dct.append(file_path)  # 将文件路径添加到 file_dct 列表中
        time.sleep(1)
    return file_dct
