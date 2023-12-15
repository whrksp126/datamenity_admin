from datamenity.models import User, session_scope, CrawlerRule, Hotel, OTAType, Environment, UserHasCompetition, UserHasCrawlerRule
from datamenity.ota.OTAGoodchoice import OTAGoodchoice
from datamenity.ota.OTABooking import OTABooking
from datamenity.ota.OTAExpedia import OTAExpedia
from datamenity.ota.OTAAgoda import OTAAgoda
from datamenity.ota.OTAInterpark import OTAInterpark
from datamenity.ota.OTAYanolja import OTAYanolja
from datamenity.ota.OTADaily import OTADaily
from datamenity.ota.OTAHotels import OTAHotels
from datamenity.ota.OTATrip import OTATrip
from datamenity.ota.OTAWings import OTAWings
from datamenity.ota.OTAKensington import OTAKensington
import boto3
import json
import requests

ota_code_to_obj = [OTAGoodchoice(), OTABooking(), OTAExpedia(), OTAAgoda(), OTAInterpark(), OTAYanolja(), OTADaily(), OTAHotels(), OTATrip(), OTAWings(), OTAKensington()]
ota_code_to_type = [OTAType.GOODCHOICE, OTAType.BOOKING, OTAType.EXPEDIA, OTAType.AGODA, OTAType.INTERPARK, OTAType.YANOLJA, OTAType.DAILY, OTAType.HOTELS, OTAType.TRIP, OTAType.WINGS, OTAType.KENSINGTON]
ota_code_to_str = ['goodchoice', 'booking', 'expedia', 'agoda', 'interpark', 'yanolja', 'daily', 'hotels', 'trip', 'wings', 'kensington']
ota_str_to_code = {
    'goodchoice': 0, 
    'booking': 1, 
    'expedia': 2, 
    'expeida': 2, 
    'agoda': 3, 
    'interpark': 4, 
    'yanolja': 5, 
    'daily': 6, 
    'hotels': 7, 
    'trip': 8, 
    'wings': 9,
    'kensington': 10
}

data = [{
	"id": 1,
	"name": "무료",
	"time": [11, 23],
	"range": 30,
	"ids": [228, 99, 207, 195, 92, 120, 103, 102, 204, 139, 191, 109, 156, 230, 90, 135, 104, 121, 198, 54, 189, 79, 66, 108, 194, 115, 131, 142, 118, 222, 106, 110, 1, 202, 116, 187, 206, 105, 87, 97, 84, 60, 117, 144, 28, 89, 114, 94, 98, 53, 232, 130, 82, 137, 145, 107, 146, 179, 201, 77, 91, 81, 88, 140, 234, 96, 224, 132, 126, 77, 91, 81, 88, 14, 234, 96, 224, 132, 126, 128, 71, 119, 175, 227, 200, 95, 205, 100, 78, 176, 199, 83, 188, 223, 101, 157, 193, 111, 58, 178, 19, 112, 158, 55, 184, 56, 70, 85, 20, 123, 124, 161, 181, 160, 86, 21, 177, 125, 185, 67, 10, 226, 57, 196, 149, 183, 72, 225, 122, 127, 129]
},
{
	"id": 2,
	"name": "크롤링 13회 30일",
	"time": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 23],
	"range": 30,
	"ids": [63, 64, 36, 22, 40, 59, 136, 31, 133, 80, 75, 76, 148, 38, 30, 35, 27, 44, 32, 41, 68, 34, 46, 26, 3, 69, 74, 37, 93, 29, 134, 47, 42, 43]
},
{
	"id": 3,
	"name": "크롤링 13회 90일",
	"time": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 23],
	"range": 90,
	"ids": [141, 231, 168, 167, 172, 174, 170, 169, 192, 171, 173, 163, 165, 1000, 229, 190, 39, 15, 166, 162, 233]
},
{
	"id": 4,
	"name": "무료 90일",
	"time": [11, 23],
	"range": 90,
	"ids": [186, 182]
},
{
	"id": 5,
	"name": "크롤링 13회 90일 (0시)",
	"time": [0, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 23],
	"range": 90,
	"ids": [180, 65]
},
{
	"id": 6,
	"name": "크롤링 24회 90일",
	"time": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
	"range": 90,
	"ids": [61, 5, 159]
},
{
	"id": 7,
	"name": "크롤링 6회",
	"time": [3, 7, 11, 15, 19, 23],
	"range": 90,
	"ids": [217, 208, 212, 214, 219, 213, 209, 210, 211, 218, 197, 215, 216, 220]
}]

