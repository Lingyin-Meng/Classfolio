import os
import uuid
import zipfile
import shutil
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from models import db, User, WebProject
from config import WEB_ROOT, MAX_ZIP_SIZE, MAX_TOTAL_WEB_SIZE, WEB_ALLOWED_MIMES
from utils.decorators import login_required, admin_required

web_bp = Blueprint('web', __name__)


def safe_ext_dir(extract_dir):
    """规范化路径，防止路径穿越"""
    return os.path.normpath(os.path.abspath(extract_dir))


def validate_zip_path(entry_name, base_dir):
    """检查 ZIP 条目是否合法：无 ../ 、无绝对路径"""
    full = os.path.normpath(os.path.join(base_dir, entry_name))
    if not full.startswith(base_dir):
        return False
    return True


@web_bp.route('/web/upload', methods=['POST'])
@login_required
def upload_zip():
    if session.get('role') == 'admin':
        return jsonify({'error': '教师账号不能上传网页项目'}), 403

    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': '没有选择文件'}), 400

    if not file.filename.lower().endswith('.zip'):
        return jsonify({'error': '仅支持 .zip 格式的压缩包'}), 400

    # 检查 ZIP 文件大小
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_ZIP_SIZE:
        return jsonify({'error': f'压缩包不能超过 {MAX_ZIP_SIZE // 1024 // 1024}MB'}), 400

    user = db.session.get(User, session['user_id'])

    # 检查该学生已部署的网页总大小
    existing_total = db.session.query(db.func.sum(WebProject.total_size)).filter(
        WebProject.uploader_id == user.id
    ).scalar() or 0
    if existing_total >= MAX_TOTAL_WEB_SIZE:
        return jsonify({'error': f'你的网页项目总大小已达上限 {MAX_TOTAL_WEB_SIZE // 1024 // 1024}MB'}), 400

    # 项目名（去除 .zip 后缀）
    project_name = file.filename[:-4].strip()
    if not project_name or len(project_name) > 80:
        return jsonify({'error': '项目名称过长或无效'}), 400

    # 非法字符检查
    forbidden_chars = set('\\/:*?"<>|')
    if any(c in project_name for c in forbidden_chars):
        return jsonify({'error': '项目名称包含非法字符'}), 400

    # 唯一文件夹名
    folder_name = f"{uuid.uuid4().hex}"
    user_dir = safe_ext_dir(os.path.join(WEB_ROOT, user.username))
    extract_dir = safe_ext_dir(os.path.join(user_dir, folder_name))

    os.makedirs(extract_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(file, 'r') as zf:
            # 检查是否包含 index.html
            entries = zf.namelist()
            has_index = any(
                os.path.basename(e.rstrip('/')) == 'index.html' or
                os.path.basename(e.rstrip('/')) == 'index.htm'
                for e in entries
            )
            if not has_index:
                shutil.rmtree(extract_dir)
                return jsonify({'error': '压缩包内必须包含 index.html 文件'}), 400

            total_size = 0
            for entry in entries:
                # 跳过目录条目
                if entry.endswith('/'):
                    continue

                if not validate_zip_path(entry, extract_dir):
                    shutil.rmtree(extract_dir)
                    return jsonify({'error': '压缩包包含非法路径，拒绝解压'}), 400

                info = zf.getinfo(entry)
                total_size += info.file_size

                if total_size > MAX_TOTAL_WEB_SIZE - existing_total:
                    shutil.rmtree(extract_dir)
                    return jsonify({'error': '解压后文件超过总大小限制'}), 400

            zf.extractall(extract_dir)

    except zipfile.BadZipFile:
        shutil.rmtree(extract_dir, ignore_errors=True)
        return jsonify({'error': '无效的 ZIP 文件'}), 400
    except Exception as e:
        shutil.rmtree(extract_dir, ignore_errors=True)
        return jsonify({'error': f'解压失败: {str(e)}'}), 500

    # 若已有同名项目，更新覆盖
    existing = WebProject.query.filter_by(uploader_id=user.id, project_name=project_name).first()
    if existing:
        # 删除旧文件夹
        old_dir = safe_ext_dir(os.path.join(WEB_ROOT, user.username, existing.folder_name))
        shutil.rmtree(old_dir, ignore_errors=True)
        existing.folder_name = folder_name
        existing.total_size = total_size
        existing.status = 'pending'
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '网页项目已更新！请等待教师审核通过',
            'project': {'id': existing.id, 'project_name': existing.project_name, 'status': existing.status}
        })

    project = WebProject(
        project_name=project_name,
        folder_name=folder_name,
        uploader_id=user.id,
        total_size=total_size,
        status='pending'
    )
    db.session.add(project)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '网页部署成功！请等待教师审核通过后对全班开放',
        'project': {'id': project.id, 'project_name': project.project_name, 'status': project.status}
    })


