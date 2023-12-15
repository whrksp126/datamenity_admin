from flask import Blueprint, Flask, request, render_template, session, url_for
from sqlalchemy import null
from datamenity.models import LogCrawler, LogScheduler, session_scope, User
from flask_login import login_required, current_user, logout_user

from datamenity.common import get_hotels, get_supported_ota
from datetime import datetime, timedelta

admin_log = Blueprint('admin_log', __name__, url_prefix='/log/')


@admin_log.route('/crawler', methods=['GET'])
@login_required
def admin_log_crawler_list():
    with session_scope () as session:
        items = session.query(LogCrawler).filter(LogCrawler.hotel_id<120)\
                                         .filter(LogCrawler.error!="")\
                                         .filter(LogCrawler.output!="").all()
        error_count = session.query(LogCrawler).filter(LogCrawler.error!="").count()
        return render_template("admin/log_crawler.html", items=items, error_count=error_count)


@admin_log.route('/scheduler', methods=['GET'])
@login_required
def admin_log_scheduler_list():
    with session_scope () as session:
        items = session.query(LogScheduler).filter(LogScheduler.crawler_type=='price')\
                                           .filter(LogScheduler.updated_at.is_(None)).all()
        return render_template("admin/log_scheduler.html", items=items)


@admin_log.route('/select_crawler', methods=['GET'])
@login_required
def admin_select_crawler():
    hotel_id = request.args.get('hotel_id')
    ota = request.args.get("ota")
    hour = request.args.get("hour")

    # hotel_id
    try:
        hotel_id = int(hotel_id)
    except Exception:
        hotel_id = None

    if hotel_id is None:
        return render_template('popup.html', msg='호텔 ID가 없습니다.')

    hotels = get_hotels()

    # ota
    try:
        ota = int(ota)
    except Exception:
        ota = None

    support_ota_dict = get_supported_ota(hotel_id)
    if ota is None:
        try:
            ota = list(support_ota_dict.keys())[0]
        except Exception:
            return render_template('popup.html', msg='OTA가 없습니다.')
    
    # hour
    try:
        hour = int(hour)
    except Exception:
        hour = None
    
    if hour is None:
        kst_now = datetime.utcnow() + timedelta(hours=9)
        hour = kst_now - timedelta(hours=1)
    
    with session_scope () as session:
        item = session.query(LogCrawler) \
            .filter(LogCrawler.hotel_id == hotel_id) \
            .filter(LogCrawler.ota == ota) \
            .filter(LogCrawler.hour == hour).first()

        return render_template("admin/select_crawler.html", hotels=hotels, support_ota_dict=support_ota_dict, hotel_id=hotel_id, ota=ota, hour=hour, item=item)
