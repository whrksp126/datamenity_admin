from ast import keyword
from flask import Blueprint, Flask, request, render_template, session, redirect, url_for, jsonify
from flask_login import current_user, login_user, logout_user, login_required, LoginManager
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from datamenity.models import session_scope, User, HotelError, HotelErrorType, Hotel
from datamenity.legacy_models import PostgresUser, postgres_session_scope

from datamenity.config import PAGE_SIZE
from datamenity.common import pagination, get_user_types, get_hotels, get_crawler_rules, get_competition_hotel_list
from datamenity.crawler import ota_code_to_str, ota_code_to_label, ota_str_to_code, ota_code_to_type
import json
import boto3
import traceback
from datetime import datetime, timedelta

admin_error_log = Blueprint('admin_error_log', __name__, url_prefix='/error/')


def get_hotel_error_types():
    with session_scope() as session:
        hotel_error_types = session.query(HotelErrorType).all()
        result = dict()
        result[0] = '분류 없음'
        for h in hotel_error_types:
            result[h.id] = h.name
        return result


@admin_error_log.route('/hotel/list', methods=['GET'])
@login_required
def error_hotel_list():
    page = request.args.get('page', type=int, default=1)
    name = request.args.get('name', '')
    hotel_error_types = get_hotel_error_types()
    hotel_error_type = request.args.get('hotel_error_type', default='')
    if hotel_error_type == '':
        hotel_error_type = None
    is_fix = request.args.get('is_fix', False)
    if is_fix != False:
        is_fix = True
    updated_from = request.args.get('updated_from')
    updated_to = request.args.get('updated_to')
    created_from = request.args.get('created_from')
    created_to = request.args.get('created_to')

    with session_scope() as session:
        # 호텔 id 로 이름 찾기
        hotel_id_to_name = dict()
        hotel_ids = set()
        hotel_query = session.query(Hotel).filter(Hotel.name.ilike('%{}%'.format(name.replace(' ', '%')))).all()
        for h in hotel_query:
            hotel_id_to_name[h.id] = dict(name=h.name, link=json.loads(h.link))
            hotel_ids.add(h.id)
        
        # 호텔 에러 데이터 조회
        query = session.query(HotelError).filter(HotelError.is_fix.is_(is_fix), HotelError.hotel_id.in_(hotel_ids))
        if updated_from is not None:
            updated_from = datetime.strptime(updated_from, '%Y-%m-%d_%H:%M:%S')
            query = query.filter(HotelError.updated_at >= updated_from)
        if updated_to is not None:
            updated_to = datetime.strptime(updated_to, '%Y-%m-%d_%H:%M:%S')
            query = query.filter(HotelError.updated_at < updated_to)
        if created_from is not None:
            created_from = datetime.strptime(created_from, '%Y-%m-%d_%H:%M:%S')
            query = query.filter(HotelError.scanned_at >= created_from)
        if created_to is not None:
            created_to = datetime.strptime(created_to, '%Y-%m-%d_%H:%M:%S')
            query = query.filter(HotelError.scanned_at < created_to)

        if hotel_error_type is not None:
            if hotel_error_type == '0':
                query = query.filter(HotelError.hotel_error_type == None)
            elif hotel_error_type not in hotel_error_types:
                query = query.filter(HotelError.hotel_error_type == hotel_error_type)

        query = query.order_by(HotelError.created_at.desc())

        # 에러타입별 카운팅 - 초기화
        error_type_to_cnt = dict()
        error_type_to_cnt[0] = 0
        for k, v in hotel_error_types.items():
            error_type_to_cnt[k] = 0
        
        # 에러타입별 카운팅
        error_items = query.all()
        for item in error_items:
            hotel_error_type_code = item.hotel_error_type
            if hotel_error_type_code is None:
                hotel_error_type_code = 0
            error_type_to_cnt[hotel_error_type_code] += 1

        # 페이지네이션
        items = pagination(query, PAGE_SIZE, page)
        for item in items['items']:
            item['name'] = hotel_id_to_name[item['id']]['name']
            ota_code = ota_str_to_code[item['ota_type'].name.lower()]
            try:
                url = hotel_id_to_name[item['id']]['link'][str(ota_code)]['url']
            except:
                url = ''
            item['url'] = url

        return render_template("admin/hotel_error/error_list.html", items=items, hotel_error_types=hotel_error_types, hotel_error_type=hotel_error_type, keyword=name, error_type_to_cnt=error_type_to_cnt)


@admin_error_log.route('/api/set_error_type', methods=['POST'])
@login_required
def set_error_type():
    hotel_id = request.json.get('hotel_id')
    ota_type = request.json.get('ota_type')
    scanned_at = request.json.get('scanned_at')
    error_type = request.json.get('error_type')
    if error_type == '0':
        error_type = None

    with session_scope() as session:
        hotel_error_item = session.query(HotelError).filter(
            HotelError.hotel_id == hotel_id,
            HotelError.ota_type == ota_str_to_code[ota_type.lower()] + 1,
            HotelError.scanned_at == scanned_at
        ).first()

        if not hotel_error_item:
            return jsonify(code=404, msg='존재하지 않는 에러입니다.')
        
        hotel_error_item.hotel_error_type = error_type
        session.commit()
        
    return jsonify(code=200)


from datamenity.factories.celery import configure_celery
from datamenity.factories.application import create_application
from datamenity.crawler import crawler_handler

app = create_application()
celery = configure_celery(app)


@celery.task(queue='test_queue', default_retry_delay=30 * 60, max_retries=1)
def run_test_crawler_price(crawler_type, hour, hotel_id, hotel_link, ota, rule):
    try:
        print('[run]', crawler_type, hour, hotel_id, hotel_link, ota, rule)
        crawler_handler(crawler_type, hour, hotel_id, hotel_link, ota, rule)
        print('[run complete]', crawler_type, hotel_id, ota, rule)
    except Exception as e:
        print(e)


# scheduler/test
@admin_error_log.route('/scheduler/test', methods=['GET', 'POST'])
@login_required
def error_scheduler_test():
    crawler_type = request.form.get('crawler_type', 'price')
    hotel_id = int(request.form.get('hotel_id', 1))
    ota = int(request.form.get('ota', 0))

    with session_scope() as session:
        if request.method == 'POST':        
            hotel_item = session.query(Hotel).filter(Hotel.id == hotel_id).first()
            if not hotel_item:
                return render_template('popup.html', msg='존재하지 않는 호텔')
            
            hour = (datetime.utcnow() + timedelta(hours=9)).hour
            hotel_link = json.loads(hotel_item.link)
            rule = [dict(range=30, time=16777215)]

            print('#5')
            run_test_crawler_price(crawler_type, hour, hotel_id, hotel_link[str(ota)], ota, rule)
            print('#6')

        return render_template("admin/hotel_error/error_scheduler_test.html", ota_str_to_code=ota_str_to_code, crawler_type=crawler_type, hotel_id=hotel_id, ota=ota)