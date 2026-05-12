import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    """解决打包后静态资源路径偏移问题"""
    bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(bundle_dir, path)

if __name__ == "__main__":
    # 这里的 main.py 替换成你 TeamAI 的主启动文件名
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"), 
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())