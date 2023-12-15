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


def replace_price(txt):
    txt = re.sub(r'[^0-9]', '', txt)
    return int(float(txt))


class OTAKensington(OTABase):
    def get_hotel_id(self, args, url):
        parts = urlparse(url)
        qs = dict(parse_qsl(parts.query))
        return qs['search_bran_cd']
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        try:
            resp = self.requests_get(requests, 'https://www.kensington.co.kr/reservation/result_room?search_bran_cd={}&search_stay_start_dt={}&search_stay_end_dt={}&search_room_cnt=1&search_people_adult_cnt=2&search_people_adult_cnts=2&search_people_child_cnt=0&search_people_child_cnts=0&search_code_type=&search_code=&pack_cd=&room_type_cd=&pay_type=P&memflag='.format(hotel_id, checkin, checkout))
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])
        
        soup = BeautifulSoup(resp.content, 'html.parser', from_encoding='utf-8')
        items = soup.find("ul", attrs={"class", "item_list"})
        room_items = items.find_all("li", attrs={"class", "item"})

        rooms = []
        for room in room_items:
            title = room.find("div", attrs={"class", "title"}).get_text()
            price = replace_price(room.find("div", attrs={"class", "discount_price"}).get_text())
            room_id = room.find('i')['data-room-type-cd']

            rooms.append(dict(
                room_id=room_id, 
                name=title, 
                remain=1,
                price=price,
            ))
        
        return dict(
            code=200,
            rooms=rooms,
        )
    
    def scrape_reviews(self, output, args, url, hotel_id, page):
        return dict(code=200, comments=[])
