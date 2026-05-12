import streamlit as st
from PIL import Image

def render(model):
    """
    图片反推专家子模块：修复响应逻辑与预览控制
    """
    st.subheader("📸 SKU 视觉反推与定向提示词提取")

    # 核心修复 1：统一使用 'reverse_proxy_data' 键名，确保与中心调度器对齐
    if 'reverse_proxy_data' not in st.session_state:
        st.session_state['reverse_proxy_data'] = None

    with st.container(border=True):
        col_up, col_sel = st.columns([1, 1])
        with col_up:
            # 增加 key 确保上传组件的独立性
            re_img = st.file_uploader("上传参考图 (300px 自动缩放)：", type=["png", "jpg", "jpeg"], key="re_up_tool")
        with col_sel:
            target_platform = st.radio(
                "AI 绘图优化目标：",
                ["Midjourney (V6.0)", "即梦 (Jimeng)"],
                horizontal=True,
                key="target_sel"
            )
            re_style_hint = st.selectbox(
                "核心风格倾向：", 
                ["丑萌经济 (Ugly-cute)", "3D 盲盒/卡通", "中式美学", "赛博科技"],
                key="style_sel"
            )

    if re_img:
        st.markdown("---")
        c1, c2 = st.columns([1, 2])
        with c1:
            # 核心要求：严格控制预览图宽度为 300px
            st.image(re_img, caption="🖼️ 视觉参考预览", width=300) 
        
        with c2:
            # 核心修复 2：将分析按钮放置在列中，并增加点击后的 UI 状态更新
            if st.button("🔍 执行定向反向分析", type="primary", use_container_width=True):
                with st.spinner(f"正在分析并生成针对 {target_platform} 的提示词..."):
                    try:
                        img_in = Image.open(re_img)
                        # 优化后的反推提示词逻辑
                        target_instr = "针对 Midjourney 格式，使用英文，含材质参数与 --ar 比例。" if "Midjourney" in target_platform else "针对即梦 (Jimeng) 格式，使用中文描述，强调氛围感与光影。"
                        
                        re_prompt = f"""
                        作为视觉分析专家，请解析此图。
                        1. 材质与构图逻辑解析；
                        2. 视觉关键词（风格：{re_style_hint}）；
                        3. 【{target_platform} 专用 Prompt】：{target_instr}。
                        """
                        re_res = model.generate_content([re_prompt, img_in])
                        
                        # 核心修复 3：数据存入后立即重定向，确保内容即时显示
                        st.session_state['reverse_proxy_data'] = re_res.text
                        st.rerun() 
                    except Exception as e:
                        st.error(f"分析失败，请检查网络或 API 额度：{str(e)}")
            
            # 显示结果区
            if st.session_state['reverse_proxy_data']:
                st.success(f"✅ 已生成针对 {target_platform} 的提示词：")
                st.markdown(st.session_state['reverse_proxy_data'])
                # 提供清除功能以便重新分析
                if st.button("🧹 清除当前结果"):
                    st.session_state['reverse_proxy_data'] = None
                    st.rerun()