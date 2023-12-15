from sqlalchemy import BIGINT, Column, Integer, BigInteger, String, Text, Date, Boolean, DateTime, ForeignKey, Enum, Index, UniqueConstraint, Float, Numeric, ForeignKeyConstraint
from werkzeug.security import generate_password_hash
  
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy.sql import func
  
from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.types import TypeDecorator

from datamenity.config import DATABASE_HOST, DATABASE_DB, DATABASE_PORT, DATABASE_PASSWORD, DATABASE_USER

import json
import enum
import datetime

url = 'mysql://{}:{}@{}:{}/{}'.format(
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_HOST,
    DATABASE_PORT,
    DATABASE_DB
)
  
engine = create_engine(url, echo=False, connect_args={'charset': 'utf8'}, pool_pre_ping=True, pool_size=20, max_overflow=100)
Base = declarative_base()
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


# 변경시 datamenity/crawler.py 파일도 수정
class OTAType(enum.Enum):
    GOODCHOICE = ('GOODCHOICE', '여기어때')
    BOOKING = ('BOOKING', '부킹닷컴')
    EXPEDIA = ('EXPEDIA', '익스피디아')
    AGODA = ('AGODA', '아고다')
    INTERPARK = ('INTERPARK', '인터파크')
    YANOLJA = ('YANOLJA', '야놀자')
    DAILY = ('YANOLJA', '데일리호텔')
    HOTELS = ('HOTELS', '호텔스닷컴')
    TRIP = ('TRIP', '트립닷컴')
    WINGS = ('WINGS', '윙스부킹')
    KENSINGTON = ('KENSINGTON', '켄싱턴')
    IKYU = ('IKYU', 'ikyu (일본)')
    RAKUTEN = ('RAKUTEN', 'Rakuten (일본)')
    JALAN = ('JALAN', 'Jalan (일본)')
    
    def __init__(self, title, description):
        self.title = title
        self.description = description


