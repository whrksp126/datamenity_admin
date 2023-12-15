from datamenity.models import Compare, CompareHasTag, Environment, User, UserHasCompetition, session_scope, Room, Hotel, RoomTag, RoomTagHasRoom, RoomPrice, RoomPriceCurrent, CrawlerRule, Hotel, LogScheduler, LogCrawler, OTAType
from datamenity.log import print_log
from soynlp.hangle import levenshtein, decompose
from datetime import datetime, timedelta
import json

def get_len(keyword):
    length = 0
    for c in keyword:
        if ord('가') <= ord(c) <= ord('힣'):
            length += 3
        else:
            length += 1
    return length

# 편집거리 기반, s1 문자열 내의 s2 문자열 위치를 찾는다
# s1 안의 문자열 s2 포함에 대한 오차 허용은 2자이다.
def find_keyword(s1, s2, debug=False):
    if len(s1) < len(s2):
        return find_keyword(s2, s1, debug)

    if len(s2) == 0:
        return dict(pos=0, match=0)

    def substitution_cost(c1, c2):
        # 같으면, 초중종성이 같으므로 3
        #if c1 == c2:
        #    return 3
        
        # 한글 확인
        is_c1_kor = False
        is_c2_kor = False
        if ord('가') <= ord(c1) <= ord('힣'):
            is_c1_kor = True
        if ord('가') <= ord(c2) <= ord('힣'):
            is_c2_kor = True
        
        # 같은 만큼 가중치
        if is_c1_kor and is_c2_kor:     # 둘다 한글일 때
            return 3 - levenshtein(decompose(c1), decompose(c2))
        elif is_c1_kor or is_c2_kor:    # 각각 한글, 한글아닐때 -> 매칭안됨
            return 0
        else:                           # 둘다 영문/특수문자일때 -> 매칭확인
            return 1 if c1.lower() == c2.lower() else 0

    pos = -1
    max_val = 0
    previous_row = [0 for _ in range(len(s2) + 1)]
    for i, c1 in enumerate(s1):
        current_row = [0]
        for j, c2 in enumerate(s2):
            # 테이블에 값 기록
            insertions = previous_row[0]
            deletions = current_row[j]
            substitutions = previous_row[j] + substitution_cost(c1, c2)
            curr_val = max(insertions, deletions, substitutions)
            current_row.append(curr_val)

            # 최대매칭일 경우 위치를 기록
            if max_val < curr_val:
                max_val = curr_val
                pos = i

        # 디버그모드일 경우 출력
        if debug:
            print(['%3d'%v for v in current_row[1:]])

        # 행단위 테이블 생성으로 메모리 최소화
        previous_row = current_row

    return dict(pos=pos, match=max_val)


# step 1을 수행하는 함수
# setting, 객실명을 통해 roomtype을 판정하는 함수 (roomtype 이름이 반환됨)
# setting 형태는 다음과 같음 (dist 는 판정시 허용할 자모음 오차 거리, weight 는 판정시 가중치 높은게 우선)
'''
[{
    'name':'대분류명',
    'items': [{
        'name': '중분류명',
        'items': [{'name': '소분류명', dist: 3, weight: 10}, ...]
    }, ...]
}, ...]
'''
def judge_roomtype_step1(output, room_name, setting):
    print_log(output, '# 1단계 수행', True)

    check_list = []
    priority = 0
    for main_category in setting:
        for middle_category in main_category['items']:
            for sub_category in middle_category['items']:
                check_list.append(dict(
                    keyword=sub_category['name'],
                    dist=int(sub_category['dist']),
                    weight=int(sub_category['weight']),
                    mid_result=middle_category['name'],
                    result=main_category['name'],
                    priority=priority
                ))
        priority += 1
    
    curr_weight = -1
    selected_item = None
    for item in check_list:
        keyword = item['keyword']
        threshold = get_len(keyword) - item['dist']       # 판정 허용 경계선 계산
        result = find_keyword(room_name, keyword)           # 판정 진행
        if result['match'] < threshold:                     # 만약 경계선 이하라면 넘어감
            continue

        # 경계선 이상의 키워드라면, 가중치를 비교하여 룸타입 판정
        print_log(output, '{} > {} > {} (weight: {})'.format(item['result'], item['mid_result'], item['keyword'], item['weight']), True)
        weight = item['weight']
        if curr_weight < weight:
            curr_weight = weight
            selected_item = item
    
    if selected_item is None:
        print_log(output, '## {} (없음)'.format(room_name), True)
    else:
        print_log(output, '## {} ({} > {} > {})'.format(room_name, selected_item['result'], selected_item['mid_result'], selected_item['keyword']), True)
    return selected_item


