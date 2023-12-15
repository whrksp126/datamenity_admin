from datamenity.models import User, session_scope, CrawlerRule, Hotel, OTAType, Environment
import boto3
import json
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
#from threading import Thread
import multiprocessing as mp


ota_code_to_str = ['goodchoice', 'booking', 'expedia', 'agoda', 'interpark', 'yanolja', 'daily', 'hotels', 'trip', 'wings', 'kensington']
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
    'kensington': 10
}

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id='AKIAQM7ZLHBXEVUEXNO4',
    aws_secret_access_key='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',
    region_name='ap-northeast-2'
)
dynamo_crawling_target = dynamodb.Table('crawling_target')
dynamo_subscriber = dynamodb.Table('subscriber')
dynamo_priceinfo = dynamodb.Table('PriceInfo')
dynamo_reviewinfo = dynamodb.Table('ReviewInfo')
dynamo_review = dynamodb.Table('Review')

day_of_weeks = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

running = mp.Value('i', 0)
mutex = None
def initializer(semaphore):
    global mutex
    mutex = semaphore


def get_name(target):
    try:
        target_name = target['yanolja_name']
    except:
        try:
            target_name = target['goodchoice_name']
        except:
            try:
                target_name = target['booking_name']
            except:
                try:
                    target_name = target['agoda_name']
                except:
                    try:
                        target_name = target['hotels_name']
                    except:
                        try:
                            target_name = target['expedia_name']
                        except:
                            try:
                                target_name = target['interpark_name']
                            except:
                                target_name = target['kensington_name']
    return target_name

def get_hotel_list(no, keyword):
    f = open('report/{}. {}호텔리스트.csv'.format(no, keyword), mode='w', encoding='utf-8')

    columns = ['hotel_name', 'address', 'city', 'region', 'otas']
    f.write(u'\ufeff')
    f.write(','.join(columns) + '\n')
    with session_scope() as session:
        hotels = session.query(Hotel).filter(Hotel.addr.like('%{}%'.format(keyword))).all()
        for h in hotels:
            addr_splits = h.addr.split(' ')
            otas = []
            for i in range(len(ota_code_to_str)):
                if (h.otas & (1 << i)):
                    otas.append(ota_code_to_str[i])

            record = [h.name, h.addr, addr_splits[0], addr_splits[1], '/'.join(otas)]
            print(record)
            f.write(','.join(record) + '\n')
    f.close()


def daily_prices_thread(args):
    no, keyword, sep, hotel_id, hotel_name, ota_str, address, started_at, ended_at = args
    print('START', hotel_id, hotel_name, ota_str, address, started_at, ended_at)
    result_str = ''
    addr_splits = address.split(' ')
    
    scanned_date = started_at
    while scanned_date < ended_at:
        scanned_date_str = scanned_date.strftime('%Y%m%d')
        scanned_date_str_f = scanned_date.strftime('%Y-%m-%d')

        for d in range(90):
            booking_date = scanned_date + timedelta(days=d)
            booking_date_str = booking_date.strftime('%Y%m%d')
            booking_date_str_f = booking_date.strftime('%Y-%m-%d')
            if d % 30 == 0:
                print('## {:6d} > {} {}'.format(hotel_id, scanned_date_str_f, booking_date_str_f))

            lowest = 1e10
            highest = 0

            for hour in range(24):
                hour_str = '{:02d}'.format(hour)
                price_info_meta = dynamo_priceinfo.query(KeyConditionExpression=Key('id').eq('{}-{}-index-{}-{}-{}00'.format(hotel_id, ota_str, scanned_date_str, booking_date_str, hour_str)))
                if len(price_info_meta['Items']) == 0:
                    continue
                price_info_meta = price_info_meta['Items'][0]

                for stay_price_idx in price_info_meta['ne_stay_price']:
                    price_info_item = dynamo_priceinfo.query(KeyConditionExpression=Key('id').eq(str(hotel_id) + scanned_date_str + booking_date_str + hour_str + '00' + ota_str + str(stay_price_idx)))
                    if len(price_info_item['Items']) == 0:
                        continue
                    price_info_item = price_info_item['Items'][0]

                    stay_price = price_info_item['stay_price']
                    try:
                        stay_price = int(stay_price)
                    except ValueError:
                        continue
                    if stay_price < 10000:
                        continue

                    room_name = '"{}"'.format(price_info_item['room_name'].replace('"', '\''))
                    
                    lowest = min(lowest, stay_price)
                    highest = max(highest, stay_price)
            
            if highest == 0:
                continue

            record = [hotel_name, ota_str, room_name, addr_splits[0], addr_splits[1], address, scanned_date_str_f, booking_date_str_f, day_of_weeks[booking_date.weekday()], str(lowest), str(highest), str((lowest + highest) / 2)]
            record_str = ','.join(record) + '\n'
            result_str = result_str + record_str
            
        scanned_date += timedelta(days=1)

    with mutex:
        running.value -= 1
        f = open('report/{}. {}일일가격({}분기).csv'.format(no, keyword, sep), mode='a', encoding='utf-8')
        f.write(u'\ufeff')
        f.write(result_str)
        f.close()
        print('END [remain={}]'.format(running.value), hotel_id, hotel_name, ota_str, address, started_at, ended_at)


