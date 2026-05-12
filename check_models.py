import google.generativeai as genai

# 填入你的 Key
genai.configure(api_key="AIzaSyCTTqticeK9_75luM1eh-QUfBBTi3rrM3g")

print("正在获取可用模型列表...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"可用模型: {m.name}")
except Exception as e:
    print(f"出错了: {e}")