# proxy
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

def set_ota(hotel_id, ota, url):
	with session_scope() as session:
		hotel_item = session.query(Hotel).filter(Hotel.id == hotel_id).first()
		hotel_item.otas |= 1 << ota
		link = json.loads(hotel_item.link)
		link[str(ota)] = dict(url=url, hid=ota_code_to_obj[ota].get_hotel_id(args, url))
		hotel_item.link = json.dumps(link)
		print(hotel_item.link)
		session.commit()

def insert_crawler_rule(data):
    with session_scope() as session:
        for d in data:
            flag = 0
            for t in d['time']:
                flag |= 1 << t
            rule = CrawlerRule(d['name'], d['range'], flag)
            session.add(rule)
        session.commit()

def get_hotels_info():
	dynamodb = boto3.resource(
		'dynamodb',
		aws_access_key_id='AKIAQM7ZLHBXEVUEXNO4',
		aws_secret_access_key='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',
		region_name='ap-northeast-2'
	)
	dynamo_subscriber = dynamodb.Table('subscriber')

	sub_resp = dynamo_subscriber.scan()
	sub_items = sub_resp['Items']

	while 'LastEvaluatedKey' in sub_resp:
		sub_resp = dynamo_subscriber.scan(ExclusiveStartKey=sub_resp['LastEvaluatedKey'])
		sub_items.extend(sub_resp['Items'])

	subs_to_target_id = dict()
	for item in sub_items:
		if item['id'] not in subs_to_target_id:
			subs_to_target_id[item['id']] = []
		if 'my_target_id' not in item:
			print('## ERROR', item['id'])
			continue
		subs_to_target_id[item['id']].append(item['my_target_id'])
	
	print(subs_to_target_id)


