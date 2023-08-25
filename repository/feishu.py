from typing import Union, List, Optional, Union
from fastapi import BackgroundTasks, HTTPException
import requests
import os
import json
import models.feishu_api as models
import mimetypes
# from sessions.chat_session_feishu import ChatSessionFeishu
# from models.feishu_api import FeishuChatSessionKey
from sessions.session_manager import global_chat_session_feishu_manager, global_msg_id_que
from configs import APP_ID, APP_SECRET,FEISHU_API_VERBOSE
import  time
import re 
import httpx
import asyncio

tenant_access_token_dict = {}
tenant_access_token=""
tenant_access_token_expire = 0
global_titles = {} #key: sub_id, value: title/name
global_ticket_title={}
DEFAULT_TENANT_ACCESS_TOKEN = ""
DEFAULT_TENANT_ACCESS_TOKEN_EXPIRE=0

# async def process_new_message(input:models.OnNewMessageInput):
#     print('start processing new msg')
#     if FEISHU_API_VERBOSE:
#         print(input.json(indent=2))
#     # renew_tenant_access_token()
#     message = input.event.message
#     message_type=message.message_type
#     message_id=message.message_id
#     if message_id in list(global_msg_id_que.queue):
#         return
#     session_key = FeishuChatSessionKey(
#         chat_id=message.chat_id, 
#         open_id=input.event.sender.sender_id.open_id,
#         user_id=input.event.sender.sender_id.user_id
#     )
#     feishu_chat_session:ChatSessionFeishu=await global_chat_session_feishu_manager.get_chat_session(session_key=session_key)
#     feishu_chat_session.renew_tenant_access_token()
#     # download_path = f"./chat_save_dir/{message.chat_id}/"
#     # if not os.path.exists(download_path):
#     #     os.makedirs(download_path)
#     match message_type:
#         case "file":
#             # content=feishu_models.Content.parse_raw(input.event.message.content)
#             content=json.loads(input.event.message.content)
#             # print("content:", content)
#             (succ, downloaded_path)=feishu_repos.download_files(
#                 message_id=message_id,
#                 file_key=content['file_key'],
#                 file_type='file',
#                 download_path=feishu_chat_session.save_file_dir+content['file_name']
#             )
#             if succ:
#                 global_msg_id_que.put(message_id)
#                 print(downloaded_path, " downloaded")
#                 feishu_chat_session.on_file_upload(
#                     file_saved_path=downloaded_path
#                 )
#                 feishu_repos.reply_message(
#                 message_id=message_id, 
#                 data= models.FeishuReplyMessageData(
#                     content=json.dumps({"text":"我已经成功收到了这个文件，请提问吧！"}),
#                     msg_type='text'
#                 ))
#         case "image":
#             feishu_repos.reply_message(
#                 message_id=message_id, 
#                 data= models.FeishuReplyMessageData(
#                     content=json.dumps({"text":"Sorry, I can't deal with Images Now"}),
#                     msg_type='text'
#                 ))
#             return
#         case "text":
#             try:
#                 msg = json.loads(message.content).get("text")
#             except ValueError:
#                 print(message.content)
#                 print('json.load error')
            
#             global_msg_id_que.put(message_id)
#             urls = find_urls(msg)
#             if len(urls) >0:
#                 feishu_urls = check_feishu_urls(urls)
#                 if len(feishu_urls) > 0 and len(feishu_urls) == len(urls):
#                     reply_message(
#                         message_id=message_id,
#                         data= models.FeishuReplyMessageData(
#                             content=json.dumps({"text":"你的消息中含有飞书文档的url，我将开始下载这些文件。请确保你有访问这些文档的权限。"}),
#                             msg_type='text'
#                         ),
#                         tenant_access_token=feishu_chat_session.tenant_access_token
#                     )
#                     all_export = await deal_with_feishu_urls(
#                         message_id=message_id, 
#                         feishu_urls=feishu_urls, 
#                         download_path=feishu_chat_session.save_file_dir,
#                         tenant_access_token=feishu_chat_session.tenant_access_token
#                     )
#                     if not all_export:
#                         reply_text="文件导出时似乎遇到了问题，可能有部分文件我没导出。请确保你的URL是正确的，或者联系开发人员。"
#                     else:
#                         reply_text="所有文档/文件我都导出了，现在可以开始回答你的问题"
#                     reply_message(
#                         message_id=message_id,
#                         data= models.FeishuReplyMessageData(
#                             content=json.dumps({"text":reply_text}),
#                             msg_type='text'
#                         ),
#                         tenant_access_token=feishu_chat_session.tenant_access_token
#                     )
#                     #回复后结束
#                     if not all_export:
#                         return
#                     url_map_prompt = f""
#                     for item in all_export:
#                         file_name=item.download_path.split('/')[-1]
#                         url_map_prompt += f"the file of url:```{item.url}``` is exported and saved as {file_name}\n"
#                         feishu_chat_session.on_file_upload(
#                             file_saved_path=item.download_path
#                         )
                    