def get_daily_prices(no, keyword, sep, started_at, ended_at):
    f = open('report/{}. {}일일가격({}분기).csv'.format(no, keyword, sep), mode='w', encoding='utf-8')
    columns = ['hotel_name', 'ota', 'room_name', 'city', 'region', 'address', 'scrape_date', 'booking_date', 'day_of_week', 'lowest_price', 'highest_price', 'average_price']
    f.write(u'\ufeff')
    f.write(','.join(columns) + '\n')
    f.close()

    inputs = []
    with session_scope() as session:
        hotels = session.query(Hotel).filter(Hotel.addr.like('%{}%'.format(keyword))).all()

        for h in hotels:
            target_item = dynamo_crawling_target.query(KeyConditionExpression=Key('id').eq(str(h.id)))
            if len(target_item['Items']) == 0:
                return None
            target_item = target_item['Items'][0]

            for ota_str in ota_code_to_str:
                link_key = '{}_link'.format(ota_str)
                if link_key in target_item:
                    inputs.append((no, keyword, sep, h.id, h.name, ota_str, h.addr, started_at, ended_at,))
    
    running.value = len(inputs)
    semaphore = mp.Semaphore()
    with mp.Pool(processes=200, initializer=initializer, initargs=[semaphore]) as pool:
        pool.map(daily_prices_thread, inputs)


def time_prices_thread(args):
    no, keyword, sep, hotel_id, hotel_name, ota_str, address, started_at, ended_at = args
    print(hotel_id, hotel_name, ota_str, address, started_at, ended_at)
    result_str = ''
    result_list = []
    addr_splits = address.split(' ')
    
    scanned_date = started_at
    while scanned_date < ended_at:
        scanned_date_str = scanned_date.strftime('%Y%m%d')

        for d in range(90):
            booking_date = scanned_date + timedelta(days=d)
            booking_date_str = booking_date.strftime('%Y%m%d')
            booking_date_str_f = booking_date.strftime('%Y-%m-%d')
            if d % 30 == 0:
                print('## {:6d} > {} {}'.format(hotel_id, scanned_date_str, booking_date_str))

            for hour in range(24):
                hour_str = '{:02d}'.format(hour)
                scanned_date_str_f = '{} {:02d}:00:00'.format(scanned_date.strftime('%Y-%m-%d'), hour)
                price_info_meta = dynamo_priceinfo.query(KeyConditionExpression=Key('id').eq('{}-{}-index-{}-{}-{}00'.format(hotel_id, ota_str, scanned_date_str, booking_date_str, hour_str)))
                if len(price_info_meta['Items']) == 0:
                    continue
                price_info_meta = price_info_meta['Items'][0]

                for stay_price_idx in price_info_meta['ne_stay_price']:
                    price_info_item = dynamo_priceinfo.query(KeyConditionExpression=Key('id').eq(str(hotel_id) + scanned_date_str + booking_date_str + hour_str + '00' + ota_str + str(stay_price_idx)))
                    if len(price_info_item['Items']) == 0:
                        continue
                    price_info_item = price_info_item['Items'][0]

                    stay_price = price_info_item['stay_price']
                    try:
                        stay_price = int(stay_price)
                    except ValueError:
                        continue
                    if stay_price < 10000:
                        continue

                    room_name = '"{}"'.format(price_info_item['room_name'].replace('"', '\''))

                    record = [hotel_name, ota_str, room_name, addr_splits[0], addr_splits[1], address, scanned_date_str_f, booking_date_str_f, day_of_weeks[booking_date.weekday()], str(stay_price)]
                    record_str = ','.join(record) + '\n'
                    result_list.append(record_str)
                    #result_str = result_str + record_str
            
        scanned_date += timedelta(days=1)
    
    result_str = ''.join(result_list)
    with mutex:
        running.value -= 1
        f = open('report/{}. {}시간별가격({}분기).csv'.format(no, keyword, sep), mode='a', encoding='utf-8')
        f.write(u'\ufeff')
        f.write(result_str)
        f.close()
        print('END [remain={}]'.format(running.value), hotel_id, hotel_name, ota_str, address, started_at, ended_at)