def get_hotels():
	dynamodb = boto3.resource(
		'dynamodb',
		aws_access_key_id='AKIAQM7ZLHBXEVUEXNO4',
		aws_secret_access_key='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',
		region_name='ap-northeast-2'
	)

	dynamo_subscriber = dynamodb.Table('subscriber')
	dynamo_crawling_target = dynamodb.Table('crawling_target')

	sub_resp = dynamo_subscriber.scan()
	cra_resp = dynamo_crawling_target.scan()

	sub_items = sub_resp['Items']
	cra_items = cra_resp['Items']

	while 'LastEvaluatedKey' in sub_resp:
		sub_resp = dynamo_subscriber.scan(ExclusiveStartKey=sub_resp['LastEvaluatedKey'])
		sub_items.extend(sub_resp['Items'])
	
	while 'LastEvaluatedKey' in cra_resp:
		cra_resp = dynamo_crawling_target.scan(ExclusiveStartKey=cra_resp['LastEvaluatedKey'])
		cra_items.extend(cra_resp['Items'])

	subs_to_target_id = dict()
	hotel_info = dict()
	for item in cra_items:
		if item['id'] == 'index':
			continue
		
		hotel_info[str(item['id'])] = dict(
			hotel_id=int(item['id']),
			name=item.get('name', ''),
			addr=item.get('addr', ''),
			road_addr=item.get('road_addr', '')
		)

	result = []
	for item in sub_items:
		if 'my_target_id' not in item:
			continue

		ota_flag = 0
		for o in item['ota']:
			ota_flag |= 1 << ota_str_to_code[o]
		
		link_dict = dict()
		for s in ota_code_to_str:
			if '{}_link'.format(s) in item:
				if s == 'kensington':
					url = 'https://kensington.co.kr/reservation/result_room?search_bran_cd={}&search_stay_start_dt=2022-07-21&search_stay_end_dt=2022-07-22&search_room_cnt=1&search_people_adult_cnt=2&search_people_adult_cnts=2&search_people_child_cnt=0&search_people_child_cnts=0&search_code_type=&search_code=&pack_cd=&room_type_cd=&pay_type=P&memflag='.format(item['{}_link'.format(s)])
				else:
					url = item['{}_link'.format(s)]
				link_dict[ota_str_to_code[s]] = dict(url=url)
		
		item_obj = dict(
			id=int(item['id']),
			otas=ota_flag,
			link=link_dict,
		)

		my_target_id = str(item['my_target_id'])
		if my_target_id in hotel_info:
			item_obj.update(hotel_info[my_target_id])
		
		subs_to_target_id[str(item['id'])] = item_obj
	
	cnt = 0
	with session_scope() as session:
		for k, v in subs_to_target_id.items():
			if 'hotel_id' in v:
				item = session.query(Hotel).filter(Hotel.id == int(v['hotel_id'])).first()
				if not item:
					item = Hotel(v['name'], v['otas'], json.dumps(v['link']), v['addr'], v['road_addr'])
					session.add(item)
				else:
					item.name = v['name']
					item.otas = v['otas']
					item.link = json.dumps(v['link'])
					item.addr = v['addr']
					item.road_addr = v['road_addr']
				print(v['hotel_id'], v['name'], v['addr'], v['road_addr'])
				session.commit()
				cnt += 1
	print('##', cnt)


def get_all_targets():
	dynamodb = boto3.resource(
		'dynamodb',
		aws_access_key_id='AKIAQM7ZLHBXEVUEXNO4',
		aws_secret_access_key='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',
		region_name='ap-northeast-2'
	)

	dynamo_crawling_target = dynamodb.Table('crawling_target')
	cra_resp = dynamo_crawling_target.scan()
	cra_items = cra_resp['Items']

	while 'LastEvaluatedKey' in cra_resp:
		cra_resp = dynamo_crawling_target.scan(ExclusiveStartKey=cra_resp['LastEvaluatedKey'])
		cra_items.extend(cra_resp['Items'])
	
	cnt = 0
	with session_scope() as session:
		for item in cra_items:
			if item['id'] == 'index':
				continue
			
			hotel_id=int(item['id']),
			name=item.get('name', ''),
			addr=item.get('addr', ''),
			road_addr=item.get('road_addr', '')

			print(hotel_id, name, addr)

			item = session.query(Hotel).filter(Hotel.id == hotel_id).first()
			if not item:
				item = Hotel(name, 0, '{}', addr, road_addr)
				item.id = hotel_id
				session.add(item)
			else:
				item.name = name
				item.addr = addr
				item.road_addr = road_addr
			session.commit()
			cnt += 1

	print('##', cnt)


