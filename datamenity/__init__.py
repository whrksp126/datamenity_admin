from flask import Flask, render_template, redirect, request
from werkzeug.urls import url_encode
from sqlalchemy.sql.functions import current_user
from flask_login import LoginManager
from celery import Celery
from datamenity.error_checker import check_error
from datamenity.api.roomtype import judge_roomtype
from datamenity.config import SECRET_KEY, USE_ADMIN_SERVER
#from datamenity.crawler import make_celery
import copy
import json
import random

from datamenity.factories.celery import configure_celery
from datamenity.factories.application import create_application

'''
def create_app():
    app = Flask(__name__)
    app.config.from_object('datamenity.config')
    return app
app = create_app()
'''

app = create_application()
app.secret_key = SECRET_KEY
login_manager = LoginManager()
login_manager.init_app(app)

celery = configure_celery(app)

if USE_ADMIN_SERVER:
    from datamenity.views.account import admin_account
    from datamenity.views.hotels import admin_hotels
    from datamenity.views.log import admin_log
    from datamenity.views.usergroup import admin_usergroup
    from datamenity.views.banner import admin_banner
    from datamenity.views.roomtype import admin_roomtype
    from datamenity.views.error_log import admin_error_log

    app.register_blueprint(admin_account)
    app.register_blueprint(admin_hotels)
    app.register_blueprint(admin_log)
    app.register_blueprint(admin_usergroup)
    app.register_blueprint(admin_banner)
    app.register_blueprint(admin_roomtype)
    app.register_blueprint(admin_error_log)

from datamenity.views.api import admin_api
app.register_blueprint(admin_api)


from datamenity.models import RoomPrice, User, session_scope, CrawlerRule, Hotel, LogCrawler, LogScheduler, Environment, Room, RoomTag, RoomTagHasRoom, UserHasCompetition
@login_manager.user_loader
def user_loader(user_id):
    with session_scope() as session:
        try:
            user = session.query(User).filter(User.id == user_id).first()
            session.close()
            return user
        except:
            return None


@app.login_manager.unauthorized_handler
def unauth_handler():
    return render_template('popup.html', msg='관리자 로그인이 필요합니다.', redirect='/')


@app.template_global()
def modify_query(**new_values):
    args = request.args.copy()

    for key, value in new_values.items():
        args[key] = value

    return '{}?{}'.format(request.path, url_encode(args))


from botocore.exceptions import ClientError
import boto3
from datamenity.common import get_crawler_price_works, get_crawler_review_works
from datamenity.crawler import crawler_handler, refresh_crawler_price, ota_code_to_str, get_proxy_environment
import traceback
import datetime
import time


@celery.task(queue='windows', default_retry_delay=30 * 60, max_retries=1)
def run_crawler_windows(crawler_type, hour, hotel_id, hotel_link, ota, rule):
    try:
        print('[run]', crawler_type, hour, hotel_id, hotel_link, ota, rule)
        crawler_handler(crawler_type, hour, hotel_id, hotel_link, ota, rule)
        print('[run complete]', crawler_type, hotel_id, ota, rule)
    except Exception as e:
        print(e)


@celery.task(queue='review', default_retry_delay=30 * 60, max_retries=1)
def run_crawler_review(crawler_type, hour, hotel_id, hotel_link, ota, rule):
    try:
        print('[run]', crawler_type, hour, hotel_id, hotel_link, ota, rule)
        crawler_handler(crawler_type, hour, hotel_id, hotel_link, ota, rule)
        print('[run complete]', crawler_type, hotel_id, ota, rule)
    except Exception as e:
        print(e)


@celery.task(queue='linux', default_retry_delay=30 * 60, max_retries=1)
def run_crawler(crawler_type, hour, hotel_id, hotel_link, ota, rule):
    try:
        print('[run]', crawler_type, hour, hotel_id, hotel_link, ota, rule)
        crawler_handler(crawler_type, hour, hotel_id, hotel_link, ota, rule)
        print('[run complete]', crawler_type, hotel_id, ota, rule)
    except Exception as e:
        print(e)


