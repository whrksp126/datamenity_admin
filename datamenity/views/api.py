from datamenity.models import Environment, User, session_scope, Room, Hotel, RoomTag, RoomTagHasRoom, RoomPrice, RoomPriceCurrent, CrawlerRule, Hotel, LogScheduler, LogCrawler, OTAType
from datamenity.api.roomtype import judge_roomtype
from flask import Blueprint, Flask, request, render_template, session, jsonify
from datamenity.models import session_scope, User
from flask_login import login_required, current_user, logout_user
from datetime import datetime, timedelta
from datamenity.crawler import ota_code_to_type
import traceback
import json

admin_api = Blueprint('admin_api', __name__, url_prefix='/api/')


def write_price_data(output, errors, now, hotel_id, ota, room_name, booking_date, rent_price, stay_price, rent_remain, stay_remain):
    ota_type = ota_code_to_type[ota]
    utcnow = datetime.utcnow()
    kstnow = utcnow + timedelta(hours=9)
    scanned_date = datetime(kstnow.year, kstnow.month, kstnow.day, kstnow.hour)
    last_scanned_date = datetime(kstnow.year, kstnow.month, kstnow.day, 23)
    
    with session_scope() as session:
        # 1. Room 찾기
        room_item = session.query(Room).filter(Room.hotel_id == hotel_id, Room.ota_type == ota_type, Room.name == room_name).first()

        if not room_item:                       # 2-1. 만약 Room 이 없다면
            # 2-1-1. Room 생성 -> 에러 나면 다시 조회
            room_item = Room(hotel_id, ota_type, room_name)
            session.add(room_item)
            session.commit()
            session.refresh(room_item)
            
            try:
                # setting 가져옴
                env_item = session.query(Environment).filter(Environment.key == 'ROOMTYPE_RULE').first()
                if env_item is not None:
                    setting = json.loads(env_item.value)
                
                # 룸타입을 판단함
                roomtype_item = judge_roomtype(output, hotel_id, room_name, stay_price, setting)
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
        
        else:
            room_item.updated_at = utcnow

            '''
            # 2-1-2. TODO RoomTagHasRoom, RoomTag 추가 (커밋은 룸과 함께 함)
            room_classify_name = '스탠다드'
            room_tag_item = session.query(RoomTag).filter(RoomTag.hotel_id == hotel_id, RoomTag.name == room_classify_name).first()
            if not room_tag_item:
                try:
                    room_tag_item = RoomTag(hotel_id, room_classify_name)
                    session.add(room_tag_item)
                    session.commit()
                    session.refresh(room_tag_item)
                except IntegrityError as e:
                    room_tag_item = session.query(RoomTag).filter(RoomTag.hotel_id == hotel_id, RoomTag.name == room_classify_name).first()

            # RoomTagHasRoom 추가
            try:
                room_tag_has_room_item = RoomTagHasRoom(room_tag_item.id, room_item.id)
                session.add(room_tag_has_room_item)
                session.commit()
            except IntegrityError as e:
                pass
            '''
    
        # 3. 가격 정보 추가
        last_room_price_item = session.query(RoomPrice).filter(RoomPrice.booking_date == booking_date, RoomPrice.room_id == room_item.id, RoomPrice.scanned_date == last_scanned_date).first()
        if scanned_date != last_scanned_date:
            if not last_room_price_item:
                last_room_price_item = RoomPrice(booking_date, room_item.id, last_scanned_date, rent_price, stay_price, rent_remain, stay_remain)
                session.add(last_room_price_item)
            else:
                last_room_price_item.rent_price = rent_price
                last_room_price_item.stay_price = stay_price
                last_room_price_item.rent_remain = rent_remain
                last_room_price_item.stay_remain = stay_remain
            session.commit()
        
        room_price_item = session.query(RoomPrice).filter(RoomPrice.booking_date == booking_date, RoomPrice.room_id == room_item.id, RoomPrice.scanned_date == scanned_date).first()
        if not room_price_item:
            room_price_item = RoomPrice(booking_date, room_item.id, scanned_date, rent_price, stay_price, rent_remain, stay_remain)
            session.add(room_price_item)
        else:
            room_price_item.rent_price = rent_price
            room_price_item.stay_price = stay_price
            room_price_item.rent_remain = rent_remain
            room_price_item.stay_remain = stay_remain
        session.commit()

        room_price_curr_item = session.query(RoomPriceCurrent).filter(RoomPriceCurrent.booking_date == booking_date, RoomPriceCurrent.room_id == room_item.id).first()
        if not room_price_curr_item:
            room_price_curr_item = RoomPriceCurrent(booking_date, room_item.id, scanned_date, rent_price, stay_price, rent_remain, stay_remain)
            session.add(room_price_curr_item)
        else:
            room_price_curr_item.last_date = scanned_date
            room_price_curr_item.rent_price = rent_price
            room_price_curr_item.stay_price = stay_price
            room_price_curr_item.rent_remain = rent_remain
            room_price_curr_item.stay_remain = stay_remain
        session.commit()


@admin_api.route('/room/price/set', methods=['POST'])
def admin_api_price_set():
    output = request.json.get('output')
    errors = request.json.get('errors')
    now = request.json.get('now')
    hotel_id = request.json.get('hotel_id')
    ota = request.json.get('ota')
    room_name = request.json.get('room_name')
    booking_date = request.json.get('booking_date')
    rent_price = request.json.get('rent_price')
    stay_price = request.json.get('stay_price')
    rent_remain = request.json.get('rent_remain')
    stay_remain = request.json.get('stay_remain')

    try:
        write_price_data(output, errors, now, hotel_id, ota, room_name, booking_date, rent_price, stay_price, rent_remain, stay_remain)
    except Exception as e:
        print(traceback.print_exc())
        return jsonify(code=500, msg='{}'.format(e))
    
    return jsonify(code=200)