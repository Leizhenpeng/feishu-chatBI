from pydantic import BaseModel
from typing import List, Optional
import json
import datetime


class Message(BaseModel):
    role: str
    content:str

    def to_prompt(self):
        return f'{self.role}: "{self.content}"\n'

class PSQLAgentChatInput(BaseModel):
    messages:List[Message]