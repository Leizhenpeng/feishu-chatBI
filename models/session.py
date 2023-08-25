from pydantic import BaseModel
from typing import List, Optional
import json
import datetime
from codeinterpreterapi import CodeInterpreterSession
from custom_codeinterpreter_session import CustomCodeInterpreterSession
from sessions.chat_session_feishu import ChatSessionFeishu

class GlobalSession(BaseModel):
    session_id:str
    code_interpreter_session:CustomCodeInterpreterSession

    class Config:
        arbitrary_types_allowed = True


class FeishuChatSession(BaseModel):
    session_id:str
    chat_session: ChatSessionFeishu

    class Config:
        arbitrary_types_allowed = True
    