class UserType(Base):
    __tablename__ = 'user_type'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), nullable=False)
    rule = Column(Text, nullable=False, default='{}')

    def __init__(self, name, rule):
        self.name = name
        self.rule = rule


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(128), nullable=False, unique=True)
    user_pw = Column(String(512), nullable=False)
    user_type = Column(Integer, ForeignKey('user_type.id'), default=None)
    otas = Column(BigInteger, nullable=False, default=0)
    name = Column(String(128), nullable=False)
    manager_name = Column(String(16), nullable=False, default='')
    manager_tel = Column(String(16), nullable=False, default='')
    tel = Column(String(16), nullable=False, default='')
    address = Column(String(32), nullable=False, default='')
    address2 = Column(String(32), nullable=False, default='')
    hotel_id = Column(Integer, ForeignKey('hotel.id'), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    last_logged_at = Column(DateTime, nullable=True, default=None)
    otas_order = Column(String(256), nullable=False, default='[]')
    started_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    hotel_limit = Column(Integer, nullable=False)
    ota_limit = Column(Integer, nullable=False)
    festival_distance = Column(Integer, nullable=False, default=25)

    def __init__(self, user_id, user_pw, name, user_type, manager_name, manager_tel, tel, address, address2, hotel_id, otas, otas_order, started_at, ended_at, hotel_limit, ota_limit, festival_distance):
        self.user_id = user_id
        self.user_pw = generate_password_hash(user_pw)
        self.name = name
        self.user_type = user_type
        self.manager_name = manager_name
        self.manager_tel = manager_tel
        self.tel = tel
        self.address = address
        self.address2 = address2
        self.hotel_id = hotel_id
        self.otas = otas
        self.otas_order = otas_order
        self.started_at = started_at
        self.ended_at = ended_at
        self.hotel_limit = hotel_limit
        self.ota_limit = ota_limit
        self.festival_distance = festival_distance

    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def todict(self):
        return dict(
            id=self.id, 
            user_id=self.user_id,
            user_type=self.user_type,
            name=self.name, 
            created_at=(self.created_at + datetime.timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S'),
            last_logged_at='' if self.last_logged_at is None else (self.last_logged_at + datetime.timedelta(hours=0)).strftime('%Y-%m-%d %H:%M:%S'),
        )


# increase 넘버 조정
class Hotel(Base):
    __tablename__ = 'hotel'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    link = Column(Text, nullable=False, default='{}')
    addr = Column(String(128), nullable=False, default='')
    road_addr = Column(String(128), nullable=False, default='')
    lat = Column(Float, nullable=False, default=0)
    lng = Column(Float, nullable=False, default=0)
    roomtype_setting = Column(Text, nullable=True, default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, name, link, addr, road_addr, lat, lng):
        self.name = name
        self.link = link
        self.addr = addr
        self.road_addr = road_addr
        self.lat = lat
        self.lng = lng
    
    def todict(self):
        return dict(
            id=self.id, 
            name=self.name, 
            link=json.loads(self.link),
            addr=self.addr,
            road_addr=self.road_addr,
            created_at=self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        )


# increase 넘버 조정
class Room(Base):
    __tablename__ = 'room'
    __table_args__ = (UniqueConstraint('hotel_id', 'ota_type', 'name'),)
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    hotel_id = Column(Integer, ForeignKey('hotel.id'), nullable=False)
    ota_type = Column(Enum(OTAType), nullable=False)
    name = Column(String(512), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    normal_updated_at = Column(DateTime, nullable=True, default=None)

    def __init__(self, hotel_id, ota_type, name):
        self.hotel_id = hotel_id
        self.ota_type = ota_type
        self.name = name


class RoomPrice(Base):
    __tablename__ = 'room_price'
    booking_date = Column(DateTime, primary_key=True)
    room_id = Column(BigInteger, ForeignKey('room.id'), primary_key=True)
    scanned_date = Column(DateTime, primary_key=True)
    rent_price = Column(Integer, nullable=False)    # error code 는 음수로 표기
    stay_price = Column(Integer, nullable=False)    # error code 는 음수로 표기
    rent_remain = Column(Integer, nullable=False)
    stay_remain = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, booking_date, room_id, scanned_date, rent_price, stay_price, rent_remain, stay_remain):
        self.booking_date = booking_date
        self.room_id = room_id
        self.scanned_date = scanned_date
        self.rent_price = rent_price
        self.stay_price = stay_price
        self.rent_remain = rent_remain
        self.stay_remain = stay_remain


class RoomPriceCurrent(Base):
    __tablename__ = 'room_price_curr'
    booking_date = Column(DateTime, primary_key=True)
    room_id = Column(BigInteger, ForeignKey('room.id'), primary_key=True)
    rent_price = Column(Integer, nullable=False)    # error code 는 음수로 표기
    stay_price = Column(Integer, nullable=False)    # error code 는 음수로 표기
    rent_remain = Column(Integer, nullable=False)
    stay_remain = Column(Integer, nullable=False)
    last_date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, booking_date, room_id, last_date, rent_price, stay_price, rent_remain, stay_remain):
        self.booking_date = booking_date
        self.room_id = room_id
        self.last_date = last_date
        self.rent_price = rent_price
        self.stay_price = stay_price
        self.rent_remain = rent_remain
        self.stay_remain = stay_remain


class RoomTag(Base):
    __tablename__ = 'room_tag'
    __table_args__ = (UniqueConstraint('hotel_id', 'name'),)
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    hotel_id = Column(Integer, ForeignKey('hotel.id'), nullable=False)
    name = Column(String(64), nullable=False)
    priority = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, hotel_id, name, priority):
        self.hotel_id = hotel_id
        self.name = name
        self.priority = priority


class RoomTagHasRoom(Base):
    __tablename__ = 'room_tag_has_room'
    room_tag_id = Column(BigInteger, ForeignKey('room_tag.id'), primary_key=True)
    room_id = Column(BigInteger, ForeignKey('room.id'), primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, room_tag_id, room_id):
        self.room_tag_id = room_tag_id
        self.room_id = room_id