def get_time_prices(no, keyword, sep, started_at, ended_at):
    f = open('report/{}. {}시간별가격({}분기).csv'.format(no, keyword, sep), mode='w', encoding='utf-8')
    columns = ['hotel_name', 'ota', 'room_name', 'city', 'region', 'address', 'scraped_at', 'booking_date', 'day_of_week', 'price']
    f.write(u'\ufeff')
    f.write(','.join(columns) + '\n')
    f.close()

    inputs = []
    with session_scope() as session:
        hotels = session.query(Hotel).filter(Hotel.addr.like('%{}%'.format(keyword))).all()

        for h in hotels:
            target_item = dynamo_crawling_target.query(KeyConditionExpression=Key('id').eq(str(h.id)))
            if len(target_item['Items']) == 0:
                return None
            target_item = target_item['Items'][0]

            for ota_str in ota_code_to_str:
                link_key = '{}_link'.format(ota_str)
                if link_key in target_item:
                    inputs.append((no, keyword, sep, h.id, h.name, ota_str, h.addr, started_at, ended_at,))

    running.value = len(inputs)
    semaphore = mp.Semaphore()
    with mp.Pool(processes=200, initializer=initializer, initargs=[semaphore]) as pool:
        pool.map(time_prices_thread, inputs)
    
    print('report/{}. {}시간별가격({}분기).csv'.format(no, keyword, sep))


def daily_foret_prices_thread(args):
    no, keyword, sep, hotel_id, hotel_name, ota_str, address, started_at, ended_at = args
    print('START', hotel_id, hotel_name, ota_str, address, started_at, ended_at)
    result_str = ''
    addr_splits = address.split(' ')
    
    scanned_date = started_at
    while scanned_date < ended_at:
        scanned_date_str = scanned_date.strftime('%Y%m%d')
        scanned_date_str_f = scanned_date.strftime('%Y-%m-%d')

        for d in range(90):
            booking_date = scanned_date + timedelta(days=d)
            booking_date_str = booking_date.strftime('%Y%m%d')
            booking_date_str_f = booking_date.strftime('%Y-%m-%d')
            if d % 30 == 0:
                print('## {:6d} > {} {}'.format(hotel_id, scanned_date_str_f, booking_date_str_f))

            lowest = 1e10
            highest = 0

            for hour in range(24):
                hour_str = '{:02d}'.format(hour)
                price_info_meta = dynamo_priceinfo.query(KeyConditionExpression=Key('id').eq('{}-{}-index-{}-{}-{}00'.format(hotel_id, ota_str, scanned_date_str, booking_date_str, hour_str)))
                if len(price_info_meta['Items']) == 0:
                    continue
                price_info_meta = price_info_meta['Items'][0]

                for stay_price_idx in price_info_meta['ne_stay_price']:
                    price_info_item = dynamo_priceinfo.query(KeyConditionExpression=Key('id').eq(str(hotel_id) + scanned_date_str + booking_date_str + hour_str + '00' + ota_str + str(stay_price_idx)))
                    if len(price_info_item['Items']) == 0:
                        continue
                    price_info_item = price_info_item['Items'][0]

                    stay_price = price_info_item['stay_price']
                    try:
                        stay_price = int(stay_price)
                    except ValueError:
                        continue
                    if stay_price < 10000:
                        continue

                    room_name = '"{}"'.format(price_info_item['room_name'].replace('"', '\''))
                    
                    lowest = min(lowest, stay_price)
                    highest = max(highest, stay_price)
            
            if highest == 0:
                continue

            record = [hotel_name, 'wings', room_name, addr_splits[0], addr_splits[1], address, scanned_date_str_f, booking_date_str_f, day_of_weeks[booking_date.weekday()], str(lowest), str(highest), str((lowest + highest) / 2)]
            record_str = ','.join(record) + '\n'
            result_str = result_str + record_str
            
        scanned_date += timedelta(days=1)

    with mutex:
        running.value -= 1
        f = open('report/{}. {}일일가격({}분기).csv'.format(no, keyword, sep), mode='a', encoding='utf-8')
        f.write(u'\ufeff')
        f.write(result_str)
        f.close()
        print('END [remain={}]'.format(running.value), hotel_id, hotel_name, ota_str, address, started_at, ended_at)


