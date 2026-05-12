import streamlit as st
from tools import vision_expert, sku_researcher, video_script, modeling_assistant

def render_ai_empowerment(model):
    """
    AI 赋能中心：中心调度器
    """
    st.header("💡 AI 数字化赋能中心")
    st.info("架构已升级：模块化驱动。支持 2026 联网检索与多端提示词定向优化。")

    # 定义四大业务 Tab
    tabs = st.tabs(["📸 图片反推专家", "✍️ SKU智能文案生成", "🎬 视频脚本", "📐 3D 建模辅助"])

    with tabs[0]:
        vision_expert.render(model) # 调用反推专家模块
    
    with tabs[1]:
        sku_researcher.render(model) # 调用 SKU 调研模块
    
    with tabs[2]:
        video_script.render(model)
        
    with tabs[3]:
        modeling_assistant.render(model)