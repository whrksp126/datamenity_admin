from flask import Flask, Blueprint, request, url_for, render_template, jsonify
from flask_login import login_required, current_user, logout_user
import traceback

from datamenity.config import PAGE_SIZE

from datamenity.models import User, UserGroup, UserToUserGroup, session_scope
from datamenity.common import get_crawler_rules, get_users, pagination, get_user_types, get_hotels


admin_usergroup = Blueprint('admin_usergroup', __name__, url_prefix='/usergroup/')


def delete_usergroup(id):
    with session_scope() as session:
        usergroup_item = session.query(UserGroup).filter(UserGroup.id == id).first()
        if not usergroup_item:
            return jsonify(code=404, msg='존재하지 않는 계정입니다.')

        session.query(UserToUserGroup).filter(UserToUserGroup.usergroup_id == id).delete()
        session.query(UserGroup).filter(UserGroup.id == id).delete()
        session.commit()


@admin_usergroup.route('/edit', methods=['GET'])
@login_required
def aadmin_usergroup_edit():
    usergroup_id = request.args.get('id', type=int, default=None)

    if not usergroup_id:
        return render_template('popup.html', msg='그룹 ID 를 입력해주세요')
    
    users = get_users()

    with session_scope() as session:
        usergroup_item = session.query(UserGroup).filter(UserGroup.id == usergroup_id).first()
        user_list = session.query(User)\
                           .join(UserToUserGroup, UserToUserGroup.user_id == User.id)\
                           .filter(UserToUserGroup.usergroup_id == usergroup_id).all()

        if not usergroup_item:
            return render_template('popup.html', msg='존재하지 않는 사용자 그룹입니다.')
        return render_template("admin/usergroup_edit.html", users=users, usergroup_item=usergroup_item, user_list=user_list)


@admin_usergroup.route('/create', methods=['GET'])
@login_required
def admin_usergroup_create():
    user_types = get_user_types()
    users = get_users()
    crawler_rules = get_crawler_rules()
    return render_template("admin/usergroup_create.html", user_types=user_types, users=users, crawler_rules=crawler_rules)


@admin_usergroup.route('/api/create_or_update', methods=['POST'])
@login_required
def admin_usergroup_create_or_update():
    usergroup_id = request.json.get('usergroup_id')
    group_name = request.json.get('group_name')
    user_type = request.json.get('user_type')
    users = request.json.get('users', [])

    usergroup_item_id = None

    try:
        with session_scope() as session:
            if usergroup_id is None:  # create
                if len(group_name) == 0:
                    return jsonify(code=400, msg='사용자 그룹 이름를 입력해주세요')
                if len(users) == 0:
                    return jsonify(code=400, msg='사용자를 추가해주세요')
                usergroup_item = UserGroup(group_name)
                session.add(usergroup_item)
                session.commit()
                session.refresh(usergroup_item)
                usergroup_item_id = usergroup_item.id

                for user in users:
                    user_to_usergroup_item = UserToUserGroup(user, usergroup_item_id)
                    session.add(user_to_usergroup_item)
                    session.commit()
                    session.refresh(user_to_usergroup_item)

            else:                   # update
                usergroup_item = session.query(UserGroup).filter(UserGroup.id == usergroup_id).first()
                if not usergroup_item:
                    return jsonify(code=404, msg='해당 사용자 그룹은 존재하지 않습니다.')
                usergroup_item.name = group_name
                usergroup_item.user_type = user_type
                session.commit()

                # 사용자 그룹 추가
                session.query(UserToUserGroup).filter(UserToUserGroup.usergroup_id == usergroup_id).delete()
                for u in users:
                    session.add(UserToUserGroup(int(u) , usergroup_id))
                session.commit()
            
            # 생성
            return jsonify(code=200, msg='Success')
        
    except Exception:
        print(traceback.print_exc())

        # 생성하다가 실패한 경우, mysql 계정이 생성되었다면, 관련 데이터를 모두 지운다
        if usergroup_id is None and usergroup_item_id is not None:
            delete_usergroup(usergroup_item_id)
        
        return jsonify(code=500, msg='작업 처리 실패. 관리자에게 문의 바랍니다.')


@admin_usergroup.route('/list', methods=['GET'])
@login_required
def admin_usergroup_list():
    page = request.args.get('page', type=int, default=1)
    name = request.args.get('name', '')
    with session_scope() as session:
        query = session.query(UserGroup)\
                    .filter(UserGroup.name.ilike('%{}%'.format(name.replace(' ', '%'))))\
                    .order_by(UserGroup.created_at.desc())


        items = pagination(query, PAGE_SIZE, page)
        return render_template("admin/usergroup_list.html", items=items, keyword=name)


@admin_usergroup.route('/api/delete', methods=['POST'])
@login_required
def admin_usergroup_api_delete():
    id = request.json.get('id')

    if not id:
        return jsonify(code=400, msg='계정 id 를 입력해주세요')

    try:
        delete_usergroup(id)
        return jsonify(code=200, msg='Success')
    except Exception as e:
        print(traceback.print_exc())
        return jsonify(code=500, msg='{}'.format(e))