@celery.task(queue='rakuten', default_retry_delay=30 * 60, max_retries=1)
def run_crawler_rakuten(crawler_type, hour, hotel_id, hotel_link, ota, rule):
    try:
        print('[run]', crawler_type, hour, hotel_id, hotel_link, ota, rule)
        crawler_handler(crawler_type, hour, hotel_id, hotel_link, ota, rule)
        print('[run complete]', crawler_type, hotel_id, ota, rule)
    except Exception as e:
        print(e)
    

@celery.task(name='tasks.refresh_run_crawler', queue='refresh')
def refresh_run_crawler(hour, hotel_id, url, hid, ota, checkin):
    try:
        print('[run] hour:{}, hotel_id:{}, url:{}, hid:{}, ota:{}', hour, hotel_id, url, hid, ota)
        output = []
        errors = []
        refresh_crawler_price(output, errors, hour, hotel_id, url, hid, ota, checkin)
        print('[run complete] hotel_id:{}, ota:{}'.format(hotel_id, ota))
    except Exception as e:
        print(e)


@celery.task(name='tasks.celery_refresh_price', queue='refresh', default_retry_delay=30 * 60, max_retries=0)
def celery_refresh_price(user_id, booking_date, hour):
    # 현재 시간
    current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    print('[ENQUEUE START]', current_time.strftime('%Y-%m-%d %H:%M:%S'))

    output = []
    errors = []

    with session_scope() as session:
        # OTA 개수를 가져옴
        ota_len = len(ota_code_to_str)

        # 사용자 크롤링 OTA 조회
        user_item = session.query(User.hotel_id, User.otas, Hotel.link) \
            .join(Hotel, Hotel.id == User.hotel_id) \
            .filter(User.id == user_id).first()
        otas = user_item.otas

        # hotel_id 조회 (내호텔, 경쟁호텔)
        competitions = session.query(UserHasCompetition.competition_id, Hotel.link) \
            .join(Hotel, Hotel.id == UserHasCompetition.competition_id) \
            .filter(UserHasCompetition.user_id == user_id).all()
        hotels = [dict(hotel_id=user_item.hotel_id, link=user_item.link)]
        for competition in competitions:
            hotels.append(dict(hotel_id=competition.competition_id, link=competition.link))
        
        # 크롤러 작업 생성
        for ota in range(ota_len):
            if (otas & (1 << ota)) > 0:
                # 트립닷컴은 현재 linux 지원 안함
                if str(ota) == '8':
                    continue

                for hotel in hotels:
                    hotel_id = hotel['hotel_id']
                    try:
                        link = json.loads(hotel['link'])
                        link = link.get(str(ota), {})
                    except Exception:
                        link = {}
                    
                    url = link.get('url')
                    if not url:
                        continue
                    hid = link.get('hid')
                    if not hid:
                        continue
                        
                    # 크롤러 수행
                    refresh_run_crawler.delay(hour, hotel_id, url, hid, ota, booking_date)
        
        current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        print('[ENQUEUE END]', current_time.strftime('%Y-%m-%d %H:%M:%S'))


@celery.task(name='tasks.change_proxy', default_retry_delay=30 * 60, max_retries=0, queue='proxy_manager')
def change_proxy(proxy_no):
    ec2 = boto3.client('ec2', region_name="ap-northeast-2")

    curr = datetime.datetime.utcnow()
    if (curr.minute % 2) != int(proxy_no) - 1:
        return

    with session_scope() as session:
        env_item = session.query(Environment).filter(Environment.key == 'PROXY_{}'.format(proxy_no)).first()
        
        try:
            env_value = json.loads(env_item.value)
        except Exception:
            env_value = None

        # 프록시 서버 정보 없다면 에러 발생
        if env_value is None or 'instance_id' not in env_value or env_value['instance_id'] is None:
            raise Exception('프록시 서버를 Environment에 지정해주세요')

        # 이미 할당된 정보가 있다면 릴리스
        if env_value.get('alloc_id') is not None:
            resp = ec2.release_address(AllocationId=env_value['alloc_id'])
            env_value['ip'] = None
            env_value['alloc_id'] = None
            env_item.value = json.dumps(env_value)
            session.commit()

        # Elastic IP 할당
        allocation = ec2.allocate_address(Domain='vpc')
        if allocation['ResponseMetadata']['HTTPStatusCode'] == 200:
            # 할당 적용 (env 에 적용)
            response = ec2.associate_address(AllocationId=allocation['AllocationId'], InstanceId=env_value['instance_id'])
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                # 할당 정보 저장
                env_item.value = json.dumps(dict(alloc_id=allocation['AllocationId'], ip=allocation['PublicIp'], instance_id=env_value['instance_id']))
                print('Proxy : {}, ip : {}'.format(proxy_no, allocation['PublicIp']))
                session.commit()
            else:
                # 에러 발생시 IP 릴리즈
                ec2.release_address(AllocationId=allocation['AllocationId'])


