import traceback
from datamenity.ota.OTABase import OTABase, ExceptionReadTimeout
from datamenity.config import BASE_DIR, SELENIUM_VERSION

from selenium import webdriver
import undetected_chromedriver.v2 as uc
from pyvirtualdisplay import Display

import requests
import datetime
import json
import time
import browsercookie
import re

pattern_hotel_id = re.compile('\.h([0-9]*)\.Hotel\-Information')
pattern_total_count = re.compile('totalCount[^\{]*\{([^\}]*)\}')
pattern_overall_rating = re.compile('averageOverallRating[^\{]*\{([^\}]*)\}')
#v\\\"averageOverallRating\\\"


def replace_price(txt):
    txt = re.sub(r'[^0-9]', '', txt.replace(',', ''))
    return int(float(txt))


class OTAExpedia(OTABase):
    def get_hotel_id(self, args, url):
        m = pattern_hotel_id.search(url)
        hotel_id = m.group(1)
        return hotel_id
    
    def scrape_prices_preprocess(self, args, url, hotel_id, checkin, checkout):
        virtual_display = None
        driver = None

        try:
            virtual_display = Display(visible=0, size=(500, 500))
            virtual_display.start()

            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--headless')
            options.add_argument('--enable-javascript')
            options.add_argument('--disable-gpu')
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.0.0 Safari/537.36'.format(SELENIUM_VERSION)
            options.add_argument('User-Agent={0}'.format(user_agent))
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', True)
            options.add_argument('--proxy-server={}'.format(args['proxy']['SELENIUM_PROXY']))

            driver=uc.Chrome(executable_path='{}/driver/chromedriver'.format(BASE_DIR), version_main=SELENIUM_VERSION, chrome_options=options,service_args=['--quiet'], seleniumwire_options=args['proxy']['SELENIUM_PROXY'], use_subprocess=True)

            new_url = 'https://www.expedia.co.kr/Busan-Hotels-Kent-Hotel-Gwangalli-By-Kensington.h14858808.Hotel-Information?chain=&chkin={}&chkout={}&daysInFuture=&destType=MARKET&top_cur=KRW'.format(checkin.replace('-', '.'), checkout.replace('-', '.'))

            try:
                driver.get(new_url)
            except ExceptionReadTimeout:
                return dict(code=403)
            
            session = requests.Session()
            for c in driver.get_cookies():
                session.cookies.update({c['name']: c['value']})
                if c['name'] == 'DUAID':
                    args['duaid'] = c['value']

            driver.quit()
            driver = None
            virtual_display.stop()
            virtual_display = None

            args['session'] = session
        except Exception as e:
            print(traceback.print_exc())
            if virtual_display is not None:
                virtual_display.stop()
            if driver is not None:
                driver.quit()
            raise Exception('expedia 초기화 과정중 에러 발생 : {}'.format(e))
        return dict(code=200)
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        session = args['session']

        in_y, in_m, in_d = checkin.split('-')
        out_y, out_m, out_d = checkout.split('-')
        in_y = int(in_y)
        in_m = int(in_m)
        in_d = int(in_d)
        out_y = int(out_y)
        out_m = int(out_m)
        out_d = int(out_d)

        duaid = args['duaid']
        '''
        try:
            duaid = session.cookies.get('DUAID', '')
        except requests.cookies.CookieConflictError:
            return dict(code=403, rooms=[])
        '''

        headers = {
            'x-page-id': 'page.Hotels.Infosite.Information,H,30',
            'client-info': 'shopping-pwa,06e60a6b7371b560f358d838f5d6aadaa09a953b,us-west-2',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="{}", "Chromium";v="{}"'.format(SELENIUM_VERSION, SELENIUM_VERSION),
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.0.0 Safari/537.36'.format(SELENIUM_VERSION),
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        json_params = [
            {
                "operationName":"PropertyOffersQuery",
                "variables":{
                    "propertyId":"{}".format(hotel_id),
                    "searchCriteria":{
                        "primary":{
                            "dateRange":{
                                "checkInDate":{"day":in_d,"month":in_m,"year":in_y},
                                "checkOutDate":{"day":out_d,"month":out_m,"year":out_y}},
                                "destination":{
                                    "regionName":None,
                                    "regionId":None,
                                    "coordinates":None,
                                    "pinnedPropertyId":None,
                                    "propertyIds":None,
                                    "mapBounds":None
                            },
                            "rooms":[{"adults":2,"children":[]}]
                        },
                        "secondary":{
                            "counts":[],
                            "booleans":[],
                            "selections":[
                                {
                                    "id":"sort",
                                    "value":"RECOMMENDED"},
                                {
                                    "id":"privacyTrackingState",
                                    "value":"CAN_NOT_TRACK"
                                }
                            ]
                        }
                    },
                    "shoppingContext":{"multiItem":None},
                    "travelAdTrackingInfo":None,
                    "searchOffer":None,
                    "context":{
                        "siteId":16,
                        "locale":"ko_KR",
                        "eapid":0,
                        "currency":"KRW",
                        "device":{"type":"DESKTOP"},
                        "identity":{
                            "duaid":duaid,
                            "expUserId":"-1",
                            "tuid":"1",
                            "authState":"ANONYMOUS"
                        },
                        "privacyTrackingState":"CAN_TRACK",
                        "debugContext":{"abacusOverrides":[],"alterMode":"RELEASED"}
                    }
                },
                "query":"query PropertyOffersQuery($context: ContextInput!, $propertyId: String!, $searchCriteria: PropertySearchCriteriaInput, $shoppingContext: ShoppingContextInput, $travelAdTrackingInfo: PropertyTravelAdTrackingInfoInput, $searchOffer: SearchOfferInput, $referrer: String) {\n  propertyOffers(\n    context: $context\n    propertyId: $propertyId\n    referrer: $referrer\n    searchCriteria: $searchCriteria\n    searchOffer: $searchOffer\n    shoppingContext: $shoppingContext\n    travelAdTrackingInfo: $travelAdTrackingInfo\n  ) {\n    id\n    loading {\n      accessibilityLabel\n      __typename\n    }\n    ...PropertyLevelOffersMessageFragment\n    ...ListingsHeaderFragment\n    ...VipMessagingFragment\n    ...PropertyTripSummaryFragment\n    ...SingleOfferFragment\n    ...PropertyStickyBookBarFragment\n    ...PropertyOffersFragment\n    ...PropertySpaceDetailsFragment\n    ...PropertySearchLinkFragment\n    ...PropertyUnitListViewFragment\n    ...FilterPillsFragment\n    ...LoyaltyDiscountToggleFragment\n    ...LegalDisclaimerFragment\n    __typename\n  }\n}\n\nfragment PropertyLevelOffersMessageFragment on OfferDetails {\n  propertyLevelOffersMessage {\n    ...MessageResultFragment\n    __typename\n  }\n  __typename\n}\n\nfragment MessageResultFragment on MessageResult {\n  title {\n    text\n    ...MessagingResultTitleMediaFragment\n    __typename\n  }\n  subtitle {\n    text\n    ...MessagingResultTitleMediaFragment\n    __typename\n  }\n  action {\n    primary {\n      ...MessageActionContent\n      __typename\n    }\n    secondary {\n      ...MessageActionContent\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment MessageActionContent on MessagingAction {\n  text\n  linkUrl\n  referrerId\n  actionDetails {\n    action\n    accessibilityLabel\n    __typename\n  }\n  analytics {\n    linkName\n    referrerId\n    __typename\n  }\n  __typename\n}\n\nfragment MessagingResultTitleMediaFragment on MessagingResultTitle {\n  icon {\n    id\n    description\n    size\n    __typename\n  }\n  illustration {\n    assetUri {\n      value\n      __typename\n    }\n    description\n    __typename\n  }\n  mark {\n    id\n    __typename\n  }\n  egdsMark {\n    id\n    __typename\n  }\n  __typename\n}\n\nfragment VipMessagingFragment on OfferDetails {\n  propertyHighlightSection {\n    ...PropertyHighlightSectionFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyHighlightSectionFragment on PropertyHighlightSection {\n  label\n  header {\n    badge {\n      theme\n      text\n      __typename\n    }\n    mark {\n      id\n      description\n      __typename\n    }\n    text\n    __typename\n  }\n  subSections {\n    description\n    contents {\n      icon {\n        id\n        withBackground\n        description\n        __typename\n      }\n      value\n      __typename\n    }\n    __typename\n  }\n  footerLink {\n    icon {\n      id\n      __typename\n    }\n    link {\n      referrerId\n      uri {\n        relativePath\n        value\n        __typename\n      }\n      target\n      __typename\n    }\n    value\n    accessibilityLabel\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyTripSummaryFragment on OfferDetails {\n  tripSummary {\n    ...TripSummaryFragment\n    __typename\n  }\n  __typename\n}\n\nfragment TripSummaryFragment on TripSummaryContent {\n  header {\n    text\n    __typename\n  }\n  summary {\n    value\n    __typename\n  }\n  price {\n    options {\n      displayPrice {\n        formatted\n        __typename\n      }\n      strikeOut {\n        formatted\n        __typename\n      }\n      accessibilityLabel\n      priceDisclaimer {\n        content\n        tertiaryUIButton {\n          primary\n          action {\n            analytics {\n              referrerId\n              linkName\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        trigger {\n          clientSideAnalytics {\n            linkName\n            referrerId\n            __typename\n          }\n          value\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    priceMessaging {\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment SingleOfferFragment on OfferDetails {\n  ...PropertySingleRatePlanFragment\n  __typename\n}\n\nfragment PropertySingleRatePlanFragment on OfferDetails {\n  errorMessage {\n    ...ErrorMessageFragment\n    __typename\n  }\n  alternateAvailabilityMsg {\n    ...AlternateAvailabilityMsgFragment\n    __typename\n  }\n  ...AlternateDatesFragment\n  singleUnitOffer {\n    accessibilityLabel\n    ...TotalPriceFragment\n    ...PropertySingleOfferDetailsFragment\n    ratePlans {\n      priceDetails {\n        ...PriceBreakdownSummaryFragment\n        ...PricePresentationDialogFragment\n        __typename\n      }\n      marketingSection {\n        ...MarketingSectionFragment\n        __typename\n      }\n      shareUrl {\n        accessibilityLabel\n        value\n        link {\n          clientSideAnalytics {\n            linkName\n            referrerId\n            __typename\n          }\n          uri {\n            relativePath\n            value\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ...ReservePropertyFragment\n      __typename\n    }\n    __typename\n  }\n  ...PropertySingleOfferDialogLinkFragment\n  __typename\n}\n\nfragment ErrorMessageFragment on MessageResult {\n  title {\n    text\n    __typename\n  }\n  action {\n    primary {\n      text\n      linkUrl\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment AlternateAvailabilityMsgFragment on LodgingComplexLinkMessage {\n  text {\n    value\n    __typename\n  }\n  actionLink {\n    link {\n      uri {\n        relativePath\n        value\n        __typename\n      }\n      __typename\n    }\n    value\n    __typename\n  }\n  __typename\n}\n\nfragment AlternateDatesFragment on OfferDetails {\n  alternateDates {\n    header {\n      text\n      subText\n      __typename\n    }\n    options {\n      ...AlternateDateOptionFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment AlternateDateOptionFragment on AlternateDateOption {\n  dates {\n    link {\n      uri {\n        relativePath\n        __typename\n      }\n      referrerId\n      __typename\n    }\n    value\n    __typename\n  }\n  price {\n    displayPrice {\n      formatted\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TotalPriceFragment on SingleUnitOfferDetails {\n  totalPrice {\n    label {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    amount {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingEnrichedMessageFragment on LodgingEnrichedMessage {\n  __typename\n  subText\n  value\n  theme\n  state\n  accessibilityLabel\n  icon {\n    id\n    size\n    __typename\n  }\n  mark {\n    id\n    __typename\n  }\n  egdsMark {\n    url {\n      value\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PropertySingleOfferDetailsFragment on SingleUnitOfferDetails {\n  id\n  ...PriceMessagesFragment\n  ratePlans {\n    ...SingleUnitPriceSummaryFragment\n    ...HighlightedMessagesFragment\n    __typename\n  }\n  ...SingleOfferAvailabilityCtaFragment\n  __typename\n}\n\nfragment PriceMessagesFragment on SingleUnitOfferDetails {\n  displayPrice {\n    priceMessages {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment SingleUnitPriceSummaryFragment on RatePlan {\n  ...PropertyOffersPriceChangeMessageFragment\n  ...PropertyRatePlanBadgeFragment\n  priceDetails {\n    pointsApplied\n    ...LodgingPriceSummaryFragment\n    price {\n      ...PriceSummaryFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingPriceSummaryFragment on Offer {\n  price {\n    options {\n      leadingCaption\n      displayPrice {\n        formatted\n        __typename\n      }\n      disclaimer {\n        value\n        __typename\n      }\n      priceDisclaimer {\n        content\n        primaryButton {\n          text\n          __typename\n        }\n        trigger {\n          icon {\n            description\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      accessibilityLabel\n      strikeOut {\n        formatted\n        __typename\n      }\n      loyaltyPrice {\n        unit\n        amount {\n          formatted\n          __typename\n        }\n        totalStrikeOutPoints {\n          formatted\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    priceMessaging {\n      value\n      theme\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyRatePlanBadgeFragment on RatePlan {\n  badge {\n    theme_temp\n    text\n    icon_temp {\n      id\n      description\n      size\n      title\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyOffersPriceChangeMessageFragment on RatePlan {\n  headerMessage {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PriceSummaryFragment on PropertyPrice {\n  displayMessages {\n    lineItems {\n      ...PriceMessageFragment\n      ...EnrichedMessageFragment\n      __typename\n    }\n    __typename\n  }\n  options {\n    leadingCaption\n    displayPrice {\n      formatted\n      __typename\n    }\n    disclaimer {\n      value\n      __typename\n    }\n    priceDisclaimer {\n      content\n      primaryButton {\n        text\n        __typename\n      }\n      trigger {\n        icon {\n          description\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    accessibilityLabel\n    strikeOut {\n      formatted\n      __typename\n    }\n    loyaltyPrice {\n      unit\n      amount {\n        formatted\n        __typename\n      }\n      totalStrikeOutPoints {\n        formatted\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  priceMessaging {\n    value\n    theme\n    __typename\n  }\n  __typename\n}\n\nfragment PriceMessageFragment on DisplayPrice {\n  __typename\n  role\n  price {\n    formatted\n    accessibilityLabel\n    __typename\n  }\n  disclaimer {\n    content\n    primaryUIButton {\n      accessibility\n      primary\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment EnrichedMessageFragment on LodgingEnrichedMessage {\n  __typename\n  value\n  state\n}\n\nfragment HighlightedMessagesFragment on RatePlan {\n  id\n  highlightedMessages {\n    ...LodgingPlainDialogFragment\n    ...LodgingEnrichedMessageFragment\n    ...LodgingPlainMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingPlainDialogFragment on LodgingPlainDialog {\n  content\n  primaryUIButton {\n    ...UIPrimaryButtonFragment\n    __typename\n  }\n  secondaryUIButton {\n    ...UISecondaryButtonFragment\n    __typename\n  }\n  primaryButton {\n    text\n    analytics {\n      linkName\n      referrerId\n      __typename\n    }\n    __typename\n  }\n  trigger {\n    clientSideAnalytics {\n      linkName\n      referrerId\n      __typename\n    }\n    icon {\n      description\n      id\n      __typename\n    }\n    theme\n    value\n    secondaryValue\n    __typename\n  }\n  __typename\n}\n\nfragment UIPrimaryButtonFragment on UIPrimaryButton {\n  primary\n  action {\n    __typename\n    analytics {\n      referrerId\n      linkName\n      __typename\n    }\n    ... on UILinkAction {\n      resource {\n        value\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment UISecondaryButtonFragment on UISecondaryButton {\n  primary\n  action {\n    __typename\n    analytics {\n      referrerId\n      linkName\n      __typename\n    }\n    ... on UILinkAction {\n      resource {\n        value\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment LodgingPlainMessageFragment on LodgingPlainMessage {\n  value\n  __typename\n}\n\nfragment SingleOfferAvailabilityCtaFragment on SingleUnitOfferDetails {\n  availabilityCallToAction {\n    ...AvailabilityCallToActionFragment\n    __typename\n  }\n  __typename\n}\n\nfragment AvailabilityCallToActionFragment on AvailabilityCallToAction {\n  __typename\n  ... on LodgingPlainMessage {\n    __typename\n    value\n  }\n  ... on LodgingButton {\n    __typename\n    text\n  }\n}\n\nfragment MarketingSectionFragment on MarketingSection {\n  title {\n    text\n    __typename\n  }\n  feeDialog {\n    title\n    content\n    tertiaryUIButton {\n      primary\n      __typename\n    }\n    trigger {\n      value\n      mark {\n        id\n        __typename\n      }\n      icon {\n        id\n        size\n        __typename\n      }\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  paymentDetails {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment ReservePropertyFragment on RatePlan {\n  paymentPolicy {\n    paymentType\n    heading\n    descriptions {\n      heading\n      items {\n        text\n        __typename\n      }\n      __typename\n    }\n    price {\n      ...PriceSummaryFragment\n      __typename\n    }\n    __typename\n  }\n  priceDetails {\n    ...PriceBreakdownSummaryFragment\n    __typename\n  }\n  ...PropertyReserveButtonFragment\n  __typename\n}\n\nfragment PropertyReserveButtonFragment on RatePlan {\n  id\n  reserveCallToAction {\n    __typename\n    ... on EtpDialog {\n      trigger {\n        value\n        accessibilityLabel\n        __typename\n      }\n      toolbar {\n        icon {\n          description\n          __typename\n        }\n        title\n        __typename\n      }\n      __typename\n    }\n    ... on LodgingForm {\n      ...PropertyLodgingFormButtonFragment\n      __typename\n    }\n  }\n  etpDialogTopMessage {\n    ...MessageResultFragment\n    __typename\n  }\n  priceDetails {\n    action {\n      ... on SelectPackageActionInput {\n        packageOfferId\n        __typename\n      }\n      __typename\n    }\n    price {\n      multiItemPriceToken\n      __typename\n    }\n    hotelCollect\n    propertyNaturalKeys {\n      id\n      checkIn {\n        month\n        day\n        year\n        __typename\n      }\n      checkOut {\n        month\n        day\n        year\n        __typename\n      }\n      inventoryType\n      noCreditCard\n      ratePlanId\n      roomTypeId\n      ratePlanType\n      rooms {\n        childAges\n        numberOfAdults\n        __typename\n      }\n      shoppingPath\n      __typename\n    }\n    noCreditCard\n    paymentModel\n    ...PropertyPaymentOptionsFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyLodgingFormButtonFragment on LodgingForm {\n  action\n  inputs {\n    ... on LodgingTextInput {\n      name\n      type\n      value\n      __typename\n    }\n    __typename\n  }\n  method\n  submit {\n    text\n    accessibilityLabel\n    analytics {\n      linkName\n      referrerId\n      __typename\n    }\n    lodgingClientSideAnalyticsSuccess {\n      campaignId\n      events {\n        banditDisplayed\n        eventTarget\n        eventType\n        payloadId\n        __typename\n      }\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyPaymentOptionsFragment on Offer {\n  etpModalPolicies\n  loyaltyMessage {\n    ... on LodgingEnrichedMessage {\n      value\n      state\n      __typename\n    }\n    __typename\n  }\n  offerBookButton {\n    ...PropertyLodgingFormButtonFragment\n    __typename\n  }\n  ...PropertyPaymentPriceFragment\n  price {\n    ...PriceSummaryFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyPaymentPriceFragment on Offer {\n  price {\n    lead {\n      formatted\n      __typename\n    }\n    priceMessaging {\n      value\n      theme\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertySingleOfferDialogLinkFragment on OfferDetails {\n  singleUnitOfferDialog {\n    content {\n      ...PropertySingleOfferDetailsFragment\n      ratePlans {\n        priceDetails {\n          ...PriceBreakdownSummaryFragment\n          ...PricePresentationDialogFragment\n          __typename\n        }\n        marketingSection {\n          ...MarketingSectionFragment\n          __typename\n        }\n        ...ReservePropertyFragment\n        __typename\n      }\n      __typename\n    }\n    trigger {\n      value\n      __typename\n    }\n    toolbar {\n      icon {\n        description\n        __typename\n      }\n      title\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PricePresentationDialogFragment on Offer {\n  pricePresentationDialog {\n    toolbar {\n      title\n      icon {\n        description\n        __typename\n      }\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      __typename\n    }\n    trigger {\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      value\n      __typename\n    }\n    __typename\n  }\n  pricePresentation {\n    title {\n      primary\n      __typename\n    }\n    sections {\n      ...PricePresentationSectionFragment\n      __typename\n    }\n    footer {\n      header\n      messages {\n        ...PriceLineElementFragment\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PricePresentationSectionFragment on PricePresentationSection {\n  header {\n    name {\n      ...PricePresentationLineItemEntryFragment\n      __typename\n    }\n    enrichedValue {\n      ...PricePresentationLineItemEntryFragment\n      __typename\n    }\n    __typename\n  }\n  subSections {\n    ...PricePresentationSubSectionFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PricePresentationSubSectionFragment on PricePresentationSubSection {\n  header {\n    name {\n      primaryMessage {\n        __typename\n        ... on PriceLineText {\n          primary\n          __typename\n        }\n        ... on PriceLineHeading {\n          primary\n          __typename\n        }\n      }\n      __typename\n    }\n    enrichedValue {\n      ...PricePresentationLineItemEntryFragment\n      __typename\n    }\n    __typename\n  }\n  items {\n    ...PricePresentationLineItemFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PricePresentationLineItemFragment on PricePresentationLineItem {\n  enrichedValue {\n    ...PricePresentationLineItemEntryFragment\n    __typename\n  }\n  name {\n    ...PricePresentationLineItemEntryFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PricePresentationLineItemEntryFragment on PricePresentationLineItemEntry {\n  primaryMessage {\n    ...PriceLineElementFragment\n    __typename\n  }\n  secondaryMessages {\n    ...PriceLineElementFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PriceLineElementFragment on PricePresentationLineItemMessage {\n  __typename\n  ...PriceLineTextFragment\n  ...PriceLineHeadingFragment\n  ...InlinePriceLineTextFragment\n}\n\nfragment PriceLineTextFragment on PriceLineText {\n  __typename\n  theme\n  primary\n  weight\n  additionalInfo {\n    ...AdditionalInformationPopoverFragment\n    __typename\n  }\n  icon {\n    id\n    description\n    size\n    __typename\n  }\n}\n\nfragment AdditionalInformationPopoverFragment on AdditionalInformationPopover {\n  icon {\n    id\n    description\n    size\n    __typename\n  }\n  enrichedSecondaries {\n    ...AdditionalInformationPopoverSectionFragment\n    __typename\n  }\n  analytics {\n    linkName\n    referrerId\n    __typename\n  }\n  __typename\n}\n\nfragment AdditionalInformationPopoverSectionFragment on AdditionalInformationPopoverSection {\n  __typename\n  ... on AdditionalInformationPopoverTextSection {\n    ...AdditionalInformationPopoverTextSectionFragment\n    __typename\n  }\n  ... on AdditionalInformationPopoverListSection {\n    ...AdditionalInformationPopoverListSectionFragment\n    __typename\n  }\n  ... on AdditionalInformationPopoverGridSection {\n    ...AdditionalInformationPopoverGridSectionFragment\n    __typename\n  }\n}\n\nfragment AdditionalInformationPopoverTextSectionFragment on AdditionalInformationPopoverTextSection {\n  __typename\n  text {\n    text\n    __typename\n  }\n}\n\nfragment AdditionalInformationPopoverListSectionFragment on AdditionalInformationPopoverListSection {\n  __typename\n  content {\n    __typename\n    items {\n      text\n      __typename\n    }\n  }\n}\n\nfragment AdditionalInformationPopoverGridSectionFragment on AdditionalInformationPopoverGridSection {\n  __typename\n  subSections {\n    header {\n      name {\n        primaryMessage {\n          ...AdditionalInformationPopoverGridLineItemMessageFragment\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    items {\n      name {\n        ...AdditionalInformationPopoverGridLineItemEntryFragment\n        __typename\n      }\n      enrichedValue {\n        ...AdditionalInformationPopoverGridLineItemEntryFragment\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment AdditionalInformationPopoverGridLineItemEntryFragment on PricePresentationLineItemEntry {\n  primaryMessage {\n    ...AdditionalInformationPopoverGridLineItemMessageFragment\n    __typename\n  }\n  secondaryMessages {\n    ...AdditionalInformationPopoverGridLineItemMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment AdditionalInformationPopoverGridLineItemMessageFragment on PricePresentationLineItemMessage {\n  ... on PriceLineText {\n    __typename\n    primary\n  }\n  ... on PriceLineHeading {\n    __typename\n    tag\n    size\n    primary\n  }\n  __typename\n}\n\nfragment PriceLineHeadingFragment on PriceLineHeading {\n  __typename\n  primary\n  tag\n  size\n  additionalInfo {\n    ...AdditionalInformationPopoverFragment\n    __typename\n  }\n  icon {\n    id\n    description\n    size\n    __typename\n  }\n}\n\nfragment InlinePriceLineTextFragment on InlinePriceLineText {\n  __typename\n  inlineItems {\n    ...PriceLineTextFragment\n    __typename\n  }\n}\n\nfragment PropertyStickyBookBarFragment on OfferDetails {\n  soldOut\n  stickyBar {\n    qualifier\n    subText\n    stickyButton {\n      text\n      targetRef\n      __typename\n    }\n    price {\n      formattedDisplayPrice\n      accessibilityLabel\n      priceDisclaimer {\n        content\n        primaryUIButton {\n          primary\n          __typename\n        }\n        trigger {\n          icon {\n            id\n            size\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    structuredData {\n      itemprop\n      itemscope\n      itemtype\n      content\n      __typename\n    }\n    __typename\n  }\n  ...PropertySingleOfferDialogLinkFragment\n  __typename\n}\n\nfragment PropertyOffersFragment on OfferDetails {\n  ...ListingsHeaderFragment\n  ...AlternateDatesFragment\n  ...ListingsErrorMessageFragment\n  ...ListingsFragment\n  ...StickyBarDisclaimerFragment\n  ...ShoppingContextFragment\n  offerLevelMessages {\n    ...MessageResultFragment\n    __typename\n  }\n  ...PropertyFilterPillsFragment\n  __typename\n}\n\nfragment ListingsHeaderFragment on OfferDetails {\n  listingsHeader {\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment ListingsErrorMessageFragment on OfferDetails {\n  errorMessage {\n    ...ErrorMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment ListingsFragment on OfferDetails {\n  listings {\n    ...PropertyUnitFragment\n    __typename\n  }\n  categorizedListings {\n    ...PropertyUnitCategorizationFragment\n    ...VerticalMessagingCardFragment\n    ...LodgingHeaderFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyUnitFragment on PropertyUnit {\n  __typename\n  ... on PropertyUnit {\n    id\n    header {\n      ...PropertyOffersHeaderFragment\n      __typename\n    }\n    features {\n      ...PropertyFeaturesFragment\n      __typename\n    }\n    unitGallery {\n      accessibilityLabel\n      images {\n        image {\n          description\n          url\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    ratePlans {\n      ...RatePlanWithAmenitiesFragment\n      __typename\n    }\n    ratePlansExpando {\n      ...RatePlansExpandoFragment\n      __typename\n    }\n    ...AvailabilityCtaFragment\n    roomAmenities {\n      ...RoomAmenitiesDescriptionFragment\n      __typename\n    }\n    detailsDialog {\n      ...PropertyOffersDetailsDialogFragment\n      toolbar {\n        clientSideAnalytics {\n          referrerId\n          linkName\n          __typename\n        }\n        __typename\n      }\n      trigger {\n        ...LinkTriggerFragment\n        clientSideAnalytics {\n          referrerId\n          linkName\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    spaceDetails {\n      ...SpaceDetailsFragment\n      __typename\n    }\n    ...SleepingArrangementsFragment\n    __typename\n  }\n}\n\nfragment PropertyOffersHeaderFragment on LodgingHeader {\n  text\n  subText\n  __typename\n}\n\nfragment PropertyFeaturesFragment on PropertyInfoItem {\n  text\n  graphic {\n    __typename\n    ... on Icon {\n      description\n      id\n      __typename\n    }\n    ... on Mark {\n      description\n      id\n      __typename\n    }\n  }\n  moreInfoDialog {\n    ...LodgingPlainFullscreenDialogFragment\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingPlainFullscreenDialogFragment on LodgingPlainDialog {\n  __typename\n  content\n  trigger {\n    clientSideAnalytics {\n      linkName\n      referrerId\n      __typename\n    }\n    icon {\n      description\n      id\n      __typename\n    }\n    theme\n    value\n    __typename\n  }\n  toolbar {\n    title\n    icon {\n      description\n      __typename\n    }\n    clientSideAnalytics {\n      linkName\n      referrerId\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PropertyOffersRateViewScarcityFragment on Offer {\n  availability {\n    scarcityMessage\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyOffersDetailsDialogFragment on PropertyUnitDetailsDialog {\n  toolbar {\n    title\n    icon {\n      description\n      __typename\n    }\n    __typename\n  }\n  content {\n    ratePlanTitle {\n      text\n      __typename\n    }\n    dialogFeatures {\n      listItems {\n        text\n        icon {\n          id\n          description\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    details {\n      header {\n        text\n        subText\n        __typename\n      }\n      contents {\n        heading\n        items {\n          text\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment RatePlanWithAmenitiesFragment on RatePlan {\n  shareUrl {\n    accessibilityLabel\n    value\n    link {\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      uri {\n        relativePath\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  id\n  name\n  description\n  amenities {\n    ...RatePlanAmenitiesFragment\n    __typename\n  }\n  ...PropertyRatePlanBadgeFragment\n  paymentPolicy {\n    paymentType\n    heading\n    price {\n      ...PriceSummaryFragment\n      __typename\n    }\n    descriptions {\n      heading\n      items {\n        text\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  priceDetails {\n    optionTitle {\n      text\n      __typename\n    }\n    pointsApplied\n    ...PropertyOffersRateViewScarcityFragment\n    ...LodgingPriceSummaryFragment\n    ...PriceBreakdownSummaryFragment\n    ...PricePresentationDialogFragment\n    price {\n      ...PriceSummaryFragment\n      __typename\n    }\n    __typename\n  }\n  marketingSection {\n    ...MarketingSectionFragment\n    __typename\n  }\n  ...HighlightedMessagesFragment\n  ...PropertyOffersPriceChangeMessageFragment\n  ...PropertyReserveButtonFragment\n  loyaltyMessage {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PriceBreakdownSummaryFragment on Offer {\n  priceBreakDownSummary {\n    priceSummaryHeading {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    sections {\n      ...PriceSummarySectionFragment\n      __typename\n    }\n    disclaimers {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PriceSummarySectionFragment on PriceSummarySection {\n  sectionHeading {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  sectionFooter {\n    ...PriceSummaryFooterFragment\n    __typename\n  }\n  items {\n    ...PriceSummaryLineItemFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PriceSummaryLineItemFragment on PriceSummaryLineItem {\n  name {\n    primaryMessage {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    secondaryMessages {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    __typename\n  }\n  value {\n    primaryMessage {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    secondaryMessages {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PriceSummaryFooterFragment on PriceSummaryFooter {\n  footerMessages {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment RatePlanAmenitiesFragment on RatePlanAmenity {\n  icon {\n    id\n    description\n    size\n    __typename\n  }\n  description\n  additionalInformation\n  __typename\n}\n\nfragment LinkTriggerFragment on LodgingDialogTriggerMessage {\n  value\n  accessibilityLabel\n  __typename\n}\n\nfragment AvailabilityCtaFragment on PropertyUnit {\n  availabilityCallToAction {\n    ...AvailabilityCallToActionFragment\n    __typename\n  }\n  __typename\n}\n\nfragment RatePlansExpandoFragment on RatePlansExpando {\n  collapseButton {\n    text\n    __typename\n  }\n  expandButton {\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment SleepingArrangementsFragment on PropertyUnit {\n  spaceDetails {\n    ...SpaceDetailsHeaderFragment\n    ...SpaceDetailsSpacesFragment\n    ...SpaceDetailsFloorPlanFragment\n    __typename\n  }\n  __typename\n}\n\nfragment SpaceDetailsHeaderFragment on SpaceDetails {\n  header {\n    text\n    __typename\n  }\n  summary\n  __typename\n}\n\nfragment SpaceDetailsSpacesFragment on SpaceDetails {\n  spaces {\n    name\n    description\n    icons {\n      description\n      id\n      size\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment SpaceDetailsFloorPlanFragment on SpaceDetails {\n  floorPlan {\n    images {\n      alt\n      image {\n        description\n        url\n        __typename\n      }\n      subjectId\n      __typename\n    }\n    toolbar {\n      icon {\n        description\n        id\n        size\n        __typename\n      }\n      title\n      __typename\n    }\n    trigger {\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment RoomAmenitiesDescriptionFragment on PropertyContentSection {\n  header {\n    text\n    __typename\n  }\n  bodySubSections {\n    contents {\n      ...RoomAmenityContentFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment RoomAmenityContentFragment on PropertyContent {\n  header {\n    text\n    icon {\n      id\n      __typename\n    }\n    __typename\n  }\n  items {\n    ... on PropertyContentItemMarkup {\n      ...RoomAmenityContentTextFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment RoomAmenityContentTextFragment on PropertyContentItemMarkup {\n  content {\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment SpaceDetailsFragment on SpaceDetails {\n  ...SpaceDetailsHeaderFragment\n  ...SpaceDetailsSpacesFragment\n  ...SpaceDetailsFloorPlanFragment\n  virtualTourPrompt {\n    ...VirtualTourPromptFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyUnitCategorizationFragment on LodgingCategorizedUnit {\n  __typename\n  header {\n    ...PropertyOffersHeaderFragment\n    __typename\n  }\n  features {\n    ...PropertyFeaturesFragment\n    __typename\n  }\n  highlightedMessages {\n    ...RatePlanMessageFragment\n    __typename\n  }\n  featureHeader {\n    text\n    __typename\n  }\n  ...IncludedPerksFragment\n  ...FooterActionsFragment\n  ...UnitCategorizationFragment\n}\n\nfragment RatePlanMessageFragment on RatePlanMessage {\n  ...LodgingPlainDialogFragment\n  ...LodgingEnrichedMessageFragment\n  ...LodgingPlainMessageFragment\n  __typename\n}\n\nfragment IncludedPerksFragment on LodgingCategorizedUnit {\n  includedPerks {\n    header {\n      text\n      __typename\n    }\n    items {\n      text\n      icon {\n        description\n        id\n        __typename\n      }\n      moreInfoDialog {\n        ...LodgingPlainDialogFragment\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment FooterActionsFragment on LodgingCategorizedUnit {\n  footerActions {\n    primary\n    analytics {\n      linkName\n      referrerId\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment UnitCategorizationFragment on LodgingCategorizedUnit {\n  primarySelections {\n    propertyUnit {\n      ...UnitCategorizationPropertyUnitFragment\n      __typename\n    }\n    primarySelection {\n      ...UnitCategorizationSelectionFragment\n      __typename\n    }\n    secondarySelections {\n      recommendedSelection\n      secondarySelection {\n        ...UnitCategorizationSelectionFragment\n        __typename\n      }\n      tertiarySelections {\n        ...UnitCategorizationSelectionFragment\n        dialog {\n          ...LodgingPlainFullscreenDialogFragment\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  primaryHeader {\n    ...SelectionHeaderFragment\n    __typename\n  }\n  secondaryHeader {\n    ...SelectionHeaderFragment\n    __typename\n  }\n  tertiaryHeader {\n    ...SelectionHeaderFragment\n    __typename\n  }\n  __typename\n}\n\nfragment SelectionHeaderFragment on LodgingOfferSelectionHeader {\n  title {\n    text\n    subText\n    __typename\n  }\n  ...UnitCategorizationComplexDialogFragment\n  __typename\n}\n\nfragment UnitCategorizationComplexDialogFragment on LodgingOfferSelectionHeader {\n  dialog {\n    content {\n      content\n      title {\n        text\n        __typename\n      }\n      __typename\n    }\n    primaryUIButton {\n      ...UIPrimaryButtonFragment\n      __typename\n    }\n    toolbar {\n      title\n      icon {\n        description\n        __typename\n      }\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      __typename\n    }\n    trigger {\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      icon {\n        id\n        description\n        __typename\n      }\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment UnitCategorizationPropertyUnitFragment on PropertyUnit {\n  ...AvailabilityCtaFragment\n  detailsDialog {\n    ...PropertyOffersDetailsDialogFragment\n    toolbar {\n      clientSideAnalytics {\n        referrerId\n        linkName\n        __typename\n      }\n      __typename\n    }\n    trigger {\n      ...LinkTriggerFragment\n      clientSideAnalytics {\n        referrerId\n        linkName\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  id\n  ratePlans {\n    ...RatePlanWithAmenitiesFragment\n    ...UnitCategorizationRatePlanFragment\n    __typename\n  }\n  roomAmenities {\n    ...RoomAmenitiesDescriptionFragment\n    __typename\n  }\n  unitGallery {\n    accessibilityLabel\n    images {\n      image {\n        description\n        url\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  spaceDetails {\n    ...SpaceDetailsFragment\n    __typename\n  }\n  __typename\n}\n\nfragment UnitCategorizationRatePlanFragment on RatePlan {\n  shareUrl {\n    accessibilityLabel\n    value\n    link {\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      uri {\n        relativePath\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  description\n  id\n  loyaltyMessage {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  paymentPolicy {\n    paymentType\n    heading\n    descriptions {\n      heading\n      items {\n        text\n        __typename\n      }\n      __typename\n    }\n    price {\n      ...PriceSummaryFragment\n      __typename\n    }\n    __typename\n  }\n  priceDetails {\n    pointsApplied\n    ...PropertyOffersRateViewScarcityFragment\n    ...LodgingPriceSummaryFragment\n    ...PriceBreakdownSummaryFragment\n    ...PricePresentationDialogFragment\n    price {\n      ...PriceSummaryFragment\n      __typename\n    }\n    __typename\n  }\n  ...HighlightedMessagesFragment\n  ...PropertyOffersPriceChangeMessageFragment\n  ...PropertyRatePlanBadgeFragment\n  ...PropertyReserveButtonFragment\n  offerNotifications {\n    ...LodgingNotificationsCardFragment\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingNotificationsCardFragment on LodgingNotificationsCard {\n  header {\n    text\n    __typename\n  }\n  messages {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment UnitCategorizationSelectionFragment on LodgingOfferOption {\n  clientSideAnalytics {\n    linkName\n    referrerId\n    __typename\n  }\n  description\n  enabled\n  optionId\n  price\n  subText\n  accessibilityLabel\n  liveAnnounceMessage\n  liveAnnouncePoliteness\n  selected\n  __typename\n}\n\nfragment VerticalMessagingCardFragment on MessageResult {\n  title {\n    text\n    __typename\n  }\n  subtitle {\n    text\n    __typename\n  }\n  featuredImage {\n    url\n    description\n    __typename\n  }\n  action {\n    primary {\n      text\n      referrerId\n      actionDetails {\n        action\n        accessibilityLabel\n        __typename\n      }\n      __typename\n    }\n    secondary {\n      text\n      referrerId\n      actionDetails {\n        action\n        accessibilityLabel\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingHeaderFragment on LodgingHeader {\n  text\n  accessibilityLabel\n  impressionAnalytics {\n    event\n    referrerId\n    __typename\n  }\n  __typename\n}\n\nfragment StickyBarDisclaimerFragment on OfferDetails {\n  stickyBar {\n    price {\n      disclaimer {\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment ShoppingContextFragment on OfferDetails {\n  shoppingContext {\n    multiItem {\n      id\n      packageType\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyFilterPillsFragment on OfferDetails {\n  id\n  offerFilters {\n    accessibilityHeader\n    liveAnnounce\n    filterPills {\n      ...LodgingEGDSBasicPillFragment\n      ...LodgingFilterDialogPillFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingEGDSBasicPillFragment on EGDSBasicPill {\n  primary\n  accessibility\n  selected\n  name\n  value\n  __typename\n}\n\nfragment LodgingFilterDialogPillFragment on LodgingFilterDialogPill {\n  triggerPill {\n    primary\n    selected\n    __typename\n  }\n  filterDialog {\n    ...FilterDialogPillFragment\n    __typename\n  }\n  __typename\n}\n\nfragment FilterDialogPillFragment on LodgingFilterSelectionDialog {\n  dialog {\n    footer {\n      buttons {\n        primary\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  clearAll {\n    primary\n    __typename\n  }\n  filterSection {\n    primary\n    ... on ShoppingMultiSelectionField {\n      id\n      primary\n      options {\n        id\n        primary\n        value\n        selected\n        disabled\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  toolbar {\n    title\n    __typename\n  }\n  __typename\n}\n\nfragment PropertySpaceDetailsFragment on OfferDetails {\n  spaceDetails {\n    ...SpaceDetailsHeaderFragment\n    ...SpaceDetailsSpacesFragment\n    ...SpaceDetailsFloorPlanFragment\n    virtualTourPrompt {\n      ...VirtualTourPromptFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment VirtualTourPromptFragment on VirtualTourPrompt {\n  heading {\n    text\n    __typename\n  }\n  button {\n    accessibility\n    primary\n    icon {\n      description\n      id\n      __typename\n    }\n    action {\n      resource {\n        value\n        __typename\n      }\n      accessibility\n      __typename\n    }\n    __typename\n  }\n  heroImage {\n    description\n    url\n    cameraMovement\n    __typename\n  }\n  caption {\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment PropertySearchLinkFragment on OfferDetails {\n  propertySearchLink {\n    ...LodgingLinkMessageFragment\n    __typename\n  }\n  partnerPropertySearchLink {\n    ...LodgingLinkMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingLinkMessageFragment on LodgingLinkMessage {\n  icon {\n    id\n    __typename\n  }\n  link {\n    clientSideAnalytics {\n      referrerId\n      linkName\n      __typename\n    }\n    uri {\n      relativePath\n      value\n      __typename\n    }\n    referrerId\n    __typename\n  }\n  value\n  __typename\n}\n\nfragment PropertyUnitListViewFragment on OfferDetails {\n  categorizedListings {\n    ...PropertyUnitListViewElementFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyUnitListViewElementFragment on LodgingCategorizedUnit {\n  header {\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment FilterPillsFragment on OfferDetails {\n  filterPills {\n    pillLabel\n    query\n    type\n    value\n    __typename\n  }\n  __typename\n}\n\nfragment LoyaltyDiscountToggleFragment on OfferDetails {\n  loyaltyDiscount {\n    saveWithPointsMessage\n    saveWithPointsActionMessage\n    __typename\n  }\n  __typename\n}\n\nfragment LegalDisclaimerFragment on OfferDetails {\n  legalDisclaimer {\n    content {\n      markupType\n      text\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"
            }
        ]

        try:
            response = self.requests_post(session, 'https://www.expedia.co.kr/graphql', json=json_params, headers=headers, **args['proxy']['REQUESTS_PROXY']).json()
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])

        if 'statusCode' in response and response['statusCode'] != 200:
            return dict(
                code=504,
                rooms=[],
            )
        
        rooms = []
        for resp_item in response:
            if resp_item is not None and resp_item['data'] is not None and resp_item['data']['propertyOffers'] is not None and resp_item['data']['propertyOffers']['categorizedListings'] is not None:
                for categorized_listings in resp_item['data']['propertyOffers']['categorizedListings']:
                    # TODO : header 없는 경우가 있음
                    if 'header' not in categorized_listings:
                        continue
                    
                    room_name = categorized_listings['header']['text']
                    price = None
                    price_without_tax = 1e10
                    whole_price = 1e10

                    for primary_section in categorized_listings['primarySelections']:
                        room_id = primary_section['propertyUnit']['id']

                        for rateplan in primary_section['propertyUnit']['ratePlans']:

                            # reserveCallToAction 가 있다면 아래의 방법은 생략함
                            if 'reserveCallToAction' in rateplan and 'inputs' in rateplan['reserveCallToAction']:
                                for inp in rateplan['reserveCallToAction']['inputs']:
                                    if inp['name'] == 'totalPriceWithTaxesAndFees' and int(float(inp['value'])) < whole_price:
                                        whole_price = int(float(inp['value']))
                                continue

                            # priceDetails 가 있다면 아래의 방법은 생략함
                            if 'priceDetails' in rateplan:
                                for price_detail in rateplan['priceDetails']:
                                    if 'inputs' in price_detail['offerBookButton']:
                                        for inp in price_detail['offerBookButton']['inputs']:
                                            if inp['name'] == 'totalPriceWithTaxesAndFees' and int(float(inp['value'])) < whole_price:
                                                whole_price = int(float(inp['value']))
                                continue

                            # 세금 미포함된 가격 조회될 수 있음
                            for policy in rateplan['paymentPolicy']:
                                if policy['paymentType'] in ['PAY_NOW', 'PAY_LATER', 'PAY_LATER_WITH_DEPOSIT']:
                                    if 'price' not in policy or 'displayMessages' not in policy['price'] or policy['price']['displayMessages'] is None:
                                        continue
                                    for message in policy['price']['displayMessages']:
                                        for line_item in message['lineItems']:
                                            if line_item['__typename'] == 'LodgingEnrichedMessage':
                                                try:
                                                    whole_price = min(whole_price, replace_price(line_item['value']))
                                                    if whole_price < 10000:
                                                        whole_price = 1e10
                                                except:
                                                    whole_price = 1e10
                                            elif line_item['__typename'] == 'DisplayPrice' and line_item['role'] == 'LEAD':
                                                try:
                                                    price_without_tax = min(price_without_tax, replace_price(line_item['price']['formatted']))
                                                    if price_without_tax < 10000:
                                                        price_without_tax = 1e10
                                                except:
                                                    price_without_tax = 1e10
                    
                    if whole_price < 1e10:
                        price = whole_price
                    elif price_without_tax < 1e10:
                        price = price_without_tax

                    if price is None:
                        continue
                    
                    rooms.append(dict(
                        room_id=room_id, 
                        name=room_name, 
                        remain=1,
                        price=price,
                    ))
            elif resp_item is not None and resp_item['data'] is not None and resp_item['data']['propertyOffers'] is not None and resp_item['data']['propertyOffers']['listings'] is not None:
                for listings in resp_item['data']['propertyOffers']['listings']:
                    # TODO : header 없는 경우가 있음??
                    if 'header' not in listings:
                        continue
                    
                    room_name = listings['header']['text']
                    price = None

                    for rateplan in listings['ratePlans']:
                        room_id = rateplan['id']

                        if True:
                            price_without_tax = 1e10
                            whole_price = 1e10

                            for policy in rateplan['paymentPolicy']:
                                if policy['paymentType'] in ['PAY_NOW', 'PAY_LATER', 'PAY_LATER_WITH_DEPOSIT']:
                                    if 'price' not in policy or 'displayMessages' not in policy['price'] or policy['price']['displayMessages'] is None:
                                        continue
                                    for message in policy['price']['displayMessages']:
                                        for line_item in message['lineItems']:
                                            if line_item['__typename'] == 'LodgingEnrichedMessage':
                                                whole_price = min(whole_price, replace_price(line_item['value']))
                                            elif line_item['__typename'] == 'DisplayPrice' and line_item['role'] == 'LEAD':
                                                price_without_tax = min(price_without_tax, replace_price(line_item['price']['formatted']))
                            
                            if whole_price < 1e10:
                                price = whole_price
                            elif price_without_tax < 1e10:
                                price = price_without_tax
                        
                        if price is not None:
                            break

                    if price is None:
                        continue
                    
                    rooms.append(dict(
                        room_id=room_id, 
                        name=room_name, 
                        remain=1,
                        price=price,
                    ))

        return dict(
            code=200,
            rooms=rooms,
        )

    def scrape_reviews(self, output, args, url, hotel_id, page):
        session = requests.Session()

        duaid = session.cookies.get('DUAID', '')
        kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        kst2 = kst + datetime.timedelta(days=1)

        size = 100
        startIndex = (page - 1) * size

        headers = {
            'x-page-id': 'page.Hotels.Infosite.Information,H,30',
            'client-info': 'shopping-pwa,06e60a6b7371b560f358d838f5d6aadaa09a953b,us-west-2',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="{}", "Chromium";v="{}"'.format(SELENIUM_VERSION, SELENIUM_VERSION),
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.0.0 Safari/537.36'.format(SELENIUM_VERSION),
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        params = [{
                "operationName": "PropertyFilteredReviewsQuery",
                "variables": {
                    "context": {
                        "siteId": 16,
                        "locale": "ko_KR",
                        "eapid": 0,
                        "currency": "KRW",
                        "device": {"type": "DESKTOP"},
                        "identity": {
                            "duaid": "fdc0554e-2949-4f5f-8727-f790c87cd076",
                            "expUserId": "-1",
                            "tuid": "1",
                            "authState": "ANONYMOUS",
                        },
                        "privacyTrackingState": "CAN_TRACK",
                        "debugContext": {"abacusOverrides": [], "alterMode": "RELEASED"},
                    },
                    "propertyId": "{}".format(hotel_id),
                    "searchCriteria": {
                        "primary": {
                            "dateRange": None,
                            "rooms": [{"adults": 2}],
                            "destination": {"regionId": "178308"},
                        },
                        "secondary": {
                            "booleans": [
                                {"id": "includeRecentReviews", "value": True},
                                {"id": "includeRatingsOnlyReviews", "value": True},
                                {"id": "overrideEmbargoForIndividualReviews", "value": True}
                            ],
                            "counts": [
                                {"id": "startIndex", "value": startIndex},
                                {"id": "size", "value": 100},
                            ],
                            "selections": [
                                {"id": "sortBy", "value": "NEWEST_TO_OLDEST"}
                            ],
                        },
                    },
                },
                "query": "query PropertyFilteredReviewsQuery($context: ContextInput!, $propertyId: String!, $searchCriteria: PropertySearchCriteriaInput!) {\n  propertyReviewSummaries(\n    context: $context\n    propertyIds: [$propertyId]\n    searchCriteria: $searchCriteria\n  ) {\n    ...__PropertyReviewSummaryFragment\n    __typename\n  }\n  propertyInfo(context: $context, propertyId: $propertyId) {\n    id\n    reviewInfo(searchCriteria: $searchCriteria) {\n      ...__PropertyReviewsListFragment\n      ...__WriteReviewLinkFragment\n      sortAndFilter {\n        ...TravelerTypeFragment\n        ...SortTypeFragment\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment __PropertyReviewSummaryFragment on PropertyReviewSummary {\n  accessibilityLabel\n  overallScoreWithDescription\n  propertyReviewCountDetails {\n    fullDescription\n    __typename\n  }\n  ...ReviewDisclaimerFragment\n  reviewSummaryDetails {\n    label\n    ratingPercentage\n    formattedRatingOutOfMax\n    __typename\n  }\n  totalCount {\n    raw\n    __typename\n  }\n  __typename\n}\n\nfragment ReviewDisclaimerFragment on PropertyReviewSummary {\n  reviewDisclaimer\n  reviewDisclaimerLabel\n  reviewDisclaimerUrl {\n    value\n    accessibilityLabel\n    link {\n      url\n      __typename\n    }\n    __typename\n  }\n  reviewDisclaimerAccessibilityLabel\n  __typename\n}\n\nfragment __PropertyReviewsListFragment on PropertyReviews {\n  summary {\n    paginateAction {\n      text\n      analytics {\n        referrerId\n        linkName\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  reviews {\n    contentDirectFeedbackPromptId\n    ...ReviewParentFragment\n    managementResponses {\n      ...ReviewChildFragment\n      __typename\n    }\n    reviewInteractionSections {\n      primaryDisplayString\n      reviewInteractionType\n      __typename\n    }\n    __typename\n  }\n  ...NoResultsMessageFragment\n  __typename\n}\n\nfragment ReviewParentFragment on PropertyReview {\n  id\n  superlative\n  locale\n  title\n  brandType\n  reviewScoreWithDescription {\n    label\n    value\n    __typename\n  }\n  text\n  submissionTime {\n    longDateFormat\n    __typename\n  }\n  themes {\n    ...ReviewThemeFragment\n    __typename\n  }\n  reviewFooter {\n    ...PropertyReviewFooterSectionFragment\n    __typename\n  }\n  ...FeedbackIndicatorFragment\n  ...AuthorFragment\n  ...PhotosFragment\n  ...TravelersFragment\n  ...ReviewTranslationInfoFragment\n  ...PropertyReviewSourceFragment\n  ...PropertyReviewRegionFragment\n  __typename\n}\n\nfragment AuthorFragment on PropertyReview {\n  reviewAuthorAttribution {\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment PhotosFragment on PropertyReview {\n  id\n  photos {\n    description\n    url\n    __typename\n  }\n  __typename\n}\n\nfragment TravelersFragment on PropertyReview {\n  travelers\n  __typename\n}\n\nfragment ReviewThemeFragment on ReviewThemes {\n  icon {\n    id\n    __typename\n  }\n  label\n  __typename\n}\n\nfragment FeedbackIndicatorFragment on PropertyReview {\n  reviewInteractionSections {\n    primaryDisplayString\n    accessibilityLabel\n    reviewInteractionType\n    __typename\n  }\n  __typename\n}\n\nfragment ReviewTranslationInfoFragment on PropertyReview {\n  translationInfo {\n    loadingTranslationText\n    targetLocale\n    translatedBy {\n      description\n      __typename\n    }\n    translationCallToActionLabel\n    seeOriginalText\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyReviewSourceFragment on PropertyReview {\n  propertyReviewSource {\n    accessibilityLabel\n    graphic {\n      description\n      id\n      size\n      token\n      url {\n        value\n        __typename\n      }\n      __typename\n    }\n    text {\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyReviewRegionFragment on PropertyReview {\n  reviewRegion {\n    id\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyReviewFooterSectionFragment on PropertyReviewFooterSection {\n  messages {\n    seoStructuredData {\n      itemscope\n      itemprop\n      itemtype\n      content\n      __typename\n    }\n    text {\n      ... on EGDSPlainText {\n        text\n        __typename\n      }\n      ... on EGDSGraphicText {\n        text\n        graphic {\n          ... on Mark {\n            description\n            id\n            size\n            url {\n              ... on HttpURI {\n                relativePath\n                value\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment ReviewChildFragment on ManagementResponse {\n  id\n  header {\n    text\n    __typename\n  }\n  response\n  __typename\n}\n\nfragment NoResultsMessageFragment on PropertyReviews {\n  noResultsMessage {\n    __typename\n    ...MessagingCardFragment\n    ...EmptyStateFragment\n  }\n  __typename\n}\n\nfragment MessagingCardFragment on UIMessagingCard {\n  graphic {\n    __typename\n    ... on Icon {\n      id\n      description\n      __typename\n    }\n  }\n  primary\n  secondaries\n  __typename\n}\n\nfragment EmptyStateFragment on UIEmptyState {\n  heading\n  body\n  __typename\n}\n\nfragment TravelerTypeFragment on SortAndFilterViewModel {\n  sortAndFilter {\n    name\n    label\n    options {\n      label\n      isSelected\n      optionValue\n      description\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment __WriteReviewLinkFragment on PropertyReviews {\n  writeReviewLink {\n    link {\n      uri {\n        value\n        relativePath\n        __typename\n      }\n      clientSideAnalytics {\n        referrerId\n        linkName\n        __typename\n      }\n      __typename\n    }\n    value\n    accessibilityLabel\n    __typename\n  }\n  __typename\n}\n\nfragment SortTypeFragment on SortAndFilterViewModel {\n  sortAndFilter {\n    name\n    label\n    options {\n      label\n      isSelected\n      optionValue\n      description\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n",
            }
        ]

        try:
            resp = self.requests_post(requests, 'https://www.expedia.co.kr/graphql', json=params, headers=headers).json()
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])

        result = []
        for resp_item in resp:
            try:
                for review in resp_item['data']['propertyInfo']['reviewInfo']['reviews']:
                    reply = []
                    if review.get('managementResponses') is not None:
                        for management_resp in review['managementResponses']:
                            headers = management_resp['header']['text'].replace('답변 제공: ', '').split(' 님, ')
                            reply.append(dict(
                                author=headers[0],
                                content=management_resp['response'],
                                created_at=datetime.datetime.strptime(headers[1], '%Y년 %m월 %d일')
                            ))
                    
                    categories = []
                    for group_name in review['travelers']:
                        if '나홀로 여행' in group_name:
                            categories.append('나홀로 여행')
                        elif '연인' in group_name:
                            categories.append('커플')
                        elif '친구' in group_name:
                            categories.append('친구')
                        elif '가족' in group_name:
                            categories.append('가족')
                    
                    if len(categories) == 0:
                        category = '기타'
                    else:
                        category = ','.join(categories)
                    
                    result.append(dict(
                        id=review['id'],
                        author=review['reviewAuthorAttribution']['text'],
                        content='{}\n{}'.format(review['title'], review['text']),
                        category=category,
                        score=int(review['reviewScoreWithDescription']['value'].split('/')[0]),
                        created_at=datetime.datetime.strptime(review['submissionTime']['longDateFormat'], '%Y년 %m월 %d일'),
                        reply=reply
                    ))
            except:
                return dict(code=500, comments=[])

        # 리뷰 개수, 평점
        score = None
        count = None

        headers = {
            'x-page-id': 'page.Hotels.Infosite.Information,H,30',
            'client-info': 'shopping-pwa,06e60a6b7371b560f358d838f5d6aadaa09a953b,us-west-2',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="{}", "Chromium";v="{}"'.format(SELENIUM_VERSION, SELENIUM_VERSION),
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.0.0.0 Safari/537.36'.format(SELENIUM_VERSION),
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        try:
            resp = self.requests_get(requests, '{}?pwaDialog=reviews-property-reviews-1'.format(url), headers=headers).text
            
            m = pattern_overall_rating.search(resp)
            if m is not None:
                rating_str = m.group(1)
                rating_str = '{' + str(rating_str.replace('\\', '')) + '}'
                rating_json = json.loads(rating_str)
                score = float(rating_json['formatted'].replace(',', ''))
            
            m = pattern_total_count.search(resp)
            if m is not None:
                count_str = m.group(1)
                count_str = '{' + str(count_str.replace('\\', '')) + '}'
                count_json = json.loads(count_str)
                if 'formatted' in count_json:
                    count = int(count_json['formatted'].replace(',', ''))
                else:
                    count = int(count_json['raw'])
            
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])
        except Exception:
            print(traceback.print_exc())
            pass
        
        return dict(code=200, comments=result, score=score, count=count)
