import os
from models.feishu_api import FeishuAppInfo
ENV_FLAG = os.environ.get('ENV_FLAG')
chat_save_file_path_feishu='./chat_save_dir/'
APP_ID=os.environ.get('APP_ID')
APP_SECRET= os.environ.get('APP_SECRET')
CODEBOX_API_KEY=None
try:
    CODEBOX_API_KEY = os.environ.get('CODEBOX_API_KEY')
except Exception as e:
    pass
    
FEISHU_API_VERBOSE=os.environ.get('FEISHU_API_VERBOSE')
DEFAULT_FEISHU_APP_INFO= FeishuAppInfo(
    app_id = os.environ.get('APP_ID'),
    app_secret = os.environ.get('APP_SECRET'),
    openai_api_key=os.environ.get('OPENAI_API_KEY')
)