import gradio as gr
import shutil
import os
import re
from chains.local_doc_qa import LocalDocQA
from configs.model_config import *
import models.shared as shared
from models.loader.args import parser
from models.loader import LoaderCheckPoint
from module.presets import *
from module.toolkit import get_current_domain_with_port, shorten_str

local_doc_qa = LocalDocQA()

flag_csv_logger = gr.CSVLogger()

def get_local_doc_qa():
    return local_doc_qa

pre_token = 0
def init_model():
    """ 
    解析命令行参数，加载模型，初始化配置，并测试模型是否成功加载 
    """
    args = parser.parse_args()  # 解析命令行参数，并将结果保存在 args 变量中

    args_dict = vars(args)  # 将 args 转换为字典类型
    shared.loaderCheckPoint = LoaderCheckPoint(args_dict)  # 创建一个 LoaderCheckPoint 对象，并将其保存在 shared.loaderCheckPoint 变量中
    llm_model_ins = shared.loaderLLM()  # 加载模型，并将返回的模型对象保存在 llm_model_ins 变量中
    llm_model_ins.set_history_len(LLM_HISTORY_LEN)  # 设置模型的历史记录长度
    
    try:
        local_doc_qa.init_cfg(llm_model=llm_model_ins)  # 初始化配置，将加载的模型对象传递给 llm_model 参数
        response_generator = local_doc_qa.get_general_answer("你是谁？我们之间最大会话长度是多少？", chat_history=[], streaming=False)  # 测试模型是否成功加载，传递的参数为 "你好"，表示测试模型对于简单的问候语的回复是否正常。
        response, history, status_text = next(response_generator)
        logger.info(history)
        logger.info(status_text)
        
        reply = """模型已成功加载，可以开始对话"""
        logger.info(reply)
        return reply

    except Exception as e:
        logger.error(e)
        reply = """⚠️模型未成功加载，请到页面左上角【模型配置】选项卡中重新选择后点击【加载模型】按钮"""
        
        if str(e) == "Unknown platform: darwin":
            logger.error("该报错可能因为您使用的是 macOS 操作系统，需先下载模型至本地后执行 Web UI，具体方法请参考项目 README 中本地部署方法及常见问题："
                        " https://github.com/imClumsyPanda/langchain-ChatGLM")
        else:
            logger.error(reply)
        
        return reply


def reinit_model(llm_model, embedding_model, llm_history_len, no_remote_model, use_ptuning_v2, use_lora ,temperature, top_k, history):
    """
    根据传递的参数重新加载模型，并初始化配置
    
    参数：
    llm_model：表示加载的模型路径。
    embedding_model：表示加载的嵌入模型路径。
    llm_history_len：表示模型的历史记录长度。
    no_remote_model：表示是否使用远程模型。
    use_ptuning_v2：表示是否使用 ptuning_v2。
    use_lora：表示是否使用 LoRA。
    top_k：表示搜索时返回的最大文档数。
    history：表示用户的历史记录，是一个列表，每个元素都是一个列表，包含两个元素，第一个元素是用户提出的问题，第二个元素是问题的答案或者搜索结果。
    """
    try:
        # 加载LLM模型
        llm_model_ins = shared.loaderLLM(llm_model, no_remote_model, use_ptuning_v2)
        llm_model_ins.set_history_len(llm_history_len)
        llm_model_ins.set_temperature(temperature)
        
        # 初始化本地文档问答模块
        local_doc_qa.init_cfg(llm_model=llm_model_ins, embedding_model=embedding_model, top_k=top_k)
        response_generator = local_doc_qa.get_general_answer("你是谁？我们之间最大会话长度是多少？", chat_history=[], streaming=False)  # 测试模型是否成功加载，传递的参数为 "你好"，表示测试模型对于简单的问候语的回复是否正常。
        response, history, status_text = next(response_generator)
        logger.info(history)
        logger.info(status_text)
        
        model_status = """模型已成功重新加载，可以开始对话，或从下方选择模式后开始对话"""
        logger.info(model_status)
    except Exception as e:
        logger.error(e)
        model_status = """⚠️模型未成功重新加载，请到页面左上角【模型配置】选项卡中重新选择后点击【加载模型】按钮"""
        logger.error(model_status)
    
    return model_status


def cancel_outputing():
    logger.info("中止输出……")
    local_doc_qa.interrupt()