class Compare(Base):
    __tablename__ = 'compare'
    __table_args__ = (UniqueConstraint('owner', 'name'),)       # TODO : 추가해야함
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    owner = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    name = Column(String(64), nullable=False)
    priority = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, owner, name, priority):
        self.owner = owner
        self.name = name
        self.priority = priority


class CompareHasTag(Base):
    __tablename__ = 'compare_has_tag'
    compare_id = Column(BigInteger, ForeignKey('compare.id'), primary_key=True)
    room_tag_id = Column(BigInteger, ForeignKey('room_tag.id'), primary_key=True)

    def __init__(self, compare_id, room_tag_id, priority):
        self.compare_id = compare_id
        self.room_tag_id = room_tag_id


class CrawlerRule(Base):
    __tablename__ = 'crawler_rule'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    range = Column(Integer, nullable=False)
    time = Column(Integer, nullable=False)
    hotel_limit = Column(Integer, nullable=False)
    ota_limit = Column(Integer, nullable=False)

    def __init__(self, name, range, time, hotel_limit, ota_limit):
        self.name = name
        self.range = range
        self.time = time
        self.hotel_limit = hotel_limit
        self.ota_limit = ota_limit
    
    def todict(self):
        time_list = []
        for i in range(25):
            is_set = (self.time & (1 << i)) > 0
            if is_set:
                time_list.append(str(i))
        
        return dict(
            id=self.id, 
            name=self.name,
            range=self.range,
            time=self.time,
            description='{}) {}일 - {}시, hotel {}개, ota {}개'\
                        .format(self.name.split('_')[0] ,self.range, ', '.join(time_list), self.hotel_limit, self.ota_limit),
        )


class UserHasCrawlerRule(Base):
    __tablename__ = 'user_has_crawler_rule'
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    crawler_rule_id = Column(Integer, ForeignKey('crawler_rule.id'), primary_key=True)

    def __init__(self, user_id, crawler_rule_id):
        self.user_id = user_id
        self.crawler_rule_id = crawler_rule_id


class UserHasCompetition(Base):
    __tablename__ = 'user_has_competition'
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    competition_id = Column(Integer, ForeignKey('hotel.id'), primary_key=True, index=True)
    priority = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    def __init__(self, user_id, competition_id, priority, created_at):
        self.user_id = user_id
        self.competition_id = competition_id
        self.priority = priority
        self.created_at = created_at


class HotelReview(Base):
    __tablename__ = 'hotel_review'
    hotel_id = Column(Integer, ForeignKey('hotel.id'), primary_key=True)
    ota_type = Column(Enum(OTAType), nullable=False, primary_key=True)
    review_id = Column(String(32), nullable=False, primary_key=True)
    author = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    reply = Column(Text, nullable=False, default='[]')
    created_at = Column(DateTime, nullable=False, index=True)
    ota_category = Column(String, nullable=False, default='')
    sentiment_category = Column(String(256), nullable=False, default='')
    sentiment_score = Column(Float, nullable=True, default=None)
    tokenized = Column(Text, nullable=True, default=None)
 
    def __init__(self, hotel_id, ota_type, review_id, author, content, score, reply, created_at):
        self.hotel_id = hotel_id
        self.ota_type = ota_type
        self.review_id = review_id
        self.author = author
        self.content = content
        self.score = score
        self.reply = reply
        self.created_at = created_at


class HotelReviewMeta(Base):
    __tablename__ = 'hotel_review_meta'
    hotel_id = Column(Integer, ForeignKey('hotel.id'), primary_key=True)
    ota_type = Column(Enum(OTAType), nullable=False, primary_key=True)
    score = Column(Float, nullable=False)
    count = Column(Integer, nullable=False)
    executed_at = Column(DateTime, nullable=False)

    def __init__(self, hotel_id, ota_type, score, count, executed_at):
        self.hotel_id = hotel_id
        self.ota_type = ota_type
        self.score = score
        self.count = count
        self.executed_at = executed_at


