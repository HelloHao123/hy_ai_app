import streamlit as st
from PIL import Image

def render_video_script_generator(model):
    """针对 Seedance 2.0 优化的视频脚本生成模块"""
    st.header("🎥 Seedance 2.0 视频脚本专家")
    st.write("基于视觉灵感，生成符合 Seedance 2.0 高性能渲染要求的提示词与脚本。")

    v_file = st.file_uploader("上传视频灵感图", type=["jpg", "png"], key="v_script_up")

    if v_file:
        img = Image.open(v_file)
        # 保持缩略图预览一致性
        st.image(img, width=150, caption="灵感来源")

        if st.button("🚀 生成 Seedance 2.0 专用脚本", type="primary"):
            with st.spinner("Gemini 正在为 Seedance 2.0 优化分镜..."):
                # 针对 Seedance 2.0 的专业级指令
                instr = """
                你是一位精通 Seedance 2.0 视频生成的顶级视觉导演。请分析图片并撰写一个 15 秒的电影级视频脚本。
                
                请严格按以下结构输出：
                
                ### 🎬 [Seedance 2.0 Master Prompt]
                (这里提供一段 200 字以内、针对 Seedance 2.0 优化的全英文提示词。
                要求包含：Subject, Action, Cinematic Lighting, Camera Movement(如: Dolly in, Pan left), 
                and Material details. 结尾加入质量词: 4k, high fidelity, 60fps。)

                ---
                ### 📑 [分镜脚本详情]
                - **0-5s (开场)**: 视觉画面描述 + 镜头轨迹。
                - **5-10s (发展)**: 细节特写 + 动态变化。
                - **10-15s (结尾)**: 品牌/商品定格 + 氛围升华。

                ---
                ### 💡 [Seedance 参数建议]
                - **Motion Score (运动幅度)**: 推荐值 (1-10)。
                - **Creative Guidance**: 推荐值。
                - **音效建议**: 配合该画面的 BGM 风格。
                """
                
                try:
                    # 利用 Paid Tier 处理复杂视觉指令
                    res = model.generate_content([instr, img])
                    
                    with st.container(border=True):
                        st.markdown(res.text)
                        st.success("✅ 脚本已针对 Seedance 2.0 物理引擎完成优化。")
                        st.caption("提示：直接复制 Master Prompt 到 Seedance 的输入框即可开始渲染。")
                        
                except Exception as e:
                    st.error(f"脚本生成失败: {e}")