def judge_roomtype_step2(output, hotel_id, price):
    print_log(output, '# 2단계 수행', True)
    
    kst_now = datetime.utcnow() + timedelta(hours=9)
    selected_item = None

    with session_scope() as session:
        rooms = session.query(RoomTag.name, Room.id, Room.name.label('room_name')) \
            .join(RoomTagHasRoom, RoomTag.id == RoomTagHasRoom.room_tag_id) \
            .join(Room, Room.id == RoomTagHasRoom.room_id) \
            .filter(RoomTag.hotel_id == hotel_id).all()
        print_log(output, '## 호텔의 총 분류된 객실수 : {}'.format(len(rooms)), True)

        roomid_to_tagname = dict()
        room_ids = []
        for r in rooms:
            room_ids.append(r.id)
            roomid_to_tagname[r.id] = dict(result=r.name, room_name=r.room_name)

        prices = session.query(RoomPrice).filter(
            RoomPrice.booking_date > kst_now - timedelta(days=1),
            RoomPrice.room_id.in_(room_ids),
            RoomPrice.scanned_date > kst_now - timedelta(days=1),
            RoomPrice.stay_price == price
        ).limit(1000).all()
        print_log(output, '## 가격 일치 객실수 : {}'.format(len(prices)), True)

        for p in prices:
            if p.room_id in roomid_to_tagname:
                selected_item = roomid_to_tagname[p.room_id]
    
    if selected_item is None:
        print_log(output, '## {}원 (없음)'.format(price), True)
    else:
        print_log(output, '## {} - {}원 ({})'.format(selected_item['room_name'], price, selected_item['result']), True)
    return selected_item


# 특정 호텔에서 객실명에 대한 룸타입 판정 및 적용
def judge_roomtype(output, hotel_id, room_name, setting):
    # step 1
    result = judge_roomtype_step1(output, room_name, setting)
    if result is not None:
        return result

    # step 2
    '''
    # 사용하지 마세요
    with session_scope() as session:
        result = judge_roomtype_step2(output, hotel_id, price)
        if result is not None:
            return result
    '''

    return None


