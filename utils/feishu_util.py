import requests
import json
import time
from typing import Union
from configs import APP_ID, APP_SECRET,FEISHU_API_VERBOSE
import models.feishu_api as schemas

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
        return (content.get('tenant_access_token'), content['expire'] + int(time.time()))
    except ValueError as e:
        print(e)
    return (None, 0)

def renew_tenant_access_token(tenant_access_token_expire: int, app_info:schemas.FeishuAppInfo):
    if int(time.time()) >= tenant_access_token_expire:
        return get_tenant_access_token(app_id=app_info.app_id, app_secret=app_info.app_secret)
    return (None, 0)