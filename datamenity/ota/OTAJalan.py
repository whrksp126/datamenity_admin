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


class OTAJalan(OTABase):
    def get_hotel_id(self, args, url):
        s = url.split('/')[3]
        return ''.join([i for i in s if i.isdigit()])
    
    def scrape_prices_preprocess(self, args, url, hotel_id, checkin, checkout):
        hotel_id = self.get_hotel_id(args, url)
        session = requests.Session()

        try:
            url = 'https://www.jalan.net/yad{}/plan/'.format(hotel_id)
            response = self.requests_get(session, url, **args['proxy']['REQUESTS_PROXY'])
            
            if response.status_code == 403:
                return dict(code=403, rooms=[])
            
            response = response.content
            soup = BeautifulSoup(response, 'html.parser')

            title_items = soup.find_all('li', {'class': 'p-planCassette'})
            args['jalan_names'] = dict()
            for elem in title_items:
                plancode = elem['data-plancode']
                title = elem.find('p', {'class': 'p-searchResultItem__catchPhrase'}).get_text()
                print('##', title)
                title = title
                args['jalan_names'][plancode] = title.strip()
                print(plancode, title)
            
        except ExceptionReadTimeout as e:
            print(e)
            return dict(code=403, rooms=[])
        return dict(code=200)
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        hotel_id = self.get_hotel_id(args, url)
        session = requests.Session()

        json_params = {
            "targets":[hotel_id],
            "targetType":"HOTEL_ID",
            "nights":1,
            "rooms":[{"adults":2,"children1":0,"children2":0,"children3":0,"children4":0,"children5":0}],
            "hotelTypes":[],
            "extras":[],"minPrice":0,"maxPrice":999999,
            "checkInDate":checkin
        }

        try:
            headers = {
                'Accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
                'Content-Type': 'application/json',
                'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'x-api-key': 'XBgewN64LJ',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
            }

            response = self.requests_post(session, 'https://jlnzam.net/v2/search', json=json_params, headers=headers, **args['proxy']['REQUESTS_PROXY'])
            
            if response.status_code == 403:
                return dict(code=403, rooms=[])
            response = response.json()
        except ExceptionReadTimeout as e:
            print(e)
            return dict(code=403, rooms=[])
        
        if len(response['data']['hotels']) == 0:
            return dict(code=200, rooms=[])
        
        room_dict = dict()
        rooms = []
        for h in response['data']['hotels']:
            for r in h['roomPlans']:
                room_id = r['planId']
                room_name = args['jalan_names'][room_id]
                room_price = r['totalPrice']
                room_remain = r['stock']

                room_item = dict(
                    room_id=room_id, 
                    name=room_name, 
                    remain=room_remain,
                    price=room_price,
                )

                if room_id not in room_dict:
                    room_dict[room_id] = room_item
                elif room_dict[room_id]['price'] > room_price and room_remain > 0:
                    room_dict[room_id] = room_item
        
        for k, v in room_dict.items():
            rooms.append(v)

        return dict(
            code=200,
            rooms=rooms,
        )
        
    
    def scrape_reviews(self, output, args, url, hotel_id, page):
        return dict(code=404, comments=[], score=0, count=0)