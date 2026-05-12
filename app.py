import streamlit as st
import google.generativeai as genai
import os, json
import pandas as pd
import plotly.express as px
import hashlib
import streamlit_antd_components as sac

# --- 导入自定义业务模块 ---
import member_manager
import user_dashboard
import ai_empowerment
import task_distributor
import data_manager 
import toy_generator 

# --- 【新增导入客户管理模块】 ---
import client_manager_st # 导入我们刚才创建的客户管理模块

# ================= [1. 核心配置] =================
st.set_page_config(page_title="数字贸易AI平台", layout="wide", page_icon="🖥️")

# --- 【修改 1：环境代理配置】 ---
# os.environ['http_proxy'] = 'http://127.00.1:7890'
# os.environ['https_proxy'] = 'http://127.0.0.1:7890'

# 初始化 Session State
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = "访客"
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = "Guest"

# API Key 读取
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("未找到 API Key")
    st.stop()

# ================= [2. 身份验证] =================
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

MEMBERS = member_manager.load_members()

if not st.session_state['authenticated']:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.write("#") 
        with st.container(border=True):
            st.title("🔐 系统登录")
            u_in = st.text_input("用户名")
            p_in = st.text_input("密码", type="password")
            if st.button("登录平台", type="primary", use_container_width=True):
                input_hashed = hash_password(p_in.strip())
                user_data = next((m for m in MEMBERS if m.get('name') == u_in and 
                                 str(m.get('password')) in [p_in, input_hashed]), None)
                if user_data:
                    st.session_state.update({"authenticated": True, "user_name": user_data['name'], "user_role": user_data['role']})
                    st.rerun()
                else: st.error("账号或密码错误")
    st.stop()

# ================= [3. 【关键修改：极致性能与稳定性配置】] =================
def load_db():
    try:
        with open("assignments.json", 'r', encoding='utf-8') as f: return json.load(f)
    except: return []

def save_db(data):
    with open("assignments.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 使用缓存机制防止重复初始化模型，大幅提升页面切换速度 ---
@st.cache_resource
def init_gemini_model(api_key):
    # 【修改 2：强制使用 REST 协议】
    genai.configure(api_key=api_key, transport='rest')

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    generation_config = {
        "temperature": 0.2,
        "max_output_tokens": 1024, 
    }

    # 【修改 3：选择型号】
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite", 
        safety_settings=safety_settings,
        generation_config=generation_config
    )

# 执行初始化
try:
    model = init_gemini_model(API_KEY)
except Exception as e:
    st.error(f"AI 模型启动失败，请检查网络或 API Key: {e}")
    st.stop()

# ================= [4. 侧边栏导航] =================
with st.sidebar:
    st.subheader(f"👋 你好, {st.session_state['user_name']}")
    st.caption(f"权限角色: {st.session_state['user_role']}")
    st.divider()

    menu_items = [
        sac.MenuItem('个人任务看板', icon='kanban'),
        sac.MenuItem('AI 赋能中心', icon='robot'),
        sac.MenuItem('毛绒玩具生成', icon='gift'),
        # --- 【新增客户管理菜单项】 ---
        sac.MenuItem('客户信息管理', icon='people'), 
    ]
    
    if st.session_state['user_role'] == "Admin":
        menu_items.insert(0, sac.MenuItem('任务分发管理', icon='send'))
        menu_items.append(sac.MenuItem('管理后台', icon='gear', children=[
            sac.MenuItem('效能驾驶舱', icon='pie-chart'),
            sac.MenuItem('底库数据中心', icon='database'),
            sac.MenuItem('成员权限管理', icon='people'),
        ]))
    else:
        menu_items.append(sac.MenuItem('账号设置', icon='key'))

    selected = sac.menu(menu_items, format_func='title', open_all=True, size='sm')
    
    st.sidebar.divider()
    if st.button("🚪 退出系统", use_container_width=True):
        st.session_state['authenticated'] = False
        st.rerun()

# ================= [5. 页面路由逻辑] =================

page_map = {
    '任务分发管理': 'admin', '个人任务看板': 'user', 
    'AI 赋能中心': 'ai_empowerment', '毛绒玩具生成': 'toy_gen',
    '效能驾驶舱': 'dashboard', '底库数据中心': 'data', 
    '成员权限管理': 'member_mgmt', '账号设置': 'member_mgmt',
    # --- 【新增客户管理路由映射】 ---
    '客户信息管理': 'client_manager', 
}

current_page = page_map.get(selected)

if current_page == 'admin':
    task_distributor.render_task_distributor(model, [m['name'] for m in MEMBERS], load_db, save_db, st.session_state['user_name'], st.session_state['user_role'])

elif current_page == 'user':
    user_dashboard.render_user_dashboard(st.session_state['user_name'], st.session_state['user_role'], load_db, save_db)

elif current_page == 'ai_empowerment':
    ai_empowerment.render_ai_empowerment(model)

elif current_page == 'toy_gen':
    toy_generator.render_toy_generator(model)

elif current_page == 'dashboard':
    st.header("📊 效能驾驶舱")
    db = load_db()
    if db:
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.container(border=True): st.metric("总任务", len(db))
        df = pd.DataFrame(db).explode('owner')
        st.plotly_chart(px.bar(df['owner'].value_counts().reset_index(), x='owner', y='count', title="工作量分布"), use_container_width=True)
    else: st.info("暂无数据")

elif current_page == 'data':
    data_manager.render_ui(load_db, save_db)

elif current_page == 'member_mgmt':
    if st.session_state['user_role'] == "Admin": member_manager.render_ui()
    else: member_manager.render_user_settings(st.session_state['user_name'])

# --- 【新增客户管理页面渲染逻辑】 ---
elif current_page == 'client_manager':
    client_manager_st.render_client_manager()
