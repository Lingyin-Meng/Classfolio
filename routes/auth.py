import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()

        if not username or not password:
            flash('姓名和密码不能为空', 'danger')
            return render_template('register.html')

        if len(username) > 20:
            flash('姓名长度不能超过20个字符', 'danger')
            return render_template('register.html')

        if password != confirm:
            flash('两次输入的密码不一致', 'danger')
            return render_template('register.html')

        if len(password) < 4:
            flash('密码长度至少为4位', 'danger')
            return render_template('register.html')

        existing = User.query.filter_by(username=username).first()
        if existing:
            flash('该姓名已被注册', 'danger')
            return render_template('register.html')

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(username=username, password_hash=hashed.decode('utf-8'), role='student', status='pending')
        db.session.add(user)
        db.session.commit()

        flash('注册成功！请等待教师审核通过后登录', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username, role='student').first()
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            flash('姓名或密码错误', 'danger')
            return render_template('login.html')

        if user.status == 'pending':
            flash('账号正在等待教师审核，请耐心等待', 'warning')
            return render_template('login.html')

        if user.status == 'rejected':
            flash('您的账号审核未通过，请联系教师', 'danger')
            return render_template('login.html')

        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        flash(f'欢迎回来，{user.username}！', 'success')
        return redirect(url_for('upload.home'))

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('auth.login'))
