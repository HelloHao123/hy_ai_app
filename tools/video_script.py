import streamlit as st
from PIL import Image

def render(model):
    st.subheader("🎬 营销视频脚本导演 (Short Video Script)")
    if 'video_data' not in st.session_state: st.session_state['video_data'] = None

    with st.container(border=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            prod_img = st.file_uploader("上传 SKU 参考图：", type=["png", "jpg", "jpeg"], key="video_up")
            if prod_img: st.image(prod_img, width=220)
        with c2:
            platform = st.selectbox("目标短视频平台：", ["TikTok", "Instagram Reels", "YouTube Shorts"])
            duration = st.select_slider("预期视频时长 (秒)：", options=[15, 30, 60], value=15)
            script_style = st.selectbox("脚本叙事风格：", ["沉浸式开箱 (Unboxing)", "痛点解决 (Problem/Solution)", "丑萌剧情 (Storytelling)", "极速快剪 (Fast Cut)"])

    if st.button("📽️ 生成短视频分镜脚本", type="primary", use_container_width=True):
        if prod_img:
            with st.spinner("正在分析 SKU 卖点并编排镜头..."):
                img = Image.open(prod_img)
                prompt = f"""
                你是一位精通东盟市场的短视频编导。请为该产品创作一个 {duration} 秒的 {platform} 脚本。
                风格定位：{script_style}。
                要求：
                1. 包含 3-5 个具体分镜（镜头、画面内容、音频/配音、字幕建议）；
                2. 黄金 3 秒：必须有一个强有力的 Hook（钩子）开头；
                3. 提供 5 个配套的本地化热搜 Hashtags。
                """
                res = model.generate_content([prompt, img])
                st.session_state['video_data'] = res.text
        else: st.warning("请先上传产品图片。")

    if st.session_state['video_data']:
        st.markdown("---")
        st.markdown(st.session_state['video_data'])
        st.download_button("📥 导出拍摄脚本", st.session_state['video_data'], file_name="Video_Script.md")