@celery.task(name='tasks.enqueue_jobs', default_retry_delay=30 * 60, max_retries=0, queue='job_manager')
def enqueue_jobs():
    '''
    # 프록시 정보 변경
    ec2 = boto3.client('ec2', region_name="ap-northeast-2")
    while True:
        try:
            with session_scope() as session:
                env_item = session.query(Environment).filter(Environment.key == 'PROXY').first()

                # 이미 할당된 정보가 있다면 릴리스
                if env_item is not None:
                    env_value = json.loads(env_item.value)
                    if env_value.get('alloc_id') is not None:
                        resp = ec2.release_address(AllocationId=env_value['alloc_id'])
                        if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
                            continue
                        env_value['ip'] = None
                        env_value['alloc_id'] = None
                        env_item.value = json.dumps(env_value)
                else:
                    env_value = dict(alloc_id=None, ip=None, instance_id='i-02e81f336a46a39ba')
                    session.add(Environment('PROXY', json.dumps(env_value)))
                session.commit()

                # 프록시 서버 정보 없다면 에러 발생
                if 'instance_id' not in env_value and env_value['instance_id'] is None:
                    raise Exception('프록시 서버를 Environment에 지정해주세요')

                # Elastic IP 할당
                allocation = ec2.allocate_address(Domain='vpc')
                if allocation['ResponseMetadata']['HTTPStatusCode'] == 200:
                    # 할당 적용 (env 에 적용)
                    response = ec2.associate_address(AllocationId=allocation['AllocationId'], InstanceId=env_value['instance_id'])
                    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                        # 할당 정보 저장
                        env_item.value = json.dumps(dict(alloc_id=allocation['AllocationId'], ip=allocation['PublicIp'], instance_id=env_value['instance_id']))
                        session.commit()
                    else:
                        # 에러 발생시 IP 릴리즈
                        ec2.release_address(AllocationId=allocation['AllocationId'])
                        continue
            
            break
        except Exception as e:
            # TODO ERROR 메시지 발송
            print(e)
            time.sleep(30)
    '''

    # 현재 시간
    current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    print('[ENQUEUE START]', current_time.strftime('%Y-%m-%d %H:%M:%S'))

    # 크롤러 로그 초기화 (현재시간 기준 로그)
    with session_scope() as session:
        session.query(LogCrawler).filter(LogCrawler.crawler_type.in_(['price', 'review']), LogCrawler.hour == current_time.hour).delete()

    # celery 큐 초기화
    # celery.control.purge()

    # 수행해야할 가격 크롤링 작업 목록을 가져옵니다
    price_works = get_crawler_price_works(current_time.hour)
    review_works = get_crawler_review_works(current_time.hour)
    random.shuffle(price_works)
    random.shuffle(review_works)

    # 스케쥴러 로그 작성 (전체 작업 개수 업데이트)
    with session_scope() as session:
        log_scheduler_price = session.query(LogScheduler).filter(LogScheduler.crawler_type == 'price', LogScheduler.hour == current_time.hour).first()
        if not log_scheduler_price:
            log_scheduler_price = LogScheduler('price', current_time.hour, len(price_works))
            session.add(log_scheduler_price)
        else:
            log_scheduler_price.works_count = len(price_works)
            log_scheduler_price.created_at = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
            log_scheduler_price.updated_at = None

        log_scheduler_review = session.query(LogScheduler).filter(LogScheduler.crawler_type == 'review', LogScheduler.hour == current_time.hour).first()
        if not log_scheduler_review:
            log_scheduler_review = LogScheduler('review', current_time.hour, len(review_works))
            session.add(log_scheduler_review)
        else:
            log_scheduler_review.works_count = len(review_works)
            log_scheduler_review.created_at = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
            log_scheduler_review.updated_at = None
        session.commit()

    # celery 작업 추가 (가격 작업)
    for w in price_works:
        if str(w['ota']) == '8':
            #run_crawler_windows.delay('price', current_time.hour, w['id'], w['link'], w['ota'], w['rule'])
            pass
        elif str(w['ota']) == '12':
            run_crawler_rakuten.delay('price', current_time.hour, w['id'], w['link'], w['ota'], w['rule'])
        else:
            run_crawler.delay('price', current_time.hour, w['id'], w['link'], w['ota'], w['rule'])
        #print('price', w['id'], w['link'], w['ota'], w['rule'])

    # celery 작업 추가 (리뷰 작업)
    for w in review_works:
        run_crawler_review.delay('review', current_time.hour, w['id'], w['link'], w['ota'], None)
        #print('review', w['id'], w['link'], w['ota'])
    
    current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    print('[ENQUEUE END]', current_time.strftime('%Y-%m-%d %H:%M:%S'))

    # 지금으로 부터 1시간 전 크롤링에 대한 체크를 수행함
    prev_time = current_time - datetime.timedelta(hours=1)
    prev_time.replace(minute=0, second=0, microsecond=0)
    year, month, day, hour = prev_time.year, prev_time.month, prev_time.day, prev_time.hour
    check_error(year, month, day, hour)


