import traceback
from datamenity.crawler import get_proxy_environment
from datamenity.models import User, session_scope, CrawlerRule, Hotel, OTAType, Environment
from datamenity.ota.OTAGoodchoice import OTAGoodchoice
from datamenity.ota.OTAYanolja import OTAYanolja
from datamenity.ota.OTAHotels import OTAHotels
from datamenity.ota.OTAInterpark import OTAInterpark
from datamenity.ota.OTADaily import OTADaily
from datamenity.ota.OTAKensington import OTAKensington
from datamenity.ota.OTAWings import OTAWings
from datamenity.ota.OTAAgoda import OTAAgoda
from datamenity.ota.OTABooking import OTABooking
from datamenity.ota.OTAExpedia import OTAExpedia
from datamenity.ota.OTARakuten import OTARakuten

from datamenity.ota.OTATrip import OTATrip
import datetime
import time
import json

from selenium import webdriver
import undetected_chromedriver.v2 as uc
from pyvirtualdisplay import Display

def json_default(value):
    if isinstance(value, datetime.date):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError('not JSON serializable')

print('#start', datetime.datetime.now())

print('-- init start --', datetime.datetime.now())

'''
virtual_display = Display(visible=0, size=(500, 500))
virtual_display.start()

options = uc.ChromeOptions()
options.add_argument('--user-data-dir=/opt/google.chrome/chrome-data')
# options.add_argument('--disable-dev-shm-usage') # uses /tmp for memory sharing
options.add_argument('--no-first-run')
options.add_argument('--no-service-autorun')
options.add_argument('--no-default-browser-check')
options.add_argument('--password-store=basic')
options.add_argument('--incognito')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-setuid-sandbox')
options.add_argument('--proxy-server={}'.format(PROXY_SERVER))

args = dict(
    driver=uc.Chrome(driver_executable_path='{}/driver/chromedriver'.format(BASE_DIR), options=options, seleniumwire_options=SELENIUM_PROXY)
)
'''

'''
with session_scope() as session:
    env_item = session.query(Environment).filter(Environment.key == 'PROXY').first()
    env_value = json.loads(env_item.value)

    value_proxy_server = 'http://{}'.format(env_value['ip'])
    value_proxies = {
        'http':value_proxy_server,
        'https':value_proxy_server,
    }
    proxy_params = dict(
        PROXY_SERVER=value_proxy_server,
        proxies=value_proxies,
        REQUESTS_PROXY=dict(proxies=value_proxies, timeout=20),
        SELENIUM_PROXY=dict(proxy=value_proxies),
    )
    args = dict(proxy=proxy_params)
'''

'''
# completed
ota_obj = OTAYanolja()
url = 'https://place-site.yanolja.com/places/1000104461'
hotel_id = 1000104461
ota_obj = OTAYanolja()
url = 'https://www.yanolja.com/hotel/3001099'
hotel_id = 3001099

ota_obj = OTAGoodchoice()
url = 'https://www.goodchoice.kr/product/detail?ano=6546&adcno=2&sel_date=2022-08-12&sel_date2=2022-08-13'
hotel_id = 6546

ota_obj = OTAHotels()
url = 'https://kr.hotels.com/ho421229'
hotel_id = 421229

ota_obj = OTAInterpark()
url = 'https://travel.interpark.com/checkinnow/goods/GN0002152966'
hotel_id = 'GN0002152966'

ota_obj = OTADaily()
url = 'https://www.dailyhotel.com/stays/15154?dateCheckIn=2022-07-12&stays=1'
hotel_id = 15154

ota_obj = OTAKensington()
url = 'https://www.kensington.co.kr/reservation/result_room?search_bran_cd=RHK12&search_stay_start_dt=2022-07-14&search_stay_end_dt=2022-07-15&search_room_cnt=1&search_people_adult_cnt=2&search_people_adult_cnts=2&search_people_child_cnt=0&search_people_child_cnts=0&search_code_type=&search_code=&pack_cd=&room_type_cd=&pay_type=P&memflag='
hotel_id = 'RHK12'

ota_obj = OTAWings()
url = 'https://be4.wingsbooking.com/FORET2121/roomSelect?check_in=2022-07-13&check_out=2022-07-14&prm_seq_no=&cpny_seq_no=&rooms=1&adult=2&children=0'
hotel_id = 'FORET2121'

ota_obj = OTAAgoda()
url = 'https://www.agoda.com/ko-kr/kensington-hotel-yeouido-seoul/hotel/seoul-kr.html'
hotel_id = 8030

ota_obj = OTABooking()
url = 'https://www.booking.com/hotel/kr/kent-gwangalli.ko.html'
hotel_id = '1703019'

ota_obj = OTAExpedia()
url = 'https://www.expedia.co.kr/Busan-Hotels-Kent-Hotel-Gwangalli-By-Kensington.h14858808.Hotel-Information'
hotel_id = '14858808'

ota_obj = OTAWings()
url = 'https://be4.wingsbooking.com/FORET2121/roomSelect?check_in=2022-07-13&check_out=2022-07-14&prm_seq_no=&cpny_seq_no=&rooms=1&adult=2&children=0'
hotel_id = 'FORET2121'
'''

