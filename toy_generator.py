import streamlit as st
import requests
import time
import re
import random
import base64

# =================[ 1. 核心配置：从 Secrets 读取 API 密钥 ]=============
# 从 secrets 获取 ImgBB Key
IMGBB_API_KEY = st.secrets["IMGBB_API_KEY"]

# 绘图 API 配置
API_HOST = "https://grsaiapi.com" 
API_KEY = st.secrets["GRS_API_KEY"]

# =================[ 2. 图片中转站：上传至 ImgBB ]=================
def upload_image_to_imgbb(image_file):
    """
    根据 ImgBB API v1 规范上传图片
    image_file: Streamlit 上传的文件对象
    返回: 图片直链 URL
    """
    if image_file is None:
        return None
    
    url = "https://api.imgbb.com/1/upload"
    
    # 准备参数
    # expiration=600 表示图片在 10 分钟后自动删除，保护隐私且节省空间
    params = {
        "key": IMGBB_API_KEY,
        "expiration": 600 
    }
    
    # 准备文件
    files = {
        "image": image_file.getvalue()
    }

    try:
        # 使用 POST 方法上传
        response = requests.post(url, params=params, files=files, timeout=30)
        res_data = response.json()
        
        if res_data.get("success"):
            # 提取 API 返回的图片直链
            direct_url = res_data["data"]["url"]
            return direct_url
        else:
            st.error(f"ImgBB 上传失败: {res_data.get('message', '未知错误')}")
            return None
    except Exception as e:
        st.error(f"图床连接异常: {e}")
        return None

# =================[ 3. 稳定版双语提示词专家 ]=================
def refine_prompt_stable(gemini_model, config_dict):
    try:
        refine_query = f"""
        Directly act as a professional Plush Toy Industrial Designer.
        Convert input into a structured AI drawing prompt.
        
        Subject: {config_dict['subject']}, Expression: {config_dict['expression']} pose.
        Fabric: {config_dict['material']} texture, visible fibers.
        Accessories: {config_dict['accessories']}.
        Environment: {config_dict['background']}, {config_dict['style']}.
        
        Output Format:
        [EN]: (Detailed English prompt for AI drawing)
        [ZH]: (Brief Chinese design highlights)
        """
        response = gemini_model.generate_content(refine_query)
        text = response.text
        en_prompt = re.search(r'\[EN\]:(.*?)(?=\[ZH\]|$)', text, re.DOTALL).group(1).strip()
        zh_desc = re.search(r'\[ZH\]:(.*)', text, re.DOTALL).group(1).strip()
        return en_prompt, zh_desc
    except:
        return f"A high-quality plush toy, soft texture", "基础设计方案"

# =================[ 4. 绘图 API 逻辑 (支持 urls 参数) ]=================
def submit_draw_task(prompt, ref_urls=None):
    """
    提交任务，支持可选的参考图链接列表
    """
    url = f"{API_HOST}/v1/draw/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    
    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "aspectRatio": "1:1",
        "webHook": "-1", 
        "shutProgress": True 
    }
    
    # 如果有参考图链接，加入 urls 参数
    if ref_urls:
        payload["urls"] = ref_urls

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        res_data = response.json()
        if res_data.get("code") == 0:
            return res_data["data"]["id"]
        return None
    except:
        return None

def fetch_draw_result(task_id):
    """带进度反馈的轮询获取结果"""
    url = f"{API_HOST}/v1/draw/result"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    p_bar = st.progress(0)
    p_text = st.empty()
    
    for i in range(80):
        try:
            res = requests.post(url, json={"id": task_id}, headers=headers, timeout=10).json()
            if res.get("code") == 0:
                data = res["data"]
                status, progress = data.get("status"), data.get("progress", 0)
                
                # 心理安抚描述
                if progress < 20: msg = "🧶 正在解析参考图像结构..."
                elif progress < 50: msg = "🧵 正在进行虚拟缝合与布料铺设..."
                elif progress < 80: msg = "✨ 正在渲染细节纹理与环境光影..."
                else: msg = "📦 正在生成最终设计方案..."
                
                p_bar.progress(progress / 100)
                p_text.markdown(f"**{msg} ({progress}%)**")
                
                if status == "succeeded":
                    p_bar.empty(); p_text.empty()
                    return data["results"][0]["url"]
                if status == "failed":
                    p_bar.empty(); p_text.empty()
                    st.error(f"绘图失败: {data.get('failure_reason')}")
                    return None
            time.sleep(3)
        except:
            time.sleep(2)
    p_bar.empty(); p_text.error("轮询超时"); return None