def set_vector_store(vs_id, files, sentence_size):
    vs_id = str(vs_id)  # 将 vs_id 转换为字符串
    if '新建知识库' in vs_id:
        return '⚠️未选择需要加载的知识库，无法新增内容'
    vs_path = os.path.join(KB_ROOT_PATH, vs_id, "vector_store")  # 构建向量存储的路径，并将结果保存在 vs_path 变量中
    filelist = []
    if local_doc_qa.llm and local_doc_qa.embeddings:  # 如果 LLM 模型和 embedding 模型都加载成功
        if isinstance(files, list):
            for file in files:
                try:
                    filename = os.path.split(file)[-1]  # 获取路径下文件名
                    shutil.move(file, os.path.join(KB_ROOT_PATH, vs_id, "content", filename))  # 文件移动到向量存储的 content 目录下
                    filelist.append(os.path.join(KB_ROOT_PATH, vs_id, "content", filename))
                except Exception as e:
                    file_status = f'"⚠️{filename}" 处理异常，跳过'
                    pass
            if len(filelist):
                vs_path, loaded_files = local_doc_qa.init_knowledge_vector_store(filelist, vs_path, sentence_size)
                if len(loaded_files):
                    file_status = f"已新增 {len(loaded_files)} 个内容，存储完毕"
                else:
                    file_status = "⚠️搜索结果未成功入库，请检查系统或重新检索"
            else:
                file_status = "⚠️搜索结果异常，请检查系统或重新检索"
    else:
        file_status = "⚠️模型未完成加载，请先在加载模型后再导入文件"
        vs_path = None
    
    return file_status


def get_vs_list():
    # 获取知识库列表
    lst_default = ["新建知识库"]
    if not os.path.exists(KB_ROOT_PATH):
        return lst_default
    lst = os.listdir(KB_ROOT_PATH)
    if not lst:
        return lst_default
    lst.sort()
    return lst_default + lst

def get_answer(query, vs_path, history, mode, search_source, search_rang, score_threshold=VECTOR_SEARCH_SCORE_THRESHOLD,
               vector_search_top_k=VECTOR_SEARCH_TOP_K, chunk_conent: bool = True,
               chunk_size=CHUNK_SIZE, systemPromptTxt=PROMPT_TEMPLATE, streaming: bool = STREAMING):
    
    if query is None or len(query.strip()) == 0:
        yield history, "", "请输入提问内容，按回车提交"
        return
        
    if mode == "在线问答":
        for resp, history, status_text in local_doc_qa.get_search_result_based_answer(
                query=query, search_source=search_source, search_rang=search_rang, chat_history=history, streaming=streaming):
            yield history, "", status_text
        history[-1][-1] += '\n'
        source = "\n".join(
                [
                    f"""<details style="margin-top: 10px"><summary>出处[ {i + 1} ] - <a href="{doc.metadata["source"]}" target="_blank">{doc.metadata["filename"]}</a></summary>\n"""
                    f"""<div style="font-size: 15px; line-height: 1.7; color:#aaa; margin: 5px 8px 0 8px">{doc.page_content}</div>\n"""
                    f"""</details>"""
                    for i, doc in
                    enumerate(resp["source_documents"])])
        history[-1][-1] += source
        yield history, "", status_text

    elif mode == "专业问答" and vs_path is not None and os.path.exists(vs_path) and "index.faiss" in os.listdir(
            vs_path):
        for resp, history, status_text in local_doc_qa.get_knowledge_based_answer(
                query=query, vs_path=vs_path, chat_history=history, streaming=streaming):
            yield history, "", status_text
        source = "\n".join(
                [
                    f"""<details style="margin-top: 10px"><summary>出处[ {i + 1} ] - {shorten_str(os.path.split(doc.metadata["source"])[-1], 50)}</summary>\n"""
                    f"""<div style="font-size: 15px; line-height: 1.7; color:#aaa; margin: 5px 8px 0 8px">{str(doc.page_content)[:100]}...</div>\n"""
                    f"""</details>"""
                    for i, doc in
                    enumerate(resp["source_documents"])])
        history[-1][-1] += source
        yield history, "", status_text
            
    elif mode == "知识库检索":
        if vs_path is not None and os.path.exists(vs_path) and "index.faiss" in os.listdir(vs_path):
            resp, prompt, status_text = local_doc_qa.get_knowledge_based_conent_test(query=query, vs_path=vs_path,
                                                                        score_threshold=score_threshold,
                                                                        vector_search_top_k=vector_search_top_k,
                                                                        chunk_conent=chunk_conent,
                                                                        chunk_size=chunk_size)
            if not resp["source_documents"]:
                yield history + [[query,
                                  "根据您的设定，没有匹配到任何内容，请确认知识库中是否有相关资料，或检查您设置的知识相关度 Score 阈值是否过小。"]], "", status_text
            else:
                source = "\n".join(
                    [
                        f"""<details style="margin-top: 10px"><summary>相关度[ {int(doc.metadata["score"])} ] - 出处[ {i + 1} ] - {shorten_str(os.path.split(doc.metadata["source"])[-1], 50)}</summary>\n"""
                        f"""<div style="font-size: 15px; line-height: 1.7; color:#aaa; margin: 5px 8px 0 8px">{str(doc.page_content)[:100]}...</div>\n"""
                        f"""</details>"""
                        for i, doc in
                        enumerate(resp["source_documents"])])
                history.append([query, "以下内容为知识库中满足设置条件的匹配结果：\n\n" + source])
                yield history, "", status_text
        else:
            status_text = "⚠️请选择知识库后进行检索，当前未选择知识库。"
            yield history + [[query,
                              "⚠️请选择知识库后进行检索，当前未选择知识库。"]], "", status_text

    else:
        for resp, history, status_text in local_doc_qa.get_general_answer(query=query, chat_history=history, systemPromptTxt=systemPromptTxt, streaming=streaming):
            yield history, "", status_text

    flag_csv_logger.flag([query, vs_path, history, mode], username=FLAG_USER_NAME)