'''
# 스캔 규칙 넣는 스크립트
def insert_hotel_has_crawler_rule(data):
	dynamodb = boto3.resource(
		'dynamodb',
		aws_access_key_id='AKIAQM7ZLHBXEVUEXNO4',
		aws_secret_access_key='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',
		region_name='ap-northeast-2'
	)

	dynamo_subscriber = dynamodb.Table('subscriber')
	dynamo_crawling_target = dynamodb.Table('crawling_target')

	sub_resp = dynamo_subscriber.scan()
	cra_resp = dynamo_crawling_target.scan()

	sub_items = sub_resp['Items']
	cra_items = cra_resp['Items']

	while 'LastEvaluatedKey' in sub_resp:
		sub_resp = dynamo_subscriber.scan(ExclusiveStartKey=sub_resp['LastEvaluatedKey'])
		sub_items.extend(sub_resp['Items'])
	
	while 'LastEvaluatedKey' in cra_resp:
		cra_resp = dynamo_crawling_target.scan(ExclusiveStartKey=cra_resp['LastEvaluatedKey'])
		cra_items.extend(cra_resp['Items'])

	subs_to_target_id = dict()
	hotel_info = dict()
	for item in cra_items:
		if item['id'] == 'index':
			continue
		
		hotel_info[str(item['id'])] = dict(
			hotel_id=int(item['id']),
			name=item.get('name', ''),
			addr=item.get('addr', ''),
			road_addr=item.get('road_addr', '')
		)

	result = []
	for item in sub_items:
		if 'my_target_id' not in item:
			continue

		ota_flag = 0
		for o in item['ota']:
			ota_flag |= 1 << ota_str_to_code[o]
		
		link_dict = dict()
		for s in ota_code_to_str:
			if '{}_link'.format(s) in item:
				if s == 'kensington':
					url = 'https://kensington.co.kr/reservation/result_room?search_bran_cd={}&search_stay_start_dt=2022-07-21&search_stay_end_dt=2022-07-22&search_room_cnt=1&search_people_adult_cnt=2&search_people_adult_cnts=2&search_people_child_cnt=0&search_people_child_cnts=0&search_code_type=&search_code=&pack_cd=&room_type_cd=&pay_type=P&memflag='.format(item['{}_link'.format(s)])
				else:
					url = item['{}_link'.format(s)]
				link_dict[ota_str_to_code[s]] = dict(url=url)
		
		item_obj = dict(
			id=int(item['id']),
			otas=ota_flag,
			link=link_dict,
		)

		my_target_id = str(item['my_target_id'])
		if my_target_id in hotel_info:
			item_obj.update(hotel_info[my_target_id])
		
		subs_to_target_id[str(item['id'])] = item_obj

	with session_scope() as session:
		for d in data:
			for hotel_id in d['ids']:
				if str(hotel_id) not in subs_to_target_id:
					print("## ERROR", hotel_id)
					continue
				
				if 'hotel_id' in subs_to_target_id[str(hotel_id)]:
					item = session.query(HotelHasCrawlerRule).filter(HotelHasCrawlerRule.hotel_id == int(subs_to_target_id[str(hotel_id)]['hotel_id']), HotelHasCrawlerRule.crawler_rule_id == int(d['id'])).first()
					if not item:
						try:
							session.add(HotelHasCrawlerRule(int(subs_to_target_id[str(hotel_id)]['hotel_id']), int(d['id'])))		
							session.commit()
						except Exception as e:
							print('##', int(subs_to_target_id[str(hotel_id)]['hotel_id']), int(d['id']), e)
'''


# 경쟁사 넣는 스크립트
def insert_competition():
	dynamodb = boto3.resource(
		'dynamodb',
		aws_access_key_id='AKIAQM7ZLHBXEVUEXNO4',
		aws_secret_access_key='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',
		region_name='ap-northeast-2'
	)

	dynamo_subscriber = dynamodb.Table('subscriber')
	sub_resp = dynamo_subscriber.scan()
	sub_items = sub_resp['Items']

	while 'LastEvaluatedKey' in sub_resp:
		sub_resp = dynamo_subscriber.scan(ExclusiveStartKey=sub_resp['LastEvaluatedKey'])
		sub_items.extend(sub_resp['Items'])

	result = []

	with session_scope() as session:
		for item in sub_items:
			if 'my_target_id' not in item:
				continue
			if 'my_targets' not in item:
				continue

			my_target_id = int(item['my_target_id'])
			my_targets = item['my_targets']

			for t in my_targets:
				compete_id = int(t['id'])
				isactive = t['default'].get('active', True)
				print('##', my_target_id, compete_id, isactive)
				if isactive:
					
					item = session.query(HotelHasCompetition).filter(HotelHasCompetition.hotel_id == my_target_id, HotelHasCompetition.competition_id == compete_id).first()
					if not item:
						session.add(HotelHasCompetition(my_target_id, compete_id))
						session.commit()