def get_daily_foret_prices(no, keyword, sep, started_at, ended_at):
    f = open('report/{}. {}일일가격({}분기).csv'.format(no, keyword, sep), mode='w', encoding='utf-8')
    columns = ['hotel_name', 'ota', 'room_name', 'city', 'region', 'address', 'scrape_date', 'booking_date', 'day_of_week', 'lowest_price', 'highest_price', 'average_price']
    f.write(u'\ufeff')
    f.write(','.join(columns) + '\n')
    f.close()

    inputs = []
    with session_scope() as session:
        hotels = session.query(Hotel).filter(Hotel.name.like('%호텔%포레%')).all()

        for h in hotels:
            target_item = dynamo_crawling_target.query(KeyConditionExpression=Key('id').eq(str(h.id)))
            if len(target_item['Items']) == 0:
                return None
            target_item = target_item['Items'][0]
            
            link_key = 'goodchoice_link'
            if link_key in target_item:
                inputs.append((no, keyword, sep, h.id, h.name, 'goodchoice', h.addr, started_at, ended_at,))
    
    running.value = len(inputs)
    semaphore = mp.Semaphore()
    with mp.Pool(processes=200, initializer=initializer, initargs=[semaphore]) as pool:
        pool.map(daily_foret_prices_thread, inputs)


