from flask import Blueprint, Flask, request, render_template, session
from datamenity.models import BannerType, User, UserGroup, UserHasCompetition, session_scope, CrawlerRule, Hotel, UserType, Environment, UserHasCrawlerRule
from datamenity.crawler import ota_code_to_str, ota_code_to_label
import copy
import json
import random
from datamenity.crawler import get_proxy_environment
import requests


def get_competition_hotel_list(user_id):
    result = []
    with session_scope() as session:
        comps = session.query(UserHasCompetition.competition_id, Hotel.name) \
            .join(Hotel, UserHasCompetition.competition_id == Hotel.id) \
            .filter(UserHasCompetition.user_id == user_id) \
            .order_by(UserHasCompetition.priority).all()
        
        for c in comps:
            result.append(dict(id=c.competition_id, name=c.name))
        
        return result


def get_crawler_rules():
    result = dict()
    with session_scope() as session:
        rules = session.query(CrawlerRule).all()
        for rule in rules:
            item = rule.todict()
            result[item['id']] = item['description']
        return result


def get_supported_ota(hotel_id):
    result = dict()
    with session_scope() as session:
        hotel_item = session.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel_item:
            return result
        link = json.loads(hotel_item.link)
        for idx in range(len(ota_code_to_label) + 1):
            if str(idx) in link:
                result[idx] = ota_code_to_label[idx]
        return result


def get_hotels():
    with session_scope() as session:
        hotels = session.query(Hotel).all()
        result = dict()
        for h in hotels:
            result[h.id] = h.name
        return result


def get_user_types():
    with session_scope() as session:
        user_types = session.query(UserType).all()
        result = dict()
        for u in user_types:
            result[u.id] = u.name
        return result


def get_users():
    with session_scope() as session:
        users = session.query(User).all()
        result = dict()
        for u in users:
            result[u.id] = u.name
        return result


def get_usergroups():
    with session_scope() as session:
        usergroups = session.query(UserGroup).all()
        result = dict()
        for u in usergroups:
            result[u.id] = u.name
        return result


def get_banner_types():
    with session_scope() as session:
        banner_types = session.query(BannerType).all()
        result = dict()
        for b in banner_types:
            result[b.id] = b.name
        return result


def pagination(items, perpage, page):
    count = items.count()
    last_page = int(count / perpage) + 1
    list_start = int((page - 1) / 10) * 10 + 1
    list_end = min(list_start + 9, last_page)
    
    items = items.offset((page - 1) * perpage).limit(perpage).all()
    return dict(
        items=[i.todict() for i in items],
        page=page,
        page_list=[i for i in range(list_start, list_end + 1)],
        prev10=None if page <= 10 else list_start - 1,
        next10=list_end + 1 if last_page > list_end else None,
        count=count
    )


def union_rule(rule_list, rule_item):
    rule_list_len = len(rule_list)
    i = 0

    while i < rule_list_len:
        r = rule_list[i]
        if r['range'] < rule_item['range']:
            r['time'] |= rule_item['time']
        elif r['range'] == rule_item['range']:
            r['time'] |= rule_item['time']
            return rule_list
        else:
            break
        
        i += 1
    
    rule_list.insert(i, rule_item)

    # 정책이 포함관계에 있을 때, 줄임
    i = len(rule_list) - 2
    while i >= 0:
        if rule_list[i]['time'] | rule_list[i + 1]['time'] == rule_list[i + 1]['time']:
            rule_list = rule_list[:i] + rule_list[i+1:]
        i -= 1

    return rule_list


def get_crawler_price_works(hour):
    ota_len = len(ota_code_to_str)
    with session_scope() as session:
        # 호텔의 OTA 정책을 모두 가져옵니다
        hotel_items = session.query(Hotel.id, Hotel.link).all()

        ota_rule_dict = dict()
        for h in hotel_items:
            ota_rule_dict[h.id] = dict(link=h.link, otas=0)
        
        # 유저의 OTA 정책을 모두 가져옵니다
        user_items = session.query(User.hotel_id, User.otas).all()
        for u in user_items:
            if u.hotel_id is None:
                continue
            ota_rule_dict[u.hotel_id]['otas'] = u.otas

        # 호텔의 크롤러 정책을 모두 가져옵니다
        rule_items = session.query(UserHasCrawlerRule.user_id, User.hotel_id, CrawlerRule.range, CrawlerRule.time) \
            .join(CrawlerRule, UserHasCrawlerRule.crawler_rule_id == CrawlerRule.id) \
            .join(User, UserHasCrawlerRule.user_id == User.id) \
            .all()
        
        rule_dict = dict()
        for r in rule_items:
            if r.hotel_id is None:
                continue
            if r.hotel_id not in rule_dict:
                rule_dict[r.hotel_id] = []
            if ((r.time | 1) & (1 << hour)) > 0:
                rule_dict[r.hotel_id] = union_rule(rule_dict[r.hotel_id], dict(time=r.time, range=r.range))

        # 정책 복제
        result_dict = copy.deepcopy(rule_dict)
        result_ota_dict = copy.deepcopy(ota_rule_dict)

        # 경쟁사로 부터 간접 지정된 룰을 모두 가져옵니다
        competitions = session.query(UserHasCompetition.competition_id, User.hotel_id).join(User, User.id == UserHasCompetition.user_id).all()
        for c in competitions:
            if c.competition_id not in result_dict:
                result_dict[c.competition_id] = []
            if c.hotel_id in rule_dict:
                for rr in rule_dict[c.hotel_id]:
                    if c.competition_id not in result_dict:
                        result_dict[c.competition_id] = []
                    result_dict[c.competition_id] = union_rule(result_dict[c.competition_id], rr)
                    result_ota_dict[c.competition_id]['otas'] |= ota_rule_dict[c.hotel_id]['otas']
        
        # 정책을 리스트로 추출
        result = []
        for hotel_id, crawler_rule in result_dict.items():
            otas = result_ota_dict[hotel_id]['otas']
            try:
                link = json.loads(result_ota_dict[hotel_id]['link'])
            except Exception:
                link = {}
            
            for i in range(ota_len):
                if (otas & (1 << i)) > 0:
                    if str(i) not in link:
                        continue
                    result.append(dict(id=hotel_id, ota=i, rule=crawler_rule, link=link.get(str(i), {})))

        return result


def get_crawler_review_works(hour):
    ota_len = len(ota_code_to_str)
    with session_scope() as session:
        # 호텔의 OTA 정책을 모두 가져옵니다
        hotel_items = session.query(User.hotel_id, User.otas, Hotel.link) \
            .join(Hotel, Hotel.id == User.hotel_id).all()

        # 정책을 리스트로 추출
        result = []
        for h in hotel_items:
            try:
                link = json.loads(h['link'])
            except Exception:
                link = {}

            for i in range(ota_len):
                if (h.otas & (1 << i)) > 0:
                    result.append(dict(id=h.hotel_id, ota=i, rule={}, link=link.get(str(i), {})))

    return result


def get_proxy_args():
    args = dict(proxy=get_proxy_environment())
    return args


def send_message_to_slack_server(contents):
    url = 'https://hooks.slack.com/services/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'
    payload = {
        "icon_url": "https://app.datamenity.com/static/images/favicon.ico",
        'username': 'Datamenity Crawler Bot',
        'text': contents,
        'type': 'mrkdwn',
    }

    requests.post(url, json=payload)
