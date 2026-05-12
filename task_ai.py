import google.generativeai as genai
import json
import re
import os
import time

# ================= [核心配置区] =================
API_KEY = "AIzaSyC_GwwlGg7BE8NzGVRXPm4YfahnpfqlN48" 

# 这里的别名通常是 1.5 Flash 的稳定版
MODEL_NAME = "models/gemini-flash-latest" 
# 如果上面的还是 404，脚本会自动尝试下面这个
BACKUP_MODEL = "models/gemini-2.0-flash"

TEAM_MEMBERS = ["Steven", "小王", "老李", "阿强"]
DB_FILE = "assignments.json"
# ===============================================

genai.configure(api_key=API_KEY, transport='rest')

def robust_json_parser(text):
    """强力提取 JSON 数组"""
    text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except: return None
    return None

def run_task_system():
    print(f"\n{'='*20} 🤖 团队 AI 任务助手 {'='*20}")
    
    raw_input = input("\n请粘贴工作规划文本 (回车确认):\n")
    if not raw_input.strip(): return

    prompt = f"请将以下文本拆解为 JSON 数组，包含 'task' 和 'desc' 字段。只需输出 JSON，不要废话：\n{raw_input}"
    
    print(f"\n正在尝试连接模型 {MODEL_NAME}...")
    
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        try:
            response = model.generate_content(prompt)
        except Exception as e:
            # 如果主模型 404 或失败，尝试备用模型
            print(f"⚠️ 主模型连接失败，正在尝试备用模型 {BACKUP_MODEL}...")
            model = genai.GenerativeModel(BACKUP_MODEL)
            response = model.generate_content(prompt)

        tasks = robust_json_parser(response.text)
        
        if not tasks:
            print("❌ 解析失败！AI 返回的内容不是标准的 JSON 格式。")
            return

        print(f"✅ 成功拆解出 {len(tasks)} 个关键点！")

        # 读取/创建数据库
        current_data = []
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                try: current_data = json.load(f)
                except: current_data = []

        # 指派负责人
        for t in tasks:
            print(f"\n📌 任务: {t['task']}")
            print(f"📝 详情: {t['desc']}")
            print(f"👥 指派给: " + " ".join([f"({i}){name}" for i, name in enumerate(TEAM_MEMBERS)]))
            
            choice = input(f"请输入编号 (0-{len(TEAM_MEMBERS)-1})，跳过请回车: ")
            
            if choice.isdigit() and int(choice) < len(TEAM_MEMBERS):
                selected_name = TEAM_MEMBERS[int(choice)]
                current_data.append({
                    "task": t['task'],
                    "desc": t['desc'],
                    "owner": selected_name,
                    "status": "待办",
                    "created_at": time.strftime("%Y-%m-%d %H:%M")
                })
                print(f"✔️ 已指派给 {selected_name}")

        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=4)
        
        print(f"\n✨ 分配已完成！数据存入 {DB_FILE}")

    except Exception as e:
        print(f"❌ 运行异常: {e}")
        print("\n💡 提示：如果依然报错 404，请确认你的 API Key 是否在 Google AI Studio 中启用了相应的权限。")

if __name__ == "__main__":
    run_task_system()