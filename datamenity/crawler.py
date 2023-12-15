from datamenity.models import Environment, User, UserHasCompetition, UserHasCrawlerRule, session_scope, Room, Hotel, RoomTag, RoomTagHasRoom, RoomPrice, RoomPriceCurrent, CrawlerRule, Hotel, LogScheduler, LogCrawler, OTAType
from datamenity.ota.OTAGoodchoice import OTAGoodchoice
from datamenity.ota.OTABooking import OTABooking
from datamenity.ota.OTAExpedia import OTAExpedia
from datamenity.ota.OTAAgoda import OTAAgoda
from datamenity.ota.OTAInterpark import OTAInterpark
from datamenity.ota.OTAYanolja import OTAYanolja
from datamenity.ota.OTADaily import OTADaily
from datamenity.ota.OTAHotels import OTAHotels
from datamenity.ota.OTATrip import OTATrip
from datamenity.ota.OTAWings import OTAWings
from datamenity.ota.OTAKensington import OTAKensington
from datamenity.ota.OTAIkyu import OTAIkyu
from datamenity.ota.OTARakuten import OTARakuten
from datamenity.ota.OTAJalan import OTAJalan

from selenium import webdriver
import undetected_chromedriver.v2 as uc
from pyvirtualdisplay import Display

from datamenity.config import SELENIUM_PROXY, PROXY_SERVER, REQUESTS_PROXY, BASE_DIR, ADMIN_SERVER
from datetime import datetime, timedelta
from _operator import itemgetter
import traceback
import boto3
import time
import random
import requests
import json
import uuid

from datamenity.factories.celery import configure_celery
from datamenity.factories.application import create_application
from celery import current_task


ota_code_to_obj = [OTAGoodchoice(), OTABooking(), OTAExpedia(), OTAAgoda(), OTAInterpark(), OTAYanolja(), OTADaily(), OTAHotels(), OTATrip(), OTAWings(), OTAKensington(), OTAIkyu(), OTARakuten(), OTAJalan()]
ota_code_to_type = [OTAType.GOODCHOICE, OTAType.BOOKING, OTAType.EXPEDIA, OTAType.AGODA, OTAType.INTERPARK, OTAType.YANOLJA, OTAType.DAILY, OTAType.HOTELS, OTAType.TRIP, OTAType.WINGS, OTAType.KENSINGTON, OTAType.IKYU, OTAType.RAKUTEN, OTAType.JALAN]
ota_code_to_label = ['여기어때', '부킹닷컴', '익스피디아', '아고다', '인터파크', '야놀자', '데일리호텔', '호텔스닷컴', '트립닷컴', '윙스부킹', '켄싱턴호텔', 'Ikyu (일본)', 'Rakuten (일본)', 'Jalan (일본)']
ota_code_to_str = ['goodchoice', 'booking', 'expedia', 'agoda', 'interpark', 'yanolja', 'daily', 'hotels', 'trip', 'wings', 'kensington', 'ikyu', 'rakuten', 'jalan']
ota_str_to_code = {
    'goodchoice': 0, 
    'booking': 1, 
    'expedia': 2, 
    'expeida': 2, 
    'agoda': 3, 
    'interpark': 4, 
    'yanolja': 5, 
    'daily': 6, 
    'hotels': 7, 
    'trip': 8, 
    'wings': 9,
    'kensington': 10,
    'ikyu': 11,
    'rakuten': 12,
    'jalan': 13,
}

crawler_args = None

celery = configure_celery(create_application())
'''
def make_celery():
    celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    return celery
'''


def json_default(value):
    if isinstance(value, datetime.date):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError('not JSON serializable')


# XXX : 제거해야함, DynamoDB 에 기록하기
def put_price_info_in_dynamodb(item):
    url = 'https://oh24g56ytv2edkwcpla2onlqoq0lkbkv.lambda-url.ap-northeast-2.on.aws/'
    headers = {'Content-type': 'application/json'}
    payload = {'item': item}
    resp = requests.post(url, json=payload, headers=headers).text

# XXX : 제거해야함, DynamoDB 에 기록하기
def put_refresh_price_info_in_dynamodb(item):
    url = 'https://inswz4mx6ka3c4gs2btm4b6xey0aviji.lambda-url.ap-northeast-2.on.aws/'
    headers = {'Content-type': 'application/json'}
    payload = {'item': item}
    resp = requests.post(url, json=payload, headers=headers).text