#                     msg += url_map_prompt
#                     await feishu_chat_session.on_new_text_message_entered(msg=msg)
#                 else:
#                     feishu_chat_session.on_message_generated("对不起，您消息中似乎包含了非飞书的URL，我不能处理。")
#                     return
#             else:
#                 await feishu_chat_session.on_new_text_message_entered(msg=msg)
#             return

async def renew_chat_session(user_id: str, tenant_access_token:str=DEFAULT_TENANT_ACCESS_TOKEN):
    await global_chat_session_feishu_manager.renew_session_by_user_id(user_id=user_id)
    send_message(
        receive_id_type='user_id',
        body_data=models.FeishuSendMessageBody(
            receive_id=user_id,
            msg_type="text",
            content=json.dumps({"text":"好的，我已经忘记了之前的对话，请开始新的对话。"})
        )
    )

def check_feishu_urls(urls: List[str]):
    feishu_urls = []
    for item in urls:
        if 'feishu' in item:
            feishu_urls.append(item)
    return feishu_urls 

async def deal_with_feishu_urls(message_id:str,feishu_urls: List[str], download_path: str = "", tenant_access_token:str=DEFAULT_TENANT_ACCESS_TOKEN):
    export_tasks:List[models.ExportTaskStatus] = []
    for url in feishu_urls:
        print(f'dealing with {url}')
        (token, file_type) = get_file_token_by_url(url)
        print(token, file_type)
        task_tickets=[]
        if file_type in ['sheets', 'bitable']:
            sub_ids=get_sub_id(app_token=token, file_type=file_type,tenant_access_token=tenant_access_token)
            if len(sub_ids) > 0:
                for sub_id in sub_ids:
                    ticket = create_export_task(file_token=token, file_type=file_type, sub_id=sub_id,tenant_access_token=tenant_access_token)
                    task_tickets.append(ticket)
                    if sub_id in global_titles.keys():
                        global_ticket_title[ticket] = global_titles[sub_id] 
        else:
            task_tickets.append(create_export_task(file_token=token, file_type=file_type,tenant_access_token=tenant_access_token))
        for task_ticket in task_tickets:
            export_tasks.append(
                models.ExportTaskStatus(
                    url=url,
                    message_id=message_id,
                    type=file_type,
                    token=token,
                    task_ticket=task_ticket,
                    task_status=0,
                    download_path= global_ticket_title[task_ticket] if task_ticket in global_ticket_title.keys() else None
                )
            )
    max_try = 3
    all_finished = False
    while True and max_try > 0:
        print(len(export_tasks))
        for item in export_tasks:
            if item.downloaded:
                continue
            if item.task_status == 0:
                (finished, result) = await get_export_result(ticket=item.task_ticket, token=item.token,tenant_access_token=tenant_access_token)
                # print(item, finished, result)
            if finished:
                item.task_status = 1 if result else -1
                if result:
                    item.result=result
                    try:
                        if item.download_path:
                            download_file_path = download_path + item.result.file_name+'_'+ item.download_path + '.' + item.result.file_extension
                        else:
                            download_file_path = download_path + item.result.file_name+'_'+item.result.file_token + '.' + item.result.file_extension
                        print('download path=', download_file_path)
                        (download_result, path) = download_export_file(
                            item.result.file_token,
                            download_file_path,
                            tenant_access_token=tenant_access_token
                        )
                        if download_result:
                            item.download_path=download_file_path
                            item.downloaded=True
                    except Exception as e:
                        print(e)
            else:
                item.task_status = 0
        if 0 not in [item.task_status for item in export_tasks]:
            all_finished = True
            break
        await asyncio.sleep(2)
        max_try-=1
    if not all_finished:
        return False
    return export_tasks