# 특정 호텔만 룰 적용
def set_roomtype_hotel_rule(output, hotel_id, default_setting, update_setting=None, reset=False):
    print('## set_roomtype_hotel_rule - hotel_id : ', hotel_id)
    kst_now = datetime.utcnow() + timedelta(hours=9)
    week_ago = kst_now - timedelta(days=7)
    is_exist_user = True   # 호텔을 소유한 사용자가 존재하는 경우 True
    is_first = False        # 룸 타입 설정 최초일 경우, True 가 됨 (기존에 저장된 compare 개수가 0인 경우 -> 순서대로)

    with session_scope() as session:
        # 0. 호텔을 소유한 사용자 정보를 가져옴, 만약 없다면 RoomTag 만 갱신됨
        user_items = session.query(User).filter(User.hotel_id == hotel_id).all()
        '''
        if not user_item:
            is_exist_user = False
        '''
        
        # 1. 만약 reset 플래그가 세팅되어있다면, room_tag, room_tag_has_room, compare 를 초기화 한뒤 처음부터 다시 시작한다.
        if reset:
            # room_tag 조회
            room_tags = session.query(RoomTag).filter(RoomTag.hotel_id == hotel_id).all()

            # compare_has_tag 삭제
            for tag in room_tags:
                session.query(CompareHasTag).filter(CompareHasTag.room_tag_id == tag.id).delete()

            #if is_exist_user:
            for user_item in user_items:
                # compare_has_tag 삭제
                compare_items = session.query(Compare).filter(Compare.owner == user_item.id).all()
                for compare_item in compare_items:
                    session.query(CompareHasTag).filter(CompareHasTag.compare_id == compare_item.id).delete()

                # compare 삭제
                session.query(Compare).filter(Compare.owner == user_item.id).delete()
            
            # room_tag_has_room 삭제
            for tag in room_tags:
                session.query(RoomTagHasRoom).filter(RoomTagHasRoom.room_tag_id == tag.id).delete()

            # room_tag 삭제
            session.query(RoomTag).filter(RoomTag.hotel_id == hotel_id).delete()

            # 삭제 전체 일괄 커밋
            session.commit()

        # 2. 설정을 가져옴 (필요에 따라 업데이트한다)
        if update_setting is not None:
            setting = update_setting
            hotel_item = session.query(Hotel).filter(Hotel.id == hotel_id).first()
            hotel_item.roomtype_setting = json.dumps(update_setting)
            session.commit()
        else:
            setting = default_setting
        
        # 3. 등록된 room_tag 를 모두 가져옴
        room_tags = session.query(RoomTag).filter(RoomTag.hotel_id == hotel_id).all()
        tag_priority_dict = dict()
        for tag in room_tags:
            tag_priority_dict[tag.priority] = tag

        # 4. room_tag 정보를 업데이트 함
        tag_priority = 0
        for main_category in setting:
            tagname = main_category['name']

            if tag_priority not in tag_priority_dict:          # 기존에 생성된 태그가 없는 경우 -> 생성
                new_room_tag = RoomTag(hotel_id, tagname, tag_priority)
                session.add(new_room_tag)
                session.commit()
                session.refresh(new_room_tag)
                tag_priority_dict[tag_priority] = new_room_tag

            else:                                           # 기존에 생성된 태그가 있는 경우 -> tagname 변경
                tag_priority_dict[tag_priority].name = tagname

            tag_priority += 1
        session.commit()

        # 5. 모든 객실에 대해 room_tag_has_room 을 재편성한다 (최근 7일 이내 객실)
        rooms = session.query(Room).filter(Room.hotel_id == hotel_id, Room.updated_at > week_ago).all()
        for r in rooms:
            roomtype_item = judge_roomtype(output, r.hotel_id, r.name, setting)
            if roomtype_item is not None:
                room_id = r.id
                roomtype_priority = roomtype_item['priority']
                if roomtype_priority in tag_priority_dict:
                    room_tag_item = tag_priority_dict[roomtype_priority]
                    search_room_tag_has_room = session.query(RoomTagHasRoom).filter(RoomTagHasRoom.room_tag_id == room_tag_item.id, RoomTagHasRoom.room_id == room_id).first()
                    if not search_room_tag_has_room:
                        session.add(RoomTagHasRoom(room_tag_item.id, r.id))
        session.commit()
        
        # 사용자 정보가 존재하는 경우, compare 에 대한 정보 갱신 및 tag 와 매칭을 진행한다.
        #if is_exist_user:
        for user_item in user_items:
            # 등록된 compare 를 모두 가져옴 (compare 개수가 0 이라면 tag 와 순서대로 배치)
            compare_items = session.query(Compare).filter(Compare.owner == user_item.id).order_by(Compare.priority.asc()).all()
            if len(compare_items) == 0:
                is_first = True

            # 등록된 room_tag 를 모두 가져옴
            compare_priority_dict = dict()
            for compare in compare_items:
                compare_priority_dict[compare.priority] = compare

            # compare 정보를 업데이트 함
            compare_priority = 0
            for main_category in setting:
                comparename = main_category['name']

                if compare_priority not in compare_priority_dict:          # 기존에 생성된 태그가 없는 경우 -> 생성
                    new_compare = Compare(user_item.id, comparename, compare_priority)
                    session.add(new_compare)
                    session.commit()
                    session.refresh(new_compare)
                    compare_priority_dict[compare_priority] = new_compare

                else:                                           # 기존에 생성된 태그가 있는 경우 -> tagname 변경
                    compare_priority_dict[compare_priority].name = comparename

                compare_priority += 1
            session.commit()

            '''
            # 첫번째 수행일 때, compare 와 tag 를 순서대로 매칭함
            if is_first:
                # 1. 내 CompareHasTag 추가
                # 새로 생성된 태그에 대한 compare_has_tag 추가 (내 CompareHasTag)
                for compare_item in compare_items:
                    if compare_item.priority in tag_priority_dict:
                        tagid = tag_priority_dict[compare_item.priority].id
                        my_compare_has_tag = session.query(CompareHasTag).filter(CompareHasTag.compare_id == compare_item.id, CompareHasTag.room_tag_id == tagid).first()
                        if not my_compare_has_tag:
                            session.add(CompareHasTag(compare_item.id, tagid))
                        session.commit()
                
                # 2. 경쟁 CompareHasTag 추가
                # 경쟁 호텔의 각 priority 에 대한 room_tag 를 조회함
                competitions = session.query(UserHasCompetition).filter(UserHasCompetition.user_id == user_item.id).all()

                # 등록된 경쟁 호텔의 room_tag 를 색인함 (hotel_id, priority)
                compatition_room_tags = session.query(RoomTag).filter(RoomTag.hotel_id.in_([competition.competition_id for competition in competitions])).all()
                compatition_tag_priority_dict = dict()
                for ctag in compatition_room_tags:
                    if ctag.hotel_id not in compatition_tag_priority_dict:
                        compatition_tag_priority_dict[ctag.hotel_id] = dict()
                    compatition_tag_priority_dict[ctag.hotel_id][ctag.priority] = ctag

                # 새로 생성된 태그에 대한 compare_has_tag 추가 (경쟁 CompareHasTag)
                for competition in competitions:
                    competition_hotel_id = competition.competition_id

                    # hotel_id 에 대한 색인이 없다면, 해당 room_tag 가 없는 것이므로 건너뜀
                    if competition_hotel_id not in compatition_tag_priority_dict:
                        continue

                    for compare_item in compare_items:
                        # priority 에 대한 색인이 없다면, 해당 room_tag 가 없는 것이므로 건너뜀
                        if compare_item.priority not in compatition_tag_priority_dict[competition_hotel_id]:
                            continue
                        
                        tagid = compatition_tag_priority_dict[competition_hotel_id][compare_item.priority].id
                        my_compare_has_tag = session.query(CompareHasTag).filter(CompareHasTag.compare_id == compare_item.id, CompareHasTag.room_tag_id == tagid).first()
                        if not my_compare_has_tag:
                            session.add(CompareHasTag(compare_item.id, tagid))
                session.commit()
            '''

        return dict(code=200)


