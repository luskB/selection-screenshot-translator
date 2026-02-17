import json
import os
import sys

# 获取程序所在目录（支持 PyInstaller 打包）
def get_app_dir():
    if getattr(sys, 'frozen', False):
        # 打包后的 exe 文件
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(get_app_dir(), "config.json")

DEFAULT_CONFIG = {
    "engine": "google",
    "image_engine": "tencent",  # 图片翻译默认引擎
    "google_api_key": "",
    "google_proxy_mode": "auto",
    
    "deepl_api_key": "",
    "deepl_proxy_mode": "auto",
    
    "microsoft_api_key": "",
    "microsoft_region": "eastasia",
    "microsoft_proxy_mode": "direct",
    
    "tencent_secret_id": "",
    "tencent_secret_key": "",
    "tencent_region": "ap-beijing",
    "tencent_proxy_mode": "direct",
    
    "volcano_access_key": "",
    "volcano_secret_key": "",
    "volcano_region": "cn-north-1",
    "volcano_proxy_mode": "direct",
    
    "ai_api_key": "",
    "ai_endpoint": "https://api.openai.com/v1",
    "ai_model": "gpt-3.5-turbo",
    "ai_prompt": "You are a professional translator. Translate the following text to Chinese, maintaining the original tone and context: ",
    "ai_proxy_mode": "direct",
    
    "show_icon_delay": 0.5,
    "proxy_url": "http://127.0.0.1:7897",
    "auto_start": False,
    "custom_icon_path": ""
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
