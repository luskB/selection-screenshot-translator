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
    "custom_icon_path": "",
    "history_max_count": 10
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

# ── 翻译历史记录 ──
HISTORY_FILE = os.path.join(get_app_dir(), "history.json")

def load_history():
    """加载翻译历史记录"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    """保存翻译历史记录"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def add_history_record(source, result, engine, target_lang, is_image=False, max_count=10):
    """添加一条翻译历史记录，超过 max_count 时自动移除最旧的"""
    from datetime import datetime as _dt
    history = load_history()
    record = {
        "time": _dt.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source if not is_image else "[图片翻译]",
        "result": result,
        "engine": engine,
        "target_lang": target_lang,
        "is_image": is_image
    }
    history.insert(0, record)  # 最新的在前面
    if len(history) > max_count:
        history = history[:max_count]
    save_history(history)
    return history
