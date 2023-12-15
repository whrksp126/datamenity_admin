from ast import keyword
from flask import Blueprint, Flask, request, render_template, session, redirect, url_for, jsonify
from flask_login import current_user, login_user, logout_user, login_required, LoginManager
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from datamenity.models import CrawlerRule, UserHasCrawlerRule, UserHasCompetition, UserToUserGroup, session_scope, User, Compare, CompareHasTag
from datamenity.legacy_models import PostgresUser, postgres_session_scope

from datamenity.config import PAGE_SIZE
from datamenity.common import pagination, get_user_types, get_hotels, get_crawler_rules, get_competition_hotel_list
from datamenity.crawler import ota_code_to_str, ota_code_to_label
import json
import boto3
import traceback
from datetime import datetime, timedelta

admin_account = Blueprint('admin_account', __name__, url_prefix='/')


def delete_account(id):
    with session_scope() as session:
        user_item = session.query(User).filter(User.id == id).first()
        if not user_item:
            return jsonify(code=404, msg='존재하지 않는 계정입니다.')

        session.query(UserHasCrawlerRule).filter(UserHasCrawlerRule.user_id == id).delete()
        session.query(UserHasCompetition).filter(UserHasCompetition.user_id == id).delete()
        session.query(UserToUserGroup).filter(UserToUserGroup.user_id == id).delete()

        compare_list = session.query(Compare).filter(Compare.owner == id).all()
        for c in compare_list:
            session.query(CompareHasTag).filter(CompareHasTag.compare_id == c.id).delete()
        session.query(Compare).filter(Compare.owner == id).delete()

        session.query(User).filter(User.id == id).delete()
        session.commit()

        # XXX 지워야함 다이나모디비에서 삭제
        dynamo_db = boto3.resource(
            'dynamodb',
            aws_access_key_id='AKIAQM7ZLHBXEVUEXNO4',
            aws_secret_access_key='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',
            region_name='ap-northeast-2'
        )
        subscriber = dynamo_db.Table('subscriber')
        subscriber.delete_item(Key={'id': str(user_item.id)})

        # postgres (XXX 지워야함)
        with postgres_session_scope() as post_session:
            post_session.query(PostgresUser).filter(PostgresUser.userid == user_item.user_id).delete()
            post_session.commit()


@admin_account.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user_pw = request.form.get('user_pw')

        with session_scope() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                return render_template('popup.html', msg='존재하지 않는 계정입니다.')
            if user.user_type != 3:
                return render_template('popup.html', msg='존재하지 않는 계정입니다.')
            if user is not None and check_password_hash(user.user_pw, user_pw):
                login_user(user, remember=True)
                return redirect(url_for('admin_account.admin_account_list'))
            return render_template('popup.html', msg='비밀번호가 일치하지 않습니다.')

    if not current_user.is_authenticated:
        print('로그인')
        return render_template('admin/login.html')
    
    return redirect(url_for('admin_account.admin_account_list'))


@admin_account.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin_account.home'))
    

@admin_account.route('/account/list', methods=['GET'])
@login_required
def admin_account_list():
    page = request.args.get('page', type=int, default=1)
    name = request.args.get('name', '')
    user_types = get_user_types()
    sort = request.args.get('sort')
    stype = request.args.get('stype')
    type = request.args.get('type', default='0')
    with session_scope() as session:
        query = session.query(User).filter(or_(User.name.ilike('%{}%'.format(name.replace(' ', '%'))),
                                               User.user_id.ilike('%{}%'.format(name.replace(' ', '%'))),
                                               User.manager_name.ilike('%{}%'.format(name.replace(' ', '%'))),
                                               User.address.ilike('%{}%'.format(name.replace(' ', '%'))),
                                               )
                                        )
        if type != '0':
            query = query.filter(User.user_type == type)
            
        if sort is not None:
            if sort == 'email':
                sort_item = User.user_id
            elif sort == 'name':
                sort_item = User.name
            elif sort == 'created_at':
                sort_item = User.created_at
            elif sort == 'last_login':
                sort_item = User.last_logged_at
            elif sort == 'id':
                sort_item = User.id
            
            if stype == 'desc':
                sort_item = sort_item.desc()
            query = query.order_by(sort_item)
        else:
            query = query.order_by(User.created_at.desc())

        items = pagination(query, PAGE_SIZE, page)
        # print("items ",items)
        return render_template("admin/account_list.html", items=items, user_types=user_types, sort=sort, keyword=name, type=type)