#get_all_targets()
#insert_competition()

# 크롤러 url 넣는 스크립트
def insert_url():
	from selenium import webdriver
	import undetected_chromedriver.v2 as uc
	from pyvirtualdisplay import Display
	from datamenity.config import REQUESTS_PROXY, SELENIUM_PROXY, PROXY_SERVER, BASE_DIR

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

	dynamodb = boto3.resource(
		'dynamodb',
		aws_access_key_id='AKIAQM7ZLHBXEVUEXNO4',
		aws_secret_access_key='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',
		region_name='ap-northeast-2'
	)

	dynamo_crawling_target = dynamodb.Table('crawling_target')
	cra_resp = dynamo_crawling_target.scan()
	cra_items = cra_resp['Items']

	while 'LastEvaluatedKey' in cra_resp:
		cra_resp = dynamo_crawling_target.scan(ExclusiveStartKey=cra_resp['LastEvaluatedKey'])
		cra_items.extend(cra_resp['Items'])

	result = []
	for item in cra_items:
		if item['id'] == 'index':
			continue
		
		link_dict = dict()
		for s in ota_code_to_str:
			if '{}_link'.format(s) in item:
				if s == 'kensington':
					url = 'https://kensington.co.kr/reservation/result_room?search_bran_cd={}&search_stay_start_dt=2022-07-21&search_stay_end_dt=2022-07-22&search_room_cnt=1&search_people_adult_cnt=2&search_people_adult_cnts=2&search_people_child_cnt=0&search_people_child_cnts=0&search_code_type=&search_code=&pack_cd=&room_type_cd=&pay_type=P&memflag='.format(item['{}_link'.format(s)])
				else:
					url = item['{}_link'.format(s)]
				if s not in ota_str_to_code:
					continue
				try:
					hid = ota_code_to_obj[ota_str_to_code[s]].get_hotel_id(args, url)
				except:
					hid = None
				link_dict[ota_str_to_code[s]] = dict(url=url, hid=hid)
				print('##', dict(url=url, hid=hid))
		
		result.append(dict(
			id=int(item['id']),
			link=link_dict,
		))

	cnt = 0
	with session_scope() as session:
		for r in result:
			item = session.query(Hotel).filter(Hotel.id == int(r['id'])).first()
			if item is not None:
				item.link = json.dumps(r['link'])
			print(r)
			session.commit()
			cnt += 1
	print('##', cnt)


#insert_url()


def insert_hid():
	with session_scope() as session:
		hotels = session.query(Hotel).all()
		for h in hotels:
			link = json.loads(h.link)
			for k, v in link.items():
				try:
					print('##', h.id, int(k), v.get('url', ''), end='')
					hid = ota_code_to_obj[int(k)].get_hotel_id({}, v.get('url', ''))
					print(' -> ', hid)
					link[k]['hid'] = str(hid)
				except:
					print('########', h.id, int(k), v.get('url', ''))
			#print(link)
			h.link = json.dumps(link)
		session.commit()



def insert_dailyhotel_hid():
	with session_scope() as session:
		hotels = session.query(Hotel).filter(Hotel.link.ilike('%dailyhotel%')).all()
		for h in hotels:
			link = json.loads(h.link)
			item = link.get('5')
			if item is None:
				continue
			url = item.get('url')

			if 'dailyhotel' not in url:
				continue
			
			hid = item.get('hid')
			print(h.id, url, hid)

			del link['5']
			link[6] = dict(url=url, hid=hid)
			h.link = json.dumps(link)
		session.commit()