def change_mode(mode, history, vs_id):
    # 根据不同的模式进行处理
    if mode == "专业问答":
        # 更新可见性，将专业问答组件设置为可见，其他组件设置为不可见
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            [[None, init_message]] + [[None, knowledge_answer]]
        )
    elif mode == "知识库检索":
        if vs_id == "新建知识库":
            # 更新可见性，将知识库检索组件设置为可见，其他组件设置为不可见
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                [[None, init_message]] + [[None, kowledge_retrieval]]
            )
        else:
            # 更新可见性，将知识库检索组件设置为可见，其他组件也设置为可见
            return (
                gr.update(visible=True),
                gr.update(visible=True),
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                [[None, init_message]] + [[None, kowledge_retrieval]]
            )
    elif mode == "在线问答":
        # 更新可见性，将在线问答组件设置为不可见，其他组件也设置为不可见
        return (
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=True),
            [[None, init_message]] + [[None, bing_answer]]
        )
    else:
        # 更新可见性，将所有组件设置为不可见
        return (
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            [[None, init_message]]
        )


def change_chunk_conent(mode, label_conent, history):
    conent = ""
    if "chunk_conent" in label_conent:
        conent = "搜索结果上下文关联"
    elif "one_content_segmentation" in label_conent:
        conent = "内容分句入库"

    if mode:
        # 更新可见性，将组件设置为可见，将操作记录添加到历史记录中
        return (
            gr.update(visible=True),
            f"已开启{conent}"
        )
    else:
        # 更新可见性，将组件设置为不可见，将操作记录添加到历史记录中
        return (
            gr.update(visible=False),
            f"已关闭{conent}"
        )

def change_prompt(templateSelect):
    current_role = USER_PROMPT.format(role=templateSelect)
    return (
            [[None, current_role]]
        )
    
