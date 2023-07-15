import torch.backends
import os
import logging
import uuid
import torch.cuda
import nltk

# 设置
os.environ["TOKENIZERS_PARALLELISM"] = "false"

APP_NAME = "langchain-ChatGLM"
APP_ENV = "development"
APP_PORT = 7890
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.INFO)
log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log")
if not os.path.isdir(log_path):
            os.makedirs(log_path)

class ColoredFormatter(logging.Formatter):
    """自定义 Formatter，用于设置不同级别的日志输出的颜色"""
    def format(self, record):
        if record.levelno == logging.INFO:
            record.msg = "\033[32m{}\033[0m".format(record.msg)
        elif record.levelno == logging.WARNING:
            record.msg = "\033[33m{}\033[0m".format(record.msg)
        elif record.levelno == logging.DEBUG:
            record.msg = "\033[33m{}\033[0m".format(record.msg)
        elif record.levelno == logging.DEBUG:
            record.msg = "\033[33m{}\033[0m".format(record.msg)
        elif record.levelno == logging.ERROR:
            record.msg = "\033[31m{}\033[0m".format(record.msg)
        return super().format(record)


if not logger.hasHandlers():
    log_file = filepath = os.path.join(log_path, f"{APP_NAME}.log")
    # 设置 Handler
    if APP_ENV != 'development':
        handler = logging.FileHandler(log_file, encoding="utf-8")
    else:
        handler = logging.StreamHandler()

    # 设置 Formatter
    formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # 设置 Handler
    handler.setFormatter(formatter)
    # 添加 Handler
    logger.addHandler(handler)


# 在以下字典中修改属性值，以指定本地embedding模型存储位置
# 如将 "text2vec": "GanymedeNil/text2vec-large-chinese" 修改为 "text2vec": "User/Downloads/text2vec-large-chinese"
# 此处请写绝对路径
text2vec_path = f"{os.path.dirname(os.path.dirname(__file__))}/package/text2vec-large-chinese"
if not os.path.exists(text2vec_path):
    text2vec_path = 'GanymedeNil/text2vec-large-chinese'
embedding_model_dict = {
    "text2vec": text2vec_path,
}

embedding_model_dict_list = list(embedding_model_dict.keys())

# Embedding model name
EMBEDDING_MODEL = "text2vec"

# Embedding running device
EMBEDDING_DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

# supported LLM models
# llm_model_dict 处理了loader的一些预设行为，如加载位置，模型名称，模型处理器实例
# 在以下字典中修改属性值，以指定本地 LLM 模型存储位置
# 如将 "chatglm-6b" 的 "local_model_path" 由 None 修改为 "User/Downloads/chatglm-6b"
# 此处请写绝对路径
local_model_path = f"{os.path.dirname(os.path.dirname(__file__))}/package/chatglm2-6b-int4"
if not os.path.exists(local_model_path):
    local_model_path = None
llm_model_dict = {
    "chatglm2-6b-int4": {
        "name": "chatglm2-6b-int4",
        "pretrained_model_name": "THUDM/chatglm2-6b-int4",
        "local_model_path": local_model_path,
        "provides": "ChatGLM"
    },

    # "fastchat-chatglm2-6b-int4": {
    #     "name": "chatglm2-6b-int4",  # "name"修改为fastchat服务中的"model_name"
    #     "pretrained_model_name": "chatglm2-6b-int4",
    #     "local_model_path": None,
    #     "provides": "FastChatOpenAILLM",  # 使用fastchat api时，需保证"provides"为"FastChatOpenAILLM"
    #     "api_base_url": "http://localhost:8000/v1"  # "name"修改为fastchat服务中的"api_base_url"
    # },
}

llm_model_dict_list = list(llm_model_dict.keys())

# LLM 名称
LLM_MODEL = "chatglm2-6b-int4"
# 量化加载8bit 模型
LOAD_IN_8BIT = False
# Load the model with bfloat16 precision. Requires NVIDIA Ampere GPU.
BF16 = False
# 本地lora存放的位置
LORA_DIR = "loras/"

