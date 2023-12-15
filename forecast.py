from datamenity.models import session_scope, HotelReview, HotelReviewSentiment, OTAType, Environment, CompareHasTag, Compare, Hotel, Weather
from datamenity.module.forecast import mapToGrid, gridToMap
import requests
from datetime import datetime, timedelta
import time
import traceback

FORECAST_API_KEY = '17Du%2FGqm4GHdHsn2kJ7EliNMO2xOiyPQAJ05VyXTatpyszC55PbpK8HSE1AgMPCgs%2Fa63UL2qwpwm33mw04bTQ%3D%3D'

def fetch_forecast():
    kst_now = datetime.utcnow() + timedelta(hours=9)
    areas = set()
    with session_scope() as session_db:
        # 모든 호텔의 위경도를 nx, ny 로 변환
        hotels = session_db.query(Hotel).all()
        for h in hotels:
            grid = mapToGrid(h.lat, h.lng)

            if grid[0] < 0 or grid[1] < 0:
                continue
            
            areas.add(grid)
        
        # DB 에 저장된 값을 가지고 옴
        already_exist_item_dict = dict()
        weather_items = session_db.query(Weather).all()
        for weather in weather_items:
            forecast_date = weather.forecast_date
            nx = weather.nx
            ny = weather.ny
            already_exist_item_dict[(forecast_date, nx, ny)] = weather

        # nx, ny 에 대한 날씨 데이터를 result 에 기록한다
        total_len = len(areas)
        idx = 1
        for area in areas:
            nx = area[0]
            ny = area[1]
            
            print('# 1')
            try:
                r = requests.get('http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?serviceKey={}&numOfRows=2000&pageNo=1&dataType=JSON&base_date={}&base_time=0200&nx={}&ny={}'.format(FORECAST_API_KEY, kst_now.strftime('%Y%m%d'), nx, ny)).json()
            except Exception:
                print(traceback.print_exc())
                continue
            
            print('# 2')
            header = r['response']['header']
            if header['resultCode'] != '00':
                print('기상청 API 응답 에러 발생')
                return
            
            print('# 3')
            result = dict()
            for item in r['response']['body']['items']['item']:
                print(item)
                print('# 4')
                fcstDate = item['fcstDate']     # 예보일자
                fcstTime = item['fcstTime']     # 예보시각
                baseDate = item['baseDate']     # 발표일자
                baseTime = item['baseTime']     # 발표시각

                forecast_date = datetime.strptime('{}{}'.format(fcstDate, fcstTime), '%Y%m%d%H%M')
                updated_at = datetime.strptime('{}{}'.format(baseDate, baseTime), '%Y%m%d%H%M')

                print('# 5')
                key = (forecast_date, nx, ny)
                if key not in result:
                    result[key] = dict(forecast_date=forecast_date, nx=nx, ny=ny, updated_at=updated_at)
                
                # 카테고리에 따른 데이터 업데이트
                # hum (REH)
                # pop (POP) 강수확률
                # pty (PTY) 강수형태
                # rain (PCP) 강수량
                # sky (SKY) 1 맑음, 2rnfmaaksgdma, 
                # temp (TMP) 기온
                category = item['category']
                if category == 'REH':
                    result[key]['hum'] = int(item['fcstValue'])
                elif category == 'POP':
                    result[key]['pop'] = int(item['fcstValue'])
                elif category == 'PTY':
                    result[key]['pty'] = int(item['fcstValue'])
                elif category == 'PCP':
                    result[key]['rain'] = item['fcstValue']
                elif category == 'SKY':
                    result[key]['sky'] = int(item['fcstValue'])
                elif category == 'TMP':
                    result[key]['temp'] = int(item['fcstValue'])
                print('# 6')
            print('# 7')

            # update or insert
            for k, v in result.items():
                print('# 8')
                if k in already_exist_item_dict:
                    print('# 9')
                    update_item = already_exist_item_dict[k]
                    update_item.hum = v['hum']
                    update_item.pop = v['pop']
                    update_item.pty = v['pty']
                    update_item.rain = v['rain']
                    update_item.sky = v['sky']
                    update_item.temp = v['temp']
                    update_item.updated_at = v['updated_at']
                else:
                    print('# 10')
                    session_db.add(Weather(k[0], k[1], k[2], updated_at, v['hum'], v['pop'], v['pty'], v['rain'], v['sky'], v['temp']))
            
            print('# 11')
            session_db.commit()
            print('# 12')

            print('## {} / {}'.format(idx, total_len))
            idx += 1
        
        print('####')
        
        '''
        # update or insert 한다
        for k, v in result.items():
            pass
        '''
            

def batch():
    kst_now = datetime.utcnow() + timedelta(hours=9)
    if kst_now.hour != 2 or kst_now.minute != 30:
        return
    
    fetch_forecast()
    time.sleep(60)


if __name__ == '__main__':
    while True:
        batch()
        time.sleep(30)
    #fetch_forecast()