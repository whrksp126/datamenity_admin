import requests
import time


class ExceptionReadTimeout(Exception):
    def __init__(self):
        super().__init__('시간초과로 인한 정보 가져오기 실패')


class OTABase(object):
    def requests_get(self, session_obj, url, params=None, **kwargs):
        for _ in range(1):
            error = None
            try:
                return session_obj.get(url, params=params, **kwargs)
            except requests.exceptions.ReadTimeout:
                error = ExceptionReadTimeout
            except requests.exceptions.ProxyError:
                error = ExceptionReadTimeout
            except requests.exceptions.ChunkedEncodingError:
                error = ExceptionReadTimeout
            except requests.exceptions.SSLError:
                error = ExceptionReadTimeout
            except requests.exceptions.ConnectTimeout:
                error = ExceptionReadTimeout
        
        raise error
        
    def requests_post(self, session_obj, url, data=None, json=None, **kwargs):
        for _ in range(1):
            error = None
            try:
                return session_obj.post(url, data=data, json=json, **kwargs)
            except requests.exceptions.ReadTimeout:
                error = ExceptionReadTimeout
            except requests.exceptions.ProxyError:
                error = ExceptionReadTimeout
            except requests.exceptions.ChunkedEncodingError:
                error = ExceptionReadTimeout
            except requests.exceptions.SSLError:
                error = ExceptionReadTimeout
            except requests.exceptions.ConnectTimeout:
                error = ExceptionReadTimeout
        
        raise error

    def get_hotel_id(self, args, url):
        raise NotImplementedError("Subclasses must overide get_hotel_id()")

    def scrape_prices_preprocess(self, args, url, hotel_id, checkin, checkout):
        return dict(code=200)
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        raise NotImplementedError("Subclasses must overide scrape_prices()")

    def scrape_reviews_preprocess(self):
        return None

    def scrape_reviews(self, output, args, url, hotel_id, page):
        raise NotImplementedError("Subclasses must overide scrape_reviews()")
