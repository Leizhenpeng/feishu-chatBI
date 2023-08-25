from typing import Optional
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Depends, Body, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from models.psql import PSQLAgentChatInput

import models.api as models
import models.feishu_api as feishu_models
import repository.feishu as feishu_repos
import json
import os
from sessions.session_manager import global_chat_session_feishu_manager, global_msg_id_que
from sessions.chat_session_feishu import ChatSessionFeishu
from codeboxapi import CodeBox, set_api_key
import configs
from repository.feishu import deal_with_feishu_urls,reply_message,find_urls,check_feishu_urls

if configs.CODEBOX_API_KEY:
    set_api_key(configs.CODEBOX_API_KEY)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)



@app.post('/feishu_robot_webhoook')
async def on_webhook(request: Request, background_tasks: BackgroundTasks):
    body = dict(await request.json())
    # print(body,type(body))
    if "challenge" in body.keys():
        return feishu_models.FeishuAPIOutput(challenge=body['challenge'])
    if 'header' not in body.keys():
        return
    event_type= body['header']['event_type']
    print(event_type)
    # print(body)
    match event_type:
        case "im.message.receive_v1":
            input = feishu_models.OnNewMessageInput.parse_obj(body)
            background_tasks.add_task(feishu_repos.process_new_message, input=input)
            return 
        case "application.bot.menu_v6":
            try:
                event_key=body['event']['event_key']
                user_id=body['event']['operator']['operator_id']['user_id']
                print(event_key, user_id)
                background_tasks.add_task(feishu_repos.renew_chat_session, user_id=user_id)
            except Exception as e:
                print(e)
    return

@app.post('/feishu_robot_webhook_trial')
async def on_webhook(openai_api_key:str, app_id: str, app_secret:str,request: Request, background_tasks: BackgroundTasks):
    body = dict(await request.json())
    print(openai_api_key,app_id,app_secret)
    app_info=feishu_models.FeishuAppInfo(
        app_id=app_id,
        app_secret=app_secret,
        openai_api_key=openai_api_key,
    )
    print(body)
    # print(body,type(body))
    if "challenge" in body.keys():
        return feishu_models.FeishuAPIOutput(challenge=body['challenge'])
    if 'header' not in body.keys():
        return
    event_type= body['header']['event_type']
    print(event_type)
    # print(body)
    match event_type:
        case "im.message.receive_v1":
            input = feishu_models.OnNewMessageInput.parse_obj(body)
            background_tasks.add_task(process_new_message, input=input, app_info=app_info)
            return 
        case "application.bot.menu_v6":
            try:
                event_key=body['event']['event_key']
                user_id=body['event']['operator']['operator_id']['user_id']
                print(event_key, user_id)
                background_tasks.add_task(feishu_repos.renew_chat_session, user_id=user_id)
            except Exception as e:
                print(e)

def start():
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)

@app.on_event("shutdown")
async def stop():
    print("Shutting down")
    for value in global_chat_session_feishu_manager.chat_session.cache.values():
        await value.astop()


async def process_new_message(input:feishu_models.OnNewMessageInput, app_info:feishu_models.FeishuAppInfo):
    print('start processing new msg')
    if configs.FEISHU_API_VERBOSE:
        print(input.json(indent=2))
    # renew_tenant_access_token()
    message = input.event.message
    message_type=message.message_type
    message_id=message.message_id
    if message_id in list(global_msg_id_que.queue):
        return
    session_key = feishu_models.FeishuChatSessionKey(
        chat_id=message.chat_id, 
        open_id=input.event.sender.sender_id.open_id,
        user_id=input.event.sender.sender_id.user_id
    )
    feishu_chat_session:ChatSessionFeishu=await global_chat_session_feishu_manager.get_chat_session(session_key=session_key, app_info=app_info)
    feishu_chat_session.renew_tenant_access_token()
    # download_path = f"./chat_save_dir/{message.chat_id}/"
    # if not os.path.exists(download_path):
    #     os.makedirs(download_path)
    match message_type:
        case "file":
            # content=feishu_models.Content.parse_raw(input.event.message.content)
            content=json.loads(input.event.message.content)
            # print("content:", content)
            (succ, downloaded_path)=feishu_repos.download_files(
                message_id=message_id,
                file_key=content['file_key'],
                file_type='file',
                download_path=feishu_chat_session.save_file_dir+content['file_name']
            )
            if succ:
                global_msg_id_que.put(message_id)
                print(downloaded_path, " downloaded")
                feishu_chat_session.on_file_upload(
                    file_saved_path=downloaded_path
                )
                feishu_repos.reply_message(
                message_id=message_id, 
                data= feishu_models.FeishuReplyMessageData(
                    content=json.dumps({"text":"我已经成功收到了这个文件，请提问吧！"}),
                    msg_type='text'
                ))
        case "image":
            feishu_repos.reply_message(
                message_id=message_id, 
                data= feishu_models.FeishuReplyMessageData(
                    content=json.dumps({"text":"Sorry, I can't deal with Images Now"}),
                    msg_type='text'
                ))
            return
        case "text":
            try:
                msg = json.loads(message.content).get("text")
            except ValueError:
                print(message.content)
                print('json.load error')
            
            global_msg_id_que.put(message_id)
            urls = find_urls(msg)
            if len(urls) >0:
                feishu_urls = check_feishu_urls(urls)
                if len(feishu_urls) > 0 and len(feishu_urls) == len(urls):
                    reply_message(
                        message_id=message_id,
                        data= feishu_models.FeishuReplyMessageData(
                            content=json.dumps({"text":"你的消息中含有飞书文档的url，我将开始下载这些文件。请确保你有访问这些文档的权限。"}),
                            msg_type='text'
                        ),
                        tenant_access_token=feishu_chat_session.tenant_access_token
                    )
                    all_export = await deal_with_feishu_urls(
                        message_id=message_id, 
                        feishu_urls=feishu_urls, 
                        download_path=feishu_chat_session.save_file_dir,
                        tenant_access_token=feishu_chat_session.tenant_access_token
                    )
                    if not all_export:
                        reply_text="文件导出时似乎遇到了问题，可能有部分文件我没导出。请确保你的URL是正确的，或者联系开发人员。"
                    else:
                        reply_text="所有文档/文件我都导出了，现在可以开始回答你的问题"
                    reply_message(
                        message_id=message_id,
                        data= feishu_models.FeishuReplyMessageData(
                            content=json.dumps({"text":reply_text}),
                            msg_type='text'
                        ),
                        tenant_access_token=feishu_chat_session.tenant_access_token
                    )
                    #回复后结束
                    if not all_export:
                        return
                    url_map_prompt = f""
                    for item in all_export:
                        file_name=item.download_path.split('/')[-1]
                        url_map_prompt += f"the file of url:```{item.url}``` is exported and saved as {file_name}\n"
                        feishu_chat_session.on_file_upload(
                            file_saved_path=item.download_path
                        )
                    
                    msg += url_map_prompt
                    await feishu_chat_session.on_new_text_message_entered(msg=msg)
                else:
                    feishu_chat_session.on_message_generated("对不起，您消息中似乎包含了非飞书的URL，我不能处理。")
                    return
            else:
                await feishu_chat_session.on_new_text_message_entered(msg=msg)
            return

