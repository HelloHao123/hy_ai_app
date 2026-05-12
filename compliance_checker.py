import streamlit as st

def render_compliance_checker(model):
    st.header("🛡️ 合规“红线”待办清单")
    
    # 确保 session_state 初始化
    if 'shared_plan' not in st.session_state:
        st.session_state['shared_plan'] = ""

    # 使用共享的文本变量
    plan_text = st.text_area(
        "输入待评估的工作规划：", 
        value=st.session_state['shared_plan'], 
        height=150,
        key="comp_text_area"
    )
    
    # 同步到共享变量
    st.session_state['shared_plan'] = plan_text

    if st.button("🔍 生成合规 To-Do List", type="primary"):
        if plan_text:
            with st.spinner("正在提炼合规要点..."):
                prompt = f"""
                你是一位精通国资监管与外事合规的专家。请将以下规划简化为“合规待办清单”。
                要求输出 Markdown 表格：| 必须执行的操作 (Action) | 合规依据/目的 (Simple Rule) |
                规划内容：{plan_text}
                """
                res = model.generate_content(prompt)
                
                # 核心：将结果存入全局状态
                st.session_state['compliance_result'] = res.text
                
                st.markdown("---")
                st.subheader("✅ 业务执行合规清单")
                st.markdown(res.text)