from datamenity.api.roomtype import find_keyword, set_compare_has_tag, set_compare_has_tag_whole, set_roomtype_hotel_rule, set_roomtype_hotel_rule_whole, judge_roomtype


#print(find_keyword('아스탠다드 코리아', '스탠다드', True))
'''

from soynlp.hangle import levenshtein, decompose
#print(levenshtein(decompose('가'), decompose('너')))
print(decompose('가'))

'''

'''
[{
    'name':'대분류명',
    'items': [{
        'name': '중분류명',
        'items': [{'name': '소분류명', dist: 3, weight: 10}, ...]
    }, ...]
}, ...]
'''

setting = [{
	"name": "스탠다드",
	"items": [{
		"name": "스탠다드",
		"items": [{
			"name": "스탠다드",
			"dist": 1,
			"weight": 0
		}, {
			"name": "standard",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "비즈니스",
		"items": [{
			"name": "비즈니스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "business",
			"dist": 1,
			"weight": 0
		}, {
			"name": "비지니스",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "할리우드",
		"items": [{
			"name": "할리우드",
			"dist": 1,
			"weight": 0
		}, {
			"name": "hollywood",
			"dist": 1,
			"weight": 0
		}, {
			"name": "헐리우드",
			"dist": 1,
			"weight": 0
		}]
	}]
}, {
	"name": "슈페리어",
	"items": [{
		"name": "슈페리어",
		"items": [{
			"name": "슈페리어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "superior",
			"dist": 1,
			"weight": 0
		}, {
			"name": "슈피리어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "수페리어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "슈페리얼",
			"dist": 1,
			"weight": 0
		}, {
			"name": "슈피리얼",
			"dist": 1,
			"weight": 0
		}, {
			"name": "스페리어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "스패리어",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "스튜디오",
		"items": [{
			"name": "스튜디오",
			"dist": 1,
			"weight": 0
		}, {
			"name": "studio",
			"dist": 1,
			"weight": 0
		}, {
			"name": "스투디오",
			"dist": 1,
			"weight": 0
		}]
	}]
}, {
	"name": "디럭스",
	"items": [{
		"name": "디럭스",
		"items": [{
			"name": "디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe",
			"dist": 1,
			"weight": 0
		}, {
			"name": "드럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "데럭스",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미어",
		"items": [{
			"name": "프리미어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premier",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미엄",
		"items": [{
			"name": "프리미엄",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premium",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "트리플",
		"items": [{
			"name": "트리플",
			"dist": 1,
			"weight": 0
		}, {
			"name": "triple",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "패밀리",
		"items": [{
			"name": "패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "family",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "코너 디럭스",
		"items": [{
			"name": "코너 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "corner deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미어 디럭스",
		"items": [{
			"name": "프리미어 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premier deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "하이 디럭스",
		"items": [{
			"name": "하이 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "high deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "디럭스 패밀리",
		"items": [{
			"name": "디럭스 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe family",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "그랜드 디럭스",
		"items": [{
			"name": "그랜드 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "grand deluxe",
			"dist": 1,
			"weight": 0
		}, {
			"name": "그렌드 디럭스",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "이그제큐티브 그랜드 디럭스",
		"items": [{
			"name": "이그젝큐티브 그랜드 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "executive grand deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "이그제큐티브 프리미어",
		"items": [{
			"name": "이그제큐티브 프리미어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "이그젝큐티브 프리미어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "executive premier",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "이그제큐티브 프리미엄",
		"items": [{
			"name": "이그제큐티브 프리미엄",
			"dist": 1,
			"weight": 0
		}, {
			"name": "이그젝큐티브 프리미엄",
			"dist": 1,
			"weight": 0
		}, {
			"name": "executive premium",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "클럽 디럭스",
		"items": [{
			"name": "클럽 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "club deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "클럽 프리미어",
		"items": [{
			"name": "클럽 프리미어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "club premier",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "클럽 프리미엄",
		"items": [{
			"name": "클럽 프리미엄",
			"dist": 1,
			"weight": 0
		}, {
			"name": "club premium",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "코너 프리미어",
		"items": [{
			"name": "코너 프리미어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "corner premier",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "코너 프리미엄",
		"items": [{
			"name": "코너 프리미엄",
			"dist": 1,
			"weight": 0
		}, {
			"name": "corner premium",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "그랜드 패밀리",
		"items": [{
			"name": "그랜드 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "그렌드 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "그렌드 페밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "그랜드 페밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "grand family",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "클래식 디럭스",
		"items": [{
			"name": "클래식 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "classic deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "디럭스 가든",
		"items": [{
			"name": "디럭스 가든",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe garden",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미어 패밀리",
		"items": [{
			"name": "프리미어 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premier family",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미엄 패밀리",
		"items": [{
			"name": "프리미엄 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premium family",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "키즈 디럭스",
		"items": [{
			"name": "키즈 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "kids deluxe",
			"dist": 1,
			"weight": 0
		}, {
			"name": "디럭스 키즈",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe kids",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "슈퍼 디럭스",
		"items": [{
			"name": "슈퍼 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "super deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "슈퍼 디럭스 패밀리",
		"items": [{
			"name": "슈퍼 디럭스 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "super deluxe family",
			"dist": 1,
			"weight": 0
		}]
	}]
}, {
	"name": "한실",
	"items": [{
		"name": "한실",
		"items": [{
			"name": "한실",
			"dist": 1,
			"weight": 0
		}, {
			"name": "hansil",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "온돌",
		"items": [{
			"name": "온돌",
			"dist": 1,
			"weight": 0
		}, {
			"name": "ondol",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "패밀리 온돌",
		"items": [{
			"name": "패밀리 온돌",
			"dist": 1,
			"weight": 0
		}, {
			"name": "family ondol",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "패밀리 한실",
		"items": [{
			"name": "패밀리 한실",
			"dist": 1,
			"weight": 0
		}, {
			"name": "family hansil",
			"dist": 1,
			"weight": 0
		}]
	}]
}, {
	"name": "스위트",
	"items": [{
		"name": "스위트",
		"items": [{
			"name": "스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "주니어 스위트",
		"items": [{
			"name": "주니어 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "junior suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "패밀리 스위트",
		"items": [{
			"name": "패밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "페밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "family suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "로열 스위트",
		"items": [{
			"name": "로열 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "로얄 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "royal suite",
			"dist": 1,
			"weight": 0
		}, {
			"name": "loyal suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "이그제큐티브",
		"items": [{
			"name": "이그제큐티브",
			"dist": 1,
			"weight": 0
		}, {
			"name": "이그젝큐티브",
			"dist": 1,
			"weight": 0
		}, {
			"name": "executive",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "로얄 이그제큐티브",
		"items": [{
			"name": "로얄 이그제큐티브",
			"dist": 1,
			"weight": 0
		}, {
			"name": "로열 이그제큐티브",
			"dist": 1,
			"weight": 0
		}, {
			"name": "royal executive",
			"dist": 1,
			"weight": 0
		}, {
			"name": "loyal executive",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "듀플렉스 스위트",
		"items": [{
			"name": "듀플렉스 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "duplex suite",
			"dist": 1,
			"weight": 0
		}, {
			"name": "스위트 듀플렉스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "스위트 두플렉스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "듀플렉스 스위트",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "한실 스위트",
		"items": [{
			"name": "한실 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "hansil suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "이그제큐티브 스위트",
		"items": [{
			"name": "이그제큐티브 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "이그젝큐티브 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "executive suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "팔러 스위트",
		"items": [{
			"name": "polor suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "클럽 주니어 스위트",
		"items": [{
			"name": "클럽 주니어 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "club junior suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "클럽 스위트",
		"items": [{
			"name": "클럽 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "club suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "이그제큐티브 주니어 스위트",
		"items": [{
			"name": "이그제큐티브 주니어 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "이그젝큐티브 주니어 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "executive junior suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "로얄 이그제큐티브 스위트",
		"items": [{
			"name": "로얄 이그제큐티브 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "로열 이그제큐티브 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "royal executive suite",
			"dist": 1,
			"weight": 0
		}, {
			"name": "loyal executive suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "힐 스위트",
		"items": [{
			"name": "힐 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "hill suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프레스티지 힐 스위트",
		"items": [{
			"name": "프레스티지 힐 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "prestige hill suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프레스티지 스위트",
		"items": [{
			"name": "프레스티지 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "prestige suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "타워 스위트",
		"items": [{
			"name": "타워 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "tower suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "파밀리에 스위트",
		"items": [{
			"name": "파밀리에 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "familie suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "로얄 패밀리 스위트",
		"items": [{
			"name": "로얄 패밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "로열 패밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "royal family suite",
			"dist": 1,
			"weight": 0
		}, {
			"name": "loyal family suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "키즈 스위트",
		"items": [{
			"name": "키즈 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "kids suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "키즈 풀 스위트",
		"items": [{
			"name": "키즈 풀 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "kids pool suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "파노라마 스위트",
		"items": [{
			"name": "파노라마 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "panorama suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "플래티넘 스위트",
		"items": [{
			"name": "플래티넘 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "플래니늄 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "플레티넘 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "platinum suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "코너 스위트",
		"items": [{
			"name": "코너 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "corner suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "임페리얼 스위트",
		"items": [{
			"name": "임페리얼 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "imperial suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "스위트 테라스",
		"items": [{
			"name": "스위트 테라스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "suite terrace",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "그랜드 패밀리 스위트",
		"items": [{
			"name": "그랜드 패밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "grand family suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프레지덴셜 스위트",
		"items": [{
			"name": "프레지덴셜 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "presidential suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미어 스위트",
		"items": [{
			"name": "프리미어 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premier suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미엄 스위트",
		"items": [{
			"name": "프리미엄 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premium suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "디럭스 스위트",
		"items": [{
			"name": "디럭스 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미어 스위트 패밀리",
		"items": [{
			"name": "프리미어 스위트 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "프리미어 패밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premier suite family",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premier family suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "디럭스 패밀리 스위트",
		"items": [{
			"name": "디럭스 패밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "디럭스 스위트 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe suite family",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe family suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "그랜드 디럭스 스위트",
		"items": [{
			"name": "그랜드 디럭스 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "grand deluxe suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프레스티지",
		"items": [{
			"name": "프레스티지",
			"dist": 1,
			"weight": 0
		}, {
			"name": "프래스티지",
			"dist": 1,
			"weight": 0
		}, {
			"name": "prestige",
			"dist": 1,
			"weight": 0
		}]
	}]
}, {
	"name": "펜트하우스",
	"items": [{
		"name": "펜트하우스",
		"items": [{
			"name": "펜트하우스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "penthouse",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "듀플렉스 펜트하우스",
		"items": [{
			"name": "듀플렉스 펜트하우스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "duplex penthouse",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "커넥팅",
		"items": [{
			"name": "커넥팅",
			"dist": 1,
			"weight": 0
		}, {
			"name": "커넥트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "connecting",
			"dist": 1,
			"weight": 0
		}, {
			"name": "connect",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "풀빌라",
		"items": [{
			"name": "pool villa",
			"dist": 1,
			"weight": 0
		}]
	}]
}]

custom_setting = [{
	"name": "스탠다드",
	"items": [{
		"name": "스탠다드",
		"items": [{
			"name": "스탠다드",
			"dist": 1,
			"weight": 0
		}, {
			"name": "standard",
			"dist": 1,
			"weight": 0
		}, {
			"name": "디럭스 킹",
			"dist": 0,
			"weight": 999
		}, {
			"name": "Deluxe Room King",
			"dist": 0,
			"weight": 999
		}, {
			"name": "Deluxe King",
			"dist": 0,
			"weight": 999
		}, {
			"name": "디럭스룸, 킹",
			"dist": 0,
			"weight": 999
		}]
	}, {
		"name": "비즈니스",
		"items": [{
			"name": "비즈니스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "business",
			"dist": 1,
			"weight": 0
		}, {
			"name": "비지니스",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "할리우드",
		"items": [{
			"name": "할리우드",
			"dist": 1,
			"weight": 0
		}, {
			"name": "hollywood",
			"dist": 1,
			"weight": 0
		}, {
			"name": "헐리우드",
			"dist": 1,
			"weight": 0
		}]
	}]
}, {
	"name": "슈페리어",
	"items": [{
		"name": "슈페리어",
		"items": [{
			"name": "슈페리어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "superior",
			"dist": 1,
			"weight": 0
		}, {
			"name": "슈피리어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "수페리어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "슈페리얼",
			"dist": 1,
			"weight": 0
		}, {
			"name": "슈피리얼",
			"dist": 1,
			"weight": 0
		}, {
			"name": "스페리어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "스패리어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "디럭스 킹 하버뷰",
			"dist": 0,
			"weight": 9999
		}, {
			"name": "Harbour View",
			"dist": 0,
			"weight": 9999
		}]
	}, {
		"name": "스튜디오",
		"items": [{
			"name": "스튜디오",
			"dist": 1,
			"weight": 0
		}, {
			"name": "studio",
			"dist": 1,
			"weight": 0
		}, {
			"name": "스투디오",
			"dist": 1,
			"weight": 0
		}]
	}]
}, {
	"name": "디럭스",
	"items": [{
		"name": "디럭스",
		"items": [{
			"name": "디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe",
			"dist": 1,
			"weight": 0
		}, {
			"name": "드럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "데럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "디럭스 킹 오션뷰",
			"dist": 0,
			"weight": 9999
		}, {
			"name": "디럭스 트윈 오션뷰",
			"dist": 0,
			"weight": 9999
		}, {
			"name": "ocean",
			"dist": 1,
			"weight": 9999
		}]
	}, {
		"name": "프리미어",
		"items": [{
			"name": "프리미어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premier",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미엄",
		"items": [{
			"name": "프리미엄",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premium",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "트리플",
		"items": [{
			"name": "트리플",
			"dist": 1,
			"weight": 0
		}, {
			"name": "triple",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "패밀리",
		"items": [{
			"name": "패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "family",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "코너 디럭스",
		"items": [{
			"name": "코너 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "corner deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미어 디럭스",
		"items": [{
			"name": "프리미어 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premier deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "하이 디럭스",
		"items": [{
			"name": "하이 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "high deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "디럭스 패밀리",
		"items": [{
			"name": "디럭스 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe family",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "그랜드 디럭스",
		"items": [{
			"name": "그랜드 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "grand deluxe",
			"dist": 1,
			"weight": 0
		}, {
			"name": "그렌드 디럭스",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "이그제큐티브 그랜드 디럭스",
		"items": [{
			"name": "이그젝큐티브 그랜드 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "executive grand deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "이그제큐티브 프리미어",
		"items": [{
			"name": "이그제큐티브 프리미어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "이그젝큐티브 프리미어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "executive premier",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "이그제큐티브 프리미엄",
		"items": [{
			"name": "이그제큐티브 프리미엄",
			"dist": 1,
			"weight": 0
		}, {
			"name": "이그젝큐티브 프리미엄",
			"dist": 1,
			"weight": 0
		}, {
			"name": "executive premium",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "클럽 디럭스",
		"items": [{
			"name": "클럽 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "club deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "클럽 프리미어",
		"items": [{
			"name": "클럽 프리미어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "club premier",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "클럽 프리미엄",
		"items": [{
			"name": "클럽 프리미엄",
			"dist": 1,
			"weight": 0
		}, {
			"name": "club premium",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "코너 프리미어",
		"items": [{
			"name": "코너 프리미어",
			"dist": 1,
			"weight": 0
		}, {
			"name": "corner premier",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "코너 프리미엄",
		"items": [{
			"name": "코너 프리미엄",
			"dist": 1,
			"weight": 0
		}, {
			"name": "corner premium",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "그랜드 패밀리",
		"items": [{
			"name": "그랜드 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "그렌드 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "그렌드 페밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "그랜드 페밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "grand family",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "클래식 디럭스",
		"items": [{
			"name": "클래식 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "classic deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "디럭스 가든",
		"items": [{
			"name": "디럭스 가든",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe garden",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미어 패밀리",
		"items": [{
			"name": "프리미어 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premier family",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미엄 패밀리",
		"items": [{
			"name": "프리미엄 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premium family",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "키즈 디럭스",
		"items": [{
			"name": "키즈 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "kids deluxe",
			"dist": 1,
			"weight": 0
		}, {
			"name": "디럭스 키즈",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe kids",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "슈퍼 디럭스",
		"items": [{
			"name": "슈퍼 디럭스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "super deluxe",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "슈퍼 디럭스 패밀리",
		"items": [{
			"name": "슈퍼 디럭스 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "super deluxe family",
			"dist": 1,
			"weight": 0
		}]
	}]
}, {
	"name": "한실",
	"items": [{
		"name": "한실",
		"items": [{
			"name": "한실",
			"dist": 1,
			"weight": 0
		}, {
			"name": "hansil",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "온돌",
		"items": [{
			"name": "온돌",
			"dist": 1,
			"weight": 0
		}, {
			"name": "ondol",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "패밀리 온돌",
		"items": [{
			"name": "패밀리 온돌",
			"dist": 1,
			"weight": 0
		}, {
			"name": "family ondol",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "패밀리 한실",
		"items": [{
			"name": "패밀리 한실",
			"dist": 1,
			"weight": 0
		}, {
			"name": "family hansil",
			"dist": 1,
			"weight": 0
		}]
	}]
}, {
	"name": "스위트",
	"items": [{
		"name": "스위트",
		"items": [{
			"name": "스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "주니어 스위트",
		"items": [{
			"name": "주니어 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "junior suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "패밀리 스위트",
		"items": [{
			"name": "패밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "페밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "family suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "로열 스위트",
		"items": [{
			"name": "로열 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "로얄 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "royal suite",
			"dist": 1,
			"weight": 0
		}, {
			"name": "loyal suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "이그제큐티브",
		"items": [{
			"name": "이그제큐티브",
			"dist": 1,
			"weight": 0
		}, {
			"name": "이그젝큐티브",
			"dist": 1,
			"weight": 0
		}, {
			"name": "executive",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "로얄 이그제큐티브",
		"items": [{
			"name": "로얄 이그제큐티브",
			"dist": 1,
			"weight": 0
		}, {
			"name": "로열 이그제큐티브",
			"dist": 1,
			"weight": 0
		}, {
			"name": "royal executive",
			"dist": 1,
			"weight": 0
		}, {
			"name": "loyal executive",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "듀플렉스 스위트",
		"items": [{
			"name": "듀플렉스 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "duplex suite",
			"dist": 1,
			"weight": 0
		}, {
			"name": "스위트 듀플렉스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "스위트 두플렉스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "듀플렉스 스위트",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "한실 스위트",
		"items": [{
			"name": "한실 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "hansil suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "이그제큐티브 스위트",
		"items": [{
			"name": "이그제큐티브 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "이그젝큐티브 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "executive suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "팔러 스위트",
		"items": [{
			"name": "polor suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "클럽 주니어 스위트",
		"items": [{
			"name": "클럽 주니어 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "club junior suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "클럽 스위트",
		"items": [{
			"name": "클럽 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "club suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "이그제큐티브 주니어 스위트",
		"items": [{
			"name": "이그제큐티브 주니어 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "이그젝큐티브 주니어 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "executive junior suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "로얄 이그제큐티브 스위트",
		"items": [{
			"name": "로얄 이그제큐티브 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "로열 이그제큐티브 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "royal executive suite",
			"dist": 1,
			"weight": 0
		}, {
			"name": "loyal executive suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "힐 스위트",
		"items": [{
			"name": "힐 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "hill suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프레스티지 힐 스위트",
		"items": [{
			"name": "프레스티지 힐 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "prestige hill suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프레스티지 스위트",
		"items": [{
			"name": "프레스티지 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "prestige suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "타워 스위트",
		"items": [{
			"name": "타워 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "tower suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "파밀리에 스위트",
		"items": [{
			"name": "파밀리에 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "familie suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "로얄 패밀리 스위트",
		"items": [{
			"name": "로얄 패밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "로열 패밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "royal family suite",
			"dist": 1,
			"weight": 0
		}, {
			"name": "loyal family suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "키즈 스위트",
		"items": [{
			"name": "키즈 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "kids suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "키즈 풀 스위트",
		"items": [{
			"name": "키즈 풀 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "kids pool suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "파노라마 스위트",
		"items": [{
			"name": "파노라마 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "panorama suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "플래티넘 스위트",
		"items": [{
			"name": "플래티넘 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "플래니늄 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "플레티넘 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "platinum suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "코너 스위트",
		"items": [{
			"name": "코너 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "corner suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "임페리얼 스위트",
		"items": [{
			"name": "임페리얼 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "imperial suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "스위트 테라스",
		"items": [{
			"name": "스위트 테라스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "suite terrace",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "그랜드 패밀리 스위트",
		"items": [{
			"name": "그랜드 패밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "grand family suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프레지덴셜 스위트",
		"items": [{
			"name": "프레지덴셜 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "presidential suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미어 스위트",
		"items": [{
			"name": "프리미어 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premier suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미엄 스위트",
		"items": [{
			"name": "프리미엄 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premium suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "디럭스 스위트",
		"items": [{
			"name": "디럭스 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프리미어 스위트 패밀리",
		"items": [{
			"name": "프리미어 스위트 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "프리미어 패밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premier suite family",
			"dist": 1,
			"weight": 0
		}, {
			"name": "premier family suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "디럭스 패밀리 스위트",
		"items": [{
			"name": "디럭스 패밀리 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "디럭스 스위트 패밀리",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe suite family",
			"dist": 1,
			"weight": 0
		}, {
			"name": "deluxe family suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "그랜드 디럭스 스위트",
		"items": [{
			"name": "그랜드 디럭스 스위트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "grand deluxe suite",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "프레스티지",
		"items": [{
			"name": "프레스티지",
			"dist": 1,
			"weight": 0
		}, {
			"name": "프래스티지",
			"dist": 1,
			"weight": 0
		}, {
			"name": "prestige",
			"dist": 1,
			"weight": 0
		}]
	}]
}, {
	"name": "펜트하우스",
	"items": [{
		"name": "펜트하우스",
		"items": [{
			"name": "펜트하우스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "penthouse",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "듀플렉스 펜트하우스",
		"items": [{
			"name": "듀플렉스 펜트하우스",
			"dist": 1,
			"weight": 0
		}, {
			"name": "duplex penthouse",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "커넥팅",
		"items": [{
			"name": "커넥팅",
			"dist": 1,
			"weight": 0
		}, {
			"name": "커넥트",
			"dist": 1,
			"weight": 0
		}, {
			"name": "connecting",
			"dist": 1,
			"weight": 0
		}, {
			"name": "connect",
			"dist": 1,
			"weight": 0
		}]
	}, {
		"name": "풀빌라",
		"items": [{
			"name": "pool villa",
			"dist": 1,
			"weight": 0
		}]
	}]
}]


####################################################

####
## step 1. room_tag, room_tag_has_room, compare 생성
####

# 특정 호텔에 대해서 규칙 적용
# output = 출력용도, hotel_id = 규칙적용할 호텔ID, default_setting = 기본 규칙, update_setting = 호텔 특별 규칙, reset = 기존에 있던 데이터를 모두 지우고 다시 쓰기)
#set_roomtype_hotel_rule([], 301, None, lct_setting, True)
'''
set_roomtype_hotel_rule([], 1271, None, lct_setting, True)
set_roomtype_hotel_rule([], 1270, None, lct_setting, True)
set_roomtype_hotel_rule([], 1784, None, lct_setting, True)
'''

# 전체 호텔에 대해서 규칙 적용
# output = 출력용도, setting = 기본규칙, reset = 초기화해서 다시할것인지
# set_roomtype_hotel_rule_whole([], setting, True)


####
## step 2. compare_has_tag 생성
####

# 특정 호텔에 대해서 compare_has_tag 생성 (output=출력, hotel_id = compare_has_tag 를 만들 호텔아이디, reset=기존거 지우고 할 것인지)
# set_compare_has_tag([], 1271, True)

# 전체 호텔에 대해서 compare_has_tag 생성
# set_compare_has_tag_whole([], True) (output=출력, reset=기존거 지우고 할 것인지)


##############################
set_roomtype_hotel_rule_whole([], setting)
set_compare_has_tag_whole([])

####################################################
# custom 적용
#set_roomtype_hotel_rule([], 10213, None, custom_setting, True)
#set_compare_has_tag_whole([], True)
###################################################

#judge_roomtype_step1([], '슈페리어 더블룸 (Main Tower)', setting)
#judge_roomtype_step2([], 217, 110000)


#set_roomtype_hotel_rule_whole([], setting)



#print(find_keyword('Superb Ocean View Royal Suite 더블2, 싱글1개', 'Superb Ocean View'))
