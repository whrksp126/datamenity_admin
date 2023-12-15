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

pattern_hotel_id = re.compile('b_hotel_id\s*\:\s*\'([0-9]*)\'')
pattern_propeties = re.compile('b_rooms_available_and_soldout\s*\:\s*(.*)\,\s*\n')
pattern_rating = re.compile('\"aggregateRating\"\s*\:\s*(\{[^\}]*\})')


class OTABooking(OTABase):
    def get_hotel_id(self, args, url):
        chrome_cookies = browsercookie.chrome()
        session = requests.session()

        try:
            resp = self.requests_get(session, 'https://www.booking.com/searchresults.ko.html?selected_currency=KRW', cookies=chrome_cookies, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
            }, **args['proxy']['REQUESTS_PROXY']).text

            print('## url : {}'.format(url.split('?')[0]))
            resp = self.requests_get(session, url.split('?')[0], cookies=chrome_cookies, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
            }, **args['proxy']['REQUESTS_PROXY']).text
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])
        args['session'] = session
        
        m = pattern_hotel_id.search(resp)
        hotel_id = m.group(1)
        return hotel_id
    
    def scrape_prices_preprocess(self, args, url, hotel_id, checkin, checkout):
        chrome_cookies = browsercookie.chrome()
        session = requests.session()

        try:
            resp = self.requests_get(session, 'https://www.booking.com/searchresults.ko.html?selected_currency=KRW', cookies=chrome_cookies, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
            }, **args['proxy']['REQUESTS_PROXY']).text
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])
        args['session'] = session
        return dict(code=200)
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        chrome_cookies = browsercookie.chrome()
        requests_session = args['session']
        new_url = '{}?checkin={}&checkout={}'.format(url.split('?')[0], checkin, checkout)
        
        try:
            resp = self.requests_get(requests_session, new_url, cookies=chrome_cookies, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
            }, **args['proxy']['REQUESTS_PROXY']).text
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])
        
        m = pattern_propeties.search(resp)
        if not m:
            return dict(
                code=504,
                rooms=[],
            )
        properties_json = m.group(1)

        hotel_properties = json.loads(properties_json)

        rooms = []
        for h in hotel_properties:
            price = 1e9
            remain = None
            
            if 'b_blocks' in h:
                for b in h['b_blocks']:
                    b_price = int(b['b_raw_price'])
                    b_remain = int(b['b_nr_stays'])
                    if b_price < price:
                        price = b_price
                        remain = b_remain
            
            if price >= 1e9:
                continue
            
            rooms.append(dict(
                room_id='{}'.format(h['b_id']), 
                name=h['b_name'], 
                remain=remain,
                price=price,
            ))
 
        return dict(
            code=200,
            rooms=rooms,
        )

    def scrape_reviews(self, output, args, url, hotel_id, page):
        chrome_cookies = browsercookie.chrome()
        requests_session = args['session']

        pagename = url.split('/')[-1].split('.')[0]
        rows = 100
        offset = (page - 1) * rows
        review_url = 'https://www.booking.com/reviewlist.ko.html?cc1=kr&pagename={}&r_lang=&review_topic_category_id=&type=total&score=&sort=&room_id=&time_of_year=&dist=1&offset={}&rows={}&rurl=&text=&translate=&length_of_stay=1'.format(pagename, offset, rows)

        try:
            resp = self.requests_get(requests_session, review_url, cookies=chrome_cookies, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
            }, **args['proxy']['REQUESTS_PROXY']).text
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])

        soup = BeautifulSoup(resp, 'html.parser')
        items = soup.find_all('li', {'class':'review_list_new_item_block'})

        result = []
        for elem in items:
            group_name = elem.find_all('div', {'class': 'bui-list__body'})
            if len(group_name) >= 3:
                group_name = group_name[2].text.strip()
            else:
                group_name = '기타'
            right_elem = elem.find('div', {'class': 'c-review-block__right'})

            review_id = elem['data-review-url']
            author = elem.find('span', {'class': 'bui-avatar-block__title'}).text
            content = elem.find('div', {'class': 'c-review'}).text.replace('\n\n\n', '').replace('\xa0·\xa0', ': ')
            score = float(elem.find('div', {'class': 'bui-review-score__badge'}).text)
            review_date = right_elem.find('span', {'class': 'c-review-block__date'}).text
            review_date = review_date.split(':')[1].replace('\n', '').strip()
            review_date = datetime.datetime.strptime(review_date, '%Y년 %m월 %d일') - datetime.timedelta(hours=9)

            reply = []

            review_response = elem.find('div', {'class': 'c-review-block__response'})
            if review_response is not None:
                reply_author = review_response.find('div', {'class': 'c-review-block__response__title'}).text
                reply_content = review_response.find('span', {'class': 'c-review-block__response__body bui-u-hidden'})
                if reply_content is None:
                    reply_content = review_response.find('span', {'class': 'c-review-block__response__body'})
                reply_content = reply_content.text
                reply.append(dict(
                    author=reply_author,
                    content=reply_content,
                    created_at=None
                ))
            
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
                id=review_id,
                author=author,
                content=content,
                category=category,
                score=score,
                created_at=review_date.strftime('%Y-%m-%d %H:%M:%S'),
                reply=reply
            ))
        
        # 리뷰 개수, 평점
        score = None
        count = None

        try:
            resp = self.requests_get(requests, url).text

            m = pattern_rating.search(resp)
            if m is not None:
                rating_json = m.group(1)
                rating_item = json.loads(rating_json)
                score = rating_item['ratingValue']
                count = rating_item['reviewCount']
                score = float(score)
                count = int(count)
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
        except Exception:
            print(traceback.print_exc())
        
        return dict(code=200, comments=result, score=score, count=count)
