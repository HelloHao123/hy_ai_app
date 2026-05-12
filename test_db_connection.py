import pymysql

# --- 您的 MySQL 数据库连接信息 ---
# 根据您提供的配置进行修改
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'root'            # 用户名修改为 root
DB_PASSWORD = '123456'      # 密码修改为 123456
DB_NAME = 'client_tracker'  # 数据库名修改为 client_tracker
DB_CHARSET = 'utf8mb4'
# -----------------------------------------------

def test_mysql_connection():
    print("--- 正在测试 MySQL 数据库连接 ---")
    print(f"主机: {DB_HOST}:{DB_PORT}")
    print(f"用户: {DB_USER}")
    print(f"数据库: {DB_NAME}")
    print("-" * 30)

    try:
        # 尝试建立连接
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset=DB_CHARSET,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("\n✅ 恭喜！成功连接到 MySQL 数据库！")

        # 尝试执行一个简单的查询来进一步验证
        with conn.cursor() as cursor:
            # 查询版本信息
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            print(f"MySQL 服务器版本: {version['VERSION()']}")

            # 尝试查询已创建的表 (如果存在)
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            if tables:
                print("\n数据库中存在的表:")
                for table in tables:
                    print(f"  - {list(table.values())[0]}")
            else:
                print("\n数据库中目前没有表。")

    except pymysql.err.OperationalError as e:
        print(f"\n❌ 连接失败！错误信息:")
        print(f"   错误代码: {e.args[0]}")
        print(f"   错误详情: {e.args[1]}")
        
        if e.args[0] == 2003:
            print("\n  可能原因: MySQL 服务器未启动，或主机/端口配置错误。")
            print("  请确保 MySQL 服务正在运行，并且 IP 地址和端口号是正确的。")
        elif e.args[0] == 1045:
            print("\n  可能原因: 用户名或密码错误，或该用户没有权限从当前主机连接。")
            print("  请检查用户名 (`DB_USER`) 和密码 (`DB_PASSWORD`) 是否正确。")
            print("  确保用户被授权从 'localhost' (或您的服务器IP) 访问。")
            print("\n  特别提醒：root 用户通常有权限限制，不允许远程直接登录。")
            print("  如果你正在尝试从非 'localhost' 连接，需要修改 MySQL 的用户权限设置。")
        elif e.args[0] == 1049:
            print("\n  可能原因: 数据库名称错误或不存在。")
            print("  请检查数据库名称 (`DB_NAME`) 是否正确，并确保已在 MySQL 中创建该数据库。")
        else:
            print("\n  其他连接错误。")

    except Exception as e:
        print(f"\n❌ 发生未知错误: {e}")

    finally:
        if 'conn' in locals() and conn.open:
            conn.close()
            print("\nMySQL 连接已关闭。")

if __name__ == "__main__":
    test_mysql_connection()