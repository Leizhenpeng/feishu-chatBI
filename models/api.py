from pydantic import BaseModel
from typing import List, Optional
import json
import datetime


class ChatWithCodeInterpreterSession(BaseModel):
    session_id:str
    content:str
