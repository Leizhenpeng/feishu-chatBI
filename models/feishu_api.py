from pydantic import BaseModel,Field
from typing import List, Optional
import json
import datetime
from fastapi import File

class FeishuAPIOutput(BaseModel):
    challenge:str

class FeishuReplyMessageData(BaseModel):
    content: str
    msg_type: str
    uuid: Optional[str]


class FeishuSendMessageBody(BaseModel):
    receive_id: Optional[str]=None
    msg_type: Optional[str] = 'text'
    content: Optional[str] = None
    uuid: Optional[str] = None


class Header(BaseModel):
    event_id: str
    event_type: str
    create_time: str
    token: str
    app_id: str
    tenant_key: str


class SenderID(BaseModel):
    union_id: Optional[str]
    user_id: Optional[str]
    open_id :Optional[str]

class Sender(BaseModel):
    sender_id: SenderID
    sender_type: str
    tenant_key: str

class Content(BaseModel):
    text: Optional[str]

class Mentions(BaseModel):
    key: str
    id:SenderID
    name: str
    tenant_key: str

class Message(BaseModel):
    message_id: str
    root_id:Optional[str]
    parent_id: Optional[str]
    create_time: str
    chat_id: str
    chat_type: str
    message_type: str
    content: Optional[str]
    mentions: Optional[List[Mentions]]=None

class Event(BaseModel):
    sender: Sender
    message: Message

class TrialInput(BaseModel):
    app_id: str
    app_secret: str
    openai_api_key: str

class OnNewMessageInput(BaseModel):
    _schema: str=Field( alias="schema")
    header:Header
    event: Event
    extra_trial: Optional[TrialInput]


class UploadFileBody(BaseModel):
    file_type:str
    file_name:str
    duration:Optional[int]=None
    # file: Optional[File]=None
    class Config:
        extra='allow'


class UploadImageBody(BaseModel):
    image_type: str='message'
    # image: Optional[File] = None

    class Config:
        extra='allow'


class ExportTaskResult(BaseModel):
    file_extension: Optional[str]=None
    type: Optional[str]=None
    file_name: Optional[str] = None
    file_size: Optional[int]=None
    file_token: Optional[str]=None
    job_error_msg: Optional[str]=None
    job_status: Optional[int]=None

class ExportTaskStatus(BaseModel):
    url: str
    message_id: Optional[str]=None
    token: str
    type:str
    task_ticket: str
    task_status: Optional[int] = None #-1:failed, 0:waiting, 1:succ
    result:Optional[ExportTaskResult] = None
    download_path: Optional[str]=None
    downloaded:Optional[bool] = False


# class BitableQueryResult(BaseModel):

class SheetQueryResult(BaseModel):
    sheet_id: Optional[str] = None
    title:Optional[str] = None
    hidden:Optional[bool] = False
    resource_type: Optional[str] = None

class SheetQueryResultList(BaseModel):
    sheets: Optional[List[SheetQueryResult]] =None


class BitableQueryResult(BaseModel):
    table_id: Optional[str] = None
    revision: Optional[int] = None
    name: Optional[str] =None

class BitableQueryResultList(BaseModel):
    has_more: Optional[bool] = False
    page_token: Optional[str] = None
    total: Optional[int] = None
    items: Optional[List[BitableQueryResult]] = None


class FeishuChatSessionKey(BaseModel):
    chat_id: Optional[str] = None
    user_id: Optional[str] = None
    open_id: Optional[str] = None

    def __hash__(self):
        return hash((self.chat_id, self.user_id))

    def __eq__(self, other):
        if isinstance(other, FeishuChatSessionKey):
            return self.chat_id == other.chat_id and self.user_id == other.user_id
        return False


class FeishuAppInfo(BaseModel):
    app_id:Optional[str] = None
    app_secret:Optional[str] = None
    openai_api_key:Optional[str] = None