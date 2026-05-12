import streamlit as st
import re
import io
import datetime
import json
import os
from PIL import Image
import google.generativeai as genai

# --- 配置文件路径 ---
HISTORY_FILE = "sku_strategy_history.json"

# --- 1. 持久化存储工具 ---
def load_history_from_file():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"读取历史文件失败: {e}")
    return []

def save_history_to_file(history_list):
    try:
        to_save = history_list[:10]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"保存历史文件失败: {e}")

# --- 2. 图像处理工具 ---
def optimize_image(uploaded_file, max_dim=1024):
    try:
        img = Image.open(uploaded_file)
        orig_w, orig_h = img.size
        if max(orig_w, orig_h) > max_dim:
            scale = max_dim / max(orig_w, orig_h)
            img = img.resize((int(orig_w * scale), int(orig_h * scale)), Image.Resampling.LANCZOS)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        return buf.getvalue()
    except Exception as e:
        st.error(f"图片处理异常: {e}")
        return None

# --- 3. 稳健的解析逻辑 (保留符号完整性) ---
def parse_sections(full_text):
    if not full_text: return {}
    clean_text = re.sub(r'\*+---\s*([A-Z_]+)\s*---\*+', r'---\1---', full_text)
    parts = re.split(r'---([A-Z_]+)---', clean_text)
    sections = {}
    for i in range(1, len(parts), 2):
        tag = parts[i].strip()
        content = parts[i+1].strip()
        # 仅清理开头的冒号和空白，保留【】
        content = re.sub(r'^[:：\n\s*]+', '', content).strip()
        sections[tag] = content
    return sections

# --- 4. 智能提取产品预览标题 ---
def get_product_preview(sections):
    raw_name = sections.get("PRODUCT_IDENTIFIER", "").strip()
    # 彻底清洗掉 AI 误带的“精准商业名称：”等前缀
    clean_name = re.sub(r'^(精准商业名称|产品名称|产品标识|Product Identifier|Identifier)[:：\s]*', '', raw_name, flags=re.I)
    clean_name = re.sub(r'^[【】:：\n\s*]+', '', clean_name).strip()
    if len(clean_name) < 2:
        text = sections.get("LOCALIZATION_GUIDE", "")
        match = re.search(r'【(.*?)】', text)
        clean_name = match.group(1)[:12] if match else "历史调研产品"
    return clean_name[:15]

