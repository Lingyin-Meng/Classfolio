import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = os.environ.get('SECRET_KEY', 'classroom-video-platform-secret-key-change-me')

# 文件存储根目录
UPLOAD_ROOT = os.environ.get('UPLOAD_ROOT', r'D:\ClassUploads')

# 数据库
SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "data.db")}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 上传限制
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'webm', 'mov', 'avi'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov', 'avi'}

# 网页托管配置
WEB_ROOT = os.environ.get('WEB_ROOT', r'D:\ClassWebRoot')
MAX_ZIP_SIZE = 50 * 1024 * 1024  # 单个 ZIP 最大 50MB
MAX_TOTAL_WEB_SIZE = 50 * 1024 * 1024  # 单学生网页总大小 50MB
WEB_ALLOWED_MIMES = {
    '.html': 'text/html',
    '.htm': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.webp': 'image/webp',
    '.mp4': 'video/mp4',
    '.webm': 'video/webm',
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.json': 'application/json',
    '.txt': 'text/plain',
    '.md': 'text/plain',
}

# 服务器
HOST = '0.0.0.0'
PORT = 8080
