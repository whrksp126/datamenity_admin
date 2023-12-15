from datamenity.models import session_scope, HotelReview, HotelReviewSentiment, OTAType, Environment
from sqlalchemy import and_, or_


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 경고 뜨지 않게 설정
import warnings
warnings.filterwarnings('ignore')

# 그래프 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
# plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['font.size'] = 16
plt.rcParams['figure.figsize'] = 20, 10
plt.rcParams['axes.unicode_minus'] = False

# 데이터 전처리 알고리즘
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler

# 학습용과 검증용으로 나누는 함수
from sklearn.model_selection import train_test_split

# 교차 검증
# 지표를 하나만 설정할 경우
from sklearn.model_selection import cross_val_score
# 지표를 하나 이상 설정할 경우
from sklearn.model_selection import cross_validate
from sklearn.model_selection import KFold
from sklearn.model_selection import StratifiedKFold

# 모델의 최적의 하이퍼파라미터를 찾기 위한 도구
from sklearn.model_selection import GridSearchCV

# 평가함수
# 분류용
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import roc_auc_score

# 회귀용
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error

# 머신러닝 알고리즘 - 분류
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import GradientBoostingClassifier
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
from sklearn.ensemble import VotingClassifier

# 머신러닝 알고리즘 - 회귀
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge
from sklearn.linear_model import Lasso
from sklearn.linear_model import ElasticNet
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import GradientBoostingRegressor
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from sklearn.ensemble import VotingRegressor

# 차원축소
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

# 군집화
from sklearn.cluster import KMeans
from sklearn.cluster import MeanShift
from sklearn.cluster import estimate_bandwidth

# ARIMA (시계열 예측)
from statsmodels.tsa.arima_model import ARIMA
import statsmodels.api as sm

# 시간 측정을 위한 시간 모듈
import datetime

# 주식정보
from pandas_datareader import data

# 형태소 벡터를 생성하기 위한 라이브러리
from sklearn.feature_extraction.text import CountVectorizer
# 형태소 벡터를 학습 벡터로 변환한다.
from sklearn.feature_extraction.text import TfidfVectorizer

# 데이터 수집
import requests
from bs4 import BeautifulSoup
import re
import time
import os
import json

# 한국어 형태소 분석
from konlpy.tag import Okt, Hannanum, Kkma, Mecab, Komoran

# 워드 클라우드를 위한 라이브러리
#from collections import Counter
#import pytagcloud
#from IPython.display import Image

# 저장
import pickle


# 순수 한글 추출
def get_korean(text): 
    hangul = re.compile(' [^ㄱ-ㅣ가-힣]+')
    result = hangul.sub('', text)
    #result.replace('켄싱턴리조트', '')
    return result


# konlpy 라이브러리로 텍스트 데이터에서 형태소를 추출한다.
def get_pos(x):
    tagger = Okt()
    pos = tagger.pos(x)

    result = []

    for a1 in pos :
        result.append(f'{a1[0]}/{a1[1]}')
    
    return result


# 로지스틱 회귀 모델
def logistic(X, y, kfold):
    params = {
        'penalty' : ['l1', 'l2', 'elasticnet', 'none'],
        'C' : [0.0001, 0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000]
    }
    model = LogisticRegression()

    grid_clf = GridSearchCV(model, param_grid=params, scoring='f1', cv=kfold)
    grid_clf.fit(X, y)

    print(f'best_params : {grid_clf.best_params_}')
    print(f'best_score : {grid_clf.best_score_}')

    # 모델 저장
    with open('review_model.pkl', 'wb') as f:
        pickle.dump(grid_clf, f)

    return grid_clf


