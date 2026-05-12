import streamlit as st
import pandas as pd
import member_manager

def render_user_dashboard(current_user, current_role, load_db, save_db):
    st.header("📅 协同任务监控看板")
    db = load_db()
    if not db: return st.info("目前任务库为空。")

    # 数据补全
    for item in db:
        if 'is_suspended' not in item: item['is_suspended'] = False
    df = pd.DataFrame(db)
    
    try:
        team_members = [m['name'] for m in member_manager.load_members()]
    except:
        team_members = [current_user]

    # --- 1. 顶部筛选区 ---
    c1, c2 = st.columns([4, 6])
    with c1:
        if current_role == "Admin":
            all_owners = sorted(list(set([o for sub in df['owner'] for o in sub])))
            owner_sel = st.selectbox("负责人筛选", ["全员展示项目"] + all_owners, label_visibility="collapsed")
            display_df = df if owner_sel == "全员展示项目" else df[df['owner'].apply(lambda x: owner_sel in x)]
        else:
            display_df = df[df['owner'].apply(lambda x: current_user in x)]
    with c2:
        status_filter = st.radio("状态快选", options=["全部", "待办", "进行中", "已完成", "🚫已暂停"], horizontal=True, label_visibility="collapsed")
    
    if status_filter == "🚫已暂停":
        display_df = display_df[display_df['is_suspended'] == True]
    elif status_filter != "全部":
        display_df = display_df[(display_df['status'] == status_filter) & (display_df['is_suspended'] == False)]

    display_df = display_df[::-1] # 新任务置顶

    st.markdown("---")
    if display_df.empty: return st.warning("🔍 未找到匹配内容。")

    # --- 2. 任务卡片渲染 (严格栅格对齐) ---
    for idx in display_df.index:
        row = db[idx]
        is_susp = row.get('is_suspended', False)

        with st.container(border=True):
            # 第一行：表头层 (标题、协同、状态标签)
            h1, h2, h3 = st.columns([4.5, 3, 2.5])
            icon = "🚫" if is_susp else {"已完成": "✅", "进行中": "🔵", "待办": "⚪"}.get(row['status'], "❓")
            h1.markdown(f"#### {icon} {row['task']}")
            h2.markdown("**👥 协同团队**")
            h3.markdown("**⚡ 快速状态**")

            # 第二行：内容层 (描述、人员列表、下拉框)
            cont1, cont2, cont3 = st.columns([4.5, 3, 2.5])
            with cont1:
                st.caption(f"📅 发布日期: {row['date']}")
                # 限制最小高度确保对齐
                st.markdown(f"<div style='font-size:14px; min-height:60px;'>{row['desc']}</div>", unsafe_allow_html=True)
            with cont2:
                # 采用紧凑的文本排列
                for member in row['owner']:
                    st.markdown(f"<div style='font-size:13px; margin-bottom:2px;'>👤 {member}</div>", unsafe_allow_html=True)
            with cont3:
                opts = ["待办", "进行中", "已完成"]
                new_status = st.selectbox("更新进度", opts, index=opts.index(row['status']) if row['status'] in opts else 0, key=f"st_{idx}", label_visibility="collapsed")
                if new_status != row['status']:
                    db[idx]['status'] = new_status
                    save_db(db); st.rerun()

            # 第三行：管理层 (Admin 专属操作区，强制底线对齐)
            if current_role == "Admin":
                st.divider() # 强制分割线，确保下方按钮绝对对齐
                act1, act2, act3 = st.columns([4.5, 3, 2.5])
                with act1:
                    st.caption("🛠️ 管理操作")
                with act2:
                    # 改派功能
                    new_owners = st.multiselect("改派", team_members, default=row['owner'], key=f"re_{idx}", label_visibility="collapsed", placeholder="点击重新指派人员")
                    if sorted(new_owners) != sorted(row['owner']):
                        if st.button("💾 确认改派", key=f"btn_re_{idx}", use_container_width=True, type="primary"):
                            db[idx]['owner'] = new_owners
                            save_db(db); st.rerun()
                with act3:
                    # 状态控制按钮
                    b1, b2 = st.columns([1, 1])
                    if b1.button("▶️" if is_susp else "⏸️", key=f"sp_{idx}", use_container_width=True, help="恢复/中止"):
                        db[idx]['is_suspended'] = not is_susp; save_db(db); st.rerun()
                    if b2.button("🗑️", key=f"dl_{idx}", use_container_width=True, help="删除任务"):
                        db.pop(idx); save_db(db); st.rerun()

        st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)