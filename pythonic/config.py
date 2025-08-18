

class Config:
    MAIL_SERVER = "smtp.yandex.com"
    MAIL_PORT = 465
    MAIL_USE_SSL = True   # Yandex requires SSL
    MAIL_USE_TLS = False
    MAIL_USERNAME = "zaouj2005@yandex.com"
    MAIL_PASSWORD = "nmspthtyhtgywyjd"

    SECRET_KEY = "5f4d8e3b2a1c9f7e6d5c4b3a2d1e0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b"
    SQLALCHEMY_DATABASE_URI = "sqlite:///monsite.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CKEDITOR_ENABLE_CODESNIPPET = True
    CKEDITOR_FILE_UPLOADER = "main.upload"