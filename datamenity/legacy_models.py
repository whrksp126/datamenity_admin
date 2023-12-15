# XXX 지워야함 (기존 코드, postgres)
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy.sql import func

url = 'postgresql://{}:{}@{}:{}/{}'.format(
    'datamenity_service',
    'gldjfh1234',
    'datamenity-rds-production.cekwmwtvw0qx.ap-northeast-2.rds.amazonaws.com',
    5432,
    'flask_datamenity'
)

engine = create_engine(url, echo=False, client_encoding='utf8')
Base = declarative_base()
Session = sessionmaker(bind=engine)


@contextmanager
def postgres_session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

# 계정
class PostgresUser(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    userid = Column(String(300), unique=True, nullable=False)
    username = Column(String(300), nullable=False)
    userpw = Column(String(300), nullable=False)
    create_date = Column(DateTime(), nullable=False)
    pic = Column(String(300), nullable=True)
    pictel = Column(String(300), nullable=True)
    tel = Column(String(300), nullable=True)
    address = Column(String(300), nullable=True)
    address_more = Column(String(300), nullable=True)
    userStatus = Column(String(300), nullable=True)
    plan_start = Column(String(300), nullable=True)
    plan_end = Column(String(300), nullable=True)
    rateplan = Column(String(300), nullable=True)
    lastlogin_date = Column(String(300), nullable=True)

Base.metadata.create_all(engine)
