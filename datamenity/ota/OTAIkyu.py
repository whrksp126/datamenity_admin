from datamenity.ota.OTABase import OTABase, ExceptionReadTimeout
from datamenity.config import REQUESTS_PROXY, SELENIUM_PROXY

import requests
import datetime
import json
import time
import re
import browsercookie
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse


def replace_price(txt):
    txt = re.sub(r'[^0-9]', '', txt.replace(',', ''))
    return int(float(txt))


class OTAIkyu(OTABase):
    def get_hotel_id(self, args, url):
        return url.split('/')[-2]
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        hotel_id = url.split('/')[-2]
        people_count = 2
        json_params = [
            {
                "operationName":"PlansAndRoomsIkyuCollocation",
                "variables":{
                    "hasCheckInDate":True,
                    "onPlans":False,
                    "onRooms":True,
                    "plansInput":{
                        "checkInDate":"{}".format(checkin),
                        "discount":True,
                        "lodgingCount":1,
                        "peopleCount":people_count,
                        "roomCount":1,
                        "searchType":"1",
                        "sortItem":"1",
                        "sortOrder":"1",
                        "bookable":"ALL",
                        "preferBookable":True
                    },
                    "plansFirst":10,
                    "plansOffset":0,
                    "planAmountsInput":{
                        "checkInDate":"{}".format(checkin),
                        "discount":True,"lodgingCount":1,
                        "peopleCount":people_count,"roomCount":1,"searchType":"1","sortItem":"1","sortOrder":"1"
                    },
                    "roomsInput":{
                        "checkInDate":"{}".format(checkin),
                        "discount":True,
                        "lodgingCount":1,
                        "peopleCount":people_count,"roomCount":1,"searchType":"1",
                        "sortItem":"1","sortOrder":"1","bookable":"ALL","preferBookable":True
                    },
                    "roomsFirst":10,
                    "roomsOffset":0,
                    "roomAmountsInput":{"checkInDate":"{}".format(checkin),"discount":True,"lodgingCount":1,"peopleCount":people_count,"roomCount":1,"searchType":"1","sortItem":"1","sortOrder":"1"},
                    "amountsAndPlanFirst":2,
                    "amountsAndRoomFirst":2,
                    "accommodationId":"{}".format(hotel_id),
                    "accommodationAmountInput":{"checkInDate":"{}".format(checkin),"discount":True,"lodgingCount":1,"peopleCount":people_count,"roomCount":1,"searchType":"1","sortItem":"1","sortOrder":"1"}
                },
                "query":"query PlansAndRoomsIkyuCollocation($accommodationId: AccommodationIdScalar!, $accommodationAmountInput: AccommodationAmountInput, $hasCheckInDate: Boolean! = false, $onPlans: Boolean! = false, $plansInput: SearchPlansInput! = {}, $plansFirst: Int! = 3, $plansOffset: Int! = 0, $planAmountsInput: PlanAmountInput! = {sortItem: \"1\", sortOrder: \"1\"}, $onRooms: Boolean! = false, $roomsInput: SearchRoomsInput! = {}, $roomsFirst: Int! = 3, $roomsOffset: Int! = 0, $roomAmountsInput: RoomAmountInput! = {sortItem: \"1\", sortOrder: \"1\"}, $amountsAndPlanFirst: Int! = 1, $amountsAndRoomFirst: Int! = 1) {\n  accommodation(accommodationId: $accommodationId) {\n    accommodationId\n    largeArea {\n      id\n      name\n      __typename\n    }\n    allowInstantDiscount\n    goToTarget\n    breadcrumb {\n      name\n      path\n      attribute\n      __typename\n    }\n    ...DisappearingInventoryFrag @include(if: $hasCheckInDate)\n    ...lowestAmountFrag\n    searchPlans2(input: $plansInput, first: $plansFirst, offset: $plansOffset) {\n      facet @include(if: $onPlans) {\n        ...PlansFacetFrag\n        __typename\n      }\n      plans {\n        ...PlanConnectionFrag @include(if: $onPlans)\n        ...PlanConnectionTotalCountFrag\n        __typename\n      }\n      __typename\n    }\n    searchRooms2(input: $roomsInput, first: $roomsFirst, offset: $roomsOffset) {\n      facet @include(if: $onRooms) {\n        ...RoomsFacetFrag\n        __typename\n      }\n      rooms {\n        ...RoomConnectionFrag @include(if: $onRooms)\n        ...RoomConnectionTotalCountFrag\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PlansFacetFrag on SearchPlansFacet {\n  goToTarget\n  meals {\n    count\n    meal {\n      code\n      name\n      __typename\n    }\n    __typename\n  }\n  planAttributes {\n    count\n    planAttribute {\n      name\n      value\n      __typename\n    }\n    __typename\n  }\n  roomAttributes {\n    roomAttribute {\n      name\n      value\n      __typename\n    }\n    count\n    __typename\n  }\n  roomTypes {\n    count\n    roomType {\n      code\n      name\n      __typename\n    }\n    __typename\n  }\n  serviceAttributes {\n    count\n    serviceAttribute {\n      name\n      value\n      __typename\n    }\n    __typename\n  }\n  timeSale\n  __typename\n}\n\nfragment RoomsFacetFrag on SearchRoomsFacet {\n  goToTarget\n  meals {\n    count\n    meal {\n      code\n      name\n      __typename\n    }\n    __typename\n  }\n  planAttributes {\n    count\n    planAttribute {\n      name\n      value\n      __typename\n    }\n    __typename\n  }\n  roomAttributes {\n    roomAttribute {\n      name\n      value\n      __typename\n    }\n    count\n    __typename\n  }\n  roomTypes {\n    count\n    roomType {\n      code\n      name\n      __typename\n    }\n    __typename\n  }\n  serviceAttributes {\n    count\n    serviceAttribute {\n      name\n      value\n      __typename\n    }\n    __typename\n  }\n  timeSale\n  __typename\n}\n\nfragment PlanConnectionFrag on PlanConnection {\n  edges @include(if: $onPlans) {\n    node {\n      planId\n      amounts(input: $planAmountsInput, first: $amountsAndRoomFirst) {\n        edges {\n          node {\n            ...AmountAndRoomFrag\n            __typename\n          }\n          __typename\n        }\n        totalCount\n        __typename\n      }\n      useCheckInOut\n      checkInTimeFrom\n      checkInTimeTo\n      checkOutTime\n      limitedTwoWeeks\n      bookableStartSoon\n      bookableEndSoon\n      meal {\n        code\n        name\n        __typename\n      }\n      memberRank\n      name\n      isIkyuLimit\n      imageUrls(first: 1)\n      __typename\n    }\n    __typename\n  }\n  totalCount\n  __typename\n}\n\nfragment AmountAndRoomFrag on Amount2 {\n  amount\n  discountAmount\n  point\n  pointRate\n  instantPoint\n  instantPointRate\n  isUpperGoToCoupon\n  inventory\n  room {\n    roomId\n    checkInTimeFrom\n    checkInTimeTo\n    checkOutTime\n    attributes {\n      value\n      __typename\n    }\n    images(first: 1) {\n      alt\n      url\n      __typename\n    }\n    meterFrom\n    beds {\n      count\n      peopleCount\n      width\n      height\n      length\n      __typename\n    }\n    capacityMin\n    capacityMax\n    floorPlan\n    floorNumberBottom\n    floorNumberTop\n    name\n    type {\n      code\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PlanConnectionTotalCountFrag on PlanConnection {\n  totalCount\n  __typename\n}\n\nfragment RoomConnectionTotalCountFrag on RoomConnection {\n  totalCount\n  __typename\n}\n\nfragment RoomConnectionFrag on RoomConnection {\n  edges @include(if: $onRooms) {\n    node {\n      roomId\n      checkInTimeFrom\n      checkInTimeTo\n      checkOutTime\n      amounts(input: $roomAmountsInput, first: $amountsAndPlanFirst) {\n        edges {\n          node {\n            ...AmountAndPlanFrag\n            __typename\n          }\n          __typename\n        }\n        totalCount\n        __typename\n      }\n      attributes {\n        value\n        __typename\n      }\n      images(first: 99) {\n        alt\n        url\n        __typename\n      }\n      meterFrom\n      beds {\n        count\n        peopleCount\n        width\n        height\n        length\n        __typename\n      }\n      capacityMin\n      capacityMax\n      floorPlan\n      floorNumberBottom\n      floorNumberTop\n      name\n      renewalDate\n      type {\n        code\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  totalCount\n  __typename\n}\n\nfragment AmountAndPlanFrag on Amount2 {\n  amount\n  discountAmount\n  point\n  pointRate\n  instantPoint\n  instantPointRate\n  isUpperGoToCoupon\n  inventory\n  plan {\n    planId\n    checkInTimeFrom\n    checkInTimeTo\n    checkOutTime\n    useCheckInOut\n    limitedTwoWeeks\n    bookableStartSoon\n    bookableEndSoon\n    meal {\n      code\n      name\n      __typename\n    }\n    memberRank\n    name\n    imageUrls(first: 1)\n    __typename\n  }\n  __typename\n}\n\nfragment lowestAmountFrag on Accommodation {\n  amount2(input: $accommodationAmountInput) {\n    amount\n    discountAmount\n    isUpperGoToCoupon\n    point\n    pointRate\n    instantPoint\n    instantPointRate\n    __typename\n  }\n  __typename\n}\n\nfragment DisappearingInventoryFrag on Accommodation {\n  disappearingInventory(input: $roomsInput)\n  __typename\n}"
            },{
                "operationName":"AccommodationIkyuCollocation",
                "variables":{
                    "guideRecommendImageInput":{"device":"PC"},
                    "guideTopicsSpecified":True,"skipImageUrls":True,
                    "skipGuideImages2":False,"skipGuideRecommendImage":False,"preview":False,
                    "accommodationId":"{}".format(hotel_id),"device":"PC","accommodationStoriesFirst":5,
                    "recommendPeopleCount":"{}".format(people_count),"recommendDiscount":True,
                    "accommodationIntroductionFirst":10,"guideImagesFirst":5,
                    "goToTargetIgnorePeriod":True,
                    "accommodationAmountInput":{
                        "checkInDate":"{}".format(checkin),"discount":True,"lodgingCount":1,
                        "peopleCount":people_count,"roomCount":1,"searchType":"1","sortItem":"1",
                        "sortOrder":"1"
                    }
                },
                "query":"query AccommodationIkyuCollocation($accommodationId: AccommodationIdScalar!, $device: Device!, $accommodationAmountInput: AccommodationAmountInput, $guideRecommendImageInput: GuideRecommendImageInput! = {device: PC}, $accommodationStoriesFirst: Int!, $recommendPeopleCount: PeopleCountScalar!, $recommendDiscount: Boolean!, $accommodationIntroductionFirst: Int!, $guideImagesFirst: Int!, $goToTargetIgnorePeriod: Boolean!, $guideTopicsSpecified: Boolean! = false, $skipImageUrls: Boolean = true, $skipGuideImages2: Boolean = false, $skipGuideRecommendImage: Boolean = false, $preview: Boolean! = false) {\n  accommodation(accommodationId: $accommodationId) {\n    accommodationId\n    name\n    prText\n    ...AccommodationMetaFlag\n    ...AccommodationHeaderIkyuFrag\n    ...FirstViewFrag\n    ...AccommodationPrAndHygieneNotesFrag\n    ...AccommodationIntroductionAndServiceFrag\n    ...AccommodationRatingFrag\n    ...AccommodationPremiumFrag\n    ...AccommodationPhotoGalleryHeadlineFrag\n    ...AccommodationStoriesFrag\n    ...AccommodationNotesFrag\n    ...AccommodationRecommendFrag\n    ...AccommodationIntroductionFrag\n    ...AccommodationRestaurantsFrag\n    ...GuideTopicsFrag\n    ...FurusatoGiftFrag\n    __typename\n  }\n}\n\nfragment AccommodationMetaFlag on Accommodation {\n  accommodationId\n  name\n  prText\n  guideImageUrls\n  prefecture {\n    name\n    __typename\n  }\n  address\n  postalCode\n  phoneNumber\n  rating2 {\n    count\n    average\n    __typename\n  }\n  amount2(input: $accommodationAmountInput) {\n    amount\n    discountAmount\n    __typename\n  }\n  __typename\n}\n\nfragment FirstViewFrag on Accommodation {\n  accommodationId\n  name\n  isFavorite\n  allowInstantDiscount\n  prefecture {\n    name\n    __typename\n  }\n  sale {\n    code\n    __typename\n  }\n  smallArea {\n    id\n    name\n    urlPrefix\n    __typename\n  }\n  areaName\n  isIkyuPlus\n  imageUrls(first: 5) @skip(if: $skipImageUrls)\n  guideImages2(device: $device, first: $guideImagesFirst) @skip(if: $skipGuideImages2) {\n    alt\n    url\n    type\n    __typename\n  }\n  guideRecommendImage(input: $guideRecommendImageInput) @skip(if: $skipGuideRecommendImage) {\n    alt\n    url\n    __typename\n  }\n  goToTarget(ignorePeriod: $goToTargetIgnorePeriod)\n  goToAreaCouponUsableInfo\n  zenkokuCoupon {\n    usableCheckOutDateTo\n    status\n    __typename\n  }\n  zenkokuCouponTarget2\n  coupons {\n    couponId\n    code\n    name\n    price\n    limitMemberCount\n    limitMinimumPrice\n    limitMinimumPeopleCount\n    limitMinimumPeopleCountType\n    limitExpirationDateFrom\n    limitExpirationDateTo\n    limitCheckoutDateFrom\n    limitCheckoutDateTo\n    limitDayUse\n    limitPrefectureName\n    limitPrefectures {\n      code\n      name\n      __typename\n    }\n    acquired\n    __typename\n  }\n  hygieneNotes\n  logoImage {\n    alt\n    url\n    __typename\n  }\n  __typename\n}\n\nfragment AccommodationHeaderIkyuFrag on Accommodation {\n  accommodationId\n  name\n  prefecture {\n    name\n    __typename\n  }\n  sale {\n    code\n    __typename\n  }\n  smallArea {\n    id\n    name\n    urlPrefix\n    __typename\n  }\n  areaName\n  coupons {\n    couponId\n    price\n    __typename\n  }\n  genreAttributes {\n    name\n    value\n    distinction\n    __typename\n  }\n  goodFeatures\n  isIkyuPlus\n  hygieneNotes\n  logoImage {\n    alt\n    url\n    __typename\n  }\n  __typename\n}\n\nfragment AccommodationPrAndHygieneNotesFrag on Accommodation {\n  accommodationId\n  name\n  prText\n  checkInTimeTo\n  checkInTimeFrom\n  checkOutTime\n  hygieneNotes\n  roomCount\n  __typename\n}\n\nfragment AccommodationPremiumFrag on Accommodation {\n  accommodationId\n  name\n  premium\n  showPremiumBenefits\n  premiumEntryDate\n  premiumBenefits {\n    no\n    content\n    memo\n    __typename\n  }\n  __typename\n}\n\nfragment AccommodationPhotoGalleryHeadlineFrag on Accommodation {\n  accommodationId\n  photoGalleryImages(first: 999) {\n    alt\n    type\n    url\n    __typename\n  }\n  __typename\n}\n\nfragment AccommodationStoriesFrag on Accommodation {\n  accommodationId\n  stories(first: $accommodationStoriesFirst) {\n    id\n    title\n    image {\n      url\n      alt\n      __typename\n    }\n    content\n    __typename\n  }\n  __typename\n}\n\nfragment AccommodationNotesFrag on Accommodation {\n  accommodationId\n  notes\n  __typename\n}\n\nfragment AccommodationRecommendFrag on Accommodation {\n  accommodationId\n  personalization {\n    themes(first: 10, offset: 0) {\n      edges {\n        node {\n          themeId\n          name\n          accommodations(first: 10, offset: 0) {\n            edges {\n              node {\n                thumbnailImageUrl\n                accommodation {\n                  accommodationId\n                  name\n                  imageUrls\n                  prefecture {\n                    name\n                    __typename\n                  }\n                  areaName\n                  allowInstantDiscount\n                  rating2 {\n                    average\n                    __typename\n                  }\n                  amount2(\n                    input: {peopleCount: $recommendPeopleCount, discount: $recommendDiscount}\n                  ) {\n                    peopleCount\n                    amount\n                    discountAmount\n                    point\n                    pointRate\n                    instantPoint\n                    instantPointRate\n                    isUpperGoToCoupon\n                    __typename\n                  }\n                  discountAmount: amount2(\n                    input: {peopleCount: $recommendPeopleCount, discount: true}\n                  ) {\n                    amount\n                    discountAmount\n                    point\n                    pointRate\n                    instantPoint\n                    instantPointRate\n                    isUpperGoToCoupon\n                    peopleCount\n                    __typename\n                  }\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment AccommodationIntroductionFrag on Accommodation {\n  accommodationId\n  postalCode\n  prefecture {\n    name\n    __typename\n  }\n  address\n  phoneNumber\n  latitude\n  longitude\n  accessInfo\n  announcements {\n    subject\n    content\n    image {\n      url\n      alt\n      __typename\n    }\n    __typename\n  }\n  esthetic\n  fitness {\n    businessHoursFrom\n    businessHoursTo\n    lastAdmission\n    stayerPrice\n    visitorPrice\n    __typename\n  }\n  hasRoomWithOpenairBath\n  pet\n  petNote\n  pickup {\n    info\n    pickup\n    __typename\n  }\n  parking {\n    amount\n    time\n    parking\n    carLimitation\n    carCount\n    shape\n    carHeight\n    carLength\n    carWidth\n    info\n    valetService\n    valetServiceAmount\n    __typename\n  }\n  baths {\n    code {\n      code\n      name\n      __typename\n    }\n    springGround\n    __typename\n  }\n  attributes {\n    available\n    attribute {\n      name\n      value\n      __typename\n    }\n    __typename\n  }\n  restaurants(first: $accommodationIntroductionFirst) {\n    id\n    name\n    displayGenre\n    largeGenre\n    image {\n      url\n      alt\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment AccommodationRestaurantsFrag on Accommodation {\n  restaurants(first: $accommodationIntroductionFirst) {\n    id\n    name\n    displayGenre\n    largeGenre\n    image {\n      url\n      alt\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment GuideTopicsFrag on Accommodation {\n  guideTopics(type: ACCOMMODATION, preview: $preview, first: 999) @include(if: $guideTopicsSpecified) {\n    edges {\n      node {\n        ... on GuideTopicHTML {\n          __typename\n          content\n        }\n        ... on GuideTopicTemplate {\n          templateId: id\n          type\n          parts {\n            title\n            isBigTitle\n            info\n            link(device: $device)\n            linkText\n            image {\n              url\n              alt\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment FurusatoGiftFrag on Accommodation {\n  accommodationId\n  furusatoGiftUrl\n  __typename\n}\n\nfragment AccommodationIntroductionAndServiceFrag on Accommodation {\n  accommodationId\n  checkInTimeTo\n  checkInTimeFrom\n  checkOutTime\n  roomCount\n  child\n  childNote\n  openBusinessDateString\n  attributes {\n    available\n    attribute {\n      name\n      value\n      __typename\n    }\n    __typename\n  }\n  baths {\n    code {\n      code\n      name\n      __typename\n    }\n    springGround\n    __typename\n  }\n  __typename\n}\n\nfragment AccommodationRatingFrag on Accommodation {\n  accommodationId\n  pickupReviews {\n    reviewId\n    comment\n    site\n    __typename\n  }\n  rating2 {\n    accommodationEquipment\n    average\n    bathroomSpring\n    count\n    customerService\n    meal\n    roomAmenity\n    satisfaction\n    ranking {\n      rank\n      listPageUrl {\n        name\n        path\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}"
            },{
                "operationName":"SurroundingAreaSearch",
                "variables":{
                    "input":{
                        "checkInDate":"{}".format(checkin),"discount":True,"lodgingCount":1,
                        "peopleCount":people_count,"roomCount":1,"searchType":"1","sortItem":"6",
                        "sortOrder":"1","preferredAccommodationIds":["{}".format(hotel_id)],
                        "accommodationSaleCds":["01","03","04","05"],"areaIds":["140306"],
                        "hotelInnDistinctions":["1"],
                        "preferredAccommodationSaleCds":[["03"],["01"],["04"],["05"]]
                    },
                    "surroundingFirst":12,"surroundingCitySpecified":True,
                    "surroundingLandmarkSpecified":True,"surroundingPrefectureSpecified":True,
                    "surroundingSpringGroundSpecified":False,"surroundingStationSpecified":False
                },
                "query":"query SurroundingAreaSearch($input: SearchAccommodationsInput!, $surroundingFirst: Int!, $surroundingCitySpecified: Boolean!, $surroundingLandmarkSpecified: Boolean!, $surroundingPrefectureSpecified: Boolean!, $surroundingSpringGroundSpecified: Boolean!, $surroundingStationSpecified: Boolean!) {\n  searchAccommodations(input: $input, first: 0, offset: 0) {\n    surrounding {\n      ...SurroundingFrag\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment SurroundingFrag on SearchAccommodationsSurrounding {\n  cities(first: $surroundingFirst) @include(if: $surroundingCitySpecified) {\n    listPagePath\n    city {\n      id\n      name\n      __typename\n    }\n    __typename\n  }\n  landmarks(first: $surroundingFirst) @include(if: $surroundingLandmarkSpecified) {\n    listPagePath\n    landmark {\n      id\n      name\n      __typename\n    }\n    __typename\n  }\n  prefectures(first: $surroundingFirst) @include(if: $surroundingPrefectureSpecified) {\n    listPagePath\n    prefecture {\n      code\n      name\n      __typename\n    }\n    __typename\n  }\n  springGrounds(first: $surroundingFirst) @include(if: $surroundingSpringGroundSpecified) {\n    listPagePath\n    springGround {\n      id\n      name\n      __typename\n    }\n    __typename\n  }\n  stations(first: $surroundingFirst) @include(if: $surroundingStationSpecified) {\n    listPagePath\n    station {\n      id\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}"
            },{
                "operationName":"PlanAndRoomLinkInfo",
                "variables":{
                    "plansInput":{
                        "checkInDate":"{}".format(checkin),"discount":True,
                        "lodgingCount":1,"peopleCount":people_count,"roomCount":1,"searchType":"1",
                        "sortItem":"1","sortOrder":"1"
                    },
                    "roomsInput":{
                        "checkInDate":"{}".format(checkin),"discount":True,"lodgingCount":1,
                        "peopleCount":people_count,"roomCount":1,"searchType":"1","sortItem":"1",
                        "sortOrder":"1"
                    },"accommodationId":"{}".format(hotel_id),"onPlans":False,"onRooms":True
                },
                "query":"query PlanAndRoomLinkInfo($accommodationId: AccommodationIdScalar!, $onPlans: Boolean!, $plansInput: SearchPlansInput! = {}, $onRooms: Boolean!, $roomsInput: SearchRoomsInput! = {}) {\n  accommodation(accommodationId: $accommodationId) {\n    accommodationId\n    smallArea {\n      id\n      name\n      __typename\n    }\n    largeArea {\n      id\n      name\n      __typename\n    }\n    searchPlans2(input: $plansInput) @include(if: $onPlans) {\n      facet {\n        roomAttributes {\n          roomAttribute {\n            name\n            value\n            __typename\n          }\n          count\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    searchRooms2(input: $roomsInput) @include(if: $onRooms) {\n      facet {\n        roomAttributes {\n          roomAttribute {\n            name\n            value\n            __typename\n          }\n          count\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}"
            }
        ]
        headers2 = {
            'Accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
            'client-info': 'shopping-pwa,879ef38bdfb196f682493cb47d3f19dad7d5b5b6,us-west-2',
            'content-type': 'application/json',
            'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        }

        try:
            response = self.requests_post(requests, 'https://www.ikyu.com/graphql', json=json_params, headers=headers2, **args['proxy']['REQUESTS_PROXY'])
            if response.status_code == 403:
                return dict(code=403, rooms=[])
            response = response.json()
        except ExceptionReadTimeout as e:
            print(e)
            return dict(code=403, rooms=[])
        
        rooms = []
        for edge in response[0]['data']['accommodation']['searchRooms2']['rooms']['edges']:
            node = edge['node']

            room_id = node['roomId']

            if len(node['amounts']['edges']) == 0:
                continue

            room_price = node['amounts']['edges'][0]['node']['discountAmount']
            room_remain = 1
            room_name = node['name']
        
            rooms.append(dict(
                room_id=room_id, 
                name=room_name, 
                remain=room_remain,
                price=room_price,
            ))
         
        return dict(
            code=200,
            rooms=rooms,
        )

        '''
        parts = urlparse(url)
        qs = dict(parse_qsl(parts.query))
        qs['adc'] = 1
        qs['cid'] = checkin.replace('-', '')
        qs['cod'] = checkout.replace('-', '')
        qs['lc'] = 1
        qs['ppc'] = 2
        qs['rc'] = 1
        qs['si'] = 1
        qs['st'] = 1
        parts = parts._replace(query=urlencode(qs))
        new_url = urlunparse(parts)

        try:
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
            }
            r = self.requests_get(requests, new_url, headers=headers, **args['proxy']['REQUESTS_PROXY'])
            print(r.text)

            if r.status_code == 403:
                return dict(code=403, rooms=[])
            
            result = r.text
            soup = BeautifulSoup(result, 'html.parser')
            items = soup.find_all('section', {'class': 'text-gray-800'})
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])

        rooms = []
        for elem in items:
            title_elem = elem.find('a', {'rel': 'nofollow'})
            if not title_elem:
                continue
            room_name = title_elem.get_text().strip()

            elem_sections = elem.find_all('section')
            room_price = 1e10

            for elem_section in elem_sections:
                rid_elem = elem_section.find('a', {'rel': 'noopener'})
                if not rid_elem:
                    continue
                price_elem = elem_section.find('strong', {'class': 'text-3xl'})
                if not price_elem:
                    continue
                rid = rid_elem['href'].split('/')[3]

                price = replace_price(price_elem.get_text().strip())
                room_remain = 1

                if room_price > price:
                    room_price = price
                    room_id = rid
            
            if room_price >= 1e10:
                continue

            rooms.append(dict(
                room_id=room_id, 
                name=room_name, 
                remain=room_remain,
                price=room_price,
            ))
         
        return dict(
            code=200,
            rooms=rooms,
        )
        '''
    
    def scrape_reviews(self, output, args, url, hotel_id, page):
        return dict(code=404, comments=[], score=0, count=0)
        result = []

        try:
            reviews = self.requests_post(requests, 'https://www.goodchoice.kr/product/get_review_non', data={'page': page, 'ano': hotel_id}).json()
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])

        for r in reviews['result']['items']:
            reply = []
            if len(r['o_comm']) > 0:
                for o in r['o_comm']:
                    reply.append(dict(
                        author='' if o['unick'] is None else o['unick'],
                        content=o['aep_cmcont'],
                        created_at=None
                    ))
            
            result.append(dict(
                id=r['aepreg'],
                author='' if r['unick'] is None else r['unick'],
                content='{}\n{}'.format(r['epilrate_textinfo'], r['aepcont']),
                category='기타',
                score=float(r['epilrate']),
                created_at=datetime.datetime.fromtimestamp(r['aepreg']),
                reply=reply
            ))
        
        # 리뷰 개수, 평점
        score = reviews['result']['rateavg']
        count = reviews['result']['count']
 
        return dict(code=200, comments=result, score=score, count=count)
