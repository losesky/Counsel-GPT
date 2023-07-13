from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from module.toolkit import count_token, remove_html_tags, remove_all_html_tags, token_message
from vectorstores import MyFAISS
from langchain.document_loaders import TextLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import BSHTMLLoader
from langchain.document_loaders import (CSVLoader,
                                        UnstructuredFileLoader,
                                        TextLoader)
from langchain.document_loaders import Docx2txtLoader
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import UnstructuredPowerPointLoader
from configs.model_config import *
from loader.urls_loader import SeleniumURLLoader
import datetime
from textsplitter import ChineseTextSplitter
from typing import List
from utils import torch_gc
from tqdm import tqdm
from pypinyin import lazy_pinyin
from models.base import (BaseAnswer)
from agent.search_api import baidu_search, bing_search, google_search
from langchain.docstore.document import Document
from functools import lru_cache
from textsplitter.zh_title_enhance import zh_title_enhance


# patch HuggingFaceEmbeddings to make it hashable
def _embeddings_hash(self):
    return hash(self.model_name)


HuggingFaceEmbeddings.__hash__ = _embeddings_hash


# will keep CACHED_VS_NUM of vector store caches
@lru_cache(CACHED_VS_NUM)
def load_vector_store(vs_path, embeddings):
    return MyFAISS.load_local(vs_path, embeddings)


def tree(filepath, ignore_dir_names=None, ignore_file_names=None):
    """返回两个列表，第一个列表为 filepath 下全部文件的完整路径, 第二个为对应的文件名"""
    if ignore_dir_names is None:
        ignore_dir_names = []
    if ignore_file_names is None:
        ignore_file_names = []
    ret_list = []
    if isinstance(filepath, str):
        if not os.path.exists(filepath):
            print("路径不存在")
            return None, None
        elif os.path.isfile(filepath) and os.path.basename(filepath) not in ignore_file_names:
            return [filepath], [os.path.basename(filepath)]
        elif os.path.isdir(filepath) and os.path.basename(filepath) not in ignore_dir_names:
            for file in os.listdir(filepath):
                fullfilepath = os.path.join(filepath, file)
                if os.path.isfile(fullfilepath) and os.path.basename(fullfilepath) not in ignore_file_names:
                    ret_list.append(fullfilepath)
                if os.path.isdir(fullfilepath) and os.path.basename(fullfilepath) not in ignore_dir_names:
                    ret_list.extend(tree(fullfilepath, ignore_dir_names, ignore_file_names)[0])
    return ret_list, [os.path.basename(p) for p in ret_list]


def load_file(filepath, sentence_size=SENTENCE_SIZE, using_zh_title_enhance=ZH_TITLE_ENHANCE):
    if isinstance(filepath, str):
        if filepath.endswith(".doc") or filepath.endswith(".docx"):
            loader = Docx2txtLoader(filepath)
        elif filepath.endswith(".pdf"):
            loader = PyPDFLoader(filepath)
        elif filepath.endswith(".txt"):
            loader = TextLoader(filepath, encoding="utf-8")
        elif filepath.endswith(".csv"):
            loader = CSVLoader(filepath, encoding="utf-8")
        elif filepath.endswith(".ppt") or filepath.endswith(".pptx"):
            loader = UnstructuredPowerPointLoader(filepath)
        elif filepath.endswith(".html"):
            loader = BSHTMLLoader(file_path=filepath, open_encoding='utf-8')
        elif filepath.lower().endswith(".md"):
            loader = UnstructuredFileLoader(filepath, mode="elements")        
        else:
            loader = UnstructuredFileLoader(filepath, mode="elements")
    elif isinstance(filepath, list):
        loader = SeleniumURLLoader(filepath)
    
    docs = loader.load()
    if isinstance(filepath, str):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        docs = text_splitter.split_documents(docs)    
   
    if using_zh_title_enhance and isinstance(filepath, str):
        docs = zh_title_enhance(docs)
        write_check_file(filepath, docs)
    
    # logger.info(docs)
    return docs


def write_check_file(filepath, docs):
    folder_path = os.path.join(os.path.dirname(filepath), "tmp_files")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    fp = os.path.join(folder_path, 'load_file.txt')
    with open(fp, 'a+', encoding='utf-8') as fout:
        fout.write("filepath=%s,len=%s" % (filepath, len(docs)))
        fout.write('\n')
        for i in docs:
            fout.write(str(i))
            fout.write('\n')
        fout.close()


