import streamlit as st
import json, os

MEMBERS_FILE = "members.json"

def load_members():
    """从 JSON 加载成员数据"""
    if os.path.exists(MEMBERS_FILE):
        with open(MEMBERS_FILE, "r", encoding="utf-8") as f: 
            return json.load(f)
    # 默认初始管理员
    return [{"name": "Steven", "role": "Admin", "password": "123456"}]

def save_members(m):
    """保存成员数据到 JSON"""
    with open(MEMBERS_FILE, "w", encoding="utf-8") as f: 
        json.dump(m, f, ensure_ascii=False, indent=4)

def render_ui():
    """
    【管理员界面】
    包含：添加成员、查看列表、删除成员、重置他人密码
    """
    st.header("👥 事业部成员权限管理")
    m = load_members()
    
    # --- 添加新成员 ---
    with st.expander("➕ 添加新成员"):
        with st.form("add"):
            n = st.text_input("姓名")
            p = st.text_input("初始密码", value="123456")
            r = st.selectbox("角色", ["Admin", "Employee"])
            if st.form_submit_button("确认添加"):
                if n:
                    m.append({"name": n, "password": p, "role": r})
                    save_members(m)
                    st.success(f"已成功添加成员: {n}")
                    st.rerun()
                else:
                    st.error("姓名不能为空")
    
    st.markdown("---")
    
    # --- 成员列表与操作 ---
    for i, user in enumerate(m):
        c1, c2, c3 = st.columns([3, 3, 2])
        c1.write(f"**{user['name']}** ({user['role']})")
        
        # 重置密码功能 (Admin 专用)
        if c2.button(f"重置为 123456", key=f"r_{i}"):
            user['password'] = "123456"
            save_members(m)
            st.toast(f"已重置 {user['name']} 的密码")
            
        # 删除功能 (不能删除初始管理员 Steven)
        if c3.button("🗑️", key=f"d_{i}"): 
            if user['name'] != "Steven":
                m.pop(i)
                save_members(m)
                st.rerun()
            else:
                st.warning("系统核心管理员不可删除")

def render_user_settings(current_username):
    """
    【个人设置界面】
    供普通员工或管理员修改自己的密码
    """
    st.header("👤 个人账号设置")
    m = load_members()
    
    # 在列表中定位当前登录的用户
    user_index = next((i for i, u in enumerate(m) if u["name"] == current_username), None)
    
    if user_index is not None:
        user = m[user_index]
        st.info(f"您好，**{user['name']}**。您可以在下方修改您的个人登录密码。")
        
        with st.form("change_pw_form"):
            new_p = st.text_input("设置新密码", type="password")
            conf_p = st.text_input("确认新密码", type="password")
            
            if st.form_submit_button("确认修改密码", use_container_width=True):
                if not new_p:
                    st.error("新密码不能为空")
                elif new_p != conf_p:
                    st.error("两次输入的密码不一致，请检查")
                else:
                    # 更新密码并写入文件
                    m[user_index]["password"] = new_p
                    save_members(m)
                    st.success("密码修改成功！下次登录请使用新密码。")
    else:
        st.error("在系统中未找到您的用户信息，请联系管理员核实。")