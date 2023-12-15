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

pattern_room_id1 = re.compile('^pop_room_detail\((.*)\);$')
pattern_room_id = re.compile('armgno=([0-9]*)')


class OTAGoodchoice(OTABase):
    def get_hotel_id(self, args, url):
        parts = urlparse(url)
        qs = dict(parse_qsl(parts.query))
        return qs['ano']
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        parts = urlparse(url)
        qs = dict(parse_qsl(parts.query))
        qs['sel_date'] = checkin
        qs['sel_date2'] = checkout
        parts = parts._replace(query=urlencode(qs))
        new_url = urlunparse(parts)

        try:
            result = self.requests_get(requests, new_url).text
            soup = BeautifulSoup(result, 'html.parser')
            items = soup.find_all('div', {'class':'room'})
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])

        rooms = []
        for elem in items:
            price_elems = elem.find_all('div', {'class': 'half'})
            if len(price_elems) == 0:
                stay_elem = elem
                detail_elem = stay_elem.find('button', {'class': 'gra_left_right_red'})
                if not detail_elem:
                    continue
                detail_elem = pattern_room_id.search(detail_elem['onclick'])
            else:
                stay_elem = price_elems[-1]
                detail_elem = stay_elem.find('button', {'class': 'gra_left_right_red'})
                if not detail_elem:
                    continue
                detail_elem = pattern_room_id.search(stay_elem.find('button')['onclick'])

            if stay_elem.find('b', {'style': 'color: rgba(0,0,0,1)'}):                
                price_elem = stay_elem.find('b', {'style': 'color: rgba(0,0,0,1)'})
            elif stay_elem.find('b', {'style': 'color: rgba(255,92,92,1)'}):  
                price_elem = stay_elem.find('b', {'style': 'color: rgba(255,92,92,1)'})

            if not price_elem:
                continue
            price_raw = price_elem.get_text().strip()
            if price_raw[-1] != '원':
                continue
            price_raw = price_raw[:-1].replace(',', '')
            
            room_id = detail_elem.group(1)
            room_name = elem.find('strong', {'class': 'title'}).get_text()
            room_price = int(price_raw)
            if room_price == 0:
                continue
             
            price_elem = stay_elem.find('button', {'class': 'gra_left_right_red'})
            room_remain = 0 if not price_elem else 1
             
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
        result = []

        try:
            reviews = self.requests_post(requests, 'https://www.goodchoice.kr/product/get_review_non', data={'page': page, 'ano': hotel_id}).json()
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])

        for r in reviews['result']['items']:
            reply = []
            if len(r['o_comm']) > 0:
                for o in r['o_comm']:
                    reply.append(dict(
                        author='' if o['unick'] is None else o['unick'],
                        content=o['aep_cmcont'],
                        created_at=None
                    ))
            
            result.append(dict(
                id=r['aepreg'],
                author='' if r['unick'] is None else r['unick'],
                content='{}\n{}'.format(r['epilrate_textinfo'], r['aepcont']),
                category='기타',
                score=float(r['epilrate']),
                created_at=datetime.datetime.fromtimestamp(r['aepreg']),
                reply=reply
            ))
        
        # 리뷰 개수, 평점
        score = reviews['result']['rateavg']
        count = reviews['result']['count']
 
        return dict(code=200, comments=result, score=score, count=count)