def get_review(no, keyword):
    f = open('report/{}. {}리뷰.csv'.format(no, keyword), mode='w', encoding='utf-8')
    columns = ['hotel_name', 'ota', 'city', 'region', 'address', 'contents', 'rating', 'reply', 'created_at', 'reply_created_at']
    f.write(u'\ufeff')
    f.write(','.join(columns) + '\n')
    result = []

    reviewinfo_resp = dynamo_reviewinfo.scan()
    reviewinfo_items = reviewinfo_resp['Items']
    total = len(reviewinfo_items)
    process_idx = 0

    while 'LastEvaluatedKey' in reviewinfo_resp:
        reviewinfo_resp = dynamo_crawling_target.scan(ExclusiveStartKey=reviewinfo_resp['LastEvaluatedKey'])
        reviewinfo_items.extend(reviewinfo_resp['Items'])
    
    for review_info in reviewinfo_items:
        process_idx += 1
        ota = review_info['ota']
        subscriber_id = int(review_info['subscriber_id'])

        # subscriber 조회 -> 주소 필터링 및 호텔 정보 확인
        subscriber_item = dynamo_subscriber.query(KeyConditionExpression=Key('id').eq(str(subscriber_id)))
        if len(subscriber_item['Items']) == 0:
            continue
        subscriber_item = subscriber_item['Items'][0]

        # 키워드 안맞으면 건너 띔
        if 'addr' not in subscriber_item or keyword not in subscriber_item['addr']:
            continue

        hotel_name = get_name(subscriber_item)
        print('##', hotel_name)
        addr_splits = subscriber_item['addr'].split(' ')

        idx = 1
        while True:
            print('## {} / {} - {}'.format(process_idx, total, idx))
            review_item = dynamo_review.query(KeyConditionExpression=Key('id').eq('{}-{}-{}'.format(subscriber_id, ota, idx)))
            if len(review_item['Items']) == 0:
                break
            review_item = review_item['Items'][0]

            # hotel_name(호텔명), ota(OTA), city(시/도), region(구/군), address(주소), contents(내용), rating(평점), reply(답글내용) -> 없으면 None, created_at(리뷰작성시간), reply_created_at(답글작성시간) -> 없으면 None
            created_at = datetime.strptime(review_item['date_review'], '%Y. %m. %d')

            reply = '404'
            reply_created_at = '404'

            try:
                if 'reply' in review_item:
                    reply = '"{}"'.format(review_item['reply'].replace('"', '\''))
                if 'date_reply' in review_item:
                    reply_created_at = datetime.strptime(review_item['date_reply'], '%Y. %m. %d').strftime('%Y-%m-%d %H:%M:%S')
            
                record = ['"{}"'.format(hotel_name), ota, addr_splits[0], addr_splits[1], '"{}"'.format(subscriber_item['addr']), '"{}"'.format(review_item.get('review', '').replace('"', '\'')), str(review_item['rating']), reply, created_at.strftime('%Y-%m-%d %H:%M:%S'), reply_created_at]
                record_str = ','.join(record) + '\n'
                result.append(record_str)
                #print(record_str)
            except Exception:
                idx += 1
                continue

            idx += 1
    
    result.reverse()
    for r in result:
        f.write(r)
    f.close()


def get_review_score_changes(no, keyword, started_at, ended_at):
    f = open('report/{}. {}리뷰평점변화.csv'.format(no, keyword), mode='w', encoding='utf-8')
    columns = ['hotel_name', 'ota', 'city', 'region', 'address', 'avg', 'count', 'created_at', 'day_of_week']
    f.write(u'\ufeff')
    f.write(','.join(columns) + '\n')

    reviewinfo_resp = dynamo_reviewinfo.scan()
    reviewinfo_items = reviewinfo_resp['Items']
    total = len(reviewinfo_items)

    while 'LastEvaluatedKey' in reviewinfo_resp:
        reviewinfo_resp = dynamo_crawling_target.scan(ExclusiveStartKey=reviewinfo_resp['LastEvaluatedKey'])
        reviewinfo_items.extend(reviewinfo_resp['Items'])
    
    process_idx = 0
    for review_info in reviewinfo_items:
        process_idx += 1
        ota = review_info['ota']
        subscriber_id = int(review_info['subscriber_id'])

        # subscriber 조회 -> 주소 필터링 및 호텔 정보 확인
        subscriber_item = dynamo_subscriber.query(KeyConditionExpression=Key('id').eq(str(subscriber_id)))
        if len(subscriber_item['Items']) == 0:
            continue
        subscriber_item = subscriber_item['Items'][0]

        # 키워드 안맞으면 건너 띔
        if 'addr' not in subscriber_item or keyword not in subscriber_item['addr']:
            continue

        print('## {} / {}'.format(process_idx, total))
        hotel_name = get_name(subscriber_item)
        addr_splits = subscriber_item['addr'].split(' ')
        
        idx = 1
        data = []
        while True:
            review_item = dynamo_review.query(KeyConditionExpression=Key('id').eq('{}-{}-{}'.format(subscriber_id, ota, idx)))
            if len(review_item['Items']) == 0:
                break
            review_item = review_item['Items'][0]

            created_at = datetime.strptime(review_item['date_review'], '%Y. %m. %d')
            reply = '404'
            reply_created_at = '404'

            try:
                if 'reply' in review_item:
                    reply = '"{}"'.format(review_item['reply'].replace('"', '\''))
                if 'date_reply' in review_item:
                    reply_created_at = datetime.strptime(review_item['date_reply'], '%Y. %m. %d').strftime('%Y-%m-%d %H:%M:%S')

                data.append(dict(
                    review='"{}"'.format(review_item.get('review', '').replace('"', '\'')),
                    rating=int(review_item['rating']),
                    reply=reply,
                    created_at=created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    reply_created_at=reply_created_at,
                    index=created_at
                ))
            except Exception:
                idx += 1
                continue
            idx += 1
        
        data.reverse()
        
        idx = 0
        data_len = len(data)
        ratings = []
        pivot_date = started_at

        while pivot_date < ended_at:
            print('## {} / {} - {}'.format(process_idx, total, pivot_date.strftime('%Y-%m-%d')))
            while idx < data_len:
                if data[idx]['index'] > pivot_date:
                    break
                ratings.append(data[idx]['rating'])
                idx += 1
            
            #hotel_name(호텔명), ota(OTA), city(시/도), region(구/군), address(주소), avg(댓글평점), count(댓글작성개수), created_at(댓글작성시간), day_of_week(요일)
            if len(ratings) == 0:
                record = ['"{}"'.format(hotel_name), ota, addr_splits[0], addr_splits[1], '"{}"'.format(subscriber_item['addr']), '0', '0', pivot_date.strftime('%Y-%m-%d'), day_of_weeks[pivot_date.weekday()]]
            else:
                record = ['"{}"'.format(hotel_name), ota, addr_splits[0], addr_splits[1], '"{}"'.format(subscriber_item['addr']), str(sum(ratings) / len(ratings)), str(len(ratings)), pivot_date.strftime('%Y-%m-%d'), day_of_weeks[pivot_date.weekday()]]
            record_str = ','.join(record) + '\n'
            f.write(record_str)
            
            pivot_date += timedelta(days=1)

    f.close()


if __name__ == '__main__':
    #get_hotel_list(1, '서울')
    #get_hotel_list(2, '부산')

    # 일별 가격
    #get_daily_prices(3, '서울', 1, datetime(2022, 1, 1), datetime(2022, 1, 2))
    #get_daily_prices(4, '서울', 2, datetime(2022, 4, 1), datetime(2022, 7, 1))     # OK
    #get_daily_prices(5, '서울', 3, datetime(2022, 7, 1), datetime(2022, 7, 29))    # OK

    # 일별 가격
    #get_daily_prices(6, '부산', 1, datetime(2022, 1, 1), datetime(2022, 1, 3))     # Test
    #get_daily_prices(7, '부산', 2, datetime(2022, 4, 1), datetime(2022, 7, 1))     # GOGO
    #get_daily_prices(8, '부산', 3, datetime(2022, 7, 1), datetime(2022, 7, 29))    # OK

    # 시간별 가격
    #get_time_prices(9, '서울', 1, datetime(2022, 1, 1), datetime(2022, 1, 3))
    #get_time_prices(10, '서울', 2, datetime(2022, 4, 1), datetime(2022, 7, 1))     # GOGO
    #get_time_prices(11, '서울', 3, datetime(2022, 7, 1), datetime(2022, 7, 29))    # OK

    # 시간별 가격
    #get_time_prices(12, '부산', 1, datetime(2022, 1, 1), datetime(2022, 1, 3))     # Test
    #get_time_prices(13, '부산', 2, datetime(2022, 4, 1), datetime(2022, 7, 1))
    #get_time_prices(14, '부산', 3, datetime(2022, 7, 1), datetime(2022, 7, 29))    # OK

    # 리뷰 평점 변화
    #get_review_score_changes(15, '서울', datetime(2022, 1, 1), datetime(2022, 7, 29))
    #get_review_score_changes(16, '부산', datetime(2022, 1, 1), datetime(2022, 7, 29))

    # 리뷰
    #get_review(17, '서울')
    #get_review(18, '부산')

    # 호텔포레
    #get_daily_foret_prices(19, '호텔포레', 3, datetime(2022, 7, 1), datetime(2022, 7, 29))  # OK
