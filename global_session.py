
from collections import OrderedDict
from codeinterpreterapi import CodeInterpreterSession
from custom_codeinterpreter_session import CustomCodeInterpreterSession
from models.session import GlobalSession
from typing import List

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str) -> GlobalSession:
        if key not in self.cache:
            return None
        value = self.cache.pop(key)
        # 把 key 放到最右边（也就是最新）
        self.cache[key] = value
        return value

    def put(self, key: str, value: GlobalSession) -> None:
        if key in self.cache:
            # 如果 key 已经在 cache 中，先移除旧的
            self.cache.pop(key)
        elif len(self.cache) == self.capacity:
            # 如果 cache 已满，移除最左边的元素（也就是最老的）
            self.cache.popitem(last=False)
        # 添加新的 key-value 到最右边（也就是最新）
        self.cache[key] = value

    def keys(self)->List[str]:
        return self.cache.keys()

class GlobalCodeInterpreterSessionManager(object):

    def __init__(self,):
        self.chat_session= LRUCache(10)

    

    async def get_chat_session(self, session_id:str)->GlobalSession:
        if session_id in self.chat_session.keys():
            return self.chat_session.get(session_id)
        else:
            session =await CustomCodeInterpreterSession() 
            self.chat_session[session_id]=session
            return session
    
    async def renew_code_interpreter_session(self, session_id: str):
        session=await CustomCodeInterpreterSession() 
        self.chat_session[session_id]=session
        return session

        

global_code_interpreter_session_manager=GlobalCodeInterpreterSessionManager()