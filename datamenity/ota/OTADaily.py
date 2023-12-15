from datamenity.ota.OTABase import OTABase, ExceptionReadTimeout
from datamenity.config import REQUESTS_PROXY, SELENIUM_PROXY

import requests
import datetime
import json
import time
import browsercookie


class OTADaily(OTABase):
    def get_hotel_id(self, args, url):
        return url.split('/')[-1].split('?')[0]
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        requests_session = requests.Session()

        if '/hotels/' in url:
            try:
                resp = self.requests_get(requests_session, 'https://www.dailyhotel.com/newdelhi/goodnight/api/v10/stay/pdp/{}?dateCheckIn={}&stays=1&persons=2'.format(hotel_id, checkin), headers={
                    'Accept': 'application/json;charset=UTF-8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
                    'app-version': '3.3.2',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json',
                    'Host': 'www.dailyhotel.com',
                    'Os-Type': 'PC_WEB',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
                }, **args['proxy']['REQUESTS_PROXY']).json()
            except ExceptionReadTimeout:
                return dict(code=403, rooms=[])
            
            if resp['msgCode'] == 4:        # 업체의 사정으로 판매중단한 경우
                return dict(code=200, rooms=[])

            if resp is None or resp.get('data') is None or resp['data'].get('response') is None or resp['data']['response'].get('rooms') is None:
                return dict(code=504, rooms=[])
            
            rooms = []
            for label in resp['data']['response']['rooms']['labels']:
                roomname = label['roomName']
                for rateplan in label['rateplans']:
                    # 숙박 아니면 건너 띔
                    if rateplan['useType'] != 'OVERNIGHT':
                        continue

                    # 매진시 건너 띔
                    if rateplan['soldOut']:
                        continue
                
                    rooms.append(dict(
                        room_id=rateplan['rateplanIdx'], 
                        name=roomname, 
                        remain=0 if rateplan['soldOut'] else 1,
                        price=rateplan['totalSellingPrice'],
                    ))
        elif '/stays/' in url:
            try:
                resp = self.requests_get(requests_session, 'https://www.dailyhotel.com/newdelhi/goodnight/api/v9/hotel/{}?stays=1&dateCheckIn={}&regionStayType=all'.format(hotel_id, checkin), headers={
                    'Accept': 'application/json;charset=UTF-8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
                    'app-version': '3.3.3',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json',
                    'Host': 'www.dailyhotel.com',
                    'Os-Type': 'PC_WEB',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
                }, **args['proxy']['REQUESTS_PROXY']).json()
            except ExceptionReadTimeout:
                return dict(code=403, rooms=[])
            
            if resp['msgCode'] == 4:        # 업체의 사정으로 판매중단한 경우
                return dict(code=200, rooms=[])

            if resp is None or resp.get('data') is None or resp['data'].get('rooms') is None:
                return dict(code=504, rooms=[])
            
            rooms = []
            for r in resp['data']['rooms']:
                if r['amount']['discountTotal'] is None:
                    continue
                
                rooms.append(dict(
                    room_id=r['roomIdx'], 
                    name=r['roomName'], 
                    remain=0 if r['soldOut'] else 1,
                    price=r['amount']['discountTotal'],
                ))
 
        return dict(
            code=200,
            rooms=rooms,
        )
    
    def scrape_reviews(self, output, args, url, hotel_id, page):
        result = []

        try:
            reviews = self.requests_get(requests, 'https://www.dailyhotel.com/newdelhi/goodnight/api/v10/reviews/HOTEL/{}/contents?page={}'.format(hotel_id, page), **args['proxy']['REQUESTS_PROXY']).json()
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
 
        for r in reviews['data']['contents']:
            reply = []
            if r['reviewReply'] is not None:
                reply.append(dict(
                    author=r['reviewReply']['replier'],
                    content=r['reviewReply']['reply'],
                    created_at=datetime.datetime.strptime(r['reviewReply']['repliedAt'], '%Y.%m.%d')
                ))
             
            result.append(dict(
                id=r['reviewIdx'],
                author=r['nickname'],
                content=r['comment'],
                category='기타',
                score=r['avgScore'] * 2,
                created_at=datetime.datetime.strptime(r['reviewAt'], '%Y.%m.%d'),
                reply=reply
            ))
        
        # 리뷰 개수, 평점
        score = None
        count = None

        try:
            resp = self.requests_get(requests, 'https://www.dailyhotel.com/newdelhi/goodnight/api/v9/hotel/{}?stays=1&dateCheckIn=2022-07-12&regionStayType=all'.format(hotel_id), **args['proxy']['REQUESTS_PROXY']).json()

            rating_item = resp['data']['rating']
            count = rating_item['persons']
            score = rating_item['values'] / 10
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
        except Exception:
            pass
        
        return dict(code=200, comments=result, score=score, count=count)
