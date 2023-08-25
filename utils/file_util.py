import os

def get_file_name_from_path():
    pass

def get_feishu_file_type(file_path:str):
    _ext = os.path.splitext(os.path.basename(file_path))[-1].lower()
    file_type="stream"
    match _ext:
        case '.doc','xls','ppt':
            file_type=_ext[-3]
        case '.opus':
            file_type='opus'
    return file_type
    