args = dict()
args['proxy'] = get_proxy_environment(2)
args['driver'] = None
args['virtual_display'] = None

try:
    checkin = '2023-05-06'
    checkout = '2023-05-07'

    print(args)

    ota_obj = OTABooking()
    url = 'https://www.booking.com/hotel/kr/shilla-stay-ulsan.ko.html?'

    '''
    ota_obj = OTARakuten()
    url = 'https://travel.rakuten.co.jp/HOTEL/12682/12682.html'

    ota_obj = OTAExpedia()
    url = 'https://www.expedia.co.kr/Busan-Hotels-H-Avenue-Gwangan-Beach.h35795203.Hotel-Information'

    ota_obj = OTAInterpark()
    url = 'https://travel.interpark.com/checkinnow/goods/GN0002152659'
    '''

    '''
    ota_obj = OTAExpedia()
    url = 'https://www.expedia.co.kr/Seogwipo-Hotels-Shinshin-Hotel-World-Cup.h74428323.Hotel-Information'
    hotel_id = '33397026'
    '''

    '''
    ota_obj = OTAAgoda()
    url = 'https://www.agoda.com/ko-kr/lotte-hotel-seoul/hotel/seoul-kr.html?'
    hotel_id = 6546

    ota_obj = OTABooking()
    url = 'https://www.booking.com/hotel/kr/shilla-stay-ulsan.ko.html?'
    hotel_id = '1778038'

    ota_obj = OTATrip()
    url = 'https://kr.trip.com/hotels/detail/?hotelId=5215454'
    hotel_id = '988663'

    ota_obj = OTAHotels()
    url = 'https://kr.hotels.com/ho484294/sr-suites-bundang-seongnam-hangug/?chkin=2023-03-29&chkout=2023-03-30&x_pwa=1&rfrr=HSR&pwa_ts=1680073396022&referrerUrl=aHR0cHM6Ly9rci5ob3RlbHMuY29tL0hvdGVsLVNlYXJjaA%3D%3D&useRewards=false&rm1=a2&regionId=6141665&destination=%EC%84%B1%EB%82%A8%2C+%EA%B2%BD%EA%B8%B0%2C+%ED%95%9C%EA%B5%AD&destType=MARKET&neighborhoodId=553248635976008564&selected=9613227&latLong=37.407332%2C127.116313&sort=RECOMMENDED&top_dp=148910&top_cur=KRW&mdpcid=HCOM-KR.META.HPA.HOTEL-CORESEARCH-desktop.HOTEL&mdpdtl=HTL.9613227.20230329.20230330.DDT.0.CID.15951747823.AUDID.7124075013&mctc=10&gclid=Cj0KCQjww4-hBhCtARIsAC9gR3YnJ-gdJDqTa8mbHBtM22jYD83AmZPnknPXk0xXNqWaRekRHEdy2P4aAp4uEALw_wcB&userIntent=&selectedRoomType=218127477&selectedRatePlan=274178494&expediaPropertyId=9613227'
    '''

    hotel_id = ota_obj.get_hotel_id(args, url)
    print("hotel_id : ",hotel_id)
    
    
    '''
    '''
    # 가격
    ota_obj.scrape_prices_preprocess(args, url, hotel_id, checkin, checkout)    
    result = ota_obj.scrape_prices([], args, url, hotel_id, checkin, checkout)
    print(checkin, json.dumps(result))
        
    '''
    for d in range(90):
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        checkin = (now + datetime.timedelta(days=d)).strftime('%Y-%m-%d')
        checkout = (now + datetime.timedelta(days=d+1)).strftime('%Y-%m-%d')
        result = ota_obj.scrape_prices([], args, url, hotel_id, checkin, checkout)
    '''

    '''
    '''
    # 리뷰
    result = ota_obj.scrape_reviews([], args, url, hotel_id, 1)
    print(json.dumps(result, default=str))

except Exception:
    print(traceback.print_exc())

'''
if args['virtual_display'] is not None:
    args['virtual_display'].stop()
'''
if 'driver' in args and args['driver'] is not None:
    args['driver'].quit()

while True:
    time.sleep(1)