def get_vector_store(vs_id, files, sentence_size, history, one_conent, one_content_segmentation):
    """
    根据传递的参数创建或更新向量存储，并返回向量存储的路径、历史记录和更新后的选项列表
    
    参数：
    vs_id：表示向量存储的ID。
    files：表示要添加到向量存储中的文件列表。
    sentence_size：表示文章分段的最大长度。
    history：表示用户的历史记录，是一个列表，每个元素都是一个列表，包含两个元素，第一个元素是用户提出的问题，第二个元素是问题的答案或者搜索结果。
    one_conent：表示要添加到向量存储中的单个内容。
    one_content_segmentation：表示单个内容的分词结果。
    """
    vs_id = str(vs_id)  # 将 vs_id 转换为字符串
    vs_path = os.path.join(KB_ROOT_PATH, vs_id, "vector_store")  # 构建向量存储的路径，并将结果保存在 vs_path 变量中
    filelist = []
    if local_doc_qa.llm and local_doc_qa.embeddings:  # 如果 LLM 模型和 embedding 模型都加载成功
        if isinstance(files, list):
            for file in files:
                filename = os.path.split(file.name)[-1]  # 获取路径下文件名
                shutil.move(file.name, os.path.join(KB_ROOT_PATH, vs_id, "content", filename))  # 文件移动到向量存储的 content 目录下
                filelist.append(os.path.join(KB_ROOT_PATH, vs_id, "content", filename))
            logger.info(f'filelist: {filelist}')
            vs_path, loaded_files = local_doc_qa.init_knowledge_vector_store(filelist, vs_path, sentence_size)
        else:
            vs_path, loaded_files = local_doc_qa.one_knowledge_add(vs_path, files, one_conent, one_content_segmentation, sentence_size)
        
        if len(loaded_files):
            file_status = f"已添加 {len(loaded_files)} 个内容，并已加载知识库，请开始提问"
        else:
            file_status = "⚠️文件未成功加载，请重新上传文件"
    else:
        file_status = "⚠️模型未完成加载，请先在加载模型后再导入文件"
        vs_path = None
    
    logger.info(file_status)
    
    return (
        vs_path,
        None,
        file_status,
        gr.update(choices=local_doc_qa.list_file_from_vector_store(vs_path) if vs_path else []),
        gr.update(choices=get_vs_list()),
        gr.update(visible=True)
    )
    

def change_vs_name_input(vs_id, history):
    vs_id = str(vs_id)  # 将 vs_id 转换为字符串
    file_status = ""
    if vs_id == "新建知识库":
        # 如果 vs_id 是 "新建知识库"，则返回更新 visible 属性的 gr 对象，以及其他相关参数
        return (
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False),
            None,
            file_status,
            gr.update(choices=[]),
            gr.update(visible=False),
            gr.update(visible=False)
        )
    else:
        vs_path = os.path.join(KB_ROOT_PATH, vs_id, "vector_store")
        if "index.faiss" in os.listdir(vs_path):
            # 如果 vs_path 目录下存在 "index.faiss" 文件，则表示知识库已加载
            file_status = f"已加载知识库【{vs_id}】，请开始提问"
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True),
                vs_path,
                file_status,
                gr.update(choices=local_doc_qa.list_file_from_vector_store(vs_path), value=[]),
                gr.update(visible=True),
                gr.update(visible=True)
            )
        else:
            # 如果 vs_path 目录下不存在 "index.faiss" 文件，则表示知识库未上传文件
            file_status = f"⚠️已选择知识库【{vs_id}】，但当前知识库中未上传文件，请先上传文件后，再开始提问"
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True),
                vs_path,
                file_status,
                gr.update(choices=[], value=[]),
                gr.update(visible=False),
                gr.update(visible=True)
            )
                
def select_vs_change(vs_id, history, mode):
    file_status = ""
    if vs_id == "新建知识库":
        return None, gr.update(visible=False), gr.update(visible=False), file_status

    vs_path = os.path.join(KB_ROOT_PATH, vs_id, "vector_store")
    if "index.faiss" in os.listdir(vs_path):
        file_status = f"已加载知识库【{vs_id}】，请开始提问。"
        if mode == '知识库检索':
            # 如果模式为知识库检索，则更新可见性为True
            return vs_path, gr.update(visible=True), gr.update(visible=True), file_status
        else:
            # 如果模式不是知识库检索，则更新可见性为False
            return vs_path, gr.update(visible=False), gr.update(visible=False), file_status
    else:
        file_status = f"⚠️已选择知识库【{vs_id}】，但当前知识库中未上传文件，请先上传文件后，再开始提问"
        return vs_path, gr.update(visible=False), gr.update(visible=False), file_status
        
        
# 自动化加载固定文件间中文件
def reinit_vector_store(vs_id, history):
    try:
        # 删除向量存储路径下的文件夹
        shutil.rmtree(os.path.join(KB_ROOT_PATH, vs_id, "vector_store"))
        # 重新创建向量存储路径
        vs_path = os.path.join(KB_ROOT_PATH, vs_id, "vector_store")
        # 设置文本入库分句长度限制
        sentence_size = gr.Number(value=SENTENCE_SIZE, precision=0,
                                  label="文本入库分句长度限制",
                                  interactive=True, visible=True)
        # 初始化知识库向量存储
        vs_path, loaded_files = local_doc_qa.init_knowledge_vector_store(os.path.join(KB_ROOT_PATH, vs_id, "content"),
                                                                         vs_path, sentence_size)
        model_status = """知识库构建成功"""
    except Exception as e:
        logger.error(e)
        model_status = """⚠️知识库构建未成功"""
        logger.error(model_status)
    # 返回更新后的历史记录，添加知识库构建状态
    return model_status