@admin_account.route('/account/create', methods=['GET'])
@login_required
def admin_account_create():
    user_types = get_user_types()
    hotels = get_hotels()
    crawler_rules = get_crawler_rules()
    return render_template("admin/account_create.html", user_types=user_types, hotels=hotels, crawler_rules=crawler_rules, ota_code_to_str=ota_code_to_str, ota_code_to_label=ota_code_to_label)


@admin_account.route('/account/edit', methods=['GET'])
@login_required
def admin_account_edit():
    id = request.args.get('id', type=int, default=None)

    if not id:
        return render_template('popup.html', msg='사용자 ID 를 입력해주세요')
    
    user_types = get_user_types()
    hotels = get_hotels()
    crawler_rules = get_crawler_rules()
    competitions = get_competition_hotel_list(id)

    with session_scope() as session:
        user_item = session.query(User).filter(User.id == id).first()
        user_crawler_rule = session.query(UserHasCrawlerRule).filter(UserHasCrawlerRule.user_id == id).limit(1).first()

        if not user_item:
            return render_template('popup.html', msg='존재하지 않는 사용자입니다.')
        return render_template("admin/account_edit.html", user_types=user_types, hotels=hotels, user_item=user_item, crawler_rules=crawler_rules, user_crawler_rule=user_crawler_rule, competitions=competitions, ota_code_to_str=ota_code_to_str, ota_code_to_label=ota_code_to_label)