def insert_review_in_mysql(data):
    url = 'https://y3umcvint552myvdolm6ial3ie0emhow.lambda-url.ap-northeast-2.on.aws/'
    headers = {'Content-type': 'application/json'}
    payload = {'data': data}
    resp = requests.post(url, data=json.dumps(payload, default=str), headers=headers).json()
    if resp['code'] != 200:
        print('#### ERROR !')


def insert_price_in_mysql(hotel_id, ota, booking_date, rooms):
    url = 'https://g7ozktctiu7boftkoit6nbpwcu0aqvfq.lambda-url.ap-northeast-2.on.aws/'
    headers = {'Content-type': 'application/json'}
    payload = {
        'data': {
            'hotel_id': hotel_id,
            'ota': ota,
            'booking_date': booking_date,
            'rooms': rooms
        }
    }
    resp = requests.post(url, data=json.dumps(payload, default=str), headers=headers).json()
    '''
    print(resp)
    if resp['code'] != 200:
        print('#### ERROR !')
    '''


def insert_bulk_price_in_mysql(hotel_id, ota, data):
    url = 'https://7y4tl2k7wvgjz3fecg3boc3lp40xrowd.lambda-url.ap-northeast-2.on.aws/'
    headers = {'Content-type': 'application/json'}
    payload = {
        'data': {
            'hotel_id': hotel_id,
            'ota': ota,
            'data': data,
        }
    }
    resp = requests.post(url, data=json.dumps(payload, default=str), headers=headers).json()
    print(resp)
    if resp['code'] != 200:
        print('#### ERROR !')


def get_proxy_environment(proxy_no=0):
    try:
        proxy_id = uuid.UUID(current_task.request.id).int
    except Exception:
        proxy_id = proxy_no
    url = 'https://jdwmhbsegygrpq75t6u6zrd5am0tnpyf.lambda-url.ap-northeast-2.on.aws/'
    headers = {'Content-type': 'application/json'}
    payload = {
        'data': {
            'type': 'get',
            'proxy_id': proxy_id
        }
    }
    resp = requests.post(url, data=json.dumps(payload, default=str), headers=headers).json()

    # 결과
    value_proxy_server = 'http://{}'.format(resp['ip'])
    value_proxies = {
        'http':value_proxy_server,
        'https':value_proxy_server,
    }

    proxy_params = dict(
        PROXY_SERVER=value_proxy_server,
        proxies=value_proxies,
        REQUESTS_PROXY=dict(proxies=value_proxies, timeout=20),
        SELENIUM_PROXY=dict(proxy=value_proxies),
        alloc_id=resp['alloc_id'],
        instance_id=resp['instance_id'],
        ip=resp['ip']
    )

    return proxy_params


'''
def set_proxy_environment(data):
    url = 'https://jdwmhbsegygrpq75t6u6zrd5am0tnpyf.lambda-url.ap-northeast-2.on.aws/'
    headers = {'Content-type': 'application/json'}
    payload = {
        'data': {
            'type': 'set',
            'data': data
        }
    }
    resp = requests.post(url, data=json.dumps(payload, default=str), headers=headers).json()
    if resp['code'] != 200:
        print('#### ERROR !')
'''


def write_price_data(output, errors, now, hotel_id, ota, room_name, booking_date, rent_price, stay_price, rent_remain, stay_remain):
    resp = requests.post('http://127.0.0.1/api/room/price/set', json=dict(
        hotel_id=hotel_id, 
        ota=ota, 
        room_name=room_name, 
        booking_date=booking_date.strftime('%Y-%m-%d'), 
        rent_price=rent_price, 
        stay_price=stay_price, 
        rent_remain=rent_remain, 
        stay_remain=stay_remain
    )).json()


def print_log(output, msg, is_display=True):
    if is_display:
        print('{}'.format(msg))
    output.append('{}'.format(msg))


def init_crawler_args():
    global crawler_args

    if crawler_args is None:
        crawler_args = dict()
    
    return crawler_args


