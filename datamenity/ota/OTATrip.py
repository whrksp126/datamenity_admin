from datamenity.ota.OTABase import OTABase
import seleniumwire.undetected_chromedriver.v2 as uc
import requests
import datetime
import json
import browsercookie
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import gzip


class OTATrip(OTABase):
    rooms = []

    def get_hotel_id(self, args, url):
        parts = urlparse(url)
        qs = dict(parse_qsl(parts.query))
        return qs['hotelId']

    def init_chromedriver(self, args):
        if 'driver' in args and args['driver'] is not None:
            return
        
        args['driver'] = None
        options = uc.ChromeOptions()
        #options.add_argument('--no-sandbox')
        options.add_argument('--headless')
        options.add_argument("--window-size=500,500")
        options.add_argument('--enable-javascript')
        options.add_argument('--disable-gpu')
        #options.add_argument("disable-infobars")
        #options.add_argument("--disable-extensions")
        prefs = {'profile.default_content_setting_values': {'images': 2, 'plugins' : 2, 'popups': 2, 'geolocation': 2, 'notifications' : 2, 'auto_select_certificate': 2, 'fullscreen' : 2, 'mouselock' : 2, 'mixed_script': 2, 'media_stream' : 2, 'media_stream_mic' : 2, 'media_stream_camera': 2, 'protocol_handlers' : 2, 'ppapi_broker' : 2, 'automatic_downloads': 2, 'midi_sysex' : 2, 'push_messaging' : 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop' : 2, 'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement' : 2, 'durable_storage' : 2}}
        options.add_experimental_option('prefs', prefs)
        #user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        #options.add_argument('User-Agent={}'.format(user_agent))
        
        #options.add_experimental_option("excludeSwitches", ["enable-automation"])
        #options.add_experimental_option('useAutomationExtension', True)

        #options.add_argument('--proxy-server={}'.format(args['proxy']['SELENIUM_PROXY']))
        #driver=uc.Chrome(executable_path='chromedriver.exe', version_main=103, options=options, chrome_options=options,service_args=['--quiet'], seleniumwire_options=args['proxy']['SELENIUM_PROXY'], use_subprocess=True)
        driver=uc.Chrome(executable_path='chromedriver.exe', version_main=104, options=options, chrome_options=options,service_args=['--quiet'], seleniumwire_options=args['proxy']['SELENIUM_PROXY'], use_subprocess=True)
        #driver=uc.Chrome(executable_path='chromedriver.exe', version_main=104, options=options, chrome_options=options,service_args=['--quiet'], use_subprocess=True)
        def interceptor(request, response):
            if request.url.startswith('https://kr.trip.com/restapi/soa2/16709/json/rateplan?testab='):
                response = gzip.decompress(response.body).decode('utf-8')
                resp_item = json.loads(response)
                self.rooms = []

                if 'baseRooms' in resp_item['Response']:
                    for item in resp_item['Response']['baseRooms']:
                        room_id = item['baseRoom']['roomId']
                        room_name = item['baseRoom']['roomName']

                        for room_item in item['saleRoom']:
                            remain = room_item['base']['maxQuantity']
                            price = room_item['money']['inclusivePrice']

                            self.rooms.append(dict(
                                room_id=str(room_id), 
                                name=room_name, 
                                remain=remain,
                                price=int(price),
                            ))
                    

        driver.response_interceptor = interceptor

        args['driver'] = driver

    def scrape_prices_preprocess(self, args, url, hotel_id, checkin, checkout):
        try:
            self.init_chromedriver(args)
        except Exception as e:
            if args['driver'] is not None:
                args['driver'].quit()
                args['driver'] = None
            raise Exception('trip.com 초기화 과정중 에러 발생 : {}'.format(e))
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        try:
            self.init_chromedriver(args)
            driver = args['driver']
            
            new_url = 'https://kr.trip.com/hotels/detail/?hotelId={}&checkin={}&checkout={}&adult=2&children=0&crn=1&travelpurpose=0&curr=KRW&link=title'.format(hotel_id, checkin, checkout)
            driver.get(new_url)

            result = dict(
                code=200,
                rooms=self.rooms,
            )
            print(result)
            return result
        except Exception as e:
            if args['driver'] is not None:
                args['driver'].quit()
                args['driver'] = None
            raise Exception('trip.com 초기화 과정중 에러 발생 : {}'.format(e))

    def scrape_reviews(self, output, args, url, hotel_id, page):
        chrome_cookies = browsercookie.chrome()

        json_data = {"hotelId":hotel_id,"pageIndex":page,"pageSize":100,"orderBy":1,"commentTagList":[],"commentTagV2List":[],"travelTypeList":[],"roomList":[],"packageList":[],"commonStatisticList":[],"UnusefulReviewPageIndex":1,"repeatComment":1,"functionOptions":["IntegratedTARating","hidePicAndVideoAgg"],"webpSupport":True,"platform":"online","pageID":"10320668147","head":{"Version":"","userRegion":"KR","Locale":"ko-KR","LocaleController":"ko-KR","TimeZone":"9","Currency":"KRW","PageId":"10320668147","webpSupport":True,"userIP":"","P":"40842610930","ticket":"","clientID":"1657269467144.30wye4","Frontend":{"vid":"1657269467144.30wye4","sessionID":2,"pvid":7},"group":"TRIP","bu":"IBU","platform":"PC","Union":{"AllianceID":"","SID":"","Ouid":""},"HotelExtension":{"group":"TRIP","hasAidInUrl":False,"Qid":"678577182572","WebpSupport":True,"PID":"05f24b6c-2925-4fff-8910-5a3408b5f225"}},"PageNo":2}
        resp = requests.post('https://kr.trip.com/restapi/soa2/24077/clientHotelCommentList', cookies=chrome_cookies, json=json_data, headers={
            'accept': 'application/json',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        }).json()

        result = []
        for ritem in resp['groupList']:
            for r in ritem['commentList']:
                group_name = r['travelTypeText']
                if '개인' in group_name:
                    category = '나홀로 여행'
                elif '커플' in group_name:
                    category = '커플'
                elif '친구' in group_name:
                    category = '친구'
                elif '가족' in group_name:
                    category = '가족'
                else:
                    category = '기타'

                reply = []
                result.append(dict(
                    id=r['id'],
                    author=r['userInfo']['nickName'],
                    content=r['content'],
                    category=category,
                    score=r['rating'] * 2,
                    created_at=datetime.datetime.strptime(r['createDate'], '%Y-%m-%d %H:%M:%S') - datetime.timedelta(hours=9),
                    reply=reply
                ))

        score = resp['commentRating']['ratingAll'] * 2
        count = resp['commentRating']['showCommentNum']

        return dict(code=200, comments=result, score=score, count=count)