import streamlit as st
import pandas as pd
import json
import os

def render_ui(load_db, save_db):
    st.header("📊 数字化业务数据中心")
    st.caption("作为苏豪弘业数字贸易部的底座，此处负责所有分发任务的硬核维护。")

    # 1. 加载并清洗数据
    db = load_db()
    if not db:
        st.info("💡 目前数据库为空，请先前往‘任务解析’模块分发第一批任务。")
        return

    # 预处理：确保 is_suspended 字段存在
    for item in db:
        if 'is_suspended' not in item: item['is_suspended'] = False

    df = pd.DataFrame(db)

    # ================= [ 第一部分：核心指标 (卡片式) ] =================
    with st.container(border=True):
        st.subheader("📈 实时效能统计")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("总任务数", len(df))
        with c2: 
            active = len(df[df['status'] != '已完成'])
            st.metric("未完成项", active, delta=f"{active/len(df):.0%}", delta_color="inverse")
        with c3: 
            suspended = len(df[df['is_suspended'] == True])
            st.metric("异常/中止", suspended, delta="需要关注" if suspended > 0 else "正常")
        with c4:
            owners = df['owner'].explode().nunique()
            st.metric("协同人员数", owners)

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # ================= [ 第二部分：交互式数据编辑器 ] =================
    st.subheader("📝 核心任务库底层管理")
    
    # 定义严格的列配置，确保与 user_dashboard.py 逻辑闭环
    column_config = {
        "task": st.column_config.TextColumn("📌 任务名称", width="medium", disabled=True),
        "desc": st.column_config.TextColumn("📄 详细执行描述", width="large"),
        "owner": st.column_config.ListColumn("👥 负责人名单"),
        "status": st.column_config.SelectboxColumn(
            "🚥 状态",
            options=["待办", "进行中", "已完成"],
            required=True
        ),
        "is_suspended": st.column_config.CheckboxColumn(
            "🚫 暂停",
            help="勾选后该任务将在看板中被锁定"
        ),
        "date": st.column_config.TextColumn("📅 分发日期", disabled=True)
    }

    # 极致对齐：让编辑器占满宽度，隐藏不必要的 ID 列
    # 我们只显示这些关键业务列，并强制排序
    cols_to_show = ["task", "desc", "owner", "status", "is_suspended", "date"]
    
    edited_df = st.data_editor(
        df[cols_to_show],
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key="db_editor_v2",
        num_rows="dynamic" # 允许管理员手动增减行
    )

    # ================= [ 第三部分：操作对齐区 ] =================
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    
    # 按钮对齐：左侧保存，右侧清空
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.5, 1.5, 4])
    
    with ctrl_col1:
        if st.button("💾 同步数据库", type="primary", use_container_width=True):
            try:
                # 转换回字典列表并写回 assignments.json
                updated_data = edited_df.to_dict('records')
                save_db(updated_data)
                st.success("数据已持久化！")
                st.rerun()
            except Exception as e:
                st.error(f"同步失败: {e}")

    with ctrl_col2:
        # 这个按钮与保存按钮高度完全一致
        if st.button("📥 导出 Excel", use_container_width=True):
            st.info("该功能正在接入...")

    # ================= [ 第四部分：危险操作区 ] =================
    st.markdown("---")
    with st.expander("🚨 危险操作：清空或重置任务库"):
        danger_col1, danger_col2 = st.columns([7, 3])
        with danger_col1:
            st.warning("清空数据库将抹除所有历史任务分发记录，且无法找回。")
        with danger_col2:
            if st.button("🔥 永久销毁数据", use_container_width=True):
                save_db([])
                st.rerun()