# 데이터 새로고침 가격 크롤링 함수
def refresh_crawler_price(output, errors, hour, hotel_id, url, hid, ota, checkin):
    now = datetime.utcnow() + timedelta(hours=9)
    if now.hour != hour:
        return

    crawler_args = init_crawler_args()
    crawler_args['proxy'] = wrap_get_proxy_environment(ota)

    ota_obj = ota_code_to_obj[ota]
    ota_obj.scrape_prices_preprocess(crawler_args, url, hid, now.strftime('%Y-%m-%d'), (now + timedelta(days=1)).strftime('%Y-%m-%d'))

    price_data = []

    # 체크인, 체크아웃 값 초기화
    checkin = datetime.strptime(checkin, '%Y-%m-%d')
    checkout = checkin + timedelta(days=1)
    
    try:
        # 스캔
        print_log(output, '## 스캔일자 : {} (ota : {})'.format(checkin.strftime('%Y-%m-%d'), ota))
        
        try:
            result = ota_obj.scrape_prices(output, crawler_args, url, hid, checkin.strftime('%Y-%m-%d'), checkout.strftime('%Y-%m-%d'))
            print('## ota : {}, result : {}'.format(ota, result))
        except Exception:
            print_log(errors, '[ERROR] 스캔일자 : {}'.format(checkin.strftime('%Y-%m-%d')))
            print_log(errors, traceback.print_exc(), False)
            return
        
        rooms = []
        for room in result['rooms']:
            if room['price'] < 3000:
                continue
            if any(p in room['name'] for p in ['숙박불가', '6시간', '7시간', '8시간', '9시간', '10시간', '머무ROOM']):
                continue
            rooms.append(room)

        # 가격 정보 기록 (Mysql)
        price_data.append(dict(booking_date=checkin.strftime('%Y-%m-%d'), rooms=rooms, code=result['code']))
        
    except Exception:
        print_log(errors, traceback.print_exc())
    
    try:
        insert_bulk_price_in_mysql(hotel_id, ota, price_data)
    except Exception:
        print_log(errors, traceback.print_exc())

    if 'driver' in crawler_args and crawler_args['driver'] is not None:
        crawler_args['driver'].quit()


def advanced_sleep(sleep_seconds, spend_seconds):
    remain_seconds = sleep_seconds - spend_seconds

    if remain_seconds > 0:
        time.sleep(remain_seconds)


def wrap_get_proxy_environment(ota_type):
    return get_proxy_environment()


