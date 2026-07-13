import os
import bcrypt
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models import db, User, FileRecord, WebProject
from config import UPLOAD_ROOT
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username, role='admin').first()
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            flash('管理员账号或密码错误', 'danger')
            return render_template('admin_login.html')

        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = 'admin'
        flash(f'欢迎，{user.username}老师！', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin_login.html')


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    pending_users_count = User.query.filter_by(role='student', status='pending').count()
    approved_users_count = User.query.filter_by(role='student', status='approved').count()
    pending_files_count = FileRecord.query.filter_by(status='pending').count()
    total_files = FileRecord.query.filter_by(status='approved').count()
    total_size = db.session.query(db.func.sum(FileRecord.file_size)).filter(FileRecord.status == 'approved').scalar() or 0
    pending_web_count = WebProject.query.filter_by(status='pending').count()
    total_web_count = WebProject.query.filter_by(status='approved').count()

    return render_template('admin/dashboard.html',
                           pending_users_count=pending_users_count,
                           approved_users_count=approved_users_count,
                           pending_files_count=pending_files_count,
                           total_files=total_files,
                           total_size=total_size,
                           pending_web_count=pending_web_count,
                           total_web_count=total_web_count)


@admin_bp.route('/review')
@admin_required
def review():
    pending_students = User.query.filter_by(role='student', status='pending').order_by(User.created_at.desc()).all()
    return render_template('admin/review.html', students=pending_students)


@admin_bp.route('/review/<int:user_id>', methods=['POST'])
@admin_required
def review_action(user_id):
    action = request.form.get('action', '')
    student = db.session.get(User, user_id)

    if not student or student.role != 'admin' and student.status != 'pending':
        return jsonify({'error': '学生不存在或已处理'}), 404

    if action == 'approve':
        student.status = 'approved'
        db.session.commit()
        # 创建学生文件夹
        student_dir = os.path.normpath(os.path.join(UPLOAD_ROOT, student.username))
        if student_dir.startswith(os.path.normpath(UPLOAD_ROOT)):
            os.makedirs(student_dir, exist_ok=True)
        return jsonify({'success': True, 'message': f'已通过 {student.username} 的注册'})

    elif action == 'reject':
        student.status = 'rejected'
        db.session.commit()
        return jsonify({'success': True, 'message': f'已拒绝 {student.username} 的注册'})

    return jsonify({'error': '无效操作'}), 400


@admin_bp.route('/files')
@admin_required
def all_files():
    student_filter = request.args.get('student', '').strip()
    status_filter = request.args.get('status', '').strip()
    query = FileRecord.query.join(User).order_by(FileRecord.created_at.desc())

    if student_filter:
        query = query.filter(User.username.like(f'%{student_filter}%'))

    if status_filter and status_filter in ('pending', 'approved', 'rejected'):
        query = query.filter(FileRecord.status == status_filter)

    files = query.all()
    students = User.query.filter_by(role='student', status='approved').order_by(User.username).all()

    return render_template('admin/all_files.html',
                           files=files,
                           students=students,
                           current_filter=student_filter,
                           current_status=status_filter)


@admin_bp.route('/file/<int:file_id>/review', methods=['POST'])
@admin_required
def review_file(file_id):
    action = request.form.get('action', '')
    record = db.session.get(FileRecord, file_id)
    if not record:
        return jsonify({'error': '文件不存在'}), 404

    if action == 'approve':
        record.status = 'approved'
        db.session.commit()
        return jsonify({'success': True, 'message': '文件已审核通过', 'new_status': 'approved'})

    elif action == 'reject':
        record.status = 'rejected'
        db.session.commit()
        return jsonify({'success': True, 'message': '文件已拒绝（作品被打回）', 'new_status': 'rejected'})

    return jsonify({'error': '无效操作'}), 400


@admin_bp.route('/web-projects')
@admin_required
def web_projects():
    status_filter = request.args.get('status', '').strip()
    query = WebProject.query.order_by(WebProject.deployed_at.desc())

    if status_filter and status_filter in ('pending', 'approved', 'rejected'):
        query = query.filter(WebProject.status == status_filter)

    projects = query.all()
    return render_template('admin/web_projects.html',
                           projects=projects,
                           current_status=status_filter)


@admin_bp.route('/file/<int:file_id>', methods=['DELETE'])
@admin_required
def delete_file(file_id):
    record = db.session.get(FileRecord, file_id)
    if not record:
        return jsonify({'error': '文件不存在'}), 404

    user = db.session.get(User, record.uploader_id)
    file_path = os.path.normpath(os.path.join(UPLOAD_ROOT, user.username, record.stored_name))
    if file_path.startswith(os.path.normpath(UPLOAD_ROOT)) and os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(record)
    db.session.commit()
    return jsonify({'success': True, 'message': '文件已删除'})