def find_urls(text: str):
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    if len(urls) <= 0:
        return []
    return urls

def get_tenant_access_token(app_id:str=APP_ID, app_secret:str=APP_SECRET) -> Union[str, int]:
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({
        "app_id": app_id,
        "app_secret": app_secret,
    })


    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    if FEISHU_API_VERBOSE:
        print(response.text)
    try:
        content=dict(json.loads(response.text))
        # global tenant_access_token,tenant_access_token_expire,tenant_access_token_dict
        # tenant_access_token=content.get('tenant_access_token')
        # tenant_access_token_expire = content['expire'] + int(time.time())
        tenant_access_token_dict[app_id] = (content.get('tenant_access_token'), content['expire'] + int(time.time()))
        return tenant_access_token_dict[app_id]
    except ValueError as e:
        print(e)


def renew_tenant_access_token(tenant_access_token_expire: int):
    if int(time.time()) >= tenant_access_token_expire:
        return get_tenant_access_token()

def reply_message(message_id: str, data: models.FeishuReplyMessageData,tenant_access_token: str=DEFAULT_TENANT_ACCESS_TOKEN):
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"

    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }

    
    response = requests.post(url, headers=headers, data=data.json())
    if FEISHU_API_VERBOSE:
        tag = 'reply_message'
        print(tag,json.dumps(data.json()))
        print(tag,response.status_code)
        print(tag,response.text)

def send_message(receive_id_type: str, body_data:models.FeishuSendMessageBody,tenant_access_token: str=DEFAULT_TENANT_ACCESS_TOKEN):
    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type}"

    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    response=requests.post(url,headers=headers, data=body_data.json())
    if FEISHU_API_VERBOSE:
        print(response.status_code)
        print(response.text)


def download_files(message_id:str, file_key:str, file_type:str,download_path:str,tenant_access_token: str=DEFAULT_TENANT_ACCESS_TOKEN):
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/resources/{file_key}?type={file_type}"

    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
    }
    response = requests.get(url, headers=headers)
    with open(f"{download_path}", "wb") as file:
        file.write(response.content)

    # print(response.status_code)
    if response.status_code==200:
        return (True, download_path)
    if FEISHU_API_VERBOSE:
        tag = 'download_files'
        print(tag,response.status_code)
        print(tag,response.text)
    return (False, download_path)




def upload_file(file_path:str, body:models.UploadFileBody,tenant_access_token: str=DEFAULT_TENANT_ACCESS_TOKEN):
    url = f"https://open.feishu.cn/open-apis/im/v1/files"

    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
    }
    file= open(f"{file_path}", "rb") 

    response = requests.post(url, headers=headers, data=body.dict(), files={"file":file})
    # response = requests.post(url, headers=headers, data=)

    if FEISHU_API_VERBOSE:
        tag = 'upload_file'
        print(tag,response.status_code)
        print(tag,response.content)
    try:
        response_body = json.loads(response.text)
        return response_body['data']['file_key']
    except Exception as e: print(e)

def upload_image(image_path: str, upload_body: models.UploadImageBody,tenant_access_token: str=DEFAULT_TENANT_ACCESS_TOKEN):

    url = f"https://open.feishu.cn/open-apis/im/v1/images"

    headers = {
        "Authorization": f"Bearer {tenant_access_token}"
    }
    image=open(image_path,"rb")
    response = requests.post(url, headers=headers, data=upload_body.dict(), files={"image":image})
    # response = requests.post(url, headers=headers, data=)
    if FEISHU_API_VERBOSE:
        tag = 'upload_image'
        print(tag,response.status_code)
        print(tag,response.headers['X-Tt-Logid'])  # for debug or oncall
        print(tag,response.content)  # Print Response
   
    try:
        response_body = json.loads(response.text)
        return response_body['data']['image_key']
    except Exception as e: print(e)


