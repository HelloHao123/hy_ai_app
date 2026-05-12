import streamlit as st
from gradio_client import Client, handle_file
from PIL import Image
import os

# 接入 StabilityAI 的开源 TripoSR 接口
API_URL = "https://stabilityai-triposr.hf.space/"

def render_three_view_generator(model_gemini):
    st.header("🧊 3D 三视图智能生成")
    st.write("上传单张图片，AI 将尝试重构其 3D 结构并展示多视角图。")

    uploaded_file = st.file_uploader("上传商品/玩具原图", type=["jpg", "png"], key="3d_up")

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=150, caption="输入原图")

        if st.button("🚀 生成多视角参考", type="primary"):
            with st.spinner("正在请求公开模型进行 3D 渲染，请稍候..."):
                try:
                    client = Client(API_URL)
                    # 临时存储图片
                    temp_fn = f"temp_3d_{uploaded_file.name}"
                    with open(temp_fn, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # 调用免费模型 API
                    result = client.predict(input_image=handle_file(temp_fn), api_name="/generate")

                    if os.path.exists(temp_fn): os.remove(temp_fn)

                    st.success("生成完成！")
                    # TripoSR 通常返回视频或多图路径
                    if isinstance(result, str):
                        if result.endswith('.mp4'): st.video(result)
                        else: st.image(result)
                except Exception as e:
                    st.error(f"公共服务器繁忙或调用失败: {e}")