# 룸타입 전체룰 적용 룰 적용
def set_roomtype_hotel_rule_whole(output, setting, reset=False):
    with session_scope() as session:
        # 기본룰을 db 에 저장
        env_item = session.query(Environment).filter(Environment.key == 'ROOMTYPE_RULE').first()
        if env_item is not None:
            env_item.value = json.dumps(setting)
        else:
            session.add(Environment('ROOMTYPE_RULE', json.dumps(setting)))
        session.commit()
    
        # 각 호텔마다 적용
        hotel_items = session.query(Hotel).all()
        for hotel in hotel_items:
            if hotel.roomtype_setting is not None:
                set_roomtype_hotel_rule(output, hotel.id, setting, json.loads(hotel.roomtype_setting), reset)
            else:
                set_roomtype_hotel_rule(output, hotel.id, setting, None, reset)


def set_compare_has_tag(output, hotel_id, reset=False):
    print('## set_compare_has_tag - hotel_id : ', hotel_id)
    is_exist_user = True   # 호텔을 소유한 사용자가 존재하는 경우 True

    with session_scope() as session:
        # 0. 호텔을 소유한 사용자 정보를 가져옴, 만약 없다면 RoomTag 만 갱신됨
        user_items = session.query(User).filter(User.hotel_id == hotel_id).all()
        '''
        if not user_item:
            is_exist_user = False
        '''

        for user_item in user_items:
        
            # 1. 만약 reset 플래그가 세팅되어있다면, room_tag, room_tag_has_room, compare 를 초기화 한뒤 처음부터 다시 시작한다.
            if reset:
                '''
                # room_tag 조회
                room_tags = session.query(RoomTag).filter(RoomTag.hotel_id == hotel_id).all()

                # compare_has_tag 삭제
                for tag in room_tags:
                    session.query(CompareHasTag).filter(CompareHasTag.room_tag_id == tag.id).delete()
                '''

                if is_exist_user:
                    print('##### user_item.id', user_item.id)
                    # compare_has_tag 삭제
                    compare_items = session.query(Compare).filter(Compare.owner == user_item.id).all()
                    for compare_item in compare_items:
                        session.query(CompareHasTag).filter(CompareHasTag.compare_id == compare_item.id).delete()

                # 삭제 전체 일괄 커밋
                session.commit()
            
            # 사용자 정보가 존재하는 경우, compare 에 대한 정보 갱신 및 tag 와 매칭을 진행한다.
            if is_exist_user:
                # 등록된 compare 를 모두 가져옴 (compare 개수가 0 이라면 tag 와 순서대로 배치)
                compare_items = session.query(Compare).filter(Compare.owner == user_item.id).order_by(Compare.priority.asc()).all()

                # 등록된 room_tag 를 모두 가져옴
                room_tags = session.query(RoomTag).filter(RoomTag.hotel_id == hotel_id).all()
                tag_priority_dict = dict()
                for tag in room_tags:
                    tag_priority_dict[tag.priority] = tag
                
                # 내 CompareHasTag 추가
                # 새로 생성된 태그에 대한 compare_has_tag 추가 (내 CompareHasTag)
                for compare_item in compare_items:
                    if compare_item.priority in tag_priority_dict:
                        tagid = tag_priority_dict[compare_item.priority].id
                        my_compare_has_tag = session.query(CompareHasTag).filter(CompareHasTag.compare_id == compare_item.id, CompareHasTag.room_tag_id == tagid).first()
                        if not my_compare_has_tag:
                            session.add(CompareHasTag(compare_item.id, tagid, compare_item.priority))
                        session.commit()
                
                # 2. 경쟁 CompareHasTag 추가
                # 경쟁 호텔의 각 priority 에 대한 room_tag 를 조회함
                competitions = session.query(UserHasCompetition).filter(UserHasCompetition.user_id == user_item.id).all()

                # 등록된 경쟁 호텔의 room_tag 를 색인함 (hotel_id, priority)
                compatition_room_tags = session.query(RoomTag).filter(RoomTag.hotel_id.in_([competition.competition_id for competition in competitions])).all()
                compatition_tag_priority_dict = dict()
                for ctag in compatition_room_tags:
                    if ctag.hotel_id not in compatition_tag_priority_dict:
                        compatition_tag_priority_dict[ctag.hotel_id] = dict()
                    compatition_tag_priority_dict[ctag.hotel_id][ctag.priority] = ctag

                # 새로 생성된 태그에 대한 compare_has_tag 추가 (경쟁 CompareHasTag)
                for competition in competitions:
                    competition_hotel_id = competition.competition_id

                    # hotel_id 에 대한 색인이 없다면, 해당 room_tag 가 없는 것이므로 건너뜀
                    if competition_hotel_id not in compatition_tag_priority_dict:
                        continue

                    for compare_item in compare_items:
                        # priority 에 대한 색인이 없다면, 해당 room_tag 가 없는 것이므로 건너뜀
                        if compare_item.priority not in compatition_tag_priority_dict[competition_hotel_id]:
                            continue
                        
                        tagid = compatition_tag_priority_dict[competition_hotel_id][compare_item.priority].id
                        my_compare_has_tag = session.query(CompareHasTag).filter(CompareHasTag.compare_id == compare_item.id, CompareHasTag.room_tag_id == tagid).first()
                        if not my_compare_has_tag:
                            session.add(CompareHasTag(compare_item.id, tagid, compare_item.priority))
                session.commit()

        return dict(code=200)


def set_compare_has_tag_whole(output, reset=False):
    # 각 호텔마다 적용
    with session_scope() as session:    
        hotel_items = session.query(Hotel).all()
        for hotel in hotel_items:
            set_compare_has_tag(output, hotel.id, reset)


def set_compare_has_tag_of_competitions(output, hotel_id, reset=False):
    # 경쟁 호텔 적용
    with session_scope() as session:
        set_compare_has_tag(output, hotel_id, reset)
        '''
        competitions = session.query(User.hotel_id, UserHasCompetition.user_id) \
            .join(User, User.id == UserHasCompetition.user_id) \
            .filter(UserHasCompetition.competition_id == hotel_id).all()
        for competition in competitions:
            set_compare_has_tag(output, competition.hotel_id, reset)
        '''
