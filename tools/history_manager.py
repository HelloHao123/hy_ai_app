import json
import os
from datetime import datetime

HISTORY_FILE = "search_history.json"

def save_to_history(params, result_text):
    """保存查询结果，仅保留最近10条"""
    history = load_history()
    # 构建历史记录卡片数据
    new_entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "time": datetime.now().strftime("%m-%d %H:%M"),
        "title": f"{params.get('country')} | {params.get('style')}",
        "params": params,
        "result": result_text
    }
    # 插入到最前面，并切片保留前10名
    history.insert(0, new_entry)
    history = history[:10]
    
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def load_history():
    """读取历史记录"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []