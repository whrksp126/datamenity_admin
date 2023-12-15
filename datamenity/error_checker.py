from datamenity.models import session_scope, Hotel, HotelError, HotelErrorType, Room, RoomPrice
from datamenity.crawler import ota_code_to_type
from datamenity.common import get_crawler_price_works, send_message_to_slack_server
from sqlalchemy import and_, or_
import time
from datetime import datetime, timedelta


def check_error(year, month, day, hour):
    price_works = get_crawler_price_works(hour)

    # 시간
    scanned_time = datetime(year, month, day, hour)
    thresold_time = scanned_time - timedelta(hours=9) - timedelta(hours=12)
    
    # whole_set 에 에러를 체크해야 할 호텔+OTA 리스트를 저장한다
    whole_set = set()
    for w in price_works:
        hotel_id, ota = w['id'], w['ota']
        whole_set.add((hotel_id, ota_code_to_type[ota]))
    
    with session_scope() as session:
        # 업데이트된 room 조회
        rooms = session.query(Room).filter(Room.updated_at >= thresold_time).all()

        # updated_set 에 업데이트된 hotel+ota 를 추가
        updated_set = set()
        for room in rooms:
            updated_set.add((room.hotel_id, room.ota_type))
        
        # 정책에 해당되는 호텔 중, 단 한번의 업데이트도 일어나지 않은 호텔+ota 를 찾음
        unupdated_set = whole_set - updated_set
        
        print('unupdated_set : ', len(unupdated_set))
        print('whole_set : ', len(whole_set))
        print('updated_set : ', len(updated_set))        

        # 호텔 에러 리스트 작성
        hotel_error_items = session.query(HotelError).filter(HotelError.is_fix.is_(False)).all()
        hotel_error_dict = dict()
        for h in hotel_error_items:
            hotel_error_dict[(h.hotel_id, h.ota_type)] = h
        
        # 에러에 있었다가 update 된 것 처리 (is_fix = False -> True)
        fix_cnt = 0
        for item in updated_set:
            hotel_id, ota_type = item[0], item[1]

            if (hotel_id, ota_type) in hotel_error_dict:
                if hotel_error_dict[(hotel_id, ota_type)].is_fix == False:
                    fix_cnt += 1
                    hotel_error_dict[(hotel_id, ota_type)].is_fix = True
                    hotel_error_dict[(hotel_id, ota_type)].fixed_at = scanned_time
                #hotel_error_dict[(hotel_id, ota_type)].updated_at = scanned_time
        
        # unupdated 에 없었다가 추가 된 것 처리 (생성)
        new_cnt = 0
        for item in unupdated_set:
            hotel_id, ota_type = item[0], item[1]

            if (hotel_id, ota_type) not in hotel_error_dict:
                session.add(HotelError(hotel_id, ota_type, scanned_time, None, ''))
                new_cnt += 1
            else:
                hotel_error_dict[(hotel_id, ota_type)].updated_at = scanned_time

        session.commit()
        
        # 슬랙 메시지 생성
        started_at = scanned_time
        ended_at = scanned_time + timedelta(hours=1)
        hour_fail_url = 'https://adm.datamenity.com/error/hotel/list?updated_from={}&updated_to={}'.format(started_at.strftime('%Y-%m-%d_%H:%M:%S'), ended_at.strftime('%Y-%m-%d_%H:%M:%S'))
        solved_issue_url = 'https://adm.datamenity.com/error/hotel/list?updated_from={}&updated_to={}&is_fix=t'.format(started_at.strftime('%Y-%m-%d_%H:%M:%S'), ended_at.strftime('%Y-%m-%d_%H:%M:%S'))
        new_issue_url = 'https://adm.datamenity.com/error/hotel/list?created_from={}&created_to={}'.format(started_at.strftime('%Y-%m-%d_%H:%M:%S'), ended_at.strftime('%Y-%m-%d_%H:%M:%S'))

        #if fix_cnt > 0 or new_cnt > 0:
        send_message_to_slack_server('*스캔시간 : {} ~ {}*\n*[모든 기간 예약마감 호텔]*\n  - 1 시간 동안 크롤링 수행 : {:,}건\n  - 1 시간 동안 크롤링 실패 : <{}|{:,}건>\n  - 이번에 해결된 이슈 : <{}|{:,}건>\n  - 새로 생성된 이슈 : <{}|{:,}건>\n* 마지막 알림 기준 로그 개수가 정확합니다. (에러의 상태가 변하므로)'.format(started_at.strftime('%Y-%m-%d %H시'), ended_at.strftime('%Y-%m-%d %H시'), len(whole_set), hour_fail_url, len(unupdated_set), solved_issue_url, fix_cnt, new_issue_url, new_cnt))