def get_file_token_by_url(url: str):
    splits = url.split('/')
    # print(splits)
    if len(splits) <= 3:
        return (None, None)
    token, type= splits[-1].split('?')[0], splits[-2]
    if token[-1] == '#':
        token=token[:-1]
    if type =="base":
        type='bitable'
    return (token, type)


def file_extension_matcher(file_type):
    # print('matcher, file_type= ', file_type)
    return_type= None
    match file_type:
        case 'sheets'|'bitable'|'base':
            return_type= 'csv'
        case 'doc'|'docx':
            return_type='pdf'

    return return_type 

def get_sub_id(app_token: str, file_type: str,tenant_access_token: str=DEFAULT_TENANT_ACCESS_TOKEN)-> List[str]:
    headers = {
        "Authorization": f"Bearer {tenant_access_token}"
    }
    if file_type == 'sheets':
        url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{app_token}/sheets/query"
        response=requests.get(url=url, headers=headers)
        if response.status_code==200 and response.text:
            query_list = models.SheetQueryResultList.parse_obj(json.loads(response.text)['data'])
            for item in query_list.sheets:
                global_titles[item.sheet_id] = item.title
            return [item.sheet_id for item in query_list.sheets]
    elif file_type == 'bitable':
        url=f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
        response=requests.get(url=url, headers=headers)
        if FEISHU_API_VERBOSE:
            print(response.status_code, response.text)
        if response.status_code==200 and response.text:
            query_list = models.BitableQueryResultList.parse_obj(json.loads(response.text)['data'])
            for item in query_list.items:
                global_titles[item.table_id] = item.name
            return [item.table_id for item in query_list.items]
    if url is None:
        return None
    
    

    return

#return ticket
def create_export_task(file_token, file_type, sub_id:str=None,tenant_access_token: str=DEFAULT_TENANT_ACCESS_TOKEN) -> str:
    url = f"https://open.feishu.cn/open-apis/drive/v1/export_tasks"
    headers = {
        "Authorization": f"Bearer {tenant_access_token}"
    }
    ext = file_extension_matcher(file_type)
    if file_type =="sheets":
        file_type="sheet"

    request_body = {
        "file_extension": ext,
        "token": file_token,
        "type":file_type,
        "sub_id": sub_id
    }
    
    response = requests.post(url, headers=headers, data=request_body)
    if FEISHU_API_VERBOSE:
        tag = 'create_export_task'
        print(tag, request_body)
        print(tag,response.status_code)
        print(tag,response.headers['X-Tt-Logid'])  # for debug or oncall
        print(tag,response.content)  # Print Response
    try:
        response_body = json.loads(response.text)
        return response_body['data']['ticket']
    except Exception as e:
        print(e)
        return None


async def get_export_result(ticket, token,tenant_access_token: str=DEFAULT_TENANT_ACCESS_TOKEN) -> Union[bool, models.ExportTaskResult]:
    url = f"https://open.feishu.cn/open-apis/drive/v1/export_tasks/{ticket}?token={token}"
    headers = {
        "Authorization": f"Bearer {tenant_access_token}"
    }
    async with httpx.AsyncClient() as client:
        response=await client.get(url, headers=headers)
    # response = requests.get(url, headers=headers)
    status_code= response.status_code
    # print('get_export_result ', status_code, response.text)
    try:
        result=models.ExportTaskResult.parse_obj(json.loads(response.text)['data']['result'])
    except Exception as e:
        print(e)
        return (True, None)
    job_status=result.job_status
    if job_status is not None and job_status==0:
        return (True, result)
    elif job_status>=3:
        return (True,None)
    else:
        return (False, None)
    
def download_export_file(file_token, download_path,tenant_access_token: str=DEFAULT_TENANT_ACCESS_TOKEN):
    url = f"https://open.feishu.cn/open-apis/drive/v1/export_tasks/file/{file_token}/download"

    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
    }
    response = requests.get(url, headers=headers)
    status_code=response.status_code
    # print(response,status_code)
    if status_code != 200:
        raise HTTPException(status_code=400, detail="Download failed")
    
    with open(f"{download_path}", "wb") as file:
        file.write(response.content)
    return (True, download_path)
    

    
(DEFAULT_TENANT_ACCESS_TOKEN,DEFAULT_TENANT_ACCESS_TOKEN_EXPIRE) = get_tenant_access_token()