# 가격 크롤링 함수
def crawler_price(output, errors, hour, hotel_id, url, hid, ota, rule):
    try:
        proxy_id = uuid.UUID(current_task.request.id).int % 4
    except Exception:
        proxy_id = 0
    
    now = datetime.utcnow() + timedelta(hours=9)
    '''
    # 시간이 넘을 경우 처리하지 않는 로직
    if now.hour != hour:
        return
    '''
    continuous_empty_day = 0

    crawler_args = init_crawler_args()

    ota_obj = ota_code_to_obj[ota]

    need_preprocess = True
    price_data = []
    
    start_after_day = 0
    for r in rule:
        end_after_day = r['range']
        time_flag = r['time'] | 1                       # (1 << 0) 0시에는 모두 동작

        for d in range(start_after_day, end_after_day):
            try:
                # 스캔 정책 확인 (스캔 시간 아닐 경우 반복 종료)
                if (time_flag & (1 << hour)) == 0:
                    break
                
                # 체크인, 체크아웃 날짜 지정
                checkin = (now + timedelta(days=d)).replace(second=0, minute=0, hour=0, microsecond=0)
                checkout = checkin + timedelta(days=1)

                # 스캔
                print_log(output, '## 스캔일자 : {} (ota : {}, {}시)'.format(checkin.strftime('%Y-%m-%d'), ota, hour))
                
                error_cnt = 0
                for try_cnt in range(9):
                    try:
                        # 전처리 필요시 동작
                        if need_preprocess:
                            try:
                                # 이전 전처리 자원 해제
                                if 'driver' in crawler_args and crawler_args['driver'] is not None:
                                    crawler_args['driver'].quit()

                                # 프록시 설정 값 업데이트
                                crawler_args['proxy'] = wrap_get_proxy_environment(ota)

                                # 전처리 과정 수행
                                started_at = datetime.utcnow()
                                resp = ota_obj.scrape_prices_preprocess(crawler_args, url, hid, now.strftime('%Y-%m-%d'), (now + timedelta(days=1)).strftime('%Y-%m-%d'))
                                ended_at = datetime.utcnow()
                                total_seconds = (ended_at - started_at).total_seconds()

                                # 전처리 성공시 빠져나옴
                                if resp is None or resp.get('code', 200) == 200:
                                    need_preprocess = False
                                elif resp is None or resp.get('code', 200) != 403:
                                    error_cnt += 1
                                    if error_cnt >= 3:
                                        print('전처리 에러 [proxy : {} / url : {}] - (OTA : {} / try : {}) : resp : {}'.format(proxy_id, url, ota, try_cnt, resp))
                                        break
                                    continue
                                else:
                                    print('전처리 403 에러 발생 [proxy : {} / url : {}] - (OTA : {} / try : {})'.format(proxy_id, url, ota, try_cnt))

                                    # 프록시 변경 (대기)
                                    advanced_sleep(10, total_seconds)
                                    continue

                            except Exception:
                                error_cnt += 1
                                if error_cnt >= 3:
                                    break
                                continue
                        
                        if error_cnt >= 3:
                            need_preprocess = True
                            break
                        
                        # 가격 가져옴
                        result = ota_obj.scrape_prices(output, crawler_args, url, hid, checkin.strftime('%Y-%m-%d'), checkout.strftime('%Y-%m-%d'))

                        # 접속 거부당한게 아니라면 다음으로 진행
                        if result['code'] != 403:
                            break
                            
                        print('403 에러 발생 (proxy:{} / url:{}) - (OTA : {} / try : {})'.format(proxy_id, url, ota, try_cnt))

                        # 프록시 변경 (대기)
                        advanced_sleep(10, total_seconds)

                        # 전처리 과정 필요 설정 (아예 프록시 정보가 바뀌었기 때문에)
                        need_preprocess = True

                    except Exception:
                        need_preprocess = False
                        error_cnt += 1
                        if error_cnt >= 3:
                            print_log(errors, '[ERROR] 스캔일자 : {} (proxy: {} / url : {})'.format(checkin.strftime('%Y-%m-%d'), proxy_id, url))
                            print_log(errors, traceback.print_exc(), False)
                            break
                
                rooms = []
                for room in result['rooms']:
                    if room['price'] < 3000:
                        continue
                    if any(p in room['name'] for p in ['숙박불가', '6시간', '7시간', '8시간', '9시간', '10시간', '머무ROOM']):
                        continue
                    rooms.append(room)

                if len(rooms) > 0:
                    continuous_empty_day = 0
                else:
                    continuous_empty_day += 1

                # 가격 정보 기록 (Mysql)
                price_data.append(dict(booking_date=checkin.strftime('%Y-%m-%d'), rooms=rooms, code=result['code']))
                
            except Exception:
                print_log(errors, '[ERROR] url 반영 실패 : {} (proxy:{} / url:{})'.format(checkin.strftime('%Y-%m-%d'), proxy_id, url))
                print_log(errors, traceback.print_exc())
                continuous_empty_day += 1
            
            if continuous_empty_day >= 20:
                break

        start_after_day = end_after_day
    
    try:
        insert_bulk_price_in_mysql(hotel_id, ota, price_data)
    except Exception:
        print_log(errors, traceback.print_exc())

    if 'driver' in crawler_args and crawler_args['driver'] is not None:
        crawler_args['driver'].quit()


