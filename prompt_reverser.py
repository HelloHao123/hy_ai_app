import streamlit as st
from PIL import Image
import re

def render_prompt_reverser(model):
    """
    渲染提示词反推专家模块 (多平台优化版)
    利用 Gemini 3 Flash 的强大的指令遵循和多模态能力
    """
    st.header("🎨 AI 图片提示词反推专家 (多平台版)")
    st.write("上传参考图，一键生成针对 **即梦 (Jimeng)** 和 **Midjourney** 优化的专用提示词。")
    
    # 文件上传组件
    uploaded_file = st.file_uploader("上传参考图", type=["jpg", "jpeg", "png"], key="reverser_upload")
    
    if uploaded_file:
        try:
            img = Image.open(uploaded_file)
            st.image(img, caption='分析目标', width=300)
            
            if st.button("🔍 执行多平台深度反推", type="primary"):
                with st.spinner("Gemini 正在分析画面并针对不同平台进行优化..."):
                    # --- 关键：针对多平台的结构化指令 ---
                    prompt_instruction = """
                    你是一位精通主流 AI 绘画平台的顶级提示词专家。请深入分析这张参考图，并严格按照以下要求分别输出优化的提示词。

                    请严格使用以下分隔符格式输出内容，不要包含其他多余引导语：

                    ### [Part 1: 通用视觉分析]
                    (在这里用中文详细描述画面的主体、风格、色彩、构图、光影、材质和氛围，供人工理解参考。)

                    ---

                    ### [Part 2: 即梦 (Jimeng) 专用提示词]
                    (针对即梦平台优化的英文提示词。倾向于使用描述性的长句和高质量标签组合，包含细节描述。请自动加上如 "high quality, masterpiece, highly detailed" 等提升质量的词汇。)

                    ---

                    ### [Part 3: Midjourney 专用提示词]
                    (针对 Midjourney V6 优化的英文提示词。使用逗号分隔的关键词格式。一定要根据图片内容在末尾自动添加正确的宽高比参数（如 --ar 16:9 或 --ar 2:3）和版本参数 --v 6.0。)
                    """
                    
                    response = model.generate_content([prompt_instruction, img])
                    res_text = response.text
                    
                    # --- 使用正则提取不同部分的内容 ---
                    
                    # 1. 提取即梦提示词
                    jimeng_match = re.search(r'### \[Part 2: 即梦 \(Jimeng\) 专用提示词\]\n(.*?)\n---', res_text, re.DOTALL)
                    jimeng_prompt = jimeng_match.group(1).strip() if jimeng_match else "未能解析即梦提示词，请检查原始输出。"
                    
                    # 2. 提取 Midjourney 提示词 (捕获直到文本结束)
                    mj_match = re.search(r'### \[Part 3: Midjourney 专用提示词\]\n(.*)', res_text, re.DOTALL)
                    mj_prompt = mj_match.group(1).strip() if mj_match else "未能解析 Midjourney 提示词，请检查原始输出。"

                    # --- UI 分块展示 ---
                    
                    st.subheader("🚀 平台专属优化结果")

                    # 模块 A: 即梦 (Jimeng)
                    with st.container(border=True):
                        c1, c2 = st.columns([0.1, 0.9])
                        c1.write("🇨🇳")
                        c2.write("**即梦 (Jimeng) 专用**")
                        st.code(jimeng_prompt, language="text")
                        st.caption("适用于即梦/Dreamina，已优化描述性细节。")

                    # 模块 B: Midjourney
                    with st.container(border=True):
                        c1, c2 = st.columns([0.1, 0.9])
                        c1.write("🎨")
                        c2.write("**Midjourney V6 专用**")
                        st.code(mj_prompt, language="text")
                        st.caption("适用于 MJ V6，已自动包含 --ar 等参数。")

                    # 模块 C: 通用分析 (折叠显示，供参考)
                    with st.expander("🧐 查看通用视觉分析报告 (人工参考)"):
                        analysis_match = re.search(r'### \[Part 1: 通用视觉分析\]\n(.*?)\n---', res_text, re.DOTALL)
                        analysis_text = analysis_match.group(1).strip() if analysis_match else res_text
                        st.write(analysis_text)
                        
        except Exception as e:
            st.error(f"解析过程中出现异常: {e}")
            # 如果正则提取失败，显示原始文本以便调试
            if 'res_text' in locals():
                with st.expander("查看原始模型输出 (Debug)"):
                    st.text(res_text)