def change_yanolja_otas():
	with session_scope() as session:
		hotels = session.query(Hotel).filter(Hotel.link.ilike('%dailyhotel%')).all()
		for h in hotels:
			link = json.loads(h.link)
			item = link.get('6')
			if item is None:
				continue
			url = item.get('url')

			if 'dailyhotel' not in url:
				continue
			
			hid = item.get('hid')
			print(hid, url, h.otas)

			'''
			if (h.otas & 0x20) > 0:
				h.otas = (h.otas & ~0x20) | 0x40
			print(h.id, url, h.otas)
			'''
		#session.commit()
#change_yanolja_otas()
#print(OTABooking().get_hotel_id({}, 'https://www.booking.com/hotel/kr/busan-business-busan.ko.html?'))

def allocate_elastic_ip():
	with session_scope() as session:
		session.add(Environment('PROXY', json.dumps(dict(alloc_id='eipalloc-0b70722a8c462f591', ip='43.200.92.97', instance_id='i-02e81f336a46a39ba'))))
		session.commit()
	'''
	import boto3
	from botocore.exceptions import ClientError

	ec2 = boto3.client('ec2', region_name="ap-northeast-2")

	try:
		allocation = ec2.allocate_address(Domain='vpc')
		print('## IP : ', allocation['PublicIp'])
		response = ec2.associate_address(AllocationId=allocation['AllocationId'], InstanceId='i-02e81f336a46a39ba')
		print(response)
		response = ec2.release_address(AllocationId=allocation['AllocationId'])
		print(response)
	except ClientError as e:
		print(e)
	'''

#allocate_elastic_ip()

def change_kensington_otas():
	with session_scope() as session:
		hotels = session.query(Hotel).filter(Hotel.link.ilike('%kensington%')).all()
		for h in hotels:
			link = json.loads(h.link)
			item = link.get('10')
			if item is None:
				continue
			url = item.get('url')

			if 'kensington' not in url:
				continue
			
			hid = item.get('hid')
			print(hid, url, h.otas)

			if (h.otas & 0x200) > 0:
				h.otas = (h.otas & ~0x200) | 0x400
			print(h.id, url, h.otas)
		session.commit()
#change_kensington_otas()

'''
yanolja_data = [[1060,	'https://place-site.yanolja.com/places/3001099'],
[1717,	'https://place-site.yanolja.com/places/3001057'],
[1718,	'https://place-site.yanolja.com/places/1000103524'],
[422,	'https://place-site.yanolja.com/places/3001790'],
[1716,	'https://place-site.yanolja.com/places/3000675'],
[1674,	'https://place-site.yanolja.com/places/3001061'],
[1720,	'https://place-site.yanolja.com/places/3001058'],
[913,	'https://place-site.yanolja.com/places/3001685'],
[1738,	'https://place-site.yanolja.com/places/3001820'],
[1719,	'https://place-site.yanolja.com/places/3001060'],
[1722,	'https://place-site.yanolja.com/places/3001812'],
[1721,	'https://place-site.yanolja.com/places/3001062'],
[1718,	'https://place-site.yanolja.com/places/1000103524'],
[1642,	'https://place-site.yanolja.com/places/3001056'],
[1688,	'https://place-site.yanolja.com/places/3001059'],
[1759,	'https://place-site.yanolja.com/places/3001300'],
[1770,	'https://place-site.yanolja.com/places/1000109883'],
[1744,	'https://place-site.yanolja.com/places/3001824'],
[1769,	'https://place-site.yanolja.com/places/3001791']]


for d in yanolja_data:
	set_ota(d[0], 5, d[1])
'''

