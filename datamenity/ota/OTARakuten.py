from datamenity.ota.OTABase import OTABase, ExceptionReadTimeout
from datamenity.config import REQUESTS_PROXY, SELENIUM_PROXY

import requests
import datetime
import json
import time
import re
import browsercookie
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import random

class OTARakuten(OTABase):
    def get_hotel_id(self, args, url):
        return url.split('/')[-2]
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        session = requests.Session()
        hotel_id = self.get_hotel_id(args, url)

        in_y, in_m, in_d = checkin.split('-')
        out_y, out_m, out_d = checkout.split('-')
        in_y = int(in_y)
        in_m = int(in_m)
        in_d = int(in_d)
        out_y = int(out_y)
        out_m = int(out_m)
        out_d = int(out_d)

        new_url = 'https://hotel.travel.rakuten.co.jp/hotelinfo/plan/{}?f_teikei=&f_hizuke=&f_hak=&f_dai=japan&f_chu=kyoto&f_shou=shi&f_sai=B&f_tel=&f_target_flg=&f_tscm_flg=&f_p_no=&f_custom_code=&f_search_type=&f_camp_id=&f_static=1&f_rm_equip=&f_hi1={}&f_tuki1={}&f_nen1={}&f_hi2={}&f_tuki2={}&f_nen2={}&f_heya_su=1&f_otona_su=2'.format(hotel_id, in_d, in_m, in_y, out_d, out_m, out_y)
        try:
            result = self.requests_get(requests, new_url, **args['proxy']['REQUESTS_PROXY'])
            if result.status_code == 503:
                return dict(code=403, rooms=[])
            result = result.text
            soup = BeautifulSoup(result, 'html.parser')
            #room_items = soup.find_all('li', {'class':'rm-type-wrapper'})
            plan_thumbs = soup.find_all('li', {'class':'planThumb'})
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])

        room_dict = dict()
        rooms = []

        # 기본 객실 정보 조회
        for plan_item in plan_thumbs:
            title_item = plan_item.find('h4')
            default_name = title_item.contents[-1].strip()

            room_items = plan_item.find_all('li', {'class':'rm-type-wrapper'})
            for room_item in room_items:
                room_id = room_item['id']
                room_type = '-'.join(room_id.split('-')[1:])

                room_name = room_item.find('h6', {'data-locate':'roomType-name'})
                if room_name is None:
                    room_name = default_name
                else:
                    room_name = room_name.text.strip()
                summary = room_item.find('div', {'class':'prcSummary'})
                if not summary:
                    continue

                price = 1e10
                hidden_params = summary.find_all('input', {'type': 'hidden'})
                for p in hidden_params:
                    if ('totalPrice' in p['id']) and (price > int(p['value'])):
                        price = int(p['value'])
                
                coupon_popups = summary.find_all('div', {'class': 'coupon-popup'})
                for c in coupon_popups:
                    try:
                        if price > int(c['data-pr']):
                            price = int(c['data-pr'])
                    except:
                        pass
                
                if price >= 1e10:
                    return dict(code=510, rooms=[])
                
                if (room_type not in room_dict) or room_dict[room_type]['price'] > price:
                    room_dict[room_type] = dict(title=room_name, price=price, remain=1)
        
        # 쿠폰 req str 을 가져옴
        req_str_set = set()
        coupon_popup_items = soup.find_all('div', {'class':'coupon-popup'})
        for coupon_popup_item in coupon_popup_items:
            req_str = coupon_popup_item['data-reqstr']
            req_str_set.add(req_str)
        
        # 쿠폰 조회
        for req_str in req_str_set:
            headers = {
                'Accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
                'client-info': 'shopping-pwa,879ef38bdfb196f682493cb47d3f19dad7d5b5b6,us-west-2',
                'content-type': 'application/json',
                'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            }

            api_url = 'https://cs.api.travel.rakuten.co.jp/couponapi/hotel?requestString={}'.format(req_str)
            try:
                response = self.requests_get(session, api_url, headers=headers, **args['proxy']['REQUESTS_PROXY'])
                if response.status_code == 503:
                    return dict(code=403, rooms=[])
                response = response.json()
            except ExceptionReadTimeout:
                return dict(code=403, rooms=[])

            if response['status'] != 'OK':
                return dict(code=511, rooms=[])
            
            for r in response['results']:
                room_id = '{}'.format(r['rc'])

                if room_id not in room_dict:
                    continue

                sale_price = r['dp']

                if room_dict[room_id]['price'] > sale_price:
                    room_dict[room_id]['price'] = sale_price                

        for room_id, room_item in room_dict.items():
            rooms.append(dict(
                room_id=room_id, 
                name=room_item['title'], 
                remain=room_item['remain'],
                price=room_item['price'],
            ))

        return dict(
            code=200,
            rooms=rooms,
        )
        
    
    def scrape_reviews(self, output, args, url, hotel_id, page):
        return dict(code=404, comments=[], score=0, count=0)