def generate_prompt(history_len, chat_history: List[list], systemPromptTxt: str, query: str, prompt_template: str = PROMPT_TEMPLATE) -> str:
    if '{question}' in systemPromptTxt and "{context}" in systemPromptTxt:
        prompt = prompt_template.format(question=query, context=systemPromptTxt)
    else:
        bot = ""
        if len(chat_history) > 0:
            start_index = max(0, len(chat_history) - history_len)
            for i in range(start_index, len(chat_history)):
                bot += remove_all_html_tags(chat_history[i][1]) + "\n"
                prompt = systemPromptTxt+ "\n----------\n" + bot + "\n----------\n" + "我的问题是：" + query
        else:
            prompt = systemPromptTxt+ "\n----------\n" + "我的问题是：" + query
    return prompt


def knowlege_prompt(chat_history: List[list],
                    related_docs: List[str],
                    query: str,
                    prompt_template: str = PROMPT_TEMPLATE, ) -> str:
    last_data = chat_history[-1]
    user, bot = remove_all_html_tags(last_data[0]), remove_all_html_tags(last_data[1])
    context = "\n----------\n".join([doc.page_content for doc in related_docs])
    if user and bot:
        prompt = prompt_template.replace("{user}", user).replace("{bot}", bot).replace("{question}", query).replace("{context}", context)
    elif bot:
        prompt = prompt_template.replace("user:{user}", '').replace("{bot}", bot).replace("{question}", query).replace("{context}", context)
    else:
        prompt = prompt_template.replace("user:{user}", '').replace("bot:{bot}", '').replace("{question}", query).replace("{context}", context)
    return prompt


def search_prompt(search_rang: str,
                  chat_history: List[list],
                  related_docs: List[str],
                  query: str,
                  prompt_template: str = PROMPT_TEMPLATE, ) -> str:
    if '上下文' in search_rang:
        last_data = chat_history[-1]
        context = remove_html_tags(last_data[1])
    else:
        context = "\n----------\n".join([doc.page_content for doc in related_docs])
    prompt = prompt_template.replace("user:{user}", '').replace("bot:{bot}", '').replace("{question}", query).replace("{context}", context)
    return prompt


def search_result2docs(search_rang, results):
    docs = []
    if '概要' in search_rang:
        for result in results:
            doc = Document(page_content=result["snippet"] if "snippet" in result.keys() else "",
                    metadata={"source": result["link"] if "link" in result.keys() else "",
                                "filename": result["title"] if "title" in result.keys() else ""})
            docs.append(doc)
    elif '全网' in search_rang:
        urls = []
        for result in results:
            url = result["link"]
            urls.append(url)
        docs = load_file(urls)
    return docs