# --- 5. 美化渲染组件 ---
def styled_box(content, bg_color="#f0f2f6", border_color="#dee2e6"):
    """
    将内容封装在带背景色的美化框中，支持简单的 Markdown 渲染。
    """
    # 处理换行和加粗，使其在 HTML 容器中也能保持阅读性
    html_content = content.replace('\n', '<br>')
    html_content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html_content)
    st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 18px; border-radius: 10px; 
                    border-left: 6px solid {border_color}; font-size: 14px; color: #333; line-height: 1.6;">
            {html_content}
        </div>
    """, unsafe_allow_html=True)

# --- 6. 主渲染函数 ---
def render(model):
    st.markdown("#### 🛠️ SKU 爆款实验室", help="基于实时联网数据的深度选品工具")

    if 'sku_sections' not in st.session_state:
        st.session_state['sku_sections'] = {}
    if 'sku_history' not in st.session_state:
        st.session_state['sku_history'] = load_history_from_file()

    # --- A. 配置区域 ---
    with st.container(border=True):
        c_l, c_r = st.columns([1, 2.5])
        with c_l:
            prod_img = st.file_uploader("上传 SKU 样图", type=["png", "jpg", "jpeg", "webp"], key="Uploader_V68")
            if prod_img: st.image(prod_img, width=150)
        with c_r:
            col1, col2 = st.columns(2)
            with col1:
                target_platform = st.selectbox("投放平台", ["Shopee", "Amazon", "TikTok Shop", "Lazada"])
                country = st.selectbox("目标市场", ["马来西亚 (Malaysia)", "美国 (USA)", "德国 (Germany)", "越南 (Vietnam)"])
            with col2:
                style = st.selectbox("文案调性", ["极致爆款 (Viral)", "专业严谨", "奢侈高档", "性价比驱动"])
                langs = st.multiselect("输出语种", ["英文", "马来文", "德文", "法文", "泰文", "越南文"], default=["英文", "马来文"])

    # --- B. 核心执行层 ---
    if st.button("🚀 启动全球深度调研报告", type="primary", use_container_width=True):
        if prod_img and langs:
            with st.status("正在启动高阶战略调研...", expanded=True) as status:
                status.update(label="📸 扫描视觉特征与品类属性...")
                opt_bytes = optimize_image(prod_img)
                if not opt_bytes: return

                status.update(label="📡 穿透多平台实时数据库...")
                try:
                    model.tools = [{"google_search_retrieval": {}}]
                    lang_str = "、".join(langs)
                    
                    prompt = f"""
                    针对 **{target_platform}** 平台及 **{country}** 市场执行深度调研。必须联网！
                    格式规范：严禁使用巨大标题，模块内使用 **加粗**。
                    
                    ---PRODUCT_IDENTIFIER---
                    （直接给出产品名，严禁包含任何前缀标签）

                    ---LOCALIZATION_GUIDE---
                    【实时深度调研】：包含竞品价格雷达、受众画像、准入风险、2026 流量趋势。

                    ---PROSPECT_ANALYSIS---
                    【战略预测】：包含 SWOT 分析、具体改良建议、12个月销量波峰预测。

                    ---PRICING_ADVICE---
                    【财务建议】：基于零售价反推 ideal FOB 采购价，提供 1200/2400/3600 只的阶梯建议价表格。

                    ---SOCIAL_MARKETING---
                    【营销方案】：包含拍摄脚本方向、达人策略建议、5-10个热门标签。

                    ---SEARCH_KEYWORDS---
                    【搜索关键词】：提供 10 个精准搜索关键词。

                    ---LISTING_MATRIX---
                    【多语种隔离文案】：每个语种前使用 🌍 [语种名称] 标记。语种包括：{lang_str}。
                    """
                    
                    status.update(label="🧠 正在进行多维度战略建模...")
                    response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": opt_bytes}])
                    
                    if not response.text: raise ValueError("响应为空")
                    parsed_data = parse_sections(response.text)
                    st.session_state['sku_sections'] = parsed_data
                    
                    new_record = {
                        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "prod_name": get_product_preview(parsed_data),
                        "platform": target_platform,
                        "country": country,
                        "data": parsed_data
                    }
                    st.session_state['sku_history'].insert(0, new_record)
                    st.session_state['sku_history'] = st.session_state['sku_history'][:10]
                    save_history_to_file(st.session_state['sku_history'])
                    
                    status.update(label="✅ 调研已完成", state="complete")
                    st.rerun()
                except Exception as e:
                    status.update(label="❌ 调研中止", state="error")
                    st.error(f"原因: {str(e)}")
                    return
        else:
            st.warning("请检查配置。")

    # --- C. 展现层 (视觉增强版) ---
    sections = st.session_state['sku_sections']
    if sections:
        display_name = sections.get("PRODUCT_IDENTIFIER", country)
        st.markdown(f"#### 📊 {display_name} 深度市场决策看板")
        st.caption("⚠️ 数据源于实时抓取及平台规则反推，仅供战略指导参考。")

        # 1. 实时调研 (默认展开 - 蓝色调)
        with st.expander(f"🚩 {country} 实时网络搜索调研结果", expanded=True):
            styled_box(sections.get("LOCALIZATION_GUIDE", "无数据"), bg_color="#eef7ff", border_color="#007bff")

        # 2. 前景预测 (默认折叠 - 绿色调)
        with st.expander("📈 产品前景与建设性趋势预测", expanded=False):
            styled_box(sections.get("PROSPECT_ANALYSIS", "无数据"), bg_color="#f0fff4", border_color="#28a745")

        # 3. 策略并列卡片
        col_l, col_r = st.columns(2)
        with col_l:
            with st.container(border=True):
                st.markdown("**💰 定价与阶梯采购策略 (RMB)**")
                # 财务建议使用灰色调体现专业
                styled_box(sections.get("PRICING_ADVICE", "核算中..."), bg_color="#f8f9fa", border_color="#6c757d")
        with col_r:
            with st.container(border=True):
                st.markdown("**📱 社交营销策略建议**")
                # 营销建议使用明亮黄色调
                styled_box(sections.get("SOCIAL_MARKETING", "建议中..."), bg_color="#fffbeb", border_color="#ffc107")

        # 4. 文案与关键词 (紫色调)
        with st.expander("📋 多语种合规文案 / 🔍 搜索关键词", expanded=False):
            styled_box(sections.get("LISTING_MATRIX", "文案生成中..."), bg_color="#f5f3ff", border_color="#6f42c1")
            st.divider()
            st.markdown("**核心参考关键词**")
            st.code(sections.get("SEARCH_KEYWORDS", "提取中..."))

        st.divider()
        full_report = "\n\n".join([f"---{k}---\n{v}" for k, v in sections.items()])
        st.download_button("📥 导出全维度报告", full_report, file_name=f"Strategy_{display_name}.md", use_container_width=True)

    # --- D. 历史记录 (持久化显示) ---
    st.write("") 
    with st.expander("📂 查看历史调研记录 (本地保存最近10条)", expanded=False):
        if not st.session_state['sku_history']:
            st.write("暂无记录。")
        else:
            for i, record in enumerate(st.session_state['sku_history']):
                with st.container(border=True):
                    c_info, c_pop = st.columns([3.5, 1.2])
                    with c_info:
                        name = record.get('prod_name', "历史记录")
                        st.markdown(f"🕒 `{record.get('time')}` **{name}**")
                        st.caption(f"{record.get('country')} | {record.get('platform')}")
                    with c_pop:
                        with st.popover("📄 查看摘要", use_container_width=True):
                            st.markdown(f"**{name} 快速预览**")
                            h_data = record.get('data', {})
                            st.markdown("**核心财务:**")
                            st.caption(h_data.get("PRICING_ADVICE", "")[:120] + "...")
                            st.divider()
                            if st.button("恢复完整报告", key=f"hist_res_{i}", use_container_width=True):
                                st.session_state['sku_sections'] = h_data
                                st.rerun()

if __name__ == "__main__":
    pass