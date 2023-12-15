import json
from os import remove
import uuid
from flask import Flask, Blueprint, request, url_for, render_template, jsonify, redirect
from flask_login import login_required, current_user, logout_user
from datamenity.api.roomtype import find_keyword, set_compare_has_tag, set_compare_has_tag_whole, set_roomtype_hotel_rule, set_roomtype_hotel_rule_whole, judge_roomtype, set_compare_has_tag_of_competitions
import traceback
from datetime import datetime, timedelta
from sqlalchemy import literal_column, literal, func

import boto3

from datamenity.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BUCKET_NAME, PAGE_SIZE

from datamenity.models import Banner, BannerType, Environment, Hotel, UserGroup, UserGroupHasBanner, UserToUserGroup, session_scope, Room, RoomTagHasRoom, RoomTag, RoomPrice
from datamenity.common import get_banner_types, get_crawler_rules, get_usergroups, get_users, pagination, get_user_types, get_hotels

from datamenity.views.setting import setting


admin_roomtype = Blueprint('admin_roomtype', __name__, url_prefix='/roomtype/')


@admin_roomtype.route('/api/update', methods=['POST'])
@login_required
def api_update_roomtype():
    hotel_id = request.json.get('hotel_id')
    setting = request.json.get('setting')


    with session_scope() as session:
        hotel_item = session.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel_item:
            return jsonify(code=404, msg='존재하지 않는 호텔입니다.')
        
        hotel_item.roomtype_setting = json.dumps(setting)
        session.commit()

        set_roomtype_hotel_rule([], hotel_id, None, setting, True)
        set_compare_has_tag_of_competitions([], hotel_id, True)
    
        return jsonify(code=200, msg='Success')


@admin_roomtype.route('/set_roomtype', methods=['GET'])
@login_required
def set_roomtype():
    hotel_id = request.args.get('hotel_id')

    hotels = get_hotels()

    if not hotel_id:
        hotel_id = list(hotels.items())[0][0]
    else:
        try:
            hotel_id = int(hotel_id)
        except Exception:
            return render_template('popup.html', msg='호텔 ID 가 이상합니다')
    


    with session_scope() as session:
        hotel_item = session.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel_item:
            return render_template('popup.html', msg='존재하지 않는 호텔입니다.')

        if not hotel_item.roomtype_setting:
            env_item = session.query(Environment).filter(Environment.key == 'ROOMTYPE_RULE').first()
            json_data = json.loads(env_item.value)
        else:
            json_data = json.loads(hotel_item.roomtype_setting)


        return render_template("admin/set_roomtype.html", 
        hotels=hotels, json_data=json_data)


@admin_roomtype.route('/check_roomtype', methods=['GET'])
@login_required
def check_roomtype():
    kst_now = datetime.utcnow() + timedelta(hours=8)    # 조회시간은 1시간 전의 날짜 기준이되어야 함

    hotel_id = request.args.get('hotel_id')
    hotels = get_hotels()

    if not hotel_id:
        hotel_id = list(hotels.items())[0][0]
    else:
        try:
            hotel_id = int(hotel_id)
        except Exception:
            return render_template('popup.html', msg='호텔 ID 가 이상합니다')

    with session_scope() as session:
        # 룸타입 있는 객실
        roomtype_items = session.query(Room.id, Room.ota_type, Room.name, func.min(RoomPrice.stay_price).label('price'), RoomTag.name.label('roomtype_name'), RoomTag.priority, literal('성공').label('have_roomtype'))\
                                .join(RoomPrice, RoomPrice.room_id == Room.id)\
                                .join(RoomTagHasRoom, RoomTagHasRoom.room_id == Room.id)\
                                .join(RoomTag, RoomTagHasRoom.room_tag_id == RoomTag.id) \
                                .filter(Room.hotel_id == hotel_id)\
                                .filter(RoomPrice.scanned_date >= kst_now.replace(second=0, minute=0, hour=23, microsecond=0))\
                                .group_by(Room.id) \
                                .order_by(RoomTag.priority, Room.ota_type) \
                                .all()
        save_roomtype_id = [i.id for i in roomtype_items]
        # print("@#$@#$",save_roomtype_id)

        # 룸타입 없는 객실
        non_roomtype_items = session.query(Room.id, Room.ota_type, Room.name, func.min(RoomPrice.stay_price).label('price'), literal('실패').label('have_roomtype'))\
                                .join(RoomPrice, RoomPrice.room_id == Room.id)\
                                .filter(Room.hotel_id == hotel_id, Room.id.not_in(save_roomtype_id))\
                                .filter(RoomPrice.scanned_date >= kst_now.replace(second=0, minute=0, hour=23, microsecond=0))\
                                .group_by(Room.id) \
                                .order_by(Room.ota_type) \
                                .all()
        # non_roomtype_items = [i.name for i in non_roomtype_items]
        # print("@#$@#$",non_roomtype_items)
        
        items = non_roomtype_items + roomtype_items

        # # 정렬
        # from operator import attrgetter
        # sort_key = attrgetter('have_roomtype', 'price')
        # items = sorted(items, key=sort_key, reverse=(True))

        count = {"all": len(items), 'succ':len(roomtype_items), 'fail':len(non_roomtype_items)}

    return render_template("admin/check_roomtype.html",
                           hotel_id=hotel_id, hotels=hotels, items=items, count=count)