@web_bp.route('/web/<username>/<project_folder>/<path:filepath>')
@web_bp.route('/web/<username>/<project_folder>', defaults={'filepath': 'index.html'})
@web_bp.route('/web/<username>/<project_folder>/', defaults={'filepath': 'index.html'})
def serve_web(username, project_folder, filepath):
    """静态文件服务 — 仅允许已审核通过的项目"""

    # 查找项目
    user = User.query.filter_by(username=username).first()
    if not user:
        return '学生不存在', 404

    project = WebProject.query.filter_by(
        uploader_id=user.id, folder_name=project_folder
    ).first()
    if not project or project.status != 'approved':
        return '网页项目不存在或未审核通过', 404

    base_dir = safe_ext_dir(os.path.join(WEB_ROOT, username, project_folder))

    # 路径穿越防护
    requested = safe_ext_dir(os.path.join(base_dir, filepath))
    if not requested.startswith(base_dir):
        return '禁止访问', 403

    # MIME 类型白名单
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in WEB_ALLOWED_MIMES:
        return '不支持的文件类型', 403

    if not os.path.exists(requested) or not os.path.isfile(requested):
        return '文件不存在', 404

    # send_from_directory 自带安全校验
    return send_from_directory(base_dir, filepath)


@web_bp.route('/web/projects')
@login_required
def my_projects():
    projects = WebProject.query.filter_by(uploader_id=session['user_id']).order_by(
        WebProject.deployed_at.desc()
    ).all()
    user = db.session.get(User, session['user_id'])
    result = []
    for p in projects:
        result.append({
            'id': p.id,
            'project_name': p.project_name,
            'folder_name': p.folder_name,
            'username': user.username,
            'total_size': p.total_size,
            'status': p.status,
            'deployed_at': p.deployed_at.strftime('%Y-%m-%d %H:%M')
        })
    return jsonify(result)


@web_bp.route('/web/project/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    project = db.session.get(WebProject, project_id)
    if not project:
        return jsonify({'error': '项目不存在'}), 404

    if session.get('role') != 'admin' and project.uploader_id != session['user_id']:
        return jsonify({'error': '无权删除此项目'}), 403

    user = db.session.get(User, project.uploader_id)
    project_dir = safe_ext_dir(os.path.join(WEB_ROOT, user.username, project.folder_name))
    if project_dir.startswith(safe_ext_dir(os.path.join(WEB_ROOT, user.username))):
        shutil.rmtree(project_dir, ignore_errors=True)

    db.session.delete(project)
    db.session.commit()
    return jsonify({'success': True, 'message': '网页项目已删除'})


@web_bp.route('/web/project/<int:project_id>/preview')
@login_required
def preview_url(project_id):
    project = db.session.get(WebProject, project_id)
    if not project:
        return jsonify({'error': '项目不存在'}), 404

    if project.status != 'approved':
        if session.get('role') != 'admin' and project.uploader_id != session['user_id']:
            return jsonify({'error': '项目未审核通过'}), 403

    user = db.session.get(User, project.uploader_id)
    url = f'/web/{user.username}/{project.folder_name}/index.html'
    return jsonify({'url': url})


@web_bp.route('/web/project/<int:project_id>/review', methods=['POST'])
@admin_required
def review_project(project_id):
    action = request.form.get('action', '')
    project = db.session.get(WebProject, project_id)
    if not project:
        return jsonify({'error': '项目不存在'}), 404

    if action == 'approve':
        project.status = 'approved'
        db.session.commit()
        return jsonify({'success': True, 'message': '网页项目已审核通过', 'new_status': 'approved'})

    elif action == 'reject':
        project.status = 'rejected'
        db.session.commit()
        return jsonify({'success': True, 'message': '网页项目已拒绝', 'new_status': 'rejected'})

    return jsonify({'error': '无效操作'}), 400