class HotelReviewSentiment(Base):
    __tablename__ = 'hotel_review_sentiment'
    hotel_id = Column(Integer, ForeignKey('hotel.id'), primary_key=True)
    category = Column(String(32), nullable=False, primary_key=True)
    tokenized = Column(Text, nullable=False)
    positive_reviews = Column(Integer, nullable=False)
    neutrality_reviews = Column(Integer, nullable=False)
    negative_reviews = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
 
    def __init__(self, hotel_id, category, tokenized, positive_reviews, neutrality_reviews, negative_reviews):
        self.hotel_id = hotel_id
        self.category = category
        self.tokenized = tokenized
        self.positive_reviews = positive_reviews
        self.neutrality_reviews = neutrality_reviews
        self.negative_reviews = negative_reviews


class LogScheduler(Base):
    __tablename__ = 'log_scheduler'
    crawler_type = Column(String(16), primary_key=True)
    hour = Column(Integer, primary_key=True)
    works_count = Column(Integer, nullable=False)
    error_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=None)

    def __init__(self, crawler_type, hour, works_count):
        self.crawler_type = crawler_type
        self.hour = hour
        self.works_count = works_count


class LogCrawler(Base):
    __tablename__ = 'log_crawler'
    crawler_type = Column(String(16), primary_key=True)
    hour = Column(Integer, primary_key=True)
    hotel_id = Column(Integer, ForeignKey('hotel.id'), primary_key=True)
    ota = Column(Integer, primary_key=True)
    rule = Column(Text, nullable=False, default='{}')
    output = Column(Text, nullable=False)
    error = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, crawler_type, hour, hotel_id, ota, rule, output, error):
        self.crawler_type = crawler_type
        self.hour = hour
        self.hotel_id = hotel_id
        self.ota = ota
        self.rule = rule
        self.output = output
        self.error = error


class Environment(Base):
    __tablename__ = 'environment'
    key = Column(String(32), primary_key=True)
    value = Column(Text, nullable=False, default='{}')
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, key, value):
        self.key = key
        self.value = value


# 사용자 그룹
class UserGroup(Base):
    __tablename__ = 'usergroup'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, name):
        self.name = name
    
    def todict(self):
        return dict(
            id=self.id, 
            name=self.name,
            created_at=self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        )


class UserToUserGroup(Base):
    __tablename__ = 'user_to_usergroup'
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, primary_key=True)
    usergroup_id = Column(Integer, ForeignKey('usergroup.id'), nullable=False, primary_key=True)

    def __init__(self, user_id, usergroup_id):
        self.user_id = user_id
        self.usergroup_id = usergroup_id


# 배너
class BannerType(Base):
    __tablename__ = 'banner_type'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), nullable=False)

    def __init__(self, name):
        self.name = name


