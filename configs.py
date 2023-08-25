import os
ENV_FLAG = os.environ.get('ENV_FLAG')
chat_save_file_path_feishu='./chat_save_dir/'
APP_ID=os.environ.get('APP_ID')
APP_SECRET= os.environ.get('APP_SECRET')
try:
    CODEBOX_API_SECRET = os.environ.get('CODEBOX_API_KEY')
except Exception as e:
    CODEBOX_API_SECRET=None
FEISHU_API_VERBOSE=os.environ.get('FEISHU_API_VERBOSE')
