"""创建教师管理员账号"""
import bcrypt
from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    username = input('请输入管理员姓名: ').strip()
    password = input('请输入管理员密码: ').strip()

    if not username or not password:
        print('姓名和密码不能为空')
        exit(1)

    existing = User.query.filter_by(username=username, role='admin').first()
    if existing:
        print(f'管理员 "{username}" 已存在，将更新密码')
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        existing.password_hash = hashed.decode('utf-8')
        db.session.commit()
        print('密码已更新')
    else:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        admin = User(username=username, password_hash=hashed.decode('utf-8'), role='admin', status='approved')
        db.session.add(admin)
        db.session.commit()
        print(f'管理员 "{username}" 创建成功')

print('\n请记住管理员账号和密码，用于登录教师后台')
print(f'教师后台地址: http://localhost:8080/admin/login')
