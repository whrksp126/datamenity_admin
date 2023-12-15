from os import remove
import uuid
from flask import Flask, Blueprint, request, url_for, render_template, jsonify, redirect
from flask_login import login_required, current_user, logout_user
import traceback

import boto3

from datamenity.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BUCKET_NAME, PAGE_SIZE

from datamenity.models import Banner, BannerType, UserGroup, UserGroupHasBanner, UserToUserGroup, session_scope
from datamenity.common import get_banner_types, get_crawler_rules, get_usergroups, get_users, pagination, get_user_types, get_hotels


admin_banner = Blueprint('admin_banner', __name__, url_prefix='/banner/')


def s3_connection():
    try:
        s3 = boto3.client(
                        service_name = 's3',
                        region_name = "ap-northeast-2",
                        aws_access_key_id = AWS_ACCESS_KEY_ID,
                        aws_secret_access_key = AWS_SECRET_ACCESS_KEY)
    except Exception as e:
        print(e)
    else:
        print("s3 bucket connected!")
        return s3

def s3_get_image_url(s3, filename):
    location = s3.get_bucket_location(Bucket=BUCKET_NAME)["LocationConstraint"]
    return f"https://s3.ap-northeast-2.amazonaws.com/admin.bannerimg/{filename}"

def delete_s3_bannerimg(url):
    try:
        file_name = url[56:]
        print(file_name)
        s3 = s3_connection()
        s3.delete_object(Bucket=BUCKET_NAME, Key=file_name)
    except Exception as e:
        print(e)

def delete_banner(id):
    with session_scope() as session:
        banner_item = session.query(Banner).filter(Banner.id == id).first()
        if not banner_item:
            return jsonify(code=404, msg='존재하지 않는 계정입니다.')

        url = banner_item.url
        session.query(UserGroupHasBanner).filter(UserGroupHasBanner.banner_id == id).delete()
        session.query(Banner).filter(Banner.id == id).delete()
        session.commit()

        delete_s3_bannerimg(url)



@admin_banner.route('/create', methods=['GET'])
@login_required
def admin_banner_create():
    with session_scope() as session:
        banner_types = get_banner_types()
        usergroups = get_usergroups()
        
    return render_template("admin/banner_create.html", banner_types=banner_types, usergroups=usergroups)


@admin_banner.route('/edit', methods=['GET'])
@login_required
def admin_banner_edit():
    banner_id = request.args.get('id', type=int, default=None)

    if not banner_id:
        return render_template('popup.html', msg='배너 ID 를 입력해주세요')

    with session_scope() as session:
        banner_item = session.query(Banner).filter(Banner.id == banner_id).first()
        usergroup_has_banner_item = session.query(UserGroupHasBanner).filter(UserGroupHasBanner.banner_id == banner_id).first()
        banner_types = get_banner_types()
        usergroups = get_usergroups()

        if not banner_id:
            return render_template('popup.html', msg='존재하지 않는 배너입니다.')
        return render_template("admin/banner_edit.html", banner_item=banner_item, banner_types=banner_types, usergroups=usergroups, usergroup_has_banner_item=usergroup_has_banner_item)


@admin_banner.route('/api/create_or_update', methods=['POST'])
@login_required
def admin_banner_create_or_update():
    banner_img = request.files['banner_img']
    file_name =  str(banner_img.filename)
    banner_img.save('datamenity/images/'+file_name)

    banner_id = request.form.get('banner_id')
    banner_name = request.form.get('banner_name')
    banner_type = request.form.get('banner_type')
    started_at = request.form.get('started_at')
    ended_at = request.form.get('ended_at')
    background_color = request.form.get('bg_color')
    usergroup = request.form.get('usergroup')
    link = request.form.get('link')
    
    banner_item_id = None

    s3 = s3_connection()
    s3_filename = str(uuid.uuid4())
    try:
        s3.upload_file("datamenity/images/"+file_name, BUCKET_NAME, s3_filename)
        remove("datamenity/images/"+file_name)
    except Exception as e:
        print(e)
    try:
        url = s3_get_image_url(s3, s3_filename)
    except Exception as e:
        print(e)

    try:
        with session_scope() as session:
            if banner_id is None:   # create
                banner_item = Banner(banner_name,banner_type,url,started_at,ended_at,background_color,link)
                session.add(banner_item)
                session.commit()
                session.refresh(banner_item)
                banner_item_id = banner_item.id

                usergroup_has_banner_item = UserGroupHasBanner(usergroup, banner_item_id)
                session.add(usergroup_has_banner_item)
                session.commit()
                session.refresh(usergroup_has_banner_item)

            else:                   # update
                banner_item = session.query(Banner).filter(Banner.id == banner_id).first()
                if not banner_item:
                    return render_template("popup.html", msg="배너가 존재하지 않습니다.")

                deleted_url = banner_item.url
                delete_s3_bannerimg(deleted_url)

                banner_item.name = banner_name
                banner_item.banner_type = banner_type
                banner_item.url = url
                banner_item.started_at = started_at
                banner_item.ended_at = ended_at
                banner_item.background_color = background_color
                banner_item.link = link
                session.commit()
                
                 # 배너 그룹 추가
                session.query(UserGroupHasBanner).filter(UserGroupHasBanner.banner_id == banner_id).delete()
                session.add(UserGroupHasBanner(usergroup , banner_id))
                session.commit()

            return render_template('popup.html', msg='배너를 생성하였습니다', redirect=url_for('admin_banner.admin_banner_list'))
    except Exception as e:
        # 생성하다가 실패한 경우, mysql 계정이 생성되었다면, 관련 데이터를 모두 지운다
        if banner_id is None and banner_item_id is not None:
            delete_banner(banner_item_id)
        return render_template("popup.html", msg="배너 생성 실패({})".format(traceback.print_exc()))


@admin_banner.route('/list', methods=['GET'])
@login_required
def admin_banner_list():
    page = request.args.get('page', type=int, default=1)
    name = request.args.get('name', '')
    with session_scope() as session:
        query = session.query(Banner)\
                    .filter(Banner.name.ilike('%{}%'.format(name.replace(' ', '%'))))\
                    .order_by(Banner.created_at.desc())

        items = pagination(query, PAGE_SIZE, page)
        return render_template("admin/banner_list.html", items=items, keyword=name)


@admin_banner.route('/api/delete', methods=['POST'])
@login_required
def admin_banner_api_delete():
    id = request.json.get('id')

    if not id:
        return jsonify(code=400, msg='계정 id 를 입력해주세요')

    try:
        delete_banner(id)
        return jsonify(code=200, msg='Success')
    except Exception as e:
        print(traceback.print_exc())
        return jsonify(code=500, msg='{}'.format(e))