# =================[ 5. 主渲染函数 ]=================
def render_toy_generator(gemini_model):
    st.markdown("<h2 style='color: #F8FAFC;'>🧸 AI 毛绒玩具专业设计室 </h2>", unsafe_allow_html=True)
    
    if "toy_generated_images" not in st.session_state:
        st.session_state.toy_generated_images = []

    # --- UI 输入区 ---
    with st.container(border=True):
        st.subheader("🖼️ 图片参考 (可选)")
        # 允许用户上传图片
        uploaded_file = st.file_uploader("上传一张参考图片或手绘草图", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            st.image(uploaded_file, caption="已上传参考图", width=250)
            st.success("✅ 已检测到参考图片，系统将自动开启“图生图”精准模式。")

        st.divider()
        st.subheader("🎨 设计参数")
        col1, col2, col3 = st.columns(3)
        with col1: subject = st.text_input("玩具形象", value="Panda")
        with col2: material = st.selectbox("核心材质", ["Minky (超柔绒)", "Teddy Fleece (颗粒绒)", "Long Fur (仿真长毛)"])
        with col3: expression = st.selectbox("神态表情", ["Cheerful", "Sleepy", "Neutral"])

        accessories = st.text_input("配件描述", placeholder="例如：背着一个红色的小书包")
        background = st.selectbox("环境场景", ["Studio (白底影棚)", "Cozy Room (温馨房间)", "Natural Light (自然光)"])

    if st.button("🚀 启动自动化设计流水线", type="primary", use_container_width=True):
        config_dict = {
            "subject": subject, "material": material, "expression": expression,
            "accessories": accessories, "background": background, "style": "Professional Photo"
        }

        with st.status("🏗️ 设计流水线运行中...", expanded=True) as status:
            # 1. 如果用户上传了图，先处理中转上传
            ref_urls = None
            if uploaded_file:
                st.write("📤 正在将参考图同步至云端加速引擎...")
                cloud_url = upload_image_to_imgbb(uploaded_file)
                if cloud_url:
                    ref_urls = [cloud_url]
                    st.write("✅ 图片中转成功。")
                else:
                    st.warning("⚠️ 图片中转失败，将切换为纯文生图模式。")

            # 2. Gemini 构思提示词
            st.write("🧠 行业专家正在构思设计指令...")
            en_prompt, zh_desc = refine_prompt_stable(gemini_model, config_dict)
            
            # 3. 提交绘图任务
            st.write("🖌️ 正在启动绘图引擎进行设计建模...")
            task_id = submit_draw_task(en_prompt, ref_urls=ref_urls)
            
            if task_id:
                final_img_url = fetch_draw_result(task_id)
                if final_img_url:
                    # 下载成品图片字节流
                    img_data = requests.get(final_img_url, timeout=30).content
                    
                    # 存入结果
                    st.session_state.toy_generated_images.append({
                        "content": img_data,
                        "filename": f"Plush_{int(time.time())}.png",
                        "en_prompt": en_prompt,
                        "zh_desc": zh_desc,
                        "is_i2i": True if ref_urls else False
                    })
                    status.update(label="✅ 设计生成成功！", state="complete")
                else:
                    st.error("获取结果超时。")
            else:
                st.error("任务提交失败。")

    # =================[ 陈列馆展示 ]=================
    if st.session_state.toy_generated_images:
        st.divider()
        st.subheader("🖼️ 历史作品库")
        display_list = list(reversed(st.session_state.toy_generated_images))
        for i in range(0, len(display_list), 2):
            cols = st.columns(2)
            for j in range(2):
                idx = i + j
                if idx < len(display_list):
                    item = display_list[idx]
                    with cols[j]:
                        with st.container(border=True):
                            st.image(item["content"], use_container_width=True)
                            if item.get("is_i2i"):
                                st.caption("✨ 此方案基于参考图精准生成")
                            with st.expander("📋 查看设计亮点"):
                                st.write(item.get('zh_desc'))
                            st.download_button("⬇ 下载设计稿", item["content"], file_name=item["filename"], key=f"dl_{idx}")