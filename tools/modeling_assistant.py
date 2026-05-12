import streamlit as st
from PIL import Image

def render(model):
    st.subheader("📐 3D 建模与工艺辅助 (3D Modeling Assistant)")
    if 'model_data' not in st.session_state: st.session_state['model_data'] = None

    with st.container(border=True):
        c_l, c_r = st.columns([1, 2])
        with c_l:
            ref_img = st.file_uploader("上传 3D 参考图：", type=["png", "jpg", "jpeg"], key="model_up")
            if ref_img: st.image(ref_img, width=220)
        with c_r:
            software = st.radio("首选建模软件：", ["Blender", "Cinema 4D (C4D)", "ZBrush"], horizontal=True)
            task_type = st.selectbox("分析目标：", ["拓扑结构建议 (Topology)", "UV 展开思路", "3D 打印切片优化", "材质节点配置"])

    if st.button("🛠️ 获取 3D 技术实现方案", type="primary", use_container_width=True):
        if ref_img:
            with st.spinner(f"正在分析图片中的几何逻辑与材质参数..."):
                img = Image.open(ref_img)
                # 结合 Steven 的 Razer Blade 14 性能表现与建模习惯
                prompt = f"""
                作为资深 3D 艺术家，请为此产品提供在 {software} 中的【{task_type}】实现方案。
                要求：
                1. 结构拆解：分析物体的主体结构与配件连接方式（适配 3D 打印需求）；
                2. 建模路径：推荐使用多边形建模还是雕刻逻辑；
                3. 参数建议：提供具体的细分程度、倒角数值或材质贴图通道建议。
                """
                res = model.generate_content([prompt, img])
                st.session_state['model_data'] = res.text
        else: st.warning("请先上传参考图。")

    if st.session_state['model_data']:
        st.markdown("---")
        st.success(f"已生成针对 {software} 的 {task_type} 指南：")
        st.markdown(st.session_state['model_data'])