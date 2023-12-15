from email.policy import default
from flask import Blueprint, Flask, request, render_template, session, url_for, jsonify
from datamenity.models import Hotel, LogCrawler, session_scope, User, HotelReviewMeta, HotelReview, HotelReviewSentiment, Room, RoomPrice, RoomPriceCurrent, RoomTag, RoomTagHasRoom, UserHasCompetition, HotelHasCompetition, HotelHasCrawlerRule, CompareHasTag
from datamenity.crawler import ota_code_to_str, ota_code_to_label, ota_code_to_obj
from flask_login import login_required, current_user, logout_user
from sqlalchemy import or_

from datamenity.config import PAGE_SIZE
from datamenity.common import get_supported_ota, pagination, get_proxy_args
import traceback
import json
import boto3

admin_hotels = Blueprint('admin_hotels', __name__, url_prefix='/hotels/')


# OTA URL 을 request form 으로 입력 -> otas, link 출력
def set_ota_url(data, link=dict()):
    args = get_proxy_args()

    print('set_ota_url start')
    for idx in range(len(ota_code_to_obj)):
        ota_obj = ota_code_to_obj[idx]
        url = data.get('ota_{}'.format(idx))
        if url is None:
            pass
        elif url == '':
            if str(idx) in link:
                del link[str(idx)]
        else:
            try:
                hid = ota_obj.get_hotel_id(args, url)
            except Exception as e:
                raise Exception('{} URL 을 확인해주세요'.format(ota_code_to_label[idx]))
            print('hid : ', hid)
            if type(hid) == dict:
                raise Exception('다시 시도해주세요')
            link[str(idx)] = dict(url=url, hid=hid)
    print('set_ota_url end')
    
    return link
    

@admin_hotels.route('/list', methods=['GET'])
@login_required
def admin_hotels_list():
    sort = request.args.get('sort')
    stype = request.args.get('stype')
    page = request.args.get('page', type=int, default=1)
    name = request.args.get('name', '')
    with session_scope() as session:
        query = session.query(Hotel).filter(or_(Hotel.name.ilike('%{}%'.format(name.replace(' ', '%'))),
                                                Hotel.addr.ilike('%{}%'.format(name.replace(' ', '%'))),  
                                                Hotel.road_addr.ilike('%{}%'.format(name.replace(' ', '%')))  
                                                )
                                            )

        if sort is not None:
            if sort == 'id':
                sort_item = Hotel.id
            elif sort == 'name':
                sort_item = Hotel.name
            
            if stype == 'desc':
                sort_item = sort_item.desc()
            query = query.order_by(sort_item)
        else:
            query = query.order_by(Hotel.created_at.desc())
        
        items = pagination(query, PAGE_SIZE, page)
        return render_template("admin/hotels.html", items=items, ota_code_to_str=ota_code_to_str, keyword=name, sort=sort)


# XXX : 다이나모 디비 관련코드 지워야함 (target_id=-1 이면, 못찾으니 새로 생성하란 소리)
def generate_dynamo_data(target_id, hotel_data):
    dynamo_db = boto3.resource(
        'dynamodb',
        aws_access_key_id='AKIAQM7ZLHBXEVUEXNO4',
        aws_secret_access_key='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',
        region_name='ap-northeast-2'
    )
    crawling_target = dynamo_db.Table('crawling_target')

    # 기존데이터를 가져와서 업데이트를 한다
    dynamo_item = crawling_target.get_item(Key={'id': str(target_id)})
    if not dynamo_item or 'Item' not in dynamo_item: # 검색되지 않음 -> 새로 생성
        dynamo_data = dict(
            id=str(target_id),
            account=True,
            collected=True,
            is_subscriber=True,
        )
        # type=free_trial, user_id=[]?
    else:
        dynamo_data = dynamo_item['Item']
    
    dynamo_data['addr'] = hotel_data.addr
    dynamo_data['road_addr'] = hotel_data.road_addr
    dynamo_data['name'] = hotel_data.name
    dynamo_data['LatLng'] = ['{}'.format(hotel_data.lat), '{}'.format(hotel_data.lng)]

    link = json.loads(hotel_data.link)
    for code in range(len(ota_code_to_str)):
        if str(code) in link:
            ota_string = ota_code_to_str[code]
            if ota_string == 'daily':
                ota_string = 'yanolja'
            elif ota_string == 'yanolja':
                ota_string = 'yanolja2'
            dynamo_data['{}_name'.format(ota_string)] = hotel_data.name
            dynamo_data['{}_link'.format(ota_string)] = 'https://'
    
    # 수정해야하는 경우 기존데이터 지움
    if dynamo_item is not None and 'Item' in dynamo_item:
        crawling_target.delete_item(Key={'id': str(target_id)})

    # 새로 추가함
    crawling_target.put_item(Item=dynamo_data)


