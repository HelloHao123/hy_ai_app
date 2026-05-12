import streamlit as st
from PIL import Image

def render_product_copywriter(model):
    """渲染支持东南亚小语种及缩略图预览的文案模块"""
    st.header("✍️ 商品文案智能生成 (多语种版)")
    st.write("上传商品图，AI 将为您生成符合平台特性及当地语境的爆款文案。")

    # 1. 平台与语言配置
    col_p, col_l = st.columns(2)
    
    with col_p:
        platform = st.radio(
            "选择目标发布平台：",
            ["TikTok", "Shopee", "Lazada"],
            horizontal=True
        )

    with col_l:
        target_lang = st.selectbox(
            "选择生成的当地语言：",
            ["不翻译 (仅中英)", "印尼语 (Indonesian)", "马来西亚语 (Malay)", "泰语 (Thai)", "越南语 (Vietnamese)"]
        )

    # 2. 图片上传 (限制 3 张)
    uploaded_files = st.file_uploader(
        "上传商品图片 (最多 3 张)：", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        key="copy_upload"
    )

    # 3. 优化后的图片预览：尺寸缩小为 1/4 (约 150px)
    if uploaded_files:
        if len(uploaded_files) > 3:
            st.warning("⚠️ 仅处理前 3 张图片。")
            uploaded_files = uploaded_files[:3]
        
        st.write("📝 图片预览 (缩略图):")
        cols = st.columns(len(uploaded_files))
        imgs = []
        for i, file in enumerate(uploaded_files):
            img = Image.open(file)
            imgs.append(img)
            # 设定固定宽度 150px 以达到缩小效果
            cols[i].image(img, width=150, caption=f"图 {i+1}")

        # 4. 执行生成逻辑
        if st.button(f"🚀 生成 {platform} + {target_lang} 文案", type="primary"):
            with st.spinner(f"正在进行多模态分析并翻译为 {target_lang}..."):
                try:
                    # 针对平台的专业指令
                    platform_style = {
                        "TikTok": "TikTok 风格：侧重前 3 秒钩子，高情绪价值，丰富的表情符号 (Emoji)，热门标签。",
                        "Shopee": "Shopee 风格：侧重标题 SEO 关键词堆叠，清晰的规格参数列表，促销导向。",
                        "Lazada": "Lazada 风格：侧重品牌专业感，结构化的产品优势 (USP) 描述，信任感背书。"
                    }

                    # 构建多语言指令
                    lang_instr = f"同时，请务必将文案精准翻译成地道的【{target_lang}】。" if target_lang != "不翻译 (仅中英)" else "仅提供中英文对照。"

                    base_prompt = f"""
                    作为数字贸易事业部的顶级运营专家，请分析这些图片并为 {platform} 平台撰写高转化率文案。
                    
                    要求：
                    1. 风格指南：{platform_style[platform]}
                    2. 核心内容：包含爆款标题、卖点分点、详细介绍。
                    3. 语言要求：先提供【英文】版本，再提供【中文】对照，{lang_instr}
                    4. 翻译标准：小语种翻译需符合当地购物习惯和口语表达，不要有僵硬的机翻感。
                    """

                    # 利用付费版高配额进行多模态生成
                    response = model.generate_content([base_prompt] + imgs)
                    
                    with st.container(border=True):
                        st.subheader("📄 生成结果预览")
                        st.markdown(response.text)
                        st.success(f"已根据 {platform} 算法及 {target_lang} 语境优化完成。")

                except Exception as e:
                    st.error(f"生成失败，请检查网络或 API 配置: {e}")