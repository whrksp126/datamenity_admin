from celery.schedules import crontab
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = b'7\x9dp\x80\xe0s\xee\x00\x17C4\x9a\xeaX\x18\xac'

DATABASE_USER = 'datamenity_service'
DATABASE_PASSWORD = '6Ca2l3lCwjyHD3XgLvtG'
DATABASE_HOST = 'datamenity-v2-production.cluster-cekwmwtvw0qx.ap-northeast-2.rds.amazonaws.com'
DATABASE_PORT = '3306'
DATABASE_DB = 'datamenity'

CELERY_BROKER_URL='redis://52.79.51.173:6379',
CELERY_RESULT_BACKEND='redis://52.79.51.173:6379'

PAGE_SIZE = 10

# ADMIN PAGE
USE_ADMIN_SERVER = True
ADMIN_SERVER = 'http://52.79.51.173'

# Proxy (deprecated)
PROXY_SERVER = 'http://43.200.107.149'
proxies = { 
    'http':PROXY_SERVER,
    'https':PROXY_SERVER,
}
REQUESTS_PROXY = dict(proxies=proxies)
SELENIUM_PROXY = dict(proxy=proxies)

# celery beat
CELERY_TIMEZONE = 'Asia/Seoul'
CELERY_ENABLE_UTC = False

CELERYBEAT_SCHEDULE = {
    'add-works-every-hours': {
        'task':'tasks.enqueue_jobs',
        'schedule': crontab(minute='0', hour='*'),
        'args': ()
    }
}

# file upload to S3
AWS_ACCESS_KEY_ID = 'AKIAQM7ZLHBXEVUEXNO4'
AWS_SECRET_ACCESS_KEY = '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'
BUCKET_NAME = 'admin.bannerimg'
