
from collections import OrderedDict
from codeinterpreterapi import CodeInterpreterSession
from custom_codeinterpreter_session import CustomCodeInterpreterSession
# import models.session as models
from typing import List
from sessions.chat_session_feishu import ChatSessionFeishu
from queue import Queue
import models.session as session_models
from models.feishu_api import FeishuChatSessionKey,FeishuAppInfo

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str) -> "ChatSessionFeishu":
        if key not in self.cache:
            return None
        value = self.cache.pop(key)
        # 把 key 放到最右边（也就是最新）
        self.cache[key] = value
        return value

    async def put(self, key: str, value: "ChatSessionFeishu") -> None:
        if key in self.cache:
            # 如果 key 已经在 cache 中，先移除旧的
            self.cache.pop(key)
        elif len(self.cache) == self.capacity:
            # 如果 cache 已满，移除最左边的元素（也就是最老的）
            key,value=self.cache.popitem(last=False)
            await value.astop()
        # 添加新的 key-value 到最右边（也就是最新）
        self.cache[key] = value

    def keys(self)->List[str]:
        return self.cache.keys()




class LRUCacheFeishu:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: FeishuChatSessionKey) -> "ChatSessionFeishu":
        if key not in self.cache:
            return None
        value = self.cache.pop(key)
        # 把 key 放到最右边（也就是最新）
        self.cache[key] = value
        return value

    async def put(self, key: FeishuChatSessionKey, value: "ChatSessionFeishu") -> None:
        if key in self.cache:
            # 如果 key 已经在 cache 中，先移除旧的
            self.cache.pop(key)
        elif len(self.cache) == self.capacity:
            # 如果 cache 已满，移除最左边的元素（也就是最老的）
            key,value=self.cache.popitem(last=False)
            await value.astop()
        # 添加新的 key-value 到最右边（也就是最新）
        self.cache[key] = value

    def keys(self)->List[FeishuChatSessionKey]:
        return self.cache.keys()



# class GlobalChatSessionFeishuManager(object):
#     def __init__(self,):
#         self.chat_session= LRUCache(10) 
    
#     async def get_chat_session(self, session_id:str)->"ChatSessionFeishu":
#         print(f"session_id={session_id}, cache={self.chat_session.cache}, keys = {self.chat_session.cache.keys()}")
#         session=self.chat_session.get(session_id)
#         if session is None:
#             async with ChatSessionFeishu(chat_id=session_id) as session:
#                 await self.chat_session.put(key=session_id,value=session)
#             return session
#         else:
#             return session


class GlobalChatSessionFeishuManager(object):
    def __init__(self,):
        self.chat_session= LRUCacheFeishu(10) 
    
    async def get_chat_session(self, session_key:FeishuChatSessionKey, app_info:FeishuAppInfo=None)->"ChatSessionFeishu":
        session=self.chat_session.get(session_key)
        if session is None:
            async with ChatSessionFeishu(session_key=session_key, app_info=app_info) as session:
                await self.chat_session.put(key=session_key,value=session)
            return session
        else:
            return session
    
    def get_chat_session_by_chat_id(self, chat_id)->"ChatSessionFeishu":
        for item in self.chat_session.keys():
            if item.chat_id == chat_id:
                return self.chat_session[item]
        return None
        
    async def renew_session_by_user_id(self, user_id: str)->"ChatSessionFeishu":
        print('renew', self.chat_session.keys())
        for item in self.chat_session.keys():
            if item.user_id == user_id:
                session=self.chat_session.get(item)
                app_info=session.app_info
                async with ChatSessionFeishu(session_key=item,app_info=app_info) as session:
                    await self.chat_session.put(key=item,value=session)
                    print('renewed', session)
                return session


global_chat_session_feishu_manager=GlobalChatSessionFeishuManager()
global_msg_id_que = Queue(100)