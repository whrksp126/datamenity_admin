import traceback
from datamenity.ota.OTABase import OTABase, ExceptionReadTimeout
from datamenity.config import REQUESTS_PROXY, SELENIUM_PROXY

import requests
import datetime
import json
import time
import browsercookie
import re
from bs4 import BeautifulSoup
import pytz

pattern_api_url = re.compile('hotel_id\=([0-9]*)\&')


class OTAAgoda(OTABase):
    def get_hotel_id(self, args, url):
        chrome_cookies = browsercookie.chrome()

        try:
            resp = self.requests_get(requests, url, cookies=chrome_cookies, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
                'ag-language-id': '9',
                'ag-language-locale': 'ko-kr',
            }).text
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
        
        m = pattern_api_url.search(resp)
        hotel_id = m.group(1)
        return hotel_id

    def scrape_prices_preprocess(self, args, url, hotel_id, checkin, checkout):
        session = requests.session()

        try:
            resp = self.requests_get(session, 'https://www.agoda.com/api/cronos/layout/currency/set?currencyId=26', headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
                'ag-language-id': '9',
                'ag-language-locale': 'ko-kr',
                'cr-currency-code': 'KRW',
                'cr-currency-id': '26',
            }, **args['proxy']['REQUESTS_PROXY'])
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
            
        args['session'] = session
        return dict(code=200)
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        session = args['session']
        chrome_cookies = browsercookie.chrome()
        hotel_property_url = 'https://www.agoda.com/api/cronos/property/BelowFoldParams/GetSecondaryData?finalPriceView=1&isShowMobileAppPrice=false&cid=-1&numberOfBedrooms=&familyMode=false&adults=2&children=0&rooms=1&maxRooms=0&checkIn={}&isCalendarCallout=false&childAges=&numberOfGuest=0&missingChildAges=false&travellerType=-1&showReviewSubmissionEntry=false&currencyCode=KRW&isFreeOccSearch=false&isCityHaveAsq=false&los=1&hotel_id={}&all=false&price_view=1'.format(checkin, hotel_id)
        
        try:
            hotel_property = self.requests_get(session, hotel_property_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
                'ag-language-id': '9',
                'ag-language-locale': 'ko-kr',
                'cr-currency-code': 'KRW',
                'cr-currency-id': '26',
            }, **args['proxy']['REQUESTS_PROXY']).json()
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])
        except requests.exceptions.JSONDecodeError:
            return dict(code=403, rooms=[])

        rooms = []
        if 'roomGridData' in hotel_property and 'masterRooms' in hotel_property['roomGridData'] and hotel_property['roomGridData']['masterRooms'] is not None:
            for r in hotel_property['roomGridData']['masterRooms']:
                room_id = '{}'.format(r['id'])
                room_name = r['name']
                room_remain = r['maxOccupancy']
                if len(r['rooms']) == 0:
                    continue
    
                room_price = 1e10
                for rr in r['rooms']:
                    room_price = min(room_price, rr['pricing']['displayPriceExcludeExtraBed'])
                    #room_price = min(room_price, rr['pricing']['displayPrice'])    # 세금 및 봉사료 제외가격
    
                if room_price >= 1e10:
                    continue
    
                #room_image = [img for img in r['images']]
                
                rooms.append(dict(
                    room_id=room_id, 
                    name=room_name, 
                    remain=room_remain,
                    price=int(room_price),
                ))
         
        # soldout
        if 'soldOutRooms' in hotel_property:
            for r in hotel_property['soldOutRooms']:
                room_id = '{}'.format(r['masterRoomId'])
                room_name = r['masterRoomName']
                room_remain = 0
                room_price = int(r['exclusivePrice'])
                #room_image = r['roomThumbnail']
 
                rooms.append(dict(
                    room_id=room_id, 
                    name=room_name, 
                    remain=room_remain,
                    price=int(room_price),
                ))
 
        return dict(
            code=200,
            rooms=rooms,
        )
    
    def scrape_reviews(self, output, args, url, hotel_id, page):
        chrome_cookies = browsercookie.chrome()
        result = []
        data = dict(
            demographicId=0,
            filters=dict(language=[], room=[]),
            hotelId=hotel_id,
            isCrawlablePage=True,
            isReviewPage=False,
            page=page,
            pageSize=20,
            providerId=332,
            providerIds=[332],
            searchFilters=[],
            searchKeyword='',
            sorting=1,
        )

        session = requests.Session()

        try:
            reviews = self.requests_post(session, 'https://www.agoda.com/api/cronos/property/review/ReviewComments', json=data, cookies=chrome_cookies, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
                'ag-language-id': '9',
                'ag-language-locale': 'ko-kr',
            }).json()
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
        except Exception:
            return dict(code=500, comments=[])
        
        for r in reviews['comments']:
            #print('##', r)
            reply = []
            if r['isShowReviewResponse']:
                try:
                    created_at=datetime.datetime.strptime(r['responseDate'], '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(pytz.UTC).replace(tzinfo=None)
                except:
                    created_at=datetime.datetime.strptime(r['responseDate'], '%Y-%m-%dT%H:%M:%S%z').astimezone(pytz.UTC).replace(tzinfo=None)
                reply.append(dict(
                    author=r['responderName'],
                    content=r['responseText'],
                    created_at=created_at
                ))

            try:
                created_at=datetime.datetime.strptime(r['reviewDate'], '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(pytz.UTC).replace(tzinfo=None)
            except:
                created_at=datetime.datetime.strptime(r['reviewDate'], '%Y-%m-%dT%H:%M:%S%z').astimezone(pytz.UTC).replace(tzinfo=None)
            
            group_name = r['reviewerInfo']['reviewGroupName']
            if '나홀로 여행' in group_name:
                category = '나홀로 여행'
            elif '커플' in group_name:
                category = '커플'
            elif '친구' in group_name:
                category = '친구'
            elif '가족' in group_name:
                category = '가족'
            else:
                category = '기타'
            
            result.append(dict(
                id=r['hotelReviewId'],
                author=r['reviewerInfo']['displayMemberName'],
                content='{}\n{}'.format(r['reviewTitle'], r['reviewComments']),
                score=r['rating'],
                category=category,
                created_at=created_at,
                reply=reply
            ))

        score = None
        count = None

        try:
            meta_resp = self.requests_get(requests, 'https://www.agoda.com/api/cronos/property/BelowFoldParams/GetSecondaryData?finalPriceView=1&isShowMobileAppPrice=false&cid=1891463&numberOfBedrooms=&familyMode=false&adults=2&children=0&rooms=1&maxRooms=0&checkIn=2022-07-1&isCalendarCallout=false&childAges=&numberOfGuest=0&missingChildAges=false&travellerType=1&showReviewSubmissionEntry=false&currencyCode=KRW&isFreeOccSearch=false&tag=e2e2cb83-367c-dfba-6cf5-7a699dc64e86&isCityHaveAsq=false&tspTypes=4&los=1&searchrequestid=551a2a95-b46d-4a3c-a0a1-3de7e8e5ddca&hotel_id={}&all=false&price_view=1&sessionid=x2d4o3o4byukeodmx2aj2apa&pagetypeid=7'.format(hotel_id)).json()
            review_item = meta_resp['reviews']
            score = float(review_item['score'])
            count = review_item['reviewsCount']
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
        except Exception:
            print(traceback.print_exc())

        return dict(code=200, comments=result, score=score, count=count)
