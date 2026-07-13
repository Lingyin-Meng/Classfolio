from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='student')   # 'student' / 'admin'
    status = db.Column(db.String(10), nullable=False, default='pending') # 'pending' / 'approved' / 'rejected'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    files = db.relationship('FileRecord', backref='uploader', lazy=True, cascade='all, delete-orphan')


class FileRecord(db.Model):
    __tablename__ = 'file_records'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)          # 原始文件名
    stored_name = db.Column(db.String(255), nullable=False)       # 存储用的唯一文件名
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)              # 字节
    file_type = db.Column(db.String(50), nullable=False)           # 'image' / 'video'
    mime_type = db.Column(db.String(100))
    status = db.Column(db.String(10), nullable=False, default='pending')  # 'pending' / 'approved' / 'rejected'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class WebProject(db.Model):
    __tablename__ = 'web_projects'

    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)           # 项目名称（解压后的文件夹名）
    folder_name = db.Column(db.String(100), nullable=False)            # 存储用的唯一文件夹名
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_size = db.Column(db.Integer, nullable=False, default=0)     # 解压后总大小（字节）
    status = db.Column(db.String(10), nullable=False, default='pending')  # 'pending' / 'approved' / 'rejected'
    deployed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    uploader = db.relationship('User', backref='web_projects', lazy=True)