'''
# 내 호텔 ID
def set_user_hotel_id():
	dynamodb = boto3.resource(
		'dynamodb',
		aws_access_key_id='AKIAQM7ZLHBXEVUEXNO4',
		aws_secret_access_key='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',
		region_name='ap-northeast-2'
	)
	dynamo_subscriber = dynamodb.Table('subscriber')

	sub_resp = dynamo_subscriber.scan()
	sub_items = sub_resp['Items']

	while 'LastEvaluatedKey' in sub_resp:
		sub_resp = dynamo_subscriber.scan(ExclusiveStartKey=sub_resp['LastEvaluatedKey'])
		sub_items.extend(sub_resp['Items'])

	for item in sub_items:
		if 'my_target_id' not in item:
			print('## ERROR', item['id'])
			continue
		
		with session_scope() as session:
			subscriber_id = int(item['id'])
			user_item = session.query(User).filter(User.id == subscriber_id).first()
			if not user_item:
				print('## ERROR2', subscriber_id)
				continue
			print(item['id'], item['my_target_id'])
			user_item.hotel_id = int(item['my_target_id'])
			session.commit()

set_user_hotel_id()
'''

'''
def set_user_competition():
	dynamodb = boto3.resource(
		'dynamodb',
		aws_access_key_id='AKIAQM7ZLHBXEVUEXNO4',
		aws_secret_access_key='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',
		region_name='ap-northeast-2'
	)
	dynamo_subscriber = dynamodb.Table('subscriber')

	sub_resp = dynamo_subscriber.scan()
	sub_items = sub_resp['Items']

	while 'LastEvaluatedKey' in sub_resp:
		sub_resp = dynamo_subscriber.scan(ExclusiveStartKey=sub_resp['LastEvaluatedKey'])
		sub_items.extend(sub_resp['Items'])

	for item in sub_items:
		with session_scope() as session:
			try:
				subscriber_id = int(item['id'])
			except Exception:
				print('## ERROR', item['id'])
				continue
			
			user_item = session.query(User).filter(User.id == subscriber_id).first()
			if not user_item:
				print('## ERROR2', subscriber_id)
				continue

			if 'my_targets' not in item:
				print('## ERROR3', subscriber_id)
				continue
				
			for hotel_item in item['my_targets']:
				hotel_id = int(hotel_item['id'])
				is_active = True
				if 'default' in hotel_item:
					is_active = hotel_item['default'].get('activate', True)
				
				if not is_active:
					continue
				
				user_has_competition = UserHasCompetition(user_item.id, hotel_id)
				session.add(user_has_competition)
				
			session.commit()
			print(user_item.id, len(item['my_targets']))
			

set_user_competition()
'''


def set_user_crawler_rule():
	with session_scope() as session:
		for item in data:
			for user_id in item['ids']:
				user_item = session.query(User).filter(User.id == user_id).first()
				if not user_item:
					print('ERROR4', user_id)
					continue

				user_has_crawler_rule = session.query(UserHasCrawlerRule).filter(UserHasCrawlerRule.user_id == user_id, UserHasCrawlerRule.crawler_rule_id == int(item['id'])).first()
				if user_has_crawler_rule is None:
					user_has_crawler_rule = UserHasCrawlerRule(user_id, int(item['id']))
					session.add(user_has_crawler_rule)
					session.commit()

#set_user_crawler_rule()

#set_ota(1716, 4, 'https://travel.interpark.com/checkinnow/goods/GN0002151850')

'''
# 인터파크 신규 URL로 변경
def change_interpark_url():
	with session_scope() as session:
		hotel_items = session.query(Hotel).all()

		for hotel_item in hotel_items:
			link_dict = json.loads(hotel_item.link)
			interpark_link = link_dict.get('4')
			if interpark_link is not None:
				url = interpark_link['url']
				hid = interpark_link['hid']

				resp = requests.get('https://travel.interpark.com/api/checkinnow/goods/check/{}'.format(hid)).json()
				if resp.get('data') == 'NONE':
					continue
				
				link_dict['4'] = dict(url='https://travel.interpark.com/checkinnow/goods/{}'.format(resp['data']), hid=resp['data'])
				print('###', hid, resp['data'], link_dict['4'])
				hotel_item.link = json.dumps(link_dict)
		
		session.commit()

change_interpark_url()
'''