def crawler_review(output, hour, hotel_id, url, hid, ota):
    try:
        proxy_id = uuid.UUID(current_task.request.id).int % 4
    except Exception:
        proxy_id = 0

    crawler_args = init_crawler_args()
    need_preprocess = True

    ota_obj = ota_code_to_obj[ota]
    kst_now = datetime.utcnow() + timedelta(hours=9)

    # TODO : 스캔 정책 확인 (하루 중 특정 시간에만 확인 할 경우)

    print_log(output, '## 리뷰 스캔 호텔 : {}, OTA : {} ({})'.format(hotel_id, ota, url))
    total_comments = []
    score = None
    count = None
    for page in range(1, 20):
        error_cnt = 0
        for try_cnt in range(9):
            # 전처리 필요시 동작
            if need_preprocess:
                try:
                    # 이전 전처리 자원 해제
                    if 'driver' in crawler_args and crawler_args['driver'] is not None:
                        crawler_args['driver'].quit()

                    # 프록시 설정 값 업데이트
                    crawler_args['proxy'] = wrap_get_proxy_environment(ota)

                    # 전처리 과정 수행
                    started_at = datetime.utcnow()
                    resp = ota_obj.scrape_prices_preprocess(crawler_args, url, hid, kst_now.strftime('%Y-%m-%d'), (kst_now + timedelta(days=1)).strftime('%Y-%m-%d'))
                    ended_at = datetime.utcnow()
                    total_seconds = (ended_at - started_at).total_seconds()

                    # 전처리 성공시 빠져나옴
                    if resp is None or resp.get('code', 200) == 200:
                        need_preprocess = False
                    elif resp is None or resp.get('code', 200) != 403:
                        error_cnt += 1
                        if error_cnt >= 3:
                            print('전처리 에러 [proxy : {} / url : {}] - (OTA : {} / try : {}) : resp : {}'.format(proxy_id, url, ota, try_cnt, resp))
                            break
                        continue
                    else:
                        print('전처리 403 에러 발생 [proxy : {} / url : {}] - (OTA : {} / try : {})'.format(proxy_id, url, ota, try_cnt))

                        # 프록시 변경 (대기)
                        advanced_sleep(10, total_seconds)
                        continue

                except Exception:
                    error_cnt += 1
                    if error_cnt >= 3:
                        break
                    continue
            
            result = ota_obj.scrape_reviews(output, crawler_args, url, hid, page)

            # 접속 거부당한게 아니라면 다음으로 진행
            if result['code'] != 403:
                break
            
            # 프록시 변경 (대기)
            time.sleep(10)

            # 프록시 설정 값 업데이트
            crawler_args['proxy'] = wrap_get_proxy_environment(ota)
        
        # 응답 결과가 정상이 아니라면 다음으로 건너뜀
        if result['code'] != 200:
            continue

        comments = result.get('comments', [])
        # DB에 기록
        print('@@ page : {}, hotel_id : {}, ota : {}'.format(page, hotel_id, ota))
        insert_review_in_mysql(dict(
            comments=comments,
            score=None,
            count=None,
            hotel_id=hotel_id,
            ota=ota,
            now=kst_now.strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        if len(comments) == 0:
            break

        total_comments = total_comments + comments
        score_tmp = result.get('score')
        if score_tmp is not None:
            score = score_tmp
        count_tmp = result.get('count')
        if count_tmp is not None:
            count = count_tmp
    
    # 리뷰 평점, 개수 없을 경우 예외처리
    if count is None:
        count = len(total_comments)
    if count > 0:
        if score is None:
            score = sum(c.get('score', 0) for c in total_comments) / count
    else:
        score = 0

    # DB에 기록
    print('@@ hotel_id : {}, ota : {}, score : {}, count : {}'.format(hotel_id, ota, score, count))
    insert_review_in_mysql(dict(
        comments=[],
        score=score,
        count=count,
        hotel_id=hotel_id,
        ota=ota,
        now=kst_now.strftime('%Y-%m-%d %H:%M:%S')
    ))
    print_log(output, '## 평점 : {}, 개수 : {}'.format(score, count))


def crawler_handler(crawler_type, hour, hotel_id, hotel_link, ota, rule):
    try:
        # 디버깅용 로그 데이터, 에러 로그는 traceback 으로 기록
        output = []
        errors = []

        # URL 을 가져옵니다
        url = hotel_link.get('url')
        print('url : ', url)
        if not url:
            return None

        # hid 를 추출합니다 (hid : OTA의 호텔 ID)
        hid = hotel_link.get('hid')
        print('hid : ', hid)
        if not hid:
            return None

        # 각 크롤러 모듈을 수행함
        if crawler_type == 'price':
            crawler_price(output, errors, hour, hotel_id, url, hid, ota, rule)

        elif crawler_type == 'review':
            crawler_review(output, hour, hotel_id, url, hid, ota)
        
    except Exception:
        print_log(errors, '[ERROR] hour:{}, hotel_id:{}, link:{}, ota:{}, rule:{}'.format(hour, hotel_id, hotel_link, ota_code_to_str[ota], rule), True)
        print_log(errors, traceback.format_exc(), True)