def learn_model():
    code = 0
    keyword = ''

    with session_scope() as session:
        # 전체 리뷰를 DB 에서 가져온다
        print('## {}'.format(keyword))

        hotel_reviews_pos = session.query(HotelReview).filter(
            HotelReview.score <= 10, 
            HotelReview.score >= 9, 
            HotelReview.ota_type.in_([OTAType.YANOLJA, OTAType.AGODA, OTAType.EXPEDIA, OTAType.DAILY, OTAType.HOTELS])
        )
        hotel_reviews_neg = session.query(HotelReview).filter(
            HotelReview.score <= 5, 
            HotelReview.ota_type.in_([OTAType.YANOLJA, OTAType.AGODA, OTAType.EXPEDIA, OTAType.DAILY, OTAType.HOTELS])
        )

        if code == 3:
            hotel_reviews_pos = hotel_reviews_pos.filter(or_(HotelReview.content.like('%위치%'), HotelReview.content.like('%교통%')))
            hotel_reviews_neg = hotel_reviews_neg.filter(or_(HotelReview.content.like('%위치%'), HotelReview.content.like('%교통%')))
        elif 0 < code < 8:
            hotel_reviews_pos = hotel_reviews_pos.filter(HotelReview.content.like('%{}%'.format(keyword)))
            hotel_reviews_neg = hotel_reviews_neg.filter(HotelReview.content.like('%{}%'.format(keyword)))
        elif code == 8:
            for k in ['가격', '청결', '위치/교통', '부대시설', '서비스', '객실', '조망']:
                hotel_reviews_pos = hotel_reviews_pos.filter(HotelReview.content.not_like('%{}%'.format(k)))
                hotel_reviews_neg = hotel_reviews_neg.filter(HotelReview.content.not_like('%{}%'.format(k)))
        
        hotel_reviews_pos = hotel_reviews_pos.all()
        hotel_reviews_neg = hotel_reviews_neg.all()

        datas_pos = [(review.score, 1, get_korean(review.content)) for review in hotel_reviews_pos]
        datas_neg = [(review.score, 0, get_korean(review.content)) for review in hotel_reviews_neg]
        datas = datas_pos + datas_neg
        print(len(datas))

        # dataframe 으로 변형
        df = pd.DataFrame(datas, columns=['score', 'y', 'review']) 

        # TF-IDF 벡터 (형태소의 정규화된 벡터) 얻는다
        tfidf_vectorizer = TfidfVectorizer(tokenizer=lambda x : get_pos(x))
        X = tfidf_vectorizer.fit_transform(df["review"].tolist())
        #print(tfidf_vectorizer.vocabulary_)

        # ML 생성 및 학습
        y = df["y"]
        kfold = KFold(n_splits=10, shuffle=True, random_state = 1)

        grid_clf = logistic(X, y, kfold)
        
        # 중요 단어 파악
        model = grid_clf.best_estimator_

        # 상관관계수 구하기
        a1 = (model.coef_[0])
        a2 = list(enumerate(a1))
        a3 = []
        for idx, value in a2:
            a3.append((value, idx))
        coef_pos_index = sorted(a3, reverse=True)

        # 새로운 딕셔너리 생성
        text_data_dict = {}

        # 단어 사전에 있는 단어의 수만큼 반복한다.
        for key in tfidf_vectorizer.vocabulary_ :
            # 현재 key에 해당하는 값을 가져온다.
            value = tfidf_vectorizer.vocabulary_[key]
            
            # 위의 딕셔너리에 담는다.
            text_data_dict[value] = key
            
        # 긍정적인 어조 (상관계수가 1에 가장 큰)
        top20 = coef_pos_index[:20]
        # 부정적인 어조
        bottom20 = coef_pos_index[-20:]

        # 긍정, 부정 키워드 출력
        for value, idx in top20:
            print(text_data_dict[idx])
        print('---')
        for value, idx in bottom20:
            print(text_data_dict[idx])
        
        # 모델 저장
        with open('review_model_voca_{}.pkl'.format(code), 'wb') as f:
            pickle.dump(tfidf_vectorizer.vocabulary_, f)
        
        with open('review_model_{}.pkl'.format(code), 'wb') as f:
            pickle.dump(model, f)


