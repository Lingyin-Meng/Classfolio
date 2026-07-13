from flask import Blueprint, render_template, session, redirect, url_for
from models import db, User, FileRecord, WebProject
from utils.decorators import login_required

browse_bp = Blueprint('browse', __name__)


@browse_bp.route('/browse')
@login_required
def index():
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))

    # 获取所有已批准的学生
    students = User.query.filter_by(role='student', status='approved').order_by(User.username).all()

    # 为每个学生获取已通过的文件统计和最新图片作为封面
    student_cards = []
    for student in students:
        file_count = FileRecord.query.filter_by(uploader_id=student.id, status='approved').count()
        cover = FileRecord.query.filter_by(
            uploader_id=student.id, file_type='image', status='approved'
        ).order_by(FileRecord.created_at.desc()).first()

        if file_count > 0:
            student_cards.append({
                'id': student.id,
                'username': student.username,
                'file_count': file_count,
                'cover_id': cover.id if cover else None
            })

    # 获取所有已通过的网页项目
    web_projects = WebProject.query.filter_by(status='approved').order_by(
        WebProject.deployed_at.desc()
    ).all()

    return render_template('browse.html', student_cards=student_cards, web_projects=web_projects)


@browse_bp.route('/browse/<int:user_id>')
@login_required
def student_folder(user_id):
    if session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))

    student = db.session.get(User, user_id)
    if not student or student.role != 'admin' and student.status != 'approved':
        return '学生不存在', 404

    files = FileRecord.query.filter_by(uploader_id=user_id, status='approved').order_by(FileRecord.created_at.desc()).all()

    return render_template('student_folder.html', student=student, files=files)
