import os

__all__ = [
    "site_settings",
    "database_settings"
]

BASE_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates/').replace('\\', '/')
STATIC_DIR = os.path.join(BASE_DIR, 'static/').replace('\\', '/')
LOCALE_DIR = os.path.join(BASE_DIR, 'locale/').replace('\\', '/')
IMAGE_DIR = os.path.join(STATIC_DIR, 'img/').replace('\\', '/')

ACCESS_HOST = "http://yuepai01-1251817761.file.myqcloud.com/"
BUCKET_NAME = "yuepai01"


site_settings = {
    "debug": False,
    "cookie_secret": "d13a4dbd47f042ccb47169a2fdd5e789",
    "xsrf_cookies": False,
    "login_url": "/login",
    "autoescape": None,
    "port": 8000,
    "base_path": BASE_DIR,
    "template_path": TEMPLATE_DIR,
    "static_path": STATIC_DIR,
    "locale_path": LOCALE_DIR,
    "image_path": IMAGE_DIR,
    "image_dir": "/static/img/",
    "locale_domain": "wtforms",
    "salt_length": 12,
    "image_font": STATIC_DIR + "/font/PTM55FT.ttf"
}


mail_settings = {
    "host": 'smtp.163.com',
    "port": 25,
    "email": 'youpaihust@163.com',
    "password": 'youpai666'
}


cdn_settings = {
    "cos_host": "http://gz.file.myqcloud.com/files/v2/1251817761/",
    "access_host": ACCESS_HOST,
    "appid": "1251817761",
    "bucket": BUCKET_NAME,
    "image_host": ACCESS_HOST + r'image/',
    "secretid": "AKIDprkeWDWGTeabcWfxSjkfKn57xXrvZFbh",
    "secretkey": "2oNs77ud7nSsHRPTI0SgfjgTEo8C0lKe",
}


database_settings = {
    "default": "mysql+pymysql://root:452323tmh@127.0.0.1/test?charset=utf8",
    "sqlite": "sqlite:///database.db",
}

redis_settings = {
    'host': 'localhost',
    'port': 6379,
}