def refresh_vs_list():
    # 获取知识库列表，并更新图形界面中的选择列表
    choices = get_vs_list()
    return gr.update(choices=choices), gr.update(choices=choices)


def delete_file(vs_id, files_to_delete, chatbot):
    # 获取向量存储路径和内容路径
    vs_path = os.path.join(KB_ROOT_PATH, vs_id, "vector_store")
    content_path = os.path.join(KB_ROOT_PATH, vs_id, "content")
    
    # 构建待删除文件的完整路径列表
    docs_path = [os.path.join(content_path, file) for file in files_to_delete]
    
    # 从向量存储中删除文件，并获取删除状态
    status = local_doc_qa.delete_file_from_vector_store(vs_path=vs_path, filepath=docs_path)
    
    # 如果删除状态不包含"fail"，则表示删除成功
    if "fail" not in status:
        # 遍历待删除文件的路径列表，如果文件存在，则删除文件
        for doc_path in docs_path:
            if os.path.exists(doc_path):
                os.remove(doc_path)
    
    # 获取剩余文件列表
    rested_files = local_doc_qa.list_file_from_vector_store(vs_path)
    
    # 根据删除状态和剩余文件列表的情况，设置知识库状态信息
    if "fail" in status:
        vs_status = "文件删除失败"
    elif len(rested_files) > 0:
        vs_status = "文件删除成功"
    else:
        vs_status = f"⚠️文件删除成功，知识库【{vs_id}】中无已资料，请先上传文件后，再开始提问"
    
    # 记录日志信息
    logger.info(",".join(files_to_delete) + vs_status)
    
    # 更新图形界面中的选择列表和聊天记录
    choices = local_doc_qa.list_file_from_vector_store(vs_path)
    
    return gr.update(choices=choices, value=[]), vs_status


def delete_vs(vs_id, chatbot):
    try:
        # 删除知识库目录
        shutil.rmtree(os.path.join(KB_ROOT_PATH, vs_id))
        
        # 设置删除成功的状态信息
        status = f"成功删除知识库【{vs_id}】"
        
        # 记录日志信息
        logger.info(status)
        
        # 更新图形界面操作：选择列表、按钮可见性、聊天记录可见性
        return (
            gr.update(choices=get_vs_list(), value=get_vs_list()[0]),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False),
            status,
            gr.update(visible=False)
        )
    except Exception as e:
        # 记录错误日志信息
        logger.error(e)
        
        # 设置删除失败的状态信息
        status = f"⚠️删除知识库【{vs_id}】失败"
        
        # 更新图形界面操作：按钮可见性、选择列表可见性、聊天记录可见性
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            status,
            gr.update(visible=True)
        )
        
            
def add_vs_name(vs_name):
    if vs_name is None or len(vs_name.strip()) == 0:
        vs_status = f'请输入新建知识库名称'
        # 更新图形界面操作：按钮可见性、选择列表可见性、聊天记录可见性
        return (
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False),
            vs_status,
            gr.update(visible=False)
        )
    elif vs_name in get_vs_list():
        # 如果输入的知识库名称与已有的知识库名称冲突
        vs_status = "⚠️与已有知识库名称冲突，请重新选择其他名称后提交"
        
        # 更新图形界面操作：按钮可见性、选择列表可见性、聊天记录可见性
        return (
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False),
            vs_status,
            gr.update(visible=False)
        )
    else:
        # 如果输入的知识库名称与已有的知识库名称不冲突
        
        # 新建上传文件存储路径
        if not os.path.exists(os.path.join(KB_ROOT_PATH, vs_name, "content")):
            os.makedirs(os.path.join(KB_ROOT_PATH, vs_name, "content"))
        
        # 新建向量库存储路径
        if not os.path.exists(os.path.join(KB_ROOT_PATH, vs_name, "vector_store")):
            os.makedirs(os.path.join(KB_ROOT_PATH, vs_name, "vector_store"))
        
        # 设置新增知识库成功的状态信息
        vs_status = f"""已新增知识库【{vs_name}】,在开始对话前，先完成资料上传"""
                
        # 更新图形界面操作：选择列表、按钮可见性、聊天记录可见性
        return (
            gr.update(visible=True, choices=get_vs_list(), value=vs_name),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            vs_status,
            gr.update(visible=True)
        )