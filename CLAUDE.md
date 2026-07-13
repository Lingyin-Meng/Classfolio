# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

小学信息技术课堂局域网视频/照片上传与分享平台。教师机（Windows Server 2016）作为服务器运行 Flask 后端，学生通过浏览器访问教师机 IP 上传作品、浏览同学作品。教师有独立管理后台审核账号、管理文件。

## Commands

```bash
# 启动服务器（生产模式，waitress）
python app.py

# 创建/重置教师管理员账号
python create_admin.py

# 开发模式（Debug，不建议在生产环境使用）
flask run --host=0.0.0.0 --port=8080 --debug
```

Windows 下可直接双击 `start.bat` 一键安装依赖并启动。

## Architecture

```
B/S 架构，纯局域网

教师机 (Windows Server 2016)
├── Flask (waitress WSGI server) :8080
├── SQLite (data.db)
└── D:\ClassUploads\  ← 文件存储根目录
        ├── 张三\      ← 每学生一个文件夹
        └── 李四\

学生机 (浏览器)
└── http://教师机IP:8080 → 注册/登录/上传/浏览
```

## Key files

| File | Purpose |
|------|---------|
| `app.py` | Flask 应用入口，蓝图注册，waitress 启动 |
| `config.py` | 配置：上传路径、文件大小限制、允许格式 |
| `models.py` | SQLAlchemy 模型：User (含审核状态), FileRecord |
| `routes/auth.py` | 注册/登录/登出，bcrypt 密码，审核状态拦截 |
| `routes/upload.py` | 文件上传、我的文件列表、文件服务、删除 |
| `routes/browse.py` | 同学作品卡片视图、文件夹内部视图 |
| `routes/admin.py` | 教师登录、账号审核(通过/拒绝)、全局文件看板 |
| `utils/decorators.py` | `@login_required` 和 `@admin_required` 装饰器 |

## Database

- **User**: username (唯一), password_hash (bcrypt), role (student/admin), status (pending/approved/rejected)
- **FileRecord**: filename, stored_name (UUID), uploader_id → User, file_type (image/video), file_size

文件存储路径：`D:\ClassUploads\<学生姓名>\<uuid>.<ext>`，通过数据库记录关联而非直接路径访问，防止目录遍历。

## Security notes

- 密码 bcrypt 加密，Session 管理登录态
- 文件服务走 `send_file` + 数据库路径校验，`os.path.normpath` + `startswith` 防路径穿越
- 上传文件后缀 + MIME 白名单校验，拒绝可执行文件
- 学生只能删除自己的文件，教师可删任意文件
- 未审核账号无法登录
