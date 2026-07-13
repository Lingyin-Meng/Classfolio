import os
from flask import Flask
from config import SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, UPLOAD_ROOT, WEB_ROOT
from models import db


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

    db.init_app(app)

    # 注册蓝图
    from routes.auth import auth_bp
    from routes.upload import upload_bp
    from routes.browse import browse_bp
    from routes.admin import admin_bp
    from routes.web import web_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(browse_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(web_bp)

    # 确保存储根目录存在
    os.makedirs(UPLOAD_ROOT, exist_ok=True)
    os.makedirs(WEB_ROOT, exist_ok=True)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    from config import HOST, PORT
    app = create_app()
    print(f'服务器启动: http://{HOST}:{PORT}')
    print(f'教师后台: http://{HOST}:{PORT}/admin/login')
    from waitress import serve
    serve(app, host=HOST, port=PORT)
