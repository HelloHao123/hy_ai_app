import google.generativeai as genai
import json
import os

# ================= [配置区] =================
API_KEY = "AIzaSyC_GwwlGg7BE8NzGVRXPm4YfahnpfqlN48" 

# 修正后的模型名称，确保与你的 API 权限列表一致
MODEL_NAME = "models/gemini-flash-latest" 
DB_FILE = "assignments.json"
# ===========================================

genai.configure(api_key=API_KEY, transport='rest')
model = genai.GenerativeModel(MODEL_NAME)

def run_personal_view():
    print(f"\n{'='*20} 📅 个人 AI 工作助手 {'='*20}")
    
    if not os.path.exists(DB_FILE):
        print(f"⚠️ 找不到 {DB_FILE} 文件，请先联系管理员分配任务。")
        return

    with open(DB_FILE, 'r', encoding='utf-8') as f:
        all_tasks = json.load(f)

    user_name = input("\n请输入你的姓名 (例如: Steven): ").strip()
    # 核心修复：兼容 owner 列表格式，确保能识别 ["Steven", "Jonathan"] 这样的任务
    my_tasks = [t for t in all_tasks if user_name in t.get('owner', [])]

    if not my_tasks:
        print(f"👋 {user_name}，目前你名下没有待办任务。")
        return

    print(f"\n📋 找到属于 {user_name} 的 {len(my_tasks)} 个任务。")
    print("🤖 AI 正在为你规划本周最优执行路径...")

    task_context = ""
    for i, t in enumerate(my_tasks):
        task_context += f"{i+1}. 任务名: {t['task']}\n   任务描述: {t['desc']}\n"

    # 针对数字贸易部总经理的背景进行 Prompt 优化
    prompt = f"""
    你是 {user_name} 的高效办公助理。他正负责 SOHO Holdings 与马来西亚 MMU 的合作项目。
    
    现有任务清单：
    {task_context}

    请生成一份详细的周工作排期：
    1. 逻辑分配：将任务合理分配到周一至周五。
    2. 执行细则：针对每个任务描述，给出具体的“第一步该做什么”，要具有落地的可操作性。
    3. 战略重点：指出哪个任务对“市场化战略”最具指导意义，并标出最紧迫项。
    
    请使用专业且积极的口吻输出。
    """

    try:
        response = model.generate_content(prompt)
        print("\n" + "✨" * 30)
        print(f"🚀 {user_name} 的本周 AI 自动规划方案：")
        print(response.text)
        print("\n" + "✨" * 30)
    except Exception as e:
        print(f"❌ 规划生成失败: {e}")

if __name__ == "__main__":
    run_personal_view()