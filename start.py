import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 40)
print("   课堂局域网视频共享平台 - 服务器")
print("=" * 40)
print()

# 检查 Python
try:
    subprocess.run([sys.executable, '--version'], capture_output=True, check=True)
except Exception:
    print("[错误] 未检测到 Python，请先安装 Python 3.9+")
    input("按任意键退出...")
    sys.exit(1)

# 安装依赖
print("[1/3] 安装 Python 依赖...")
result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '-q'])
if result.returncode != 0:
    print("[错误] 依赖安装失败，请检查网络连接")
    input("按任意键退出...")
    sys.exit(1)

# 检查管理员账号
print()
print("[2/3] 检查管理员账号...")
check_code = "from app import create_app; from models import db, User; app=create_app(); import sys; sys.exit(0 if User.query.filter_by(role='admin').first() else 1)"
result = subprocess.run([sys.executable, '-c', check_code])
if result.returncode != 0:
    print("未检测到管理员账号，请创建一个:")
    subprocess.run([sys.executable, 'create_admin.py'])

# 启动服务器
print()
print("[3/3] 启动服务器...")
print()
print("=" * 40)
print("   服务器启动中...")
print("   学生访问地址: http://教师机IP:8080")
print("   教师后台地址: http://教师机IP:8080/admin/login")
print()
print("   按 Ctrl+C 停止服务器")
print("=" * 40)
print()

subprocess.run([sys.executable, 'app.py'])
