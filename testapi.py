import google.generativeai as genai

# 请在这里填入你的 API Key
YOUR_API_KEY = "AIzaSyAT-ZN4f8i64C2lAQBY-s6PpgwRcFOW4s0"
genai.configure(api_key=YOUR_API_KEY)

def check_my_permissions():
    print("正在连接 Google API 检查权限...\n")
    
    try:
        # 1. 检查 API Key 是否有效
        models = genai.list_models()
        print("✅ API Key 验证成功。")
        
        # 2. 列出所有可用模型及功能
        print("\n--- 你可以使用的模型列表 ---")
        found_flash = False
        for m in models:
            # 检查模型是否支持生成内容
            if 'generateContent' in m.supported_generation_methods:
                print(f"🔹 模型名称: {m.name}")
                print(f"   显示名称: {m.display_name}")
                # 检查是否支持工具调用 (Google Search 属于工具)
                # 注意：部分 SDK 版本不直接显示 tools 字段，我们会通过下一步测试
                if "gemini-1.5-flash" in m.name:
                    found_flash = True
        
        # 3. 针对性测试：尝试初始化带搜索工具的模型
        print("\n--- 联网搜索功能专项测试 ---")
        if found_flash:
            try:
                # 尝试使用 v1beta 接口
                test_model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',
                    tools=[{"google_search_retrieval": {}}]
                )
                print("✅ 联网搜索工具 (google_search_retrieval) 配置成功。")
            except Exception as e:
                print(f"❌ 联网搜索工具配置失败: {str(e)}")
                print("   💡 提示：这通常意味着你的 API Key 权限或所在地区暂不支持此功能。")
        else:
            print("⚠️ 未发现 gemini-1.5-flash 模型，请检查 API Key 配置。")

    except Exception as e:
        print(f"❌ 访问失败: {str(e)}")
        if "API_KEY_INVALID" in str(e):
            print("   💡 请检查你的 API Key 是否输入正确。")

if __name__ == "__main__":
    check_my_permissions()