@admin_hotels.route('/create', methods=['GET', 'POST'])
@login_required
def admin_hotels_create():
    if request.method == 'POST':
        name = request.form.get('name')
        addr = request.form.get('addr')
        road_addr = request.form.get('road_addr')
        lat = request.form.get('lat')
        lng = request.form.get('lng')

        try:
            lat = float(lat)
            lng = float(lng)
        except Exception:
            return jsonify(code=400, msg='위경도 정보가 이상합니다.')

        try:
            result = set_ota_url(request.form)
        except Exception as e:
            return render_template('popup.html', msg='호텔 생성 실패 ({})'.format(e))

        with session_scope() as session:
            hotel_item = Hotel(name, json.dumps(result), addr, road_addr, lat, lng)
            session.add(hotel_item)
            session.commit()
            session.refresh(hotel_item)

            # XXX : 지워야함 dynamodb 데이터
            generate_dynamo_data(-1, hotel_item)

            return render_template('popup.html', msg='계정을 생성하였습니다', redirect=url_for('admin_hotels.admin_hotels_create'))
        
    return render_template("admin/hotels_create.html", ota_code_to_str=ota_code_to_str, ota_code_to_label=ota_code_to_label)


@admin_hotels.route('/edit', methods=['GET'])
@login_required
def admin_hotels_edit():
    hotel_id = request.args.get('id', type=int, default=None)
    
    with session_scope() as session:
        hotel_item = session.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel_item:
            return render_template('popup.html', msg='존재하지 않는 호텔입니다.')

        link_dict = json.loads(hotel_item.link)

        user_items = session.query(User).filter(User.hotel_id == hotel_id).all()
        competition_items = session.query(UserHasCompetition.user_id, User.name, User.user_id.label('email')) \
            .join(User, User.id == UserHasCompetition.user_id) \
            .filter(UserHasCompetition.competition_id == hotel_id).all()
        myhotel_users = []
        competition_users = []

        for u in user_items:
            myhotel_users.append(dict(id=u.id, name=u.name, user_id=u.user_id))
        for u in competition_items:
            competition_users.append(dict(id=u.user_id, name=u.name, user_id=u.email))
            
        return render_template("admin/hotels_edit.html", ota_code_to_str=ota_code_to_str, ota_code_to_label=ota_code_to_label, hotel_item=hotel_item, link_dict=link_dict, myhotel_users=myhotel_users, competition_users=competition_users)


@admin_hotels.route('/api/edit', methods=['POST'])
@login_required
def admin_hotels_api_edit():
    hotel_id = request.json.get('id')
    name = request.json.get('name')
    addr = request.json.get('addr')
    road_addr = request.json.get('road_addr')
    lat = request.json.get('lat')
    lng = request.json.get('lng')

    if not hotel_id:
        return jsonify(code=400, msg='hotel_id 를 입력해주세요')

    try:
        lat = float(lat)
        lng = float(lng)
    except Exception:
        return jsonify(code=400, msg='위경도 정보가 이상합니다.')
    
    with session_scope() as session:
        hotel_item = session.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel_item:
            return jsonify(code=404, msg='존재하지 않는 호텔입니다.')

        hotel_link = json.loads(hotel_item.link)

        try:
            new_hotel_link = set_ota_url(request.json, hotel_link)
        except Exception as e:
            return jsonify(code=500, msg='호텔 생성 실패 ({})'.format(e))

        hotel_item.name = name
        hotel_item.addr = addr
        hotel_item.road_addr = road_addr
        hotel_item.link = json.dumps(new_hotel_link)
        hotel_item.lat = lat
        hotel_item.lng = lng
        session.commit()

        # XXX : 지워야함 dynamodb 데이터
        generate_dynamo_data(hotel_item.id, hotel_item)

        return jsonify(code=200, msg='Success')


