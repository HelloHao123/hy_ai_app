import streamlit as st
from datetime import datetime
import re, json, os

HISTORY_FILE = "dist_history.json"

# ================= [1. 历史记录核心逻辑] =================
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return []
    return []

def save_history(original_text, assigned_tasks, creator):
    # 守卫逻辑：如果没有任务，不产生历史记录
    if not assigned_tasks:
        return

    history = load_history()
    
    # 格式化历史记录名称：调研时间 + 产品名称方式
    product_brief = original_text.strip()[:15].replace("\n", " ")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    display_name = f"调研时间: {current_time} | 项目: {product_brief}..."

    history.append({
        "timestamp": current_time,
        "display_name": display_name,
        "original_plan": original_text, 
        "tasks": assigned_tasks,
        "creator": creator
    })
    
    # 严格限制：只记录最近的十个
    if len(history) > 10:
        history = history[-10:]
        
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f: 
        json.dump(history, f, ensure_ascii=False, indent=4)

# ================= [2. 核心解析：超强鲁棒性] =================
def robust_parse_response(text):
    tasks, table = [], ""
    try:
        # 提取 JSON 数组：使用非贪婪匹配以应对 AI 在结尾添加的废话
        json_match = re.search(r'\[[\s\S]*?\]', text)
        if json_match:
            json_str = json_match.group().strip()
            # 自动清理可能包裹的 Markdown 标签
            json_str = re.sub(r'^```json\s*|```$', '', json_str)
            tasks = json.loads(json_str)
        
        # 提取合规表格
        table_match = re.search(r'\|.*Action.*\|.*Rule.*\|[\s\S]*', text)
        if table_match: 
            table = table_match.group()
            
    except Exception as e:
        st.error(f"解析详情错误: {str(e)}")
        
    return tasks, table

# ================= [3. 弹出窗口组件] =================
@st.dialog("🛡️ 数字化贸易合规性执行清单")
def show_compliance_dialog():
    """
    使用弹出窗口方式显示合规建议
    """
    if 'compliance_table' in st.session_state and st.session_state['compliance_table']:
        st.markdown(st.session_state['compliance_table'])
        st.divider()
        st.info("💡 以上建议基于苏豪弘业数字贸易合规准则生成。")
    else:
        st.warning("⚠️ 暂无合规数据。请先输入内容并点击“深度解析”。")

# ================= [4. 主渲染函数] =================
def render_task_distributor(model, team_members, load_db, save_db, current_user, current_role):
    # 状态重置
    if st.session_state.get('reset_task_distributor'):
        st.session_state['main_plan_input'] = ""
        st.session_state.pop('temp_tasks', None)
        st.session_state.pop('compliance_table', None)
        st.session_state['reset_task_distributor'] = False

    st.header("🎯 任务 AI 解析与合规中心")
    
    plan_input = st.text_area("输入业务规划、产品调研结果或市场趋势预测：", height=180, key="main_plan_input")
    
    # 按钮对齐与 UI 优化
    col_btn1, col_btn2, _ = st.columns([1.5, 1.5, 4])
    
    if col_btn1.button("✨ 深度解析", type="primary", use_container_width=True):
        if not plan_input.strip():
            st.warning("⚠️ 请先输入调研内容。")
        else:
            with st.spinner("正在解析你的任务..."): 
                # 强化提示词：要求战略指导意义
                prompt = f"""
                作为数字贸易与国企管理专家，请深度解析以下内容：{plan_input}
                要求：
                1. 提炼核心里程碑，desc 需对市场化战略有指导意义。
                2. 必须返回 JSON 数组（字段：task, desc）。
                3. 提供 Markdown 合规表格（Action, Rule）。
                """
                res = model.generate_content(prompt, transport='rest')
                tasks, table = robust_parse_response(res.text)
                
                if tasks:
                    st.session_state['temp_tasks'] = tasks
                    st.session_state['compliance_table'] = table
                    st.rerun()

    # 修改点：点击按钮触发弹出窗口
    if col_btn2.button("🛡️ 合规检查", use_container_width=True):
        show_compliance_dialog()

    # 任务分发区域 (极致对齐)
    if 'temp_tasks' in st.session_state:
        st.markdown("---")
        with st.form(key="task_assign_aligned_v12"):
            assigned = []
            st.subheader("📋 解析结果：执行项分发")
            for i, t in enumerate(st.session_state['temp_tasks']):
                with st.container(border=True):
                    # 左右极致对齐
                    c_title, c_owner = st.columns([7, 3])
                    c_title.markdown(f"**📍 任务：{t.get('task', '未命名')}**")
                    
                    owners = c_owner.multiselect(
                        "指派", 
                        team_members if current_role == "Admin" else [current_user], 
                        default=[current_user] if current_role != "Admin" else [], 
                        key=f"re_v12_{i}",
                        label_visibility="collapsed"
                    )
                    
                    # 描述行对齐
                    st.markdown(f"<div style='font-size:14px; color:#555; margin-top:5px; min-height:40px;'>{t.get('desc', '')}</div>", unsafe_allow_html=True)
                    
                    assigned.append({
                        "task": t.get('task'), "desc": t.get('desc'), 
                        "owner": owners, "status": "待办", 
                        "date": datetime.now().strftime("%Y-%m-%d")
                    })
            
            if st.form_submit_button("🚀 确认分发并存入库", use_container_width=True):
                if any(item['owner'] for item in assigned):
                    db = load_db(); db.extend(assigned); save_db(db)
                    save_history(plan_input, assigned, current_user)
                    st.session_state['reset_task_distributor'] = True
                    st.rerun()
                else: st.warning("请至少为一个任务分配负责人。")

    # ================= [📜 历史看板 - 增加空状态提示与容错] =================
    st.markdown("---")
    st.subheader("📜 调研解析历史 (最近 10 条)")
    h_data = load_history()
    
    if not h_data:
        st.info("👋 目前暂无历史解析记录。")
    else:
        for idx, rec in enumerate(reversed(h_data)):
            # 容错处理：使用 .get 获取 display_name
            safe_title = rec.get('display_name', f"历史快照 ({rec.get('timestamp')})")
            with st.expander(f"🕒 {safe_title}"):
                st.write(f"**原始文本：**\n{rec.get('original_plan')}")
                st.markdown("**解析结果：**")
                for t in rec.get('tasks', []):
                    st.write(f"- {t['task']} (执行: {', '.join(t['owner'])})")