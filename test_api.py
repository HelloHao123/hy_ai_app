import google.generativeai as genai
import os


def load_key_from_secrets():
    """从 .streamlit/secrets.toml 中读取 API Key"""
    current_folder = os.path.dirname(os.path.abspath(__file__))
    secret_path = os.path.join(current_folder, ".streamlit", "secrets.toml")

    if not os.path.exists(secret_path):
        secret_path = os.path.join(".streamlit", "secrets.toml")

    if os.path.exists(secret_path):
        try:
            with open(secret_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "GEMINI_API_KEY" in line and "=" in line:
                        return line.split("=")[1].strip().strip('"').strip("'")
        except Exception as e:
            print(f"❌ 读取文件出错: {e}")
    return None


def set_proxy(port: str):
    os.environ['HTTPS_PROXY'] = f'http://127.0.0.1:{port}'
    os.environ['HTTP_PROXY'] = f'http://127.0.0.1:{port}'
    print(f"🌐 代理已设置为端口 {port}")


def test_all_models(api_key: str):
    """列出所有模型，逐个发消息测试哪些真正可用"""
    genai.configure(api_key=api_key, transport='rest')
    print(f"✅ Key: {api_key[:4]}...{api_key[-4:]}\n")

    try:
        models = [
            m.name for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
    except Exception as e:
        print(f"❌ 获取模型列表失败: {e}")
        return

    if not models:
        print("❌ 该 Key 没有任何可用模型权限。")
        return

    print(f"共找到 {len(models)} 个模型，逐一测试中...\n" + "=" * 45)

    working = []
    for i, name in enumerate(models, 1):
        print(f"[{i:02d}/{len(models)}] {name} ... ", end="", flush=True)
        try:
            response = genai.GenerativeModel(name).generate_content("回复'ok'")
            reply = response.text.strip()[:30]
            print(f"✅ 可用  |  回复: {reply}")
            working.append(name)
        except Exception as e:
            print(f"❌ 不可用  |  {str(e)[:60]}")

    print("\n" + "=" * 45)
    if working:
        print(f"🎉 可用模型（共 {len(working)} 个）：")
        for name in working:
            print(f"  ✅ {name}")
    else:
        print("😞 所有模型均不可用，请检查网络或 Key 权限。")


if __name__ == "__main__":
    # 如需代理，取消下面两行注释并确认端口
    # PROXY_PORT = "7890"
    # set_proxy(PROXY_PORT)

    api_key = load_key_from_secrets()
    if not api_key:
        print("❌ 未找到 GEMINI_API_KEY，请检查 secrets.toml 配置。")
    else:
        test_all_models(api_key)