def arrange_room_tag(started_at, ended_at):
    output = []

    with session_scope() as session:
        # setting 가져옴
        env_item = session.query(Environment).filter(Environment.key == 'ROOMTYPE_RULE').first()
        if env_item is not None:
            setting = json.loads(env_item.value)
        
        # 기간내 room 데이터를 조회
        room_items = session.query(Room.hotel_id, Room.name, Room.id, Hotel.roomtype_setting).join(Hotel, Hotel.id == Room.hotel_id).filter(Room.created_at >= started_at, Room.created_at < ended_at).all()
        cnt = 0
        max_cnt = len(room_items)
        for room_item in room_items:
            cnt += 1
            print('## Progress : {} / {}'.format(cnt, max_cnt))
            hotel_id = room_item.hotel_id
            room_name = room_item.name
            if room_item.roomtype_setting is not None:
                hotel_setting = json.loads(room_item.roomtype_setting)
            else:
                hotel_setting = setting

            try:
                # 룸타입을 판단함
                roomtype_item = judge_roomtype(output, hotel_id, room_name, hotel_setting)
                if roomtype_item is not None:
                    roomtype_name = roomtype_item['result']
                    room_id = room_item.id

                    # RoomTag 정보를 확인함
                    roomtag_item = session.query(RoomTag).filter(RoomTag.hotel_id == hotel_id, RoomTag.name == roomtype_name).first()

                    # RoomTag 정보가 조회될 때, 객실을 RoomTag 에 추가함
                    if roomtag_item is not None:
                        room_tag_id = roomtag_item.id
                        search_room_tag_has_room = session.query(RoomTagHasRoom).filter(RoomTagHasRoom.room_tag_id == room_tag_id, RoomTagHasRoom.room_id == room_id).first()
                        if not search_room_tag_has_room:
                            session.add(RoomTagHasRoom(room_tag_id, room_id))
                            session.commit()
            except Exception:
                print(traceback.print_exc())
                session.rollback()


@celery.task(name='tasks.arrange_room_tag', queue='batch')
def celery_arrange_room_tag():
    kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    today = kst_now.replace(second=0, minute=0, hour=0, microsecond=0)
    yesterday = today - datetime.timedelta(days=1)
    arrange_room_tag(today, yesterday)
