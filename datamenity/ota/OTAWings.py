from datamenity.ota.OTABase import OTABase, ExceptionReadTimeout
from datamenity.config import REQUESTS_PROXY, SELENIUM_PROXY

import requests
import datetime
import json
import time
import browsercookie
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from bs4 import BeautifulSoup
import re

pattern_session_obj = re.compile('setSessionObj\(([^\)]*)\)')


def replace_price(txt):
    txt = re.sub(r'[^0-9]', '', txt.replace(',', ''))
    return int(float(txt))


class OTAWings(OTABase):
    def get_hotel_id(self, args, url):
        parts = urlparse(url)
        return parts.path.split('/')[1]
    
    def scrape_prices_preprocess(self, args, url, hotel_id, checkin, checkout):
        session = requests.Session()
        args['session'] = session
        
        parts = urlparse(url)
        qs = dict(parse_qsl(parts.query))
        qs['check_in'] = checkin
        qs['check_out'] = checkout
        parts = parts._replace(query=urlencode(qs))
        new_url = urlunparse(parts)
        resp = session.get(new_url).text

        m = pattern_session_obj.search(resp)
        session_obj = json.loads(m.group(1))
        args['session_obj'] = session_obj
        return dict(code=200)
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        session = args['session']
        session_obj = args['session_obj']
        
        parameter = {"pms_seq_no":session_obj['SS_PMS_SEQ_NO'],"check_in":checkin,"check_out":checkout,"rooms":"1","adult":"2","children":"0","channel_code":"WINGS_B2C","lang_type":"KO","prm_seq_no":"","cpny_seq_no":"","mmbrs_seq_no":"","ext_channel_seq_no":""}
        parameter.update(session_obj)
        parameter.update({'SS_MEMBER_INFO':''})

        form_data = {"parameter": json.dumps(parameter)}

        try:
            resp = self.requests_post(requests, 'https://be4.wingsbooking.com/{}/user/hotel/roomList'.format(hotel_id), data=form_data, headers={
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }).json()
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
        
        rooms = []
        for r in resp['result']:
            room_id = '{}'.format(r['room_seq_no'])
            room_name = r['room_name']
            room_remain = 1
            room_price = r['firstday_rate']
             
            rooms.append(dict(
                room_id=room_id, 
                name=room_name, 
                remain=room_remain,
                price=room_price,
            ))
 
        return dict(
            code=200,
            rooms=rooms,
        )
    
    def scrape_reviews(self, output, args, url, hotel_id, page):
        return dict(code=200, comments=[])
