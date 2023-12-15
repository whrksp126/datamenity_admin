from datamenity.ota.OTABase import OTABase, ExceptionReadTimeout
from datamenity.config import REQUESTS_PROXY, SELENIUM_PROXY

import requests
import datetime
import json
import time
import browsercookie


class OTAInterpark(OTABase):
    def get_hotel_id(self, args, url):
        return url.split('/')[-1].split('?')[0]
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        requests_session = requests.Session()

        try:
            resp = self.requests_post(requests_session, 'https://travel.interpark.com/api/checkinnow/goods/getRoomsListPc', headers={
                'Accept': 'application/json, text/plain, */*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Connection': 'keep-alive',
                'sec-ch-ua': '"Google Chrome";v="111", "Chromium";v="111", ";Not A Brand";v="8"',
                'sec-ch-ua-mobile': '?0',
                'sec-cha-ua-platform': 'Windows',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Host': 'travel.interpark.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }, json={
                'adultCnt': 2,
                'bedTyNm': "",
                'breakfastFreeYn': "",
                'cancelFreeYn': "",
                'checkIn': checkin.replace('-', ''),
                'checkOut': checkout.replace('-', ''),
                'dcsnItemYn': "",
                'dspyChnnl': "WEBNM",
                'goodsId': hotel_id,
                'hideClosYn': "",
                'ippCd': "00000",
                'nmprAditFreeYn': "",
                'promtnTy': "",
                'resveChnnl': "00000",
                'roomCnt': 1,
                'roomGradTy': "",
                'roomSleTy': "",
                'roomViewTy': "",
                'sort': "S0001"
            }, **args['proxy']['REQUESTS_PROXY']).json()
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])

        rooms = []

        # 데이터가 안넘어올경우
        if 'data' not in resp:
            return dict(code=504, rooms=[])

        for b in resp['data']['blocks']:
            for r in b['rooms']:
                is_soldout = r['soldOutYn'] == 'Y'
                room_id = r['goodsId']
                name = r['dspyRoomNm']
                price = 1e10
                remain_cnt = 0
    
                if is_soldout:
                    for p in r['prices']:
                        price = min(price, p['price'])
                else:
                    for p in r['prices']:
                        if p['remainRoomCnt'] == 0:
                            continue
                        if price > p['price']:
                            price = p['price']
                            remain_cnt = p['remainRoomCnt']

                if price < 3000:
                    continue
                rooms.append(dict(
                    room_id=room_id, 
                    name=name, 
                    remain=remain_cnt,
                    price=price,
                ))
                
        return dict(
            code=200,
            rooms=rooms,
        )
    
    def scrape_reviews(self, output, args, url, hotel_id, page):
        result = []

        try:
            reviews = self.requests_post(requests, 'https://travel.interpark.com/api/checkinnow/review/review/goods/{}'.format(hotel_id), headers={
                'Accept': 'application/json, text/plain, */*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Connection': 'keep-alive',
                'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-cha-ua-platform': 'Windows',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            }, json={
                'breakFastInclsYn': "",
                'imageYn': "",
                'keyword': "",
                'pageNo': page,
                'pageSize': 100,
                'roomGradTys': "",
                'roomViewTys': "",
                'tourTy': ""
            }, **args['proxy']['REQUESTS_PROXY']).json()
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
        
        for r in reviews['data']['goodsEvaluationsVo']:
            reply = []
            if r['replyVo'] is not None and len(r['replyVo']) > 0:
                for rr in r['replyVo']:
                    reply.append(dict(
                        author=rr['regId'],
                        content=rr['replyCn'],
                        created_at=datetime.datetime.strptime(rr['regDt'], '%Y-%m-%d %H:%M:%S')
                    ))
            
            result.append(dict(
                id=r['evlSeq'],
                author=r['mberId'],
                content='{}\n{}'.format(r['title'], r['evlCn']),
                category='기타',
                score=r['svcEvlTotal'],
                created_at=datetime.datetime.strptime(r['regDt'], '%Y-%m-%d'),
                reply=reply
            ))
        
        # 리뷰 개수, 평점
        score = reviews['data']['gr002Avg']
        count = reviews['links']['totalCnt']
        
        return dict(code=200, comments=result, score=score, count=count)