@admin_hotels.route('/api/delete', methods=['POST'])
@login_required
def admin_hotels_api_delete():
    hotel_id = request.json.get('id')

    if not hotel_id:
        return jsonify(code=400, msg='hotel_id 를 입력해주세요')

    with session_scope() as session:
        hotel_item = session.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel_item:
            return jsonify(code=404, msg='존재하지 않는 호텔입니다.')

        ######## 호텔 삭제
        # user_item = session.query(User).filter(User.hotel_id == hotel_id).all()
        # if user_item:
        #     return jsonify(code=404, msg="사용자 이름 : {} 의 나의호텔로 지정되어 있습니다.".format([u.name for u in user_item]))

        # user_has_competition_item = session.query(UserHasCompetition, User.name)\
        #                                     .join(User, User.id == UserHasCompetition.user_id)\
        #                                     .filter(UserHasCompetition.competition_id == hotel_id).all()
        # if user_has_competition_item:
        #     return jsonify(code=404, msg='사용자 이름 : {} 의 경쟁호텔로 지정되어 있습니다.'.format([u.name for u in user_has_competition_item]))

        # session.query(HotelReviewSentiment).filter(HotelReviewSentiment.hotel_id == hotel_id).delete()
        # session.query(HotelReviewMeta).filter(HotelReviewMeta.hotel_id == hotel_id).delete()
        # session.query(HotelReview).filter(HotelReview.hotel_id == hotel_id).delete()

        # room_items = session.query(Room).filter(Room.hotel_id == hotel_id).all()

        # for r in room_items:
        #     session.query(RoomPriceCurrent).filter(RoomPriceCurrent.room_id == r.id).delete()
        #     session.query(RoomPrice).filter(RoomPrice.room_id == r.id).delete()
        #     session.query(RoomTagHasRoom).filter(RoomTagHasRoom.room_id == r.id).delete()
        #     session.query(Room).filter(Room.id == r.id).delete()

        # # 이전에 '나의호텔'로 지정되어 있었던 호텔은 compare_has_tag도 지워야 함
        # room_tag_items = session.query(RoomTag).filter(RoomTag.hotel_id == hotel_id).all()
        # for r in room_tag_items:
        #     session.query(CompareHasTag).filter(CompareHasTag.room_tag_id == r.id).delete()
        # session.query(RoomTag).filter(RoomTag.hotel_id == hotel_id).delete()

        # session.query(LogCrawler).filter(LogCrawler.hotel_id == hotel_id).delete()
        
        # # hotel_has_competition, hotel_has_crawler_rule은 더이상 사용하지 않는 테이블
        # session.query(HotelHasCompetition).filter(HotelHasCompetition.hotel_id == hotel_id).delete()
        # session.query(HotelHasCompetition).filter(HotelHasCompetition.competition_id == hotel_id).delete()
        # session.query(HotelHasCrawlerRule).filter(HotelHasCrawlerRule.hotel_id == hotel_id).delete()
        ########


        session.query(Hotel).filter(Hotel.id == hotel_id).delete()
        session.commit()

        return jsonify(code=200, msg='Success')


@admin_hotels.route('/log', methods=['GET'])
@login_required
def admin_hotels_log():
    hotel_id = request.args.get('id', type=int, default=None)
    hotel_name = request.args.get('name', default=None)
    ota = request.args.get('ota', type=int, default=None)
    hour = request.args.get('hour', type=int, default=None)
    support_ota_dict = get_supported_ota(hotel_id)

    with session_scope() as session:
        item = session.query(LogCrawler) \
            .filter(LogCrawler.hotel_id == hotel_id) \
            .filter(LogCrawler.ota == ota) \
            .filter(LogCrawler.hour == hour).first()

        return render_template("admin/hotels_log.html", hotel_id=hotel_id, ota=ota, hour=hour, item=item, support_ota_dict=support_ota_dict, hotel_name=hotel_name)