# 리뷰 예측
def predict_reviews():
    with open('review_model_0.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('review_model_voca_0.pkl', 'rb') as f:
        vocaburary = pickle.load(f)

    # 상관관계수 구하기
    a1 = (model.coef_[0])
    a2 = list(enumerate(a1))
    a3 = []
    for idx, value in a2:
        a3.append((value, idx))
    coef_pos_index = sorted(a3, reverse=True)

    # 새로운 딕셔너리 생성
    text_data_dict = {}

    # 단어 사전에 있는 단어의 수만큼 반복한다.
    for key in vocaburary :
        # 현재 key에 해당하는 값을 가져온다.
        value = vocaburary[key]
        
        # 위의 딕셔너리에 담는다.
        text_data_dict[value] = key
    
    keyword_to_coef = dict()
    for value, idx in coef_pos_index:
        keyword_to_coef[text_data_dict[idx]] = value
    
    # 긍정, 부정 키워드 출력
    '''
    top20 = coef_pos_index[:2000]
    bottom20 = coef_pos_index[-2000:]
    for value, idx in top20:
        print('"{}", {}, ""'.format(text_data_dict[idx], value))
    for value, idx in bottom20:
        print('"{}", {}, ""'.format(text_data_dict[idx], value))
    
    with open('words.csv', 'w') as f:
        for value, idx in coef_pos_index:
            f.write('"{}", {}\n'.format(text_data_dict[idx], value))
    '''

    with session_scope() as session:
        # 전체 리뷰를 DB 에서 가져온다
        hotel_reviews = session.query(HotelReview).filter(HotelReview.sentiment_score.is_(None)).all()
        total = len(hotel_reviews)
        idx = 0

        for review in hotel_reviews:
            if review.tokenized == None:
                pos = get_pos(review.content)
                word_count = dict()
                score = 0
                for p in pos:
                    if p in keyword_to_coef:
                        if p not in word_count:
                            word_count[p] = 0
                        word_count[p] += 1
                        score += keyword_to_coef[p]
                review.tokenized = json.dumps([(k, v) for k, v in word_count.items()])
                review.sentiment_score = score
                print(review.sentiment_score, review.tokenized)
            
            idx += 1
            print('{}/{}'.format(idx, total))

            if idx % 1000 == 0:
                session.commit()
        
        session.commit()


def update_sentiment_category():
    df = pd.read_csv('words_data.csv', encoding='utf-8', )

    keyword_to_category = dict()
    keyword_to_category_db = dict()
    idx = 0
    for i in range(len(df['keyword'])):
        if type(df['category'][i]) != str:
            continue
        
        keyword = df['keyword'][i]
        category = df['category'][i]
        keyword_to_category[keyword] = set(category.split('/'))
        keyword_to_category_db[keyword] = category

        idx += 1
        if idx == 400:
            break
    
    idx = 0
    for i in reversed(range(len(df['keyword']))):
        if type(df['category'][i]) != str:
            continue
        
        keyword = df['keyword'][i]
        category = df['category'][i]
        keyword_to_category[keyword] = set(category.split('/'))
        keyword_to_category_db[keyword] = category

        idx += 1
        if idx == 400:
            break

    with session_scope() as session:
        # 전체 리뷰를 DB 에서 가져온다
        hotel_reviews = session.query(HotelReview).filter(HotelReview.sentiment_category == '').all()

        total = len(hotel_reviews)
        print('##', total)

        i = 0
        for review in hotel_reviews:
            if review.tokenized is None:
                continue
            tokenized = json.loads(review.tokenized)
            categories = set()
            for t in tokenized:
                if t[0] in keyword_to_category:
                    categories |= keyword_to_category[t[0]]
            
            review.sentiment_category = '/'.join(categories)
            if i % 1000 == 0:
                session.commit()
            i += 1
            print('{}/{}'.format(i, total))

        # 카테고리 저장
        keyword_cat = session.query(Environment).filter(Environment.key == 'SENTIMENT_CATEGORY').first()
        keyword_cat.value = json.dumps(keyword_to_category_db)
        session.commit()


def update_environment():
    with open('review_model_0.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('review_model_voca_0.pkl', 'rb') as f:
        vocaburary = pickle.load(f)

    # 상관관계수 구하기
    a1 = (model.coef_[0])
    a2 = list(enumerate(a1))
    a3 = []
    for idx, value in a2:
        a3.append((value, idx))
    coef_pos_index = sorted(a3, reverse=True)

    # 새로운 딕셔너리 생성
    text_data_dict = {}

    # 단어 사전에 있는 단어의 수만큼 반복한다.
    for key in vocaburary :
        # 현재 key에 해당하는 값을 가져온다.
        value = vocaburary[key]
        
        # 위의 딕셔너리에 담는다.
        text_data_dict[value] = key
    
    keyword_to_coef = dict()
    for value, idx in coef_pos_index[:500] + coef_pos_index[-500:]:
        keyword_to_coef[text_data_dict[idx]] = value

    with session_scope() as session:
        keyword = session.query(Environment).filter(Environment.key == 'SENTIMENT_KEYWORD').first()
        keyword.value = json.dumps(keyword_to_coef)

        session.commit()


# 모델 학습
#learn_model()

# 리뷰 예측
predict_reviews()

# 감정 카테고리 업데이트
update_sentiment_category()

# 환경 업데이트
#update_environment()

# 
#predict_reviews()
