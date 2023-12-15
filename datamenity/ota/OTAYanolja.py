import traceback
from datamenity.ota.OTABase import OTABase, ExceptionReadTimeout
from datamenity.config import REQUESTS_PROXY, SELENIUM_PROXY

import requests
import datetime
import json
import time
import browsercookie


class OTAYanolja(OTABase):
    def get_hotel_id(self, args, url):
        return url.split('/')[-1].split('?')[0].split('#')[0]

    def scrape_prices_preprocess(self, args, url, hotel_id, checkin, checkout):
        session = requests.session()
        try:
            resp = self.requests_get(session, 'https://place-site.yanolja.com/places/{}'.format(hotel_id))
            if resp.status_code == 404:
                raise Exception('존재하지 않는 호텔')
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
        args['session'] = session
        return dict(code=200)
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        hotel_id = self.get_hotel_id(args, url)
        requests_session = args['session']

        try:        
            resp = self.requests_post(requests_session, 'https://place-site.yanolja.com/api/stay.properties.detail.get?batch=1', headers={
                'Accept': 'application/json, text/plain, */*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Connection': 'keep-alive',
                'Host': 'place-site.yanolja.com',
                'Referer': 'https://place-site.yanolja.com/places/{}'.format(hotel_id),
                'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-cha-ua-platform': 'Windows',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }, **args['proxy']['REQUESTS_PROXY'], json={"0":{"propertyId":hotel_id,"query":{"checkInDate":checkin,"checkOutDate":checkout,"adultPax":2,"childrenAges":[]}}}).json()
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])

        rooms = []
        for r in resp[0]['result']['data']['roomTypes']:
            min_price = 1e9
            room_price = 1e9
            room_remain = 0
            for use_type in r['useTypes']:
                if use_type['useTypeTitle'] == '대실':
                    continue
                remain = 0 if use_type['soldOutLabel'] == '판매완료' else 1
                min_price = min(min_price, use_type['minAverageRate'])
                if remain > 0:
                    if room_price > use_type['minAverageRate']:
                        room_price = use_type['minAverageRate']
                        room_remain = remain
            
            rooms.append(dict(
                room_id=r['roomTypeId'], 
                name='{} - {}'.format(r['roomTypeName'].strip(), '' if 'roomTypeSubTitle' not in r or r['roomTypeSubTitle'] is None else r['roomTypeSubTitle'].strip()), 
                remain=room_remain,
                price=room_price if room_remain > 0 else min_price,
            ))
 
        return dict(
            code=200,
            rooms=rooms,
        )
    
    def scrape_reviews(self, output, args, url, hotel_id, page):
        result = []

        try:
            reviews = self.requests_get(requests, 'https://domestic-order-site.yanolja.com/dos-server/review/properties/{}/reviews?size=20&sort=best:desc&page={}'.format(hotel_id, page)).json()
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
 
        for r in reviews['reviews']:
            reply = []
            if 'comment' in r and r['comment'] is not None:
                reply.append(dict(
                    author='숙소 답변',
                    content=r['comment']['content'],
                    created_at=datetime.datetime.strptime(r['comment']['createdAt'], '%Y-%m-%dT%H:%M:%S')
                ))
             
            result.append(dict(
                id=r['id'],
                author=r['member']['nickname'],
                content=r['userContent']['content'],
                category='기타',
                score=r['userContent']['totalScore'] * 2,
                created_at=datetime.datetime.strptime(r['createdAt'], '%Y-%m-%dT%H:%M:%S'),
                reply=reply
            ))

        # 리뷰 개수, 평점
        score = None
        count = None

        try:
            resp = self.requests_get(requests, 'https://place-site.yanolja.com/api/stay.properties.review-top.get?batch=1&input={"0":{"propertyId":' + hotel_id + ',"query":{"roomTypeIds":""}}}', **args['proxy']['REQUESTS_PROXY']).json()
            meta_data = resp[0]['result']['data']
            score = meta_data['averageTotalScore'] * 2
            count = meta_data['reviewCount']
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
 
        return dict(code=200, comments=result, score=score, count=count)