class LocalDocQA:
    llm: BaseAnswer = None
    embeddings: object = None
    top_k: int = VECTOR_SEARCH_TOP_K
    chunk_size: int = CHUNK_SIZE
    chunk_conent: bool = True
    score_threshold: int = VECTOR_SEARCH_SCORE_THRESHOLD
    interrupted = False

    def init_cfg(self,
                 embedding_model: str = EMBEDDING_MODEL,
                 embedding_device=EMBEDDING_DEVICE,
                 llm_model: BaseAnswer = None,
                 top_k=VECTOR_SEARCH_TOP_K,
                 ):
        self.llm = llm_model
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_dict[embedding_model],
                                                model_kwargs={'device': embedding_device})
        self.top_k = top_k
        
    def interrupt(self):
        self.interrupted = True

    def recover(self):
        self.interrupted = False

    def init_knowledge_vector_store(self,
                                    filepath: str or List[str],
                                    vs_path: str or os.PathLike = None,
                                    sentence_size=SENTENCE_SIZE):
        loaded_files = []
        failed_files = []
        if isinstance(filepath, str):
            if not os.path.exists(filepath):
                print("路径不存在")
                return None
            elif os.path.isfile(filepath):
                file = os.path.split(filepath)[-1]
                try:
                    docs = load_file(filepath, sentence_size)
                    logger.info(f"{file} 已成功加载")
                    loaded_files.append(filepath)
                except Exception as e:
                    logger.error(e)
                    logger.error(f"{file} 未能成功加载")
                    return None
            elif os.path.isdir(filepath):
                docs = []
                for fullfilepath, file in tqdm(zip(*tree(filepath, ignore_dir_names=['tmp_files'])), desc="加载文件"):
                    try:
                        docs += load_file(fullfilepath, sentence_size)
                        loaded_files.append(fullfilepath)
                    except Exception as e:
                        logger.error(e)
                        failed_files.append(file)

                if len(failed_files) > 0:
                    logger.error("以下文件未能成功加载：")
                    for file in failed_files:
                        logger.error(f"{file}\n")

        else:
            docs = []
            for file in filepath:
                try:
                    docs += load_file(file)
                    logger.info(f"{file} 已成功加载")
                    loaded_files.append(file)
                except Exception as e:
                    logger.error(e)
                    logger.error(f"{file} 未能成功加载")
        if len(docs) > 0:
            logger.info("文件加载完毕，正在生成向量库")
            if vs_path and os.path.isdir(vs_path) and "index.faiss" in os.listdir(vs_path):
                vector_store = load_vector_store(vs_path, self.embeddings)
                vector_store.add_documents(docs)
                torch_gc()
            else:
                if not vs_path:
                    vs_path = os.path.join(KB_ROOT_PATH,
                                           f"""{"".join(lazy_pinyin(os.path.splitext(file)[0]))}_FAISS_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}""",
                                           "vector_store")
                vector_store = MyFAISS.from_documents(docs, self.embeddings)  # docs 为Document列表
                torch_gc()

            vector_store.save_local(vs_path)
            return vs_path, loaded_files
        else:
            logger.info("文件均未成功加载，请检查依赖包或替换为其他文件再次上传。")
            return None, loaded_files

    def one_knowledge_add(self, vs_path, one_title, one_conent, one_content_segmentation, sentence_size):
        try:
            if not vs_path or not one_title or not one_conent:
                logger.error("知识库添加错误，请确认知识库名字、标题、内容是否正确！")
                return None, [one_title]
            docs = [Document(page_content=one_conent + "\n", metadata={"source": one_title})]
            if not one_content_segmentation:
                text_splitter = ChineseTextSplitter(pdf=False, sentence_size=sentence_size)
                docs = text_splitter.split_documents(docs)
            if os.path.isdir(vs_path) and os.path.isfile(vs_path + "/index.faiss"):
                vector_store = load_vector_store(vs_path, self.embeddings)
                vector_store.add_documents(docs)
            else:
                vector_store = MyFAISS.from_documents(docs, self.embeddings)  ##docs 为Document列表
            torch_gc()
            vector_store.save_local(vs_path)
            return vs_path, [one_title]
        except Exception as e:
            logger.error(e)
            return None, [one_title]
        
    def get_general_answer(self, query, chat_history=[], systemPromptTxt=SYSTEM_PROMPT, streaming: bool = STREAMING):
        prompt = generate_prompt(self.llm._history_len(), chat_history, systemPromptTxt, query)
        self.llm.recover()
        self.recover()
        logger.info(f'通用对话: \n{prompt}')
        tmp_str = ''
        for answer_result in self.llm.generatorAnswer(prompt=prompt, history=chat_history, streaming=streaming):
            if self.interrupted:
                self.llm.interrupt()
            resp = answer_result.llm_output["answer"]
            history = answer_result.history
            history[-1][0] = query
            response = {"query": query, "result": resp, "source_documents": chat_history}
            
            bot_token_count = count_token(history[-1][1][len(tmp_str):])
            tmp_str = history[-1][1]
            all_token_counts.append(bot_token_count)
            status_text = token_message(all_token_counts)
            
            yield response, history, status_text

    def get_knowledge_based_answer(self, query, vs_path, chat_history=[], streaming: bool = STREAMING):
        vector_store = load_vector_store(vs_path, self.embeddings)
        vector_store.chunk_size = self.chunk_size
        vector_store.chunk_conent = self.chunk_conent
        vector_store.score_threshold = self.score_threshold
        related_docs_with_score = vector_store.similarity_search_with_score(query, k=self.top_k)
        torch_gc()
        self.llm.recover()
        self.recover()
        new_related_docs_with_score = [doc for doc in related_docs_with_score if int(doc.metadata["score"]) <= VECTOR_SEARCH_SCORE_THRESHOLD or VECTOR_SEARCH_SCORE_THRESHOLD == 0]
        if len(new_related_docs_with_score) > 0:
            prompt = knowlege_prompt(chat_history, new_related_docs_with_score, query)
        else:
            prompt = query

        grouped_docs = {}
        for doc in new_related_docs_with_score:
            source = doc.metadata["source"]
            score = doc.metadata["score"]
            if source not in grouped_docs:
                grouped_docs[source] = []
            grouped_docs[source].append((score, doc))
        for source in grouped_docs:
            grouped_docs[source].sort(key=lambda x: x[0])

        selected_docs = [docs[0][1] for docs in grouped_docs.values()]
        logger.info(f'专业问答: \n{prompt}')
        tmp_str = ''
        for answer_result in self.llm.generatorAnswer(prompt=prompt, history=chat_history, streaming=streaming):
            if self.interrupted:
                self.llm.interrupt()
            resp = answer_result.llm_output["answer"]
            history = answer_result.history
            history[-1][0] = query
            response = {"query": query, "result": resp, "source_documents": selected_docs}
            
            bot_token_count = count_token(history[-1][1][len(tmp_str):])
            tmp_str = history[-1][1]
            all_token_counts.append(bot_token_count)
            status_text = token_message(all_token_counts)
            
            yield response, history, status_text

    # query      查询内容
    # vs_path    知识库路径
    # chunk_conent   是否启用上下文关联
    # score_threshold    搜索匹配score阈值
    # vector_search_top_k   搜索知识库内容条数，默认搜索5条结果
    # chunk_size    匹配单段内容的连接上下文长度
    def get_knowledge_based_conent_test(self, query, vs_path, chunk_conent,
                                    score_threshold=VECTOR_SEARCH_SCORE_THRESHOLD,
                                    vector_search_top_k=VECTOR_SEARCH_TOP_K, chunk_size=CHUNK_SIZE):
        vector_store = load_vector_store(vs_path, self.embeddings)
        vector_store.chunk_conent = chunk_conent
        vector_store.score_threshold = score_threshold
        vector_store.chunk_size = chunk_size
        related_docs_with_score = vector_store.similarity_search_with_score(query, k=vector_search_top_k)
        torch_gc()
        
        new_related_docs_with_score = [doc for doc in related_docs_with_score if int(doc.metadata["score"]) <= score_threshold or score_threshold == 0]

        if not new_related_docs_with_score:
            response = {"query": query, "source_documents": []}
            return response, ""

        grouped_docs = {}
        for doc in new_related_docs_with_score:
            source = doc.metadata["source"]
            score = doc.metadata["score"]
            if source not in grouped_docs:
                grouped_docs[source] = []
            grouped_docs[source].append((score, doc))
        for source in grouped_docs:
            grouped_docs[source].sort(key=lambda x: x[0])

        selected_docs = [docs[0][1] for docs in grouped_docs.values()]
        
        prompt = "\n".join([doc.page_content for doc in new_related_docs_with_score])
        
        response = {"query": query, "source_documents": selected_docs}
        
        return response, prompt, ''

    def get_search_result_based_answer(self, query, search_source, search_rang,  chat_history=[], streaming: bool = STREAMING):
        if 'Baidu' in search_source:
            results = baidu_search(query)
        elif 'Google' in search_source:
            results = google_search(query)
        elif 'Bing' in search_source:
            results = bing_search(query)
        result_docs = search_result2docs(search_rang, results)
        prompt = search_prompt(search_rang, chat_history, result_docs, query)
        logger.info(f'在线问答: \n{prompt}')
        tmp_str = ''
        self.llm.recover()
        self.recover()
        for answer_result in self.llm.generatorAnswer(prompt=prompt, history=chat_history,
                                                      streaming=streaming):
            if self.interrupted:
                self.llm.interrupt()
            resp = answer_result.llm_output["answer"]
            history = answer_result.history
            history[-1][0] = query
            response = {"query": query,
                        "result": resp,
                        "source_documents": result_docs}
            
            bot_token_count = count_token(history[-1][1][len(tmp_str):])
            tmp_str = history[-1][1]
            all_token_counts.append(bot_token_count)
            status_text = token_message(all_token_counts)
            
            yield response, history, status_text

    def delete_file_from_vector_store(self,
                                      filepath: str or List[str],
                                      vs_path):
        vector_store = load_vector_store(vs_path, self.embeddings)
        status = vector_store.delete_doc(filepath)
        return status

    def update_file_from_vector_store(self,
                                      filepath: str or List[str],
                                      vs_path,
                                      docs: List[Document],):
        vector_store = load_vector_store(vs_path, self.embeddings)
        status = vector_store.update_doc(filepath, docs)
        return status

    def list_file_from_vector_store(self,
                                    vs_path,
                                    fullpath=False):
        vs_file = os.path.join(vs_path, "index.faiss")  # 构建向量存储的路径，并将结果保存在 vs_path 变量中
        if os.path.exists(vs_file):
            vector_store = load_vector_store(vs_path, self.embeddings)
            docs = vector_store.list_docs()
            if fullpath:
                return docs
            else:
                return [os.path.split(doc)[-1] for doc in docs]
        else:
            return []