class Banner(Base):
    __tablename__ = 'banner'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(32), nullable=False)
    banner_type = Column(Integer, ForeignKey('banner_type.id'), nullable=False)
    url = Column(String(256), nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    background_color = Column(String(32), nullable=False, default='#ffffff')
    link = Column(String(256), nullable=True)

    def __init__(self, name, banner_type, url, started_at, ended_at, background_color, link):
        self.name = name
        self.banner_type = banner_type
        self.url = url
        self.started_at = started_at
        self.ended_at = ended_at
        self.background_color = background_color
        self.link = link
            

    def todict(self):
        return dict(
            id=self.id, 
            name=self.name,
            banner_type=self.banner_type,
            url=self.url,
            started_at=self.started_at.strftime('%Y-%m-%d %H:%M:%S'),
            ended_at=self.ended_at.strftime('%Y-%m-%d %H:%M:%S'),
            created_at=self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            background_color=self.background_color
        )

class UserGroupHasBanner(Base):
    __tablename__ = 'usergroup_has_banner'
    usergroup_id = Column(Integer, ForeignKey('usergroup.id'), nullable=False, primary_key=True)
    banner_id = Column(Integer, ForeignKey('banner.id'), nullable=False, primary_key=True)

    def __init__(self, usergroup_id, banner_id):
        self.usergroup_id = usergroup_id
        self.banner_id = banner_id


class Weather(Base):
    __tablename__ = 'weather'
    forecast_date = Column(DateTime, primary_key=True)
    nx = Column(Integer, nullable=False, primary_key=True)
    ny = Column(Integer, nullable=False, primary_key=True)
    updated_at = Column(DateTime, nullable=False)
    hum = Column(Integer, nullable=True, default=None)      # 습도
    pop = Column(Integer, nullable=True, default=None)      # 강수확률
    pty = Column(Integer, nullable=True, default=None)      # 강수형태
    rain = Column(String(16), nullable=True, default=None)  # 강수량
    sky = Column(Integer, nullable=True, default=None)      # 하늘상태
    temp = Column(Integer, nullable=True, default=None)     # 기온

    def __init__(self, forecast_date, nx, ny, updated_at, hum, pop, pty, rain, sky, temp):
        self.forecast_date = forecast_date
        self.nx = nx
        self.ny = ny
        self.updated_at = updated_at
        self.hum = hum
        self.pop = pop
        self.pty = pty
        self.rain = rain
        self.sky = sky
        self.temp = temp


class Festival(Base):
    __tablename__ = 'festival'
    id = Column(Integer, primary_key=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(50), nullable=False, default='#E64B35')
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=False)
    author = Column(Integer, ForeignKey('user.id'), nullable=True)
    lat = Column(Float, nullable=False, default=0)
    lng = Column(Float, nullable=False, default=0)
    category_id = Column(Integer, ForeignKey('festival_category.id'), nullable=False)

    def __init__(self, title, description, color, started_at, ended_at, author, lat, lng, category_id):
        self.title = title
        self.description = description
        self.color = color
        self.started_at = started_at
        self.ended_at = ended_at
        self.author = author
        self.lat = lat
        self.lng = lng
        self.category_id = category_id


class FestivalCategory(Base):
    __tablename__ = 'festival_category'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    def __init__(self, name):
        self.name = name


class HotelHasCompetition(Base):
    __tablename__ = 'hotel_has_competition'
    hotel_id = Column(Integer, ForeignKey('hotel.id'), primary_key=True)
    competition_id = Column(Integer, ForeignKey('hotel.id'), primary_key=True)

    def __init__(self, hotel_id, competition_id):
        self.hotel_id = hotel_id
        self.competition_id = competition_id

class HotelHasCrawlerRule(Base):
    __tablename__ = 'hotel_has_crawler_rule'
    hotel_id = Column(Integer, ForeignKey('hotel.id'), primary_key=True)
    crawler_rule_id = Column(Integer, ForeignKey('crawler_rule.id'), primary_key=True)

    def __init__(self, hotel_id, crawler_rule_id):
        self.hotel_id = hotel_id
        self.crawler_rule_id = crawler_rule_id


class HotelError(Base):
    __tablename__ = 'hotel_error'
    hotel_id = Column(Integer, ForeignKey('hotel.id'), nullable=False, primary_key=True)
    ota_type = Column(Enum(OTAType), nullable=False, primary_key=True)
    scanned_at = Column(DateTime, nullable=False, primary_key=True)
    hotel_error_type = Column(Integer, ForeignKey('hotel_error_type.id'), nullable=True, default=None)
    memo = Column(Text, nullable=False, default='')
    is_fix = Column(Boolean, nullable=False, default=False)
    fixed_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(DateTime, nullable=True, default=None)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, hotel_id, ota_type, scanned_at, hotel_error_type, memo):
        self.hotel_id = hotel_id
        self.ota_type = ota_type
        self.scanned_at = scanned_at
        self.updated_at = scanned_at
        self.hotel_error_type = hotel_error_type
        self.memo = memo
    
    def todict(self):
        return dict(
            id=self.hotel_id, 
            ota_type=self.ota_type,
            scanned_at=self.scanned_at,
            hotel_error_type=self.hotel_error_type, 
            is_fix=self.is_fix,
            created_at=(self.created_at + datetime.timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S'),
        )


class HotelErrorType(Base):
    __tablename__ = 'hotel_error_type'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=False, default='')
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, name, description):
        self.name = name
        self.description = description


Base.metadata.create_all(engine)