@admin_account.route('/account/api/create_or_update', methods=['POST'])
@login_required
def admin_account_create_or_update():
    account_id = request.json.get('account_id')
    user_id = request.json.get('user_id')
    user_pw = request.json.get('user_pw')
    user_pw_ok = request.json.get('user_pw_ok')
    name = request.json.get('name')
    tel = request.json.get('tel')
    address = request.json.get('address')
    address2 = request.json.get('address2')
    user_type = request.json.get('user_type')
    manager_name = request.json.get('manager_name')
    manager_tel = request.json.get('manager_tel')
    hotel_id = request.json.get('hotel_id')
    competitions = request.json.get('competitions', [])
    rule_id = request.json.get('rule_id')
    otas = request.json.get('otas')
    otas_order = request.json.get('otas_order')
    otas_order_list = request.json.get('otas_order', [])
    started_at = datetime.strptime(request.json.get('started_at'), '%Y-%m-%d')
    ended_at = datetime.strptime(request.json.get('ended_at'), '%Y-%m-%d')
    hotel_limit = request.json.get('hotel_limit')
    ota_limit = request.json.get('ota_limit')

    # XXX : 축제거리 디폴트 25, 제주도일 경우 80
    if "제주" in address:
        festival_distance = 80 
    else:
        festival_distance = 25 


    kst_now = datetime.utcnow() + timedelta(hours=9)

    if user_pw != user_pw_ok:
        return jsonify(code=400, msg='비밀번호를 확인해주세요')
    if len(name) == 0:
        return jsonify(code=400, msg='이름을 입력해주세요')
    if hotel_id == '':
        hotel_id = None

    user_item_id = None

    try:
        with session_scope() as session:
            if account_id is None:  # create
                if len(user_id) == 0:
                    return jsonify(code=400, msg='아이디를 입력해주세요')
                if len(user_pw) < 4:
                    return jsonify(code=400, msg='비밀번호는 4자 이상으로 설정해주세요')
                user_item = User(user_id, user_pw, name, user_type, manager_name, manager_tel, tel, address, address2, hotel_id, otas, otas_order, started_at, ended_at, hotel_limit, ota_limit, festival_distance)
                session.add(user_item)
                session.commit()
                session.refresh(user_item)
                user_item_id = user_item.id
                user_id_check = user_item.id 

                # '모든호텔' usergroup에 추가
                usergroup_item = UserToUserGroup(user_id_check, 27)
                session.add(usergroup_item)
                session.commit()
                session.refresh(usergroup_item)

            else:                   # update
                user_item = session.query(User).filter(User.id == account_id).first()
                if not user_item:
                    return jsonify(code=404, msg='해당 사용자는 존재하지 않습니다.')
                if user_pw != '':
                    if len(user_pw) < 4:
                        return jsonify(code=400, msg='비밀번호는 4자 이상으로 설정해주세요')
                    user_item.user_pw = generate_password_hash(user_pw)
                
                old_user_id = user_item.user_id
                user_item.user_id = user_id
                user_item.name = name
                user_item.tel = tel
                user_item.address = address
                user_item.address2 = address2
                user_item.user_type = user_type
                user_item.manager_name = manager_name
                user_item.manager_tel = manager_tel
                user_item.hotel_id = hotel_id
                user_item.otas = otas
                user_item.otas_order = otas_order
                user_item.started_at = started_at
                user_item.ended_at = ended_at
                user_item.hotel_limit = hotel_limit
                user_item.ota_limit = ota_limit
                user_item.festival_distance = festival_distance
                session.commit()
                user_id_check = user_item.id

            # 크롤러 룰 (rule_id) 추가
            session.query(UserHasCrawlerRule).filter(UserHasCrawlerRule.user_id == account_id).delete()
            if rule_id != 0:
                session.add(UserHasCrawlerRule(user_item.id, rule_id))

            # competitions 중복 제거
            competitions_set = set()
            unique_competitions = []
            for c in competitions:
                if int(c) in competitions_set:
                    continue
                competitions_set.add(int(c))
                unique_competitions.append(int(c))
            competitions = unique_competitions
            
            # 경쟁사 (competitions) 추가
            # 수정시 기존 created_at을 저장하고, 값을 넣는다.
            competition_list = session.query(UserHasCompetition).filter(UserHasCompetition.user_id == account_id).all()
            competition_dict = dict()
            for c in competition_list:
                competition_dict[c.competition_id] = c.created_at
            session.query(UserHasCompetition).filter(UserHasCompetition.user_id == account_id).delete()
            if account_id is None:    # create
                priority = 1
                for c in competitions:
                    session.add(UserHasCompetition(user_item.id, int(c), priority, kst_now))
                    priority += 1
            else:                           # update
                priority = 1
                for c in competitions:
                    if int(c) in competition_dict:
                        created_at = competition_dict[int(c)]
                    else:
                        created_at = kst_now
                    session.add(UserHasCompetition(user_item.id, int(c), priority, created_at))
                    priority += 1
                

            # 커스텀호텔(켄싱턴, 윙스부킹)일 경우 해당 usergroup에 추가
            usergroup_item = None
            if 9 in json.loads(otas_order_list) : # 윙스부킹
                usergroup_check = session.query(UserToUserGroup)\
                        .filter(UserToUserGroup.user_id == user_id_check, UserToUserGroup.usergroup_id == 30).first()
                if usergroup_check is None:
                    usergroup_item = UserToUserGroup(user_id_check, 30)
            if 10 in json.loads(otas_order_list) : # 켄싱턴호텔
                usergroup_check = session.query(UserToUserGroup)\
                        .filter(UserToUserGroup.user_id == user_id_check, UserToUserGroup.usergroup_id == 31).first()
                if usergroup_check is None:
                    usergroup_item = UserToUserGroup(user_id_check, 31)
            if usergroup_item is not None:
                session.add(usergroup_item)
                session.commit()
                session.refresh(usergroup_item)

            session.commit()

            # dynamodb (XXX 지워야함)
            if rule_id != 0:
                rule_item = session.query(CrawlerRule).filter(CrawlerRule.id == rule_id).first()
                scrape_range = 0 if rule_item is None else rule_item.range
                scrape_time = [] if rule_item is None else ['{:02d}00'.format(i) for i in range(24) if (rule_item.time & (1 << i))]
                stl = len(scrape_time)
            else:
                scrape_range = 0
                scrape_time = []
                stl = len(scrape_time)
            
            dynamo_ota = []
            for code in range(len(ota_code_to_str)):
                if (otas & (1 << code)) > 0:
                    ota_string = ota_code_to_str[code]
                    if ota_string == 'daily':
                        ota_string = 'yanolja'
                    elif ota_string == 'yanolja':
                        ota_string = 'yanolja2'
                    dynamo_ota.append(ota_string)
            
            dynamo_data = dict(
                id=str(user_item.id),
                name=user_id,
                scrape_range=scrape_range,
                scrape_time=scrape_time,
                setting=dict(
                    default=stl,
                    view=stl,
                    rateplan=True
                ),
                my_target_id=str(hotel_id),
                ota=dynamo_ota,
                my_targets=[dict(id=str(c), default=dict(activate=True, type=True)) for c in competitions]
            )
            dynamo_data['m-high'] = 10000
            dynamo_data['m-low'] = 10000

            dynamo_db = boto3.resource(
                'dynamodb',
                aws_access_key_id='AKIAQM7ZLHBXEVUEXNO4',
                aws_secret_access_key='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',
                region_name='ap-northeast-2'
            )
            subscriber = dynamo_db.Table('subscriber')
            if account_id is not None:  # update
                # 기존데이터를 가져와서 업데이트를 한다
                dynamo_item = subscriber.get_item(Key={'id': str(user_item.id)})
                if 'Item' in dynamo_item:
                    dynamo_item = dynamo_item['Item']
                    dynamo_item.update(dynamo_data)
                    dynamo_data = dynamo_item

                # 기존데이터 지움
                subscriber.delete_item(Key={'id': str(user_item.id)})

                with postgres_session_scope() as post_session:
                    post_user = post_session.query(PostgresUser).filter(PostgresUser.userid == old_user_id).first()
                    if user_pw != '':
                        if len(user_pw) < 4:
                            return jsonify(code=400, msg='비밀번호는 4자 이상으로 설정해주세요')
                        post_user.userpw = generate_password_hash(user_pw)
                    post_user.userid = user_id
                    post_user.username = name
                    post_user.pic = manager_name
                    post_user.pictel = manager_tel
                    post_user.tel = tel
                    post_user.address = address
                    post_user.address_more = address2
                    post_user.userStatus = '유료' if user_type == 4 else '무료',
                    
            else:   # create
                # postgres (XXX 지워야함)
                with postgres_session_scope() as post_session:
                    user = PostgresUser(
                        userid=user_item.user_id,
                        username=name,
                        userpw=generate_password_hash(user_pw),
                        create_date=datetime.utcnow(),
                        pic=manager_name,
                        pictel=manager_tel,
                        tel=tel,
                        address=address,
                        address_more=address2,
                        userStatus='유료' if user_type == 4 else '무료',
                        plan_start='',
                        plan_end='',
                        rateplan=''
                    )
                    post_session.add(user)
                    post_session.commit()
                
                dynamo_data.update(dict(
                    agoda_name=name,
                    expedia_name=name,
                    booking_name=name,
                    agoda_link='',
                    expedia_link='',
                    booking_link='',
                    email_list=[user_id],
                    addr='{} {}'.format(address, address2),
                    name=user_id,
                    notice=True,
                    road_addr='{} {}'.format(address, address2),
                    type='유료' if user_type == 4 else '무료',
                ))

            # 생성
            subscriber.put_item(Item=dynamo_data)
            return jsonify(code=200, msg='Success')
        
    except Exception:
        print(traceback.print_exc())

        # 생성하다가 실패한 경우, mysql 계정이 생성되었다면, 관련 데이터를 모두 지운다
        if account_id is None and user_item_id is not None:
            delete_account(user_item_id)
        
        return jsonify(code=500, msg='작업 처리 실패. 관리자에게 문의 바랍니다.')


@admin_account.route('/account/api/delete', methods=['POST'])
@login_required
def admin_account_api_delete():
    id = request.json.get('id')

    if not id:
        return jsonify(code=400, msg='계정 id 를 입력해주세요')

    try:
        delete_account(id)
        return jsonify(code=200, msg='Success')
    except Exception as e:
        print(traceback.print_exc())
        return jsonify(code=500, msg='{}'.format(e))


@admin_account.route('/account/connect', methods=['GET'])
@login_required
def admin_account_connect():
    user_id = request.args.get('user_id', default=None)
    with postgres_session_scope() as post_session:
        post_user = post_session.query(PostgresUser).filter(PostgresUser.userid == user_id).first()
        post_id = str(post_user.id)
    return redirect('https://app.datamenity.com/admin/user/login?id='+post_id)
