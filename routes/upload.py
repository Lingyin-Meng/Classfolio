import os
import uuid
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from models import db, User, FileRecord, WebProject
from config import UPLOAD_ROOT, ALLOWED_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS
from utils.decorators import login_required

upload_bp = Blueprint('upload', __name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_type(ext):
    ext = ext.lower()
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return 'image'
    return 'video'


def get_user_dir(username):
    user_dir = os.path.normpath(os.path.join(UPLOAD_ROOT, username))
    # 防止路径穿越
    if not user_dir.startswith(os.path.normpath(UPLOAD_ROOT)):
        raise ValueError('非法路径')
    return user_dir


@upload_bp.route('/')
@login_required
def home():
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))
    user = db.session.get(User, session['user_id'])
    files = FileRecord.query.filter_by(uploader_id=user.id).order_by(FileRecord.created_at.desc()).all()
    web_projects = WebProject.query.filter_by(uploader_id=user.id).order_by(WebProject.deployed_at.desc()).all()
    return render_template('home.html', user=user, files=files, web_projects=web_projects)


@upload_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    if session.get('role') == 'admin':
        return jsonify({'error': '教师账号不能上传文件'}), 403

    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': '没有选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件格式，请上传图片或视频文件'}), 400

    user = db.session.get(User, session['user_id'])
    ext = file.filename.rsplit('.', 1)[1].lower()
    file_type = get_file_type(ext)
    stored_name = f"{uuid.uuid4().hex}.{ext}"

    user_dir = get_user_dir(user.username)
    os.makedirs(user_dir, exist_ok=True)

    save_path = os.path.join(user_dir, stored_name)
    file.save(save_path)
    file_size = os.path.getsize(save_path)

    record = FileRecord(
        filename=file.filename,
        stored_name=stored_name,
        uploader_id=user.id,
        file_size=file_size,
        file_type=file_type,
        mime_type=file.content_type,
        status='pending'
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '上传成功！作品已提交，请等待教师审核通过后展示给同学',
        'file': {
            'id': record.id,
            'filename': record.filename,
            'file_type': record.file_type,
            'file_size': record.file_size,
            'status': record.status
        }
    })


@upload_bp.route('/file/<int:file_id>/serve')
@login_required
def serve_file(file_id):
    record = db.session.get(FileRecord, file_id)
    if not record:
        return '文件不存在', 404

    # 审核状态权限控制：已通过→所有人可见；待审核/已拒绝→仅上传者本人和教师可见
    if record.status != 'approved':
        if session.get('role') != 'admin' and session['user_id'] != record.uploader_id:
            return '文件暂未审核通过，不可查看', 403

    user = db.session.get(User, record.uploader_id)
    file_path = os.path.normpath(os.path.join(UPLOAD_ROOT, user.username, record.stored_name))

    if not file_path.startswith(os.path.normpath(UPLOAD_ROOT)):
        return '禁止访问', 403

    if not os.path.exists(file_path):
        return '文件不存在', 404

    return send_file(file_path)


@upload_bp.route('/file/<int:file_id>/thumbnail')
@login_required
def thumbnail(file_id):
    record = db.session.get(FileRecord, file_id)
    if not record:
        return '', 404

    if record.file_type == 'image':
        return redirect(url_for('upload.serve_file', file_id=file_id))

    # 视频返回默认图标
    from flask import send_from_directory
    return '', 204


@upload_bp.route('/file/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    record = db.session.get(FileRecord, file_id)
    if not record:
        return jsonify({'error': '文件不存在'}), 404

    # 学生只能删自己的文件
    if session.get('role') != 'admin' and record.uploader_id != session['user_id']:
        return jsonify({'error': '无权删除此文件'}), 403

    user = db.session.get(User, record.uploader_id)
    file_path = os.path.normpath(os.path.join(UPLOAD_ROOT, user.username, record.stored_name))
    if file_path.startswith(os.path.normpath(UPLOAD_ROOT)) and os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(record)
    db.session.commit()
    return jsonify({'success': True, 'message': '删除成功'})


@upload_bp.route('/my-files')
@login_required
def my_files():
    files = FileRecord.query.filter_by(uploader_id=session['user_id']).order_by(FileRecord.created_at.desc()).all()
    result = []
    for f in files:
        result.append({
            'id': f.id,
            'filename': f.filename,
            'file_type': f.file_type,
            'file_size': f.file_size,
            'status': f.status,
            'created_at': f.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return jsonify(result)
