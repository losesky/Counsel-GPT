# -*- coding: utf-8 -*-

from langchain.utilities import GoogleSearchAPIWrapper
from langchain.docstore.document import Document
from configs.model_config import GOOGLE_CSE_ID, GOOGLE_API_KEY
from utils.baidu_search import BaiduSearch
from langchain.utilities import BingSearchAPIWrapper
from configs.model_config import BING_SEARCH_URL, BING_SUBSCRIPTION_KEY

def google_search(text, result_len=3):
    if not (GOOGLE_CSE_ID and GOOGLE_API_KEY):
        return [{"snippet": "First, you need to set up the proper API keys and environment variables.\
                  To set it up, create the GOOGLE_API_KEY in the Google Cloud credential console (https://console.cloud.google.com/apis/credentials) and a GOOGLE_CSE_ID using the Programmable Search Enginge (https://programmablesearchengine.google.com/controlpanel/create).\
                  Next, it is good to follow the instructions found [here](https://stackoverflow.com/questions/37083058/programmatically-searching-google-in-python-using-custom-search).",
                 "title": "env info is not found",
                 "link": "https://console.cloud.google.com/apis/credentials"}]
        
    search = GoogleSearchAPIWrapper(google_api_key=GOOGLE_API_KEY,
                                    google_cse_id=GOOGLE_CSE_ID)
    
    return search.results(text, result_len)

def baidu_search(text, result_len=3):
    search = BaiduSearch()
    
    return search.search(text, num_results=result_len)


def bing_search(text, result_len=3):
    if not (BING_SEARCH_URL and BING_SUBSCRIPTION_KEY):
        return [{"snippet": "please set BING_SUBSCRIPTION_KEY and BING_SEARCH_URL in os ENV",
                 "title": "env info is not found",
                 "link": "https://python.langchain.com/en/latest/modules/agents/tools/examples/bing_search.html"}]
    search = BingSearchAPIWrapper(bing_subscription_key=BING_SUBSCRIPTION_KEY,
                                  bing_search_url=BING_SEARCH_URL)
    return search.results(text, result_len)