# LLM lora path，默认为空，如果有请直接指定文件夹路径
LLM_LORA_PATH = ""
USE_LORA = True if LLM_LORA_PATH else False

# LLM streaming reponse
STREAMING = True

# Use p-tuning-v2 PrefixEncoder
USE_PTUNING_V2 = False

# LLM running device
LLM_DEVICE = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

# 知识库默认存储路径
KB_ROOT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")
# 知识库临时存储路径
KB_TMP_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_tmp")

# 基于上下文的prompt模版，请务必保留"{question}"和"{context}"
PROMPT_TEMPLATE = """
已知信息如下：
{context} 

user:{user} 
bot:{bot} 

用简洁和专业地回答用户的问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题” 或 “没有提供足够的相关信息”，不允许在答案中添加编造成分，答案请使用中文。 

我的问题是：
{question}
"""

# 基于上下文的prompt模版
SYSTEM_PROMPT = """我要你充当我的法律顾问，能针对问题提供全面准确的法律建议和指导，并能完成法律信息检索、合同的编写和审核以及其他与法律相关的智能问答服务。"""

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

# 缓存知识库数量
CACHED_VS_NUM = 1

# 文本分句长度
SENTENCE_SIZE = 250

# 匹配后单段上下文长度
CHUNK_SIZE = 400

# 引用上一段落字数，用于上下文
CHUNK_OVERLAP = 20

# 传入LLM的历史记录长度
LLM_HISTORY_LEN = 5

# 知识库检索时返回的匹配内容条数
VECTOR_SEARCH_TOP_K = 5

# 知识检索内容相关度 Score, 数值范围约为0-1100，如果为0，则不生效，经测试设置为小于500时，匹配结果更精准
VECTOR_SEARCH_SCORE_THRESHOLD = 0

NLTK_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nltk_data")

nltk.data.path = [NLTK_DATA_PATH] + nltk.data.path

FLAG_USER_NAME = uuid.uuid4().hex

logger.info(f"loading model config")
logger.info(f"llm device: {LLM_DEVICE} {torch.cuda.device_count()}")
logger.info(f"embedding device: {EMBEDDING_DEVICE} {torch.cuda.device_count()}")
logger.info(f"dir: {os.path.dirname(os.path.dirname(__file__))}")
logger.info(f"flagging username: {FLAG_USER_NAME}")

# 是否开启跨域，默认为False，如果需要开启，请设置为True
# is open cross domain
OPEN_CROSS_DOMAIN = False

# Bing 搜索必备变量
# 使用 Bing 搜索需要使用 Bing Subscription Key,需要在azure port中申请试用bing search
# 具体申请方式请见
# https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/create-bing-search-service-resource
# 使用python创建bing api 搜索实例详见:
# https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/quickstarts/rest/python
BING_SEARCH_URL = "https://api.bing.microsoft.com/v7.0/search"
# 注意不是bing Webmaster Tools的api key，

# 此外，如果是在服务器上，报Failed to establish a new connection: [Errno 110] Connection timed out
# 是因为服务器加了防火墙，需要联系管理员加白名单，如果公司的服务器的话，就别想了GG
BING_SUBSCRIPTION_KEY = ""

# 是否开启中文标题加强，以及标题增强的相关配置
# 通过增加标题判断，判断哪些文本为标题，并在metadata中进行标记；
# 然后将文本与往上一级的标题进行拼合，实现文本信息的增强。
ZH_TITLE_ENHANCE = False

# 默认抓取中国法院网上的法律法规
SPIDER_URL = "https://www.chinacourt.org/law.shtml"

# 保存每个token的长度
all_token_counts = []

#################################################################################################

MODULE_NAME = 'spider_logger'
logs = logging.getLogger(MODULE_NAME)
logs.setLevel(logging.INFO)
log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log")
if not os.path.isdir(log_path):
            os.makedirs(log_path)
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


# Custom Search API
GOOGLE_CSE_ID = 'a6e3d6e8c75ab4f57'
GOOGLE_API_KEY = 'AIzaSyCuab7cY7_9Fd9PgeyU2MJjQoAhjW0Q3w4'