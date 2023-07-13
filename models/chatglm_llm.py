from abc import ABC
from langchain.llms.base import LLM
from typing import Optional, List
from models.loader import LoaderCheckPoint
from models.base import (BaseAnswer,
                         AnswerResult)


class ChatGLM(BaseAnswer, LLM, ABC):
    max_token: int = 10000
    temperature: float = 0.01
    top_p = 0.9
    history_len: int = 10
    checkPoint: LoaderCheckPoint = None
    interrupted = False

    def __init__(self, checkPoint: LoaderCheckPoint = None):
        super().__init__()
        self.checkPoint = checkPoint
        
    def interrupt(self):
        self.interrupted = True

    def recover(self):
        self.interrupted = False

    @property
    def _llm_type(self) -> str:
        return "ChatGLM"

    @property
    def _check_point(self) -> LoaderCheckPoint:
        return self.checkPoint

    def _history_len(self):
        return self.history_len

    def set_history_len(self, history_len: int = 10) -> None:
        self.history_len = history_len
            
    def set_max_token(self, max_token: int = 10000) -> None:
        self.max_token = max_token
        
    def set_temperature(self, temperature: float = 0.01) -> None:
        self.temperature = temperature

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        print(f"__call:{prompt}")
        response, _ = self.checkPoint.model.chat(
            self.checkPoint.tokenizer,
            prompt,
            history=[],
            max_length=self.max_token,
            temperature=self.temperature
        )
        print(f"response:{response}")
        print(f"+++++++++++++++++++++++++++++++++++")
        return response

    def generatorAnswer(self, prompt: str,
                        history: List[List[str]] = [],
                        streaming: bool = False,
                        max_token: int = 10000,
                        temperature: float = 0.01):
        
        self.max_token = max_token
        self.temperature = temperature
        
        if streaming:
            history += [[]]
            for inum, (stream_resp, _) in enumerate(self.checkPoint.model.stream_chat(
                    self.checkPoint.tokenizer,
                    prompt,
                    history=history[-self.history_len:-1] if self.history_len > 1 else [],
                    max_length=self.max_token,
                    temperature=self.temperature
            )):
                if self.interrupted:
                    break
                else:
                    # self.checkPoint.clear_torch_cache()
                    history[-1] = [prompt, stream_resp]
                    answer_result = AnswerResult()
                    answer_result.history = history
                    answer_result.llm_output = {"answer": stream_resp}
                    yield answer_result
            
            self.checkPoint.clear_torch_cache()        
            answer_result = AnswerResult()
            answer_result.history = history
            answer_result.llm_output = {"answer": stream_resp}
            yield answer_result
                    
        else:
            response, _ = self.checkPoint.model.chat(
                self.checkPoint.tokenizer,
                prompt,
                history=history[-self.history_len:] if self.history_len > 0 else [],
                max_length=self.max_token,
                temperature=self.temperature
            )
            self.checkPoint.clear_torch_cache()
            history += [[prompt, response]]
            answer_result = AnswerResult()
            answer_result.history = history
            answer_result.llm_output = {"answer": response}
            yield answer_result


