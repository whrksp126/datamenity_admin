from datamenity.ota.OTABase import OTABase, ExceptionReadTimeout
from datamenity.config import REQUESTS_PROXY, SELENIUM_PROXY

import requests
import datetime
import json
import time
import browsercookie
import re
import traceback

pattern_hotel_id = re.compile('\.h([0-9]*)\.Hotel\-Information')
pattern_total_count = re.compile('totalCount[^\{]*\{([^\}]*)\}')
pattern_overall_rating = re.compile('averageOverallRating[^\{]*\{([^\}]*)\}')
pattern_hotel_url = re.compile('https://images.trvl-media.com/lodging/[0-9]*/[0-9]*/[0-9]*/([0-9]*)/')


def replace_price(txt):
    txt = re.sub(r'[^0-9]', '', txt.replace(',', ''))
    return int(float(txt))


class OTAHotels(OTABase):
    def get_hotel_id(self, args, url):
        return url.split('/ho')[1].split('/')[0]
    
    def scrape_prices(self, output, args, url, hotel_id, checkin, checkout):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        }

        in_y, in_m, in_d = checkin.split('-')
        out_y, out_m, out_d = checkout.split('-')
        in_y = int(in_y)
        in_m = int(in_m)
        in_d = int(in_d)
        out_y = int(out_y)
        out_m = int(out_m)
        out_d = int(out_d)

        try:
            result = self.requests_get(requests, 'https://kr.hotels.com/ho{}/?pa=1&q-check-out={}&tab=description&q-room-0-adults=2&YGF=7&q-check-in={}&MGT=1&WOE=5&WOD=4&ZSX=0&SYE=3&q-room-0-children=0'.format(hotel_id, checkout, checkin), **args['proxy']['REQUESTS_PROXY']).text
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])
        
        rooms = []
        m = pattern_hotel_url.search(result)
        if not m:
            return dict(code=403, rooms=[])
 
        hotel_propery_id = json.loads(m.group(1))
        
        json_params = [
            {
                "operationName":"PropertyOffersQuery",
                "variables":{
                    "propertyId":"{}".format(hotel_propery_id),
                    "searchCriteria":{
                        "primary":{
                            "dateRange":{
                                "checkInDate":{"day":in_d,"month":in_m,"year":in_y},
                                "checkOutDate":{"day":out_d,"month":out_m,"year":out_y}
                            },
                            "destination":{"regionName":"부산, 한국","regionId":"602043","coordinates":None,"pinnedPropertyId":"{}".format(hotel_propery_id),"propertyIds":None,"mapBounds":None},
                            "rooms":[{"adults":2,"children":[]}]
                        },
                        "secondary":{
                            "counts":[],
                            "booleans":[],
                            "selections":[
                                {"id":"sort","value":"RECOMMENDED"},
                                {"id":"privacyTrackingState","value":"CAN_NOT_TRACK"},
                                {"id":"useRewards","value":"SHOP_WITHOUT_POINTS"}
                            ],
                            "ranges":[]
                        }
                    },
                    "shoppingContext":{"multiItem":None},
                    "travelAdTrackingInfo":None,
                    "searchOffer":{"offerPrice":None,"roomTypeId":"200805011","ratePlanId":"204023228"},
                    "referrer":"HSR",
                    "context":{
                        "siteId":300000041,
                        "locale":"ko_KR",
                        "eapid":41,
                        "currency":"KRW",
                        "device":{"type":"DESKTOP"},
                        "identity":{
                            "duaid":"62df6957-0f8e-4cf9-b374-5c38d67c8bc9",
                            "expUserId":"-1",
                            "tuid":"-1",
                            "authState":"ANONYMOUS"
                        },
                        "privacyTrackingState":"CAN_TRACK",
                        "debugContext":{"abacusOverrides":[],"alterMode":"RELEASED"}
                    }
                },
                "query":"query PropertyOffersQuery($context: ContextInput!, $propertyId: String!, $searchCriteria: PropertySearchCriteriaInput, $shoppingContext: ShoppingContextInput, $travelAdTrackingInfo: PropertyTravelAdTrackingInfoInput, $searchOffer: SearchOfferInput, $referrer: String) {\n  propertyOffers(\n    context: $context\n    propertyId: $propertyId\n    referrer: $referrer\n    searchCriteria: $searchCriteria\n    searchOffer: $searchOffer\n    shoppingContext: $shoppingContext\n    travelAdTrackingInfo: $travelAdTrackingInfo\n  ) {\n    id\n    loading {\n      accessibilityLabel\n      __typename\n    }\n    ...PropertyLevelOffersMessageFragment\n    ...ListingsHeaderFragment\n    ...VipMessagingFragment\n    ...NewVipModuleFragment\n    ...PropertyTripSummaryFragment\n    ...SingleOfferFragment\n    ...PropertyStickyBookBarFragment\n    ...PropertyOffersFragment\n    ...PropertySpaceDetailsFragment\n    ...PropertySearchLinkFragment\n    ...PropertyUnitListViewFragment\n    ...FilterPillsFragment\n    ...LoyaltyDiscountToggleFragment\n    ...LegalDisclaimerFragment\n    ...HighlightedBenefitsFragment\n    __typename\n  }\n}\n\nfragment PropertyLevelOffersMessageFragment on OfferDetails {\n  propertyLevelOffersMessage {\n    ...MessageResultFragment\n    ...SparkleBannerFragment\n    __typename\n  }\n  __typename\n}\n\nfragment MessageResultFragment on MessageResult {\n  title {\n    text\n    ...MessagingResultTitleMediaFragment\n    __typename\n  }\n  subtitle {\n    text\n    ...MessagingResultTitleMediaFragment\n    __typename\n  }\n  action {\n    primary {\n      ...MessageActionContent\n      __typename\n    }\n    secondary {\n      ...MessageActionContent\n      __typename\n    }\n    __typename\n  }\n  type\n  __typename\n}\n\nfragment MessageActionContent on MessagingAction {\n  text\n  linkUrl\n  referrerId\n  actionDetails {\n    action\n    accessibilityLabel\n    __typename\n  }\n  analytics {\n    linkName\n    referrerId\n    __typename\n  }\n  __typename\n}\n\nfragment MessagingResultTitleMediaFragment on MessagingResultTitle {\n  icon {\n    id\n    description\n    size\n    spotLight\n    __typename\n  }\n  illustration {\n    assetUri {\n      value\n      __typename\n    }\n    description\n    __typename\n  }\n  mark {\n    id\n    description\n    __typename\n  }\n  egdsMark {\n    id\n    description\n    url {\n      ... on HttpURI {\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment SparkleBannerFragment on MessageResult {\n  __typename\n  title {\n    ...MessageTitleFields\n    ...MessagingResultTitleMediaFragment\n    __typename\n  }\n  subtitle {\n    ...MessageTitleFields\n    __typename\n  }\n  action {\n    primary {\n      ...MessagingActionFields\n      __typename\n    }\n    secondary {\n      ...MessagingActionFields\n      __typename\n    }\n    __typename\n  }\n  type\n}\n\nfragment MessageTitleFields on MessagingResultTitle {\n  text\n  icon {\n    description\n    id\n    __typename\n  }\n  mark {\n    description\n    id\n    __typename\n  }\n  illustration {\n    assetUri {\n      value\n      __typename\n    }\n    description\n    __typename\n  }\n  __typename\n}\n\nfragment MessagingActionFields on MessagingAction {\n  actionDetails {\n    action\n    accessibilityLabel\n    __typename\n  }\n  analytics {\n    linkName\n    referrerId\n    __typename\n  }\n  linkUrl\n  referrerId\n  text\n  __typename\n}\n\nfragment VipMessagingFragment on OfferDetails {\n  propertyHighlightSection {\n    ...PropertyHighlightSectionFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyHighlightSectionFragment on PropertyHighlightSection {\n  label\n  header {\n    badge {\n      text\n      theme_temp\n      __typename\n    }\n    mark {\n      id\n      description\n      __typename\n    }\n    text\n    __typename\n  }\n  subSections {\n    description\n    contents {\n      icon {\n        id\n        withBackground\n        description\n        __typename\n      }\n      value\n      __typename\n    }\n    __typename\n  }\n  footerLink {\n    icon {\n      id\n      __typename\n    }\n    link {\n      referrerId\n      uri {\n        relativePath\n        value\n        __typename\n      }\n      target\n      __typename\n    }\n    value\n    accessibilityLabel\n    __typename\n  }\n  __typename\n}\n\nfragment NewVipModuleFragment on OfferDetails {\n  propertyHighlightSection {\n    ...VipModuleFragment\n    __typename\n  }\n  __typename\n}\n\nfragment VipModuleFragment on PropertyHighlightSection {\n  label\n  header {\n    mark {\n      id\n      description\n      __typename\n    }\n    text\n    __typename\n  }\n  subSections {\n    title {\n      badge {\n        theme_temp\n        text\n        __typename\n      }\n      value\n      state\n      __typename\n    }\n    description\n    contents {\n      badge {\n        text\n        theme_temp\n        __typename\n      }\n      value\n      __typename\n    }\n    footerLink {\n      icon {\n        id\n        withBackground\n        description\n        __typename\n      }\n      link {\n        referrerId\n        uri {\n          relativePath\n          value\n          __typename\n        }\n        target\n        __typename\n      }\n      value\n      accessibilityLabel\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyTripSummaryFragment on OfferDetails {\n  tripSummary {\n    ...TripSummaryFragment\n    __typename\n  }\n  __typename\n}\n\nfragment TripSummaryFragment on TripSummaryContent {\n  header {\n    text\n    __typename\n  }\n  summary {\n    value\n    __typename\n  }\n  price {\n    options {\n      displayPrice {\n        formatted\n        __typename\n      }\n      strikeOut {\n        formatted\n        __typename\n      }\n      accessibilityLabel\n      priceDisclaimer {\n        content\n        tertiaryUIButton {\n          primary\n          action {\n            analytics {\n              referrerId\n              linkName\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        trigger {\n          clientSideAnalytics {\n            linkName\n            referrerId\n            __typename\n          }\n          value\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    priceMessaging {\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment SingleOfferFragment on OfferDetails {\n  ...PropertySingleRatePlanFragment\n  __typename\n}\n\nfragment PropertySingleRatePlanFragment on OfferDetails {\n  errorMessage {\n    ...ErrorMessageFragment\n    __typename\n  }\n  alternateAvailabilityMsg {\n    ...AlternateAvailabilityMsgFragment\n    __typename\n  }\n  ...AlternateDatesFragment\n  singleUnitOffer {\n    accessibilityLabel\n    ...TotalPriceFragment\n    ...PropertySingleOfferDetailsFragment\n    ratePlans {\n      priceDetails {\n        ...PriceBreakdownSummaryFragment\n        ...PricePresentationDialogFragment\n        __typename\n      }\n      marketingSection {\n        ...MarketingSectionFragment\n        __typename\n      }\n      shareUrl {\n        accessibilityLabel\n        value\n        link {\n          clientSideAnalytics {\n            linkName\n            referrerId\n            __typename\n          }\n          uri {\n            relativePath\n            value\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      ...ReservePropertyFragment\n      __typename\n    }\n    view\n    __typename\n  }\n  ...PropertySingleOfferDialogLinkFragment\n  __typename\n}\n\nfragment ErrorMessageFragment on MessageResult {\n  title {\n    text\n    __typename\n  }\n  action {\n    primary {\n      text\n      linkUrl\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment AlternateAvailabilityMsgFragment on LodgingComplexLinkMessage {\n  text {\n    value\n    __typename\n  }\n  actionLink {\n    link {\n      uri {\n        relativePath\n        value\n        __typename\n      }\n      __typename\n    }\n    value\n    __typename\n  }\n  __typename\n}\n\nfragment AlternateDatesFragment on OfferDetails {\n  alternateDates {\n    header {\n      text\n      subText\n      __typename\n    }\n    options {\n      ...AlternateDateOptionFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment AlternateDateOptionFragment on AlternateDateOption {\n  dates {\n    link {\n      uri {\n        relativePath\n        __typename\n      }\n      referrerId\n      __typename\n    }\n    value\n    __typename\n  }\n  price {\n    displayPrice {\n      formatted\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment TotalPriceFragment on SingleUnitOfferDetails {\n  totalPrice {\n    label {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    amount {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingEnrichedMessageFragment on LodgingEnrichedMessage {\n  __typename\n  subText\n  value\n  theme\n  state\n  accessibilityLabel\n  icon {\n    id\n    size\n    __typename\n  }\n  mark {\n    id\n    __typename\n  }\n  egdsMark {\n    url {\n      value\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PropertySingleOfferDetailsFragment on SingleUnitOfferDetails {\n  id\n  ...PriceMessagesFragment\n  ratePlans {\n    ...SingleUnitPriceSummaryFragment\n    ...HighlightedMessagesFragment\n    __typename\n  }\n  ...SingleOfferAvailabilityCtaFragment\n  __typename\n}\n\nfragment PriceMessagesFragment on SingleUnitOfferDetails {\n  displayPrice {\n    priceMessages {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment SingleUnitPriceSummaryFragment on RatePlan {\n  ...PropertyOffersPriceChangeMessageFragment\n  ...PropertyRatePlanBadgeFragment\n  priceDetails {\n    pointsApplied\n    ...LodgingPriceSummaryFragment\n    price {\n      ...PriceSummaryFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingPriceSummaryFragment on Offer {\n  price {\n    options {\n      leadingCaption\n      displayPrice {\n        formatted\n        __typename\n      }\n      priceDisclaimer {\n        content\n        primaryButton {\n          text\n          __typename\n        }\n        trigger {\n          icon {\n            description\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      accessibilityLabel\n      strikeOut {\n        formatted\n        __typename\n      }\n      loyaltyPrice {\n        unit\n        amount {\n          formatted\n          __typename\n        }\n        totalStrikeOutPoints {\n          formatted\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    priceMessaging {\n      value\n      theme\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyRatePlanBadgeFragment on RatePlan {\n  badge {\n    theme_temp\n    text\n    icon_temp {\n      id\n      description\n      title\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyOffersPriceChangeMessageFragment on RatePlan {\n  headerMessage {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PriceSummaryFragment on PropertyPrice {\n  displayMessages {\n    lineItems {\n      ...PriceMessageFragment\n      ...EnrichedMessageFragment\n      __typename\n    }\n    __typename\n  }\n  options {\n    leadingCaption\n    displayPrice {\n      formatted\n      __typename\n    }\n    disclaimer {\n      value\n      __typename\n    }\n    priceDisclaimer {\n      content\n      primaryButton {\n        text\n        __typename\n      }\n      trigger {\n        icon {\n          description\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    accessibilityLabel\n    strikeOut {\n      formatted\n      __typename\n    }\n    loyaltyPrice {\n      unit\n      amount {\n        formatted\n        __typename\n      }\n      totalStrikeOutPoints {\n        formatted\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  priceMessaging {\n    value\n    theme\n    __typename\n  }\n  __typename\n}\n\nfragment PriceMessageFragment on DisplayPrice {\n  __typename\n  role\n  price {\n    formatted\n    accessibilityLabel\n    __typename\n  }\n  disclaimer {\n    content\n    primaryUIButton {\n      accessibility\n      primary\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment EnrichedMessageFragment on LodgingEnrichedMessage {\n  __typename\n  value\n  state\n}\n\nfragment HighlightedMessagesFragment on RatePlan {\n  id\n  highlightedMessages {\n    ...LodgingPlainDialogFragment\n    ...LodgingEnrichedMessageFragment\n    ...LodgingPlainMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingPlainDialogFragment on LodgingPlainDialog {\n  content\n  primaryUIButton {\n    ...UIPrimaryButtonFragment\n    __typename\n  }\n  secondaryUIButton {\n    ...UISecondaryButtonFragment\n    __typename\n  }\n  primaryButton {\n    text\n    analytics {\n      linkName\n      referrerId\n      __typename\n    }\n    __typename\n  }\n  trigger {\n    clientSideAnalytics {\n      linkName\n      referrerId\n      __typename\n    }\n    icon {\n      description\n      id\n      __typename\n    }\n    theme\n    value\n    secondaryValue\n    __typename\n  }\n  __typename\n}\n\nfragment UIPrimaryButtonFragment on UIPrimaryButton {\n  primary\n  action {\n    __typename\n    analytics {\n      referrerId\n      linkName\n      __typename\n    }\n    ... on UILinkAction {\n      resource {\n        value\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment UISecondaryButtonFragment on UISecondaryButton {\n  primary\n  action {\n    __typename\n    analytics {\n      referrerId\n      linkName\n      __typename\n    }\n    ... on UILinkAction {\n      resource {\n        value\n        __typename\n      }\n      __typename\n    }\n  }\n  __typename\n}\n\nfragment LodgingPlainMessageFragment on LodgingPlainMessage {\n  value\n  __typename\n}\n\nfragment SingleOfferAvailabilityCtaFragment on SingleUnitOfferDetails {\n  availabilityCallToAction {\n    ... on LodgingPlainMessage {\n      value\n      __typename\n    }\n    ... on LodgingButton {\n      text\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment MarketingSectionFragment on MarketingSection {\n  title {\n    text\n    __typename\n  }\n  feeDialog {\n    title\n    content\n    tertiaryUIButton {\n      primary\n      __typename\n    }\n    trigger {\n      value\n      mark {\n        id\n        __typename\n      }\n      icon {\n        id\n        size\n        __typename\n      }\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  paymentDetails {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment ReservePropertyFragment on RatePlan {\n  paymentPolicy {\n    paymentType\n    heading\n    descriptions {\n      heading\n      header {\n        text\n        mark {\n          id\n          token\n          url {\n            value\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      items {\n        ...PropertyInfoMessageFragment\n        icon {\n          id\n          token\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    price {\n      ...PriceSummaryFragment\n      __typename\n    }\n    __typename\n  }\n  priceDetails {\n    ...PriceBreakdownSummaryFragment\n    __typename\n  }\n  ...PropertyReserveButtonFragment\n  __typename\n}\n\nfragment PropertyReserveButtonFragment on RatePlan {\n  id\n  reserveCallToAction {\n    __typename\n    ... on EtpDialog {\n      trigger {\n        value\n        accessibilityLabel\n        __typename\n      }\n      toolbar {\n        icon {\n          description\n          __typename\n        }\n        title\n        __typename\n      }\n      __typename\n    }\n    ... on LodgingForm {\n      ...PropertyLodgingFormButtonFragment\n      __typename\n    }\n    ... on LodgingMemberSignInDialog {\n      ...LodgingMemberSignInDialogFragment\n      __typename\n    }\n  }\n  etpDialogTopMessage {\n    ...MessageResultFragment\n    __typename\n  }\n  priceDetails {\n    action {\n      ... on SelectPackageActionInput {\n        packageOfferId\n        __typename\n      }\n      __typename\n    }\n    price {\n      multiItemPriceToken\n      __typename\n    }\n    hotelCollect\n    propertyNaturalKeys {\n      id\n      checkIn {\n        month\n        day\n        year\n        __typename\n      }\n      checkOut {\n        month\n        day\n        year\n        __typename\n      }\n      inventoryType\n      noCreditCard\n      ratePlanId\n      roomTypeId\n      ratePlanType\n      rooms {\n        childAges\n        numberOfAdults\n        __typename\n      }\n      shoppingPath\n      __typename\n    }\n    noCreditCard\n    paymentModel\n    ...PropertyPaymentOptionsFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyLodgingFormButtonFragment on LodgingForm {\n  action\n  inputs {\n    ... on LodgingTextInput {\n      name\n      type\n      value\n      __typename\n    }\n    __typename\n  }\n  method\n  submit {\n    text\n    accessibilityLabel\n    analytics {\n      linkName\n      referrerId\n      __typename\n    }\n    lodgingClientSideAnalyticsSuccess {\n      campaignId\n      events {\n        eventType\n        eventTarget\n        banditDisplayed\n        payloadId\n        __typename\n      }\n      clientSideAnalytics {\n        referrerId\n        linkName\n        __typename\n      }\n      __typename\n    }\n    lodgingRecommendationClickstreamEvent {\n      recommendationResponseId\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyPaymentOptionsFragment on Offer {\n  loyaltyMessage {\n    ... on LodgingEnrichedMessage {\n      value\n      state\n      __typename\n    }\n    __typename\n  }\n  offerBookButton {\n    ...PropertyLodgingFormButtonFragment\n    __typename\n  }\n  ...PropertyPaymentPriceFragment\n  price {\n    ...PriceSummaryFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyPaymentPriceFragment on Offer {\n  price {\n    lead {\n      formatted\n      __typename\n    }\n    priceMessaging {\n      value\n      theme\n      __typename\n    }\n    options {\n      leadingCaption\n      displayPrice {\n        formatted\n        __typename\n      }\n      disclaimer {\n        value\n        __typename\n      }\n      priceDisclaimer {\n        content\n        primaryButton {\n          text\n          __typename\n        }\n        trigger {\n          icon {\n            description\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      accessibilityLabel\n      strikeOut {\n        formatted\n        __typename\n      }\n      loyaltyPrice {\n        unit\n        amount {\n          formatted\n          __typename\n        }\n        totalStrikeOutPoints {\n          formatted\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingMemberSignInDialogFragment on LodgingMemberSignInDialog {\n  dialogTrigger: trigger {\n    value\n    accessibilityLabel\n    __typename\n  }\n  title\n  dialogContent {\n    ...EGDSParagraphFragment\n    __typename\n  }\n  actionDialog {\n    ...EGDSActionDialogFragment\n    __typename\n  }\n  __typename\n}\n\nfragment EGDSParagraphFragment on EGDSParagraph {\n  text\n  style\n  __typename\n}\n\nfragment EGDSActionDialogFragment on EGDSActionDialog {\n  closeAnalytics {\n    referrerId\n    linkName\n    __typename\n  }\n  footer {\n    ... on EGDSStackedDialogFooter {\n      buttons {\n        ... on EGDSOverlayButton {\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    ... on EGDSInlineDialogFooter {\n      buttons {\n        ... on UIPrimaryButton {\n          accessibility\n          primary\n          disabled\n          action {\n            ... on UILinkAction {\n              resource {\n                value\n                __typename\n              }\n              analytics {\n                linkName\n                referrerId\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        ... on UITertiaryButton {\n          accessibility\n          primary\n          action {\n            ... on UILinkAction {\n              resource {\n                value\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n          disabled\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyInfoMessageFragment on PropertyInfoItem {\n  text\n  icon {\n    id\n    token\n    __typename\n  }\n  state\n  graphic {\n    ... on Mark {\n      description\n      markUrl: url {\n        relativePath\n        value\n        __typename\n      }\n      size\n      id\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertySingleOfferDialogLinkFragment on OfferDetails {\n  singleUnitOfferDialog {\n    content {\n      ...PropertySingleOfferDetailsFragment\n      ratePlans {\n        priceDetails {\n          ...PriceBreakdownSummaryFragment\n          ...PricePresentationDialogFragment\n          __typename\n        }\n        marketingSection {\n          ...MarketingSectionFragment\n          __typename\n        }\n        ...ReservePropertyFragment\n        __typename\n      }\n      __typename\n    }\n    trigger {\n      value\n      secondaryValue\n      __typename\n    }\n    toolbar {\n      icon {\n        description\n        __typename\n      }\n      title\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PricePresentationDialogFragment on Offer {\n  pricePresentationDialog {\n    toolbar {\n      title\n      icon {\n        description\n        __typename\n      }\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      __typename\n    }\n    trigger {\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      value\n      __typename\n    }\n    __typename\n  }\n  pricePresentation {\n    title {\n      primary\n      __typename\n    }\n    sections {\n      ...PricePresentationSectionFragment\n      __typename\n    }\n    footer {\n      header\n      messages {\n        ...PriceLineElementFragment\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PricePresentationSectionFragment on PricePresentationSection {\n  header {\n    name {\n      ...PricePresentationLineItemEntryFragment\n      __typename\n    }\n    enrichedValue {\n      ...PricePresentationLineItemEntryFragment\n      __typename\n    }\n    __typename\n  }\n  subSections {\n    ...PricePresentationSubSectionFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PricePresentationSubSectionFragment on PricePresentationSubSection {\n  header {\n    name {\n      primaryMessage {\n        __typename\n        ... on PriceLineText {\n          primary\n          __typename\n        }\n        ... on PriceLineHeading {\n          primary\n          __typename\n        }\n      }\n      __typename\n    }\n    enrichedValue {\n      ...PricePresentationLineItemEntryFragment\n      __typename\n    }\n    __typename\n  }\n  items {\n    ...PricePresentationLineItemFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PricePresentationLineItemFragment on PricePresentationLineItem {\n  enrichedValue {\n    ...PricePresentationLineItemEntryFragment\n    __typename\n  }\n  name {\n    ...PricePresentationLineItemEntryFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PricePresentationLineItemEntryFragment on PricePresentationLineItemEntry {\n  primaryMessage {\n    ...PriceLineElementFragment\n    __typename\n  }\n  secondaryMessages {\n    ...PriceLineElementFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PriceLineElementFragment on PricePresentationLineItemMessage {\n  __typename\n  ...PriceLineTextFragment\n  ...PriceLineHeadingFragment\n  ...InlinePriceLineTextFragment\n}\n\nfragment PriceLineTextFragment on PriceLineText {\n  __typename\n  theme\n  primary\n  weight\n  additionalInfo {\n    ...AdditionalInformationPopoverFragment\n    __typename\n  }\n  icon {\n    id\n    description\n    size\n    __typename\n  }\n  graphic {\n    ...UIGraphicFragment\n    __typename\n  }\n}\n\nfragment UIGraphicFragment on UIGraphic {\n  ... on Icon {\n    ...IconFragments\n    __typename\n  }\n  ... on Mark {\n    ...MarkFragments\n    __typename\n  }\n  ... on Illustration {\n    ...IllustrationFragments\n    __typename\n  }\n  __typename\n}\n\nfragment IconFragments on Icon {\n  description\n  id\n  size\n  theme\n  title\n  withBackground\n  __typename\n}\n\nfragment MarkFragments on Mark {\n  description\n  id\n  markSize: size\n  url {\n    ... on HttpURI {\n      __typename\n      relativePath\n      value\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment IllustrationFragments on Illustration {\n  description\n  id\n  link: url\n  __typename\n}\n\nfragment AdditionalInformationPopoverFragment on AdditionalInformationPopover {\n  icon {\n    id\n    description\n    size\n    __typename\n  }\n  enrichedSecondaries {\n    ...AdditionalInformationPopoverSectionFragment\n    __typename\n  }\n  analytics {\n    linkName\n    referrerId\n    __typename\n  }\n  __typename\n}\n\nfragment AdditionalInformationPopoverSectionFragment on AdditionalInformationPopoverSection {\n  __typename\n  ... on AdditionalInformationPopoverTextSection {\n    ...AdditionalInformationPopoverTextSectionFragment\n    __typename\n  }\n  ... on AdditionalInformationPopoverListSection {\n    ...AdditionalInformationPopoverListSectionFragment\n    __typename\n  }\n  ... on AdditionalInformationPopoverGridSection {\n    ...AdditionalInformationPopoverGridSectionFragment\n    __typename\n  }\n}\n\nfragment AdditionalInformationPopoverTextSectionFragment on AdditionalInformationPopoverTextSection {\n  __typename\n  text {\n    text\n    __typename\n  }\n}\n\nfragment AdditionalInformationPopoverListSectionFragment on AdditionalInformationPopoverListSection {\n  __typename\n  content {\n    __typename\n    items {\n      text\n      __typename\n    }\n  }\n}\n\nfragment AdditionalInformationPopoverGridSectionFragment on AdditionalInformationPopoverGridSection {\n  __typename\n  subSections {\n    header {\n      name {\n        primaryMessage {\n          ...AdditionalInformationPopoverGridLineItemMessageFragment\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    items {\n      name {\n        ...AdditionalInformationPopoverGridLineItemEntryFragment\n        __typename\n      }\n      enrichedValue {\n        ...AdditionalInformationPopoverGridLineItemEntryFragment\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment AdditionalInformationPopoverGridLineItemEntryFragment on PricePresentationLineItemEntry {\n  primaryMessage {\n    ...AdditionalInformationPopoverGridLineItemMessageFragment\n    __typename\n  }\n  secondaryMessages {\n    ...AdditionalInformationPopoverGridLineItemMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment AdditionalInformationPopoverGridLineItemMessageFragment on PricePresentationLineItemMessage {\n  ... on PriceLineText {\n    __typename\n    primary\n  }\n  ... on PriceLineHeading {\n    __typename\n    tag\n    size\n    primary\n  }\n  __typename\n}\n\nfragment PriceLineHeadingFragment on PriceLineHeading {\n  __typename\n  primary\n  tag\n  size\n  additionalInfo {\n    ...AdditionalInformationPopoverFragment\n    __typename\n  }\n  icon {\n    id\n    description\n    size\n    __typename\n  }\n}\n\nfragment InlinePriceLineTextFragment on InlinePriceLineText {\n  __typename\n  inlineItems {\n    ...PriceLineTextFragment\n    __typename\n  }\n}\n\nfragment PropertyStickyBookBarFragment on OfferDetails {\n  soldOut\n  stickyBar {\n    qualifier\n    subText\n    stickyButton {\n      text\n      targetRef\n      __typename\n    }\n    price {\n      formattedDisplayPrice\n      accessibilityLabel\n      priceDisclaimer {\n        content\n        primaryUIButton {\n          primary\n          __typename\n        }\n        trigger {\n          icon {\n            id\n            size\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    propertyPrice {\n      ...PriceSummaryFragment\n      __typename\n    }\n    structuredData {\n      itemprop\n      itemscope\n      itemtype\n      content\n      __typename\n    }\n    __typename\n  }\n  ...PropertySingleOfferDialogLinkFragment\n  __typename\n}\n\nfragment PropertyOffersFragment on OfferDetails {\n  ...ListingsHeaderFragment\n  ...AlternateDatesFragment\n  ...ListingsErrorMessageFragment\n  ...ListingsFragment\n  ...StickyBarDisclaimerFragment\n  ...ShoppingContextFragment\n  offerLevelMessages {\n    ...MessageResultFragment\n    __typename\n  }\n  ...PropertyFilterPillsFragment\n  ...PropertyOffersIncludedPerksFragment\n  __typename\n}\n\nfragment ListingsHeaderFragment on OfferDetails {\n  listingsHeader {\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment ListingsErrorMessageFragment on OfferDetails {\n  errorMessage {\n    ...ErrorMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment ListingsFragment on OfferDetails {\n  listings {\n    ...PropertyUnitFragment\n    __typename\n  }\n  categorizedListings {\n    ...PropertyUnitCategorizationFragment\n    ...VerticalMessagingCardFragment\n    ...LodgingSectionHeaderFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyUnitFragment on PropertyUnit {\n  __typename\n  ... on PropertyUnit {\n    id\n    header {\n      ...PropertyOffersHeaderFragment\n      __typename\n    }\n    features {\n      ...PropertyFeaturesFragment\n      __typename\n    }\n    unitGallery {\n      accessibilityLabel\n      images {\n        image {\n          description\n          url\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    ratePlans {\n      ...RatePlanWithAmenitiesFragment\n      __typename\n    }\n    ratePlansExpando {\n      ...RatePlansExpandoFragment\n      __typename\n    }\n    ...AvailabilityCtaFragment\n    roomAmenities {\n      ...RoomAmenitiesDescriptionFragment\n      __typename\n    }\n    detailsDialog {\n      ...PropertyOffersDetailsDialogFragment\n      toolbar {\n        clientSideAnalytics {\n          referrerId\n          linkName\n          __typename\n        }\n        __typename\n      }\n      trigger {\n        ...LinkTriggerFragment\n        clientSideAnalytics {\n          referrerId\n          linkName\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    spaceDetails {\n      ...SpaceDetailsFragment\n      __typename\n    }\n    ...SleepingArrangementsFragment\n    __typename\n  }\n}\n\nfragment PropertyOffersHeaderFragment on LodgingHeader {\n  text\n  subText\n  __typename\n}\n\nfragment PropertyFeaturesFragment on PropertyInfoItem {\n  text\n  graphic {\n    __typename\n    ... on Icon {\n      description\n      id\n      __typename\n    }\n    ... on Mark {\n      description\n      id\n      url {\n        value\n        __typename\n      }\n      __typename\n    }\n  }\n  moreInfoDialog {\n    ...LodgingPlainSheetFragment\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingPlainSheetFragment on LodgingPlainDialog {\n  __typename\n  content\n  trigger {\n    clientSideAnalytics {\n      linkName\n      referrerId\n      __typename\n    }\n    icon {\n      description\n      id\n      __typename\n    }\n    theme\n    value\n    __typename\n  }\n  toolbar {\n    title\n    icon {\n      description\n      __typename\n    }\n    clientSideAnalytics {\n      linkName\n      referrerId\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PropertyOffersRateViewScarcityFragment on Offer {\n  availability {\n    scarcityMessage\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyOffersDetailsDialogFragment on PropertyUnitDetailsDialog {\n  toolbar {\n    title\n    icon {\n      description\n      __typename\n    }\n    __typename\n  }\n  content {\n    ratePlanTitle {\n      text\n      __typename\n    }\n    dialogFeatures {\n      listItems {\n        text\n        icon {\n          id\n          description\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    details {\n      header {\n        text\n        subText\n        __typename\n      }\n      contents {\n        heading\n        items {\n          text\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment RatePlanWithAmenitiesFragment on RatePlan {\n  shareUrl {\n    accessibilityLabel\n    value\n    link {\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      uri {\n        relativePath\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  id\n  name\n  amenities {\n    ...RatePlanAmenitiesFragment\n    __typename\n  }\n  ...PropertyRatePlanBadgeFragment\n  paymentPolicy {\n    paymentType\n    heading\n    price {\n      ...PriceSummaryFragment\n      __typename\n    }\n    descriptions {\n      heading\n      header {\n        text\n        mark {\n          id\n          url {\n            value\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      items {\n        ...PropertyInfoMessageFragment\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  priceDetails {\n    optionTitle {\n      text\n      __typename\n    }\n    pointsApplied\n    ...PropertyOffersRateViewScarcityFragment\n    ...LodgingPriceSummaryFragment\n    ...PriceBreakdownSummaryFragment\n    ...PricePresentationDialogFragment\n    price {\n      ...PriceSummaryFragment\n      __typename\n    }\n    __typename\n  }\n  marketingSection {\n    ...MarketingSectionFragment\n    __typename\n  }\n  ...HighlightedMessagesFragment\n  ...PropertyOffersPriceChangeMessageFragment\n  ...PropertyReserveButtonFragment\n  loyaltyMessage {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PriceBreakdownSummaryFragment on Offer {\n  priceBreakDownSummary {\n    priceSummaryHeading {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    sections {\n      ...PriceSummarySectionFragment\n      __typename\n    }\n    disclaimers {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PriceSummarySectionFragment on PriceSummarySection {\n  sectionHeading {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  sectionFooter {\n    ...PriceSummaryFooterFragment\n    __typename\n  }\n  items {\n    ...PriceSummaryLineItemFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PriceSummaryLineItemFragment on PriceSummaryLineItem {\n  name {\n    primaryMessage {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    secondaryMessages {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    __typename\n  }\n  value {\n    primaryMessage {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    secondaryMessages {\n      ...LodgingEnrichedMessageFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PriceSummaryFooterFragment on PriceSummaryFooter {\n  footerMessages {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment RatePlanAmenitiesFragment on RatePlanAmenity {\n  icon {\n    id\n    description\n    size\n    __typename\n  }\n  description\n  additionalInformation\n  id\n  __typename\n}\n\nfragment LinkTriggerFragment on LodgingDialogTriggerMessage {\n  value\n  accessibilityLabel\n  __typename\n}\n\nfragment AvailabilityCtaFragment on PropertyUnit {\n  availabilityCallToAction {\n    ... on LodgingPlainMessage {\n      value\n      __typename\n    }\n    ... on LodgingButton {\n      text\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment RatePlansExpandoFragment on RatePlansExpando {\n  collapseButton {\n    text\n    __typename\n  }\n  expandButton {\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment SleepingArrangementsFragment on PropertyUnit {\n  spaceDetails {\n    ...SpaceDetailsHeaderFragment\n    ...SpaceDetailsSpacesFragment\n    ...SpaceDetailsFloorPlanFragment\n    __typename\n  }\n  __typename\n}\n\nfragment SpaceDetailsHeaderFragment on SpaceDetails {\n  header {\n    text\n    __typename\n  }\n  summary\n  __typename\n}\n\nfragment SpaceDetailsSpacesFragment on SpaceDetails {\n  spaces {\n    name\n    description\n    icons {\n      description\n      id\n      size\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment SpaceDetailsFloorPlanFragment on SpaceDetails {\n  floorPlan {\n    images {\n      alt\n      image {\n        description\n        url\n        __typename\n      }\n      subjectId\n      __typename\n    }\n    toolbar {\n      icon {\n        description\n        id\n        size\n        __typename\n      }\n      title\n      __typename\n    }\n    trigger {\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment RoomAmenitiesDescriptionFragment on PropertyContentSection {\n  header {\n    text\n    __typename\n  }\n  bodySubSections {\n    contents {\n      ...RoomAmenityContentFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment RoomAmenityContentFragment on PropertyContent {\n  header {\n    text\n    icon {\n      id\n      __typename\n    }\n    __typename\n  }\n  items {\n    ... on PropertyContentItemMarkup {\n      ...RoomAmenityContentTextFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment RoomAmenityContentTextFragment on PropertyContentItemMarkup {\n  content {\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment SpaceDetailsFragment on SpaceDetails {\n  ...SpaceDetailsHeaderFragment\n  ...SpaceDetailsSpacesFragment\n  ...SpaceDetailsFloorPlanFragment\n  virtualTourPrompt {\n    ...VirtualTourPromptFragment\n    __typename\n  }\n  __typename\n}\n\nfragment VirtualTourPromptFragment on VirtualTourPrompt {\n  heading {\n    text\n    __typename\n  }\n  button {\n    accessibility\n    primary\n    icon {\n      description\n      id\n      __typename\n    }\n    action {\n      resource {\n        value\n        __typename\n      }\n      accessibility\n      __typename\n    }\n    __typename\n  }\n  heroImage {\n    description\n    url\n    cameraMovement\n    __typename\n  }\n  caption {\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyUnitCategorizationFragment on LodgingCategorizedUnit {\n  __typename\n  header {\n    ...PropertyOffersHeaderFragment\n    __typename\n  }\n  features {\n    ...PropertyFeaturesFragment\n    __typename\n  }\n  highlightedMessages {\n    ...RatePlanMessageFragment\n    __typename\n  }\n  featureHeader {\n    text\n    __typename\n  }\n  ...IncludedPerksFragment\n  ...FooterActionsFragment\n  ...UnitCategorizationFragment\n}\n\nfragment RatePlanMessageFragment on RatePlanMessage {\n  ...LodgingPlainDialogFragment\n  ...LodgingEnrichedMessageFragment\n  ...LodgingPlainMessageFragment\n  __typename\n}\n\nfragment IncludedPerksFragment on LodgingCategorizedUnit {\n  includedPerks {\n    header {\n      text\n      __typename\n    }\n    items {\n      text\n      icon {\n        description\n        id\n        __typename\n      }\n      moreInfoDialog {\n        ...LodgingPlainDialogFragment\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment FooterActionsFragment on LodgingCategorizedUnit {\n  footerActions {\n    primary\n    analytics {\n      linkName\n      referrerId\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment UnitCategorizationFragment on LodgingCategorizedUnit {\n  primarySelections {\n    propertyUnit {\n      ...UnitCategorizationPropertyUnitFragment\n      __typename\n    }\n    primarySelection {\n      ...UnitCategorizationSelectionFragment\n      __typename\n    }\n    secondarySelections {\n      recommendedSelection\n      secondarySelection {\n        ...UnitCategorizationSelectionFragment\n        __typename\n      }\n      tertiarySelections {\n        ...UnitCategorizationSelectionFragment\n        dialog {\n          ...LodgingPlainFullscreenDialogFragment\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  primaryHeader {\n    ...SelectionHeaderFragment\n    __typename\n  }\n  secondaryHeader {\n    ...SelectionHeaderFragment\n    __typename\n  }\n  tertiaryHeader {\n    ...SelectionHeaderFragment\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingPlainFullscreenDialogFragment on LodgingPlainDialog {\n  __typename\n  content\n  trigger {\n    clientSideAnalytics {\n      linkName\n      referrerId\n      __typename\n    }\n    icon {\n      description\n      id\n      __typename\n    }\n    theme\n    value\n    __typename\n  }\n  toolbar {\n    title\n    icon {\n      description\n      __typename\n    }\n    clientSideAnalytics {\n      linkName\n      referrerId\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment SelectionHeaderFragment on LodgingOfferSelectionHeader {\n  title {\n    text\n    subText\n    accessibilityLabel\n    __typename\n  }\n  ...UnitCategorizationComplexDialogFragment\n  __typename\n}\n\nfragment UnitCategorizationComplexDialogFragment on LodgingOfferSelectionHeader {\n  dialog {\n    content {\n      content\n      title {\n        text\n        __typename\n      }\n      __typename\n    }\n    primaryUIButton {\n      ...UIPrimaryButtonFragment\n      __typename\n    }\n    toolbar {\n      title\n      icon {\n        description\n        __typename\n      }\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      __typename\n    }\n    trigger {\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      icon {\n        id\n        description\n        __typename\n      }\n      value\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment UnitCategorizationPropertyUnitFragment on PropertyUnit {\n  ...AvailabilityCtaFragment\n  detailsDialog {\n    ...PropertyOffersDetailsDialogFragment\n    toolbar {\n      clientSideAnalytics {\n        referrerId\n        linkName\n        __typename\n      }\n      __typename\n    }\n    trigger {\n      ...LinkTriggerFragment\n      clientSideAnalytics {\n        referrerId\n        linkName\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  id\n  ratePlans {\n    ...RatePlanWithAmenitiesFragment\n    ...UnitCategorizationRatePlanFragment\n    __typename\n  }\n  roomAmenities {\n    ...RoomAmenitiesDescriptionFragment\n    __typename\n  }\n  unitGallery {\n    accessibilityLabel\n    images {\n      image {\n        description\n        url\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  spaceDetails {\n    ...SpaceDetailsFragment\n    __typename\n  }\n  __typename\n}\n\nfragment UnitCategorizationRatePlanFragment on RatePlan {\n  shareUrl {\n    accessibilityLabel\n    value\n    link {\n      clientSideAnalytics {\n        linkName\n        referrerId\n        __typename\n      }\n      uri {\n        relativePath\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  id\n  loyaltyMessage {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  paymentPolicy {\n    paymentType\n    heading\n    descriptions {\n      heading\n      header {\n        text\n        mark {\n          id\n          url {\n            value\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      items {\n        text\n        icon {\n          id\n          token\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    price {\n      ...PriceSummaryFragment\n      __typename\n    }\n    __typename\n  }\n  priceDetails {\n    pointsApplied\n    ...PropertyOffersRateViewScarcityFragment\n    ...LodgingPriceSummaryFragment\n    ...PriceBreakdownSummaryFragment\n    ...PricePresentationDialogFragment\n    price {\n      ...PriceSummaryFragment\n      __typename\n    }\n    __typename\n  }\n  ...HighlightedMessagesFragment\n  ...PropertyOffersPriceChangeMessageFragment\n  ...PropertyRatePlanBadgeFragment\n  ...PropertyReserveButtonFragment\n  offerNotifications {\n    ...LodgingNotificationsCardFragment\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingNotificationsCardFragment on LodgingNotificationsCard {\n  header {\n    text\n    __typename\n  }\n  messages {\n    ...LodgingEnrichedMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment UnitCategorizationSelectionFragment on LodgingOfferOption {\n  clientSideAnalytics {\n    linkName\n    referrerId\n    __typename\n  }\n  description\n  enabled\n  optionId\n  price\n  subText\n  accessibilityLabel\n  liveAnnounceMessage\n  liveAnnouncePoliteness\n  selected\n  __typename\n}\n\nfragment VerticalMessagingCardFragment on MessageResult {\n  title {\n    text\n    __typename\n  }\n  subtitle {\n    text\n    __typename\n  }\n  featuredImage {\n    url\n    description\n    __typename\n  }\n  action {\n    primary {\n      text\n      referrerId\n      actionDetails {\n        action\n        accessibilityLabel\n        __typename\n      }\n      __typename\n    }\n    secondary {\n      text\n      referrerId\n      actionDetails {\n        action\n        accessibilityLabel\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingSectionHeaderFragment on LodgingHeader {\n  text\n  accessibilityLabel\n  impressionAnalytics {\n    event\n    referrerId\n    __typename\n  }\n  __typename\n}\n\nfragment StickyBarDisclaimerFragment on OfferDetails {\n  stickyBar {\n    price {\n      disclaimer {\n        value\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment ShoppingContextFragment on OfferDetails {\n  shoppingContext {\n    multiItem {\n      id\n      packageType\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyFilterPillsFragment on OfferDetails {\n  id\n  offerFilters {\n    heading {\n      text\n      __typename\n    }\n    accessibilityHeader\n    liveAnnounce\n    filterPills {\n      ...LodgingEGDSBasicPillFragment\n      ...LodgingFilterDialogPillFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingEGDSBasicPillFragment on EGDSBasicPill {\n  primary\n  accessibility\n  selected\n  name\n  value\n  __typename\n}\n\nfragment LodgingFilterDialogPillFragment on LodgingFilterDialogPill {\n  triggerPill {\n    primary\n    selected\n    __typename\n  }\n  filterDialog {\n    ...FilterDialogPillFragment\n    __typename\n  }\n  __typename\n}\n\nfragment FilterDialogPillFragment on LodgingFilterSelectionDialog {\n  dialog {\n    footer {\n      buttons {\n        primary\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  clearAll {\n    primary\n    __typename\n  }\n  filterSection {\n    primary\n    ... on ShoppingMultiSelectionField {\n      id\n      primary\n      options {\n        id\n        primary\n        value\n        selected\n        disabled\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  toolbar {\n    title\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyOffersIncludedPerksFragment on OfferDetails {\n  includedPerks {\n    header {\n      text\n      __typename\n    }\n    items {\n      graphic {\n        ... on Icon {\n          description\n          id\n          __typename\n        }\n        __typename\n      }\n      moreInfoDialog {\n        ...LodgingPlainFullscreenDialogFragment\n        __typename\n      }\n      text\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertySpaceDetailsFragment on OfferDetails {\n  spaceDetails {\n    ...SpaceDetailsHeaderFragment\n    ...SpaceDetailsSpacesFragment\n    ...SpaceDetailsFloorPlanFragment\n    virtualTourPrompt {\n      ...VirtualTourPromptFragment\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment PropertySearchLinkFragment on OfferDetails {\n  propertySearchLink {\n    ...LodgingLinkMessageFragment\n    __typename\n  }\n  partnerPropertySearchLink {\n    ...LodgingLinkMessageFragment\n    __typename\n  }\n  __typename\n}\n\nfragment LodgingLinkMessageFragment on LodgingLinkMessage {\n  icon {\n    id\n    __typename\n  }\n  link {\n    clientSideAnalytics {\n      referrerId\n      linkName\n      __typename\n    }\n    uri {\n      relativePath\n      value\n      __typename\n    }\n    referrerId\n    __typename\n  }\n  value\n  __typename\n}\n\nfragment PropertyUnitListViewFragment on OfferDetails {\n  categorizedListings {\n    ...PropertyUnitListViewElementFragment\n    __typename\n  }\n  __typename\n}\n\nfragment PropertyUnitListViewElementFragment on LodgingCategorizedUnit {\n  header {\n    text\n    __typename\n  }\n  __typename\n}\n\nfragment FilterPillsFragment on OfferDetails {\n  filterPills {\n    pillLabel\n    query\n    type\n    value\n    __typename\n  }\n  __typename\n}\n\nfragment LoyaltyDiscountToggleFragment on OfferDetails {\n  loyaltyDiscount {\n    saveWithPointsMessage\n    saveWithPointsActionMessage\n    __typename\n  }\n  __typename\n}\n\nfragment LegalDisclaimerFragment on OfferDetails {\n  legalDisclaimer {\n    content {\n      markupType\n      text\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment HighlightedBenefitsFragment on OfferDetails {\n  highlightedBenefits {\n    listItems {\n      icon {\n        id\n        __typename\n      }\n      impressionAnalytics {\n        referrerId\n        __typename\n      }\n      text\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"
            }
        ]

        headers2 = {
            'Accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6',
            'client-info': 'shopping-pwa,879ef38bdfb196f682493cb47d3f19dad7d5b5b6,us-west-2',
            'content-type': 'application/json',
            'origin': 'https://kr.hotels.com',
            'referer': 'https://kr.hotels.com/ho421229/hotelpole-busan-yeog-busan-hangug/?chkin={}&chkout={}&x_pwa=1&rfrr=HSR&pwa_ts=1670808070231&referrerUrl=aHR0cHM6Ly9rci5ob3RlbHMuY29tL0hvdGVsLVNlYXJjaA%3D%3D&useRewards=false&rm1=a2&regionId=602043&destination=%EB%B6%80%EC%82%B0%2C+%ED%95%9C%EA%B5%AD&destType=MARKET&neighborhoodId=6336003&selected={}&sort=RECOMMENDED&top_dp=72727&top_cur=KRW&userIntent=&selectedRoomType=200805011&selectedRatePlan=204023228&expediaPropertyId={}'.format(checkin, checkout, hotel_propery_id, hotel_propery_id),
            'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'x-page-id': 'page.Hotels.Infosite.Information,H,30',
        }

        try:
            response = self.requests_post(requests, 'https://kr.hotels.com/graphql', json=json_params, headers=headers2, **args['proxy']['REQUESTS_PROXY']).json()
        except ExceptionReadTimeout as e:
            return dict(code=403, rooms=[])

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

                    #print()
                    #print('#######', room_name)

                    for primary_section in categorized_listings['primarySelections']:
                        room_id = primary_section['propertyUnit']['id']

                        for rateplan in primary_section['propertyUnit']['ratePlans']:
                            if 'priceDetails' not in rateplan:
                                continue

                            for price_detail in rateplan['priceDetails']:
                                # print(price_detail['price']['lead']['formatted'])

                                if price_detail['pricePresentation'] is not None:
                                    for section in price_detail['pricePresentation']['sections']:
                                        if section.get('header') is None:
                                            continue
                                        if section['header'].get('enrichedValue') is None:
                                            continue
                                        if section['header']['enrichedValue'].get('primaryMessage') is None:
                                            continue
                                        if section['header']['enrichedValue']['primaryMessage'].get('primary') is None:
                                            continue
                                        
                                        whole_price = min(whole_price, replace_price(section['header']['enrichedValue']['primaryMessage']['primary']))

                                elif price_detail['price']['displayMessages']:
                                    for display_messages in price_detail['price']['displayMessages']:
                                        for line_items in display_messages['lineItems']:
                                            if 'state' not in line_items:
                                                continue
                                            if line_items['state'] == 'BREAKOUT_TYPE_SECONDARY_PRICE':
                                                price_text = line_items['value']
                                                number = re.findall('\d+', price_text)
                                                whole_price = min(whole_price, int(''.join(number)))

                    if whole_price < 1e10:
                        price = whole_price
                    elif price_without_tax < 1e10:
                        price = price_without_tax

                    if price is None:
                        continue
                    
                    #print('@@@', price)
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

        kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        kst2 = kst + datetime.timedelta(days=1)

        size = 100
        startIndex = (page - 1) * size

        checkin = kst.strftime('%Y-%m-%d')
        checkout = kst2.strftime('%Y-%m-%d')
        try:
            result = self.requests_get(requests, 'https://kr.hotels.com/ho{}/?pa=1&q-check-out={}&tab=description&q-room-0-adults=2&YGF=7&q-check-in={}&MGT=1&WOE=5&WOD=4&ZSX=0&SYE=3&q-room-0-children=0'.format(hotel_id, checkout, checkin), **args['proxy']['REQUESTS_PROXY']).text
        except ExceptionReadTimeout:
            return dict(code=403, rooms=[])
        
        rooms = []
        m = pattern_hotel_url.search(result)
        if not m:
            return dict(code=504, rooms=[])
 
        hotel_propery_id = json.loads(m.group(1))

        headers = {
            'x-page-id': 'page.Hotels.Infosite.Information,H,30',
            'client-info': 'shopping-pwa,06e60a6b7371b560f358d838f5d6aadaa09a953b,us-west-2',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
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
                    "propertyId": "{}".format(hotel_propery_id),
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
            resp = self.requests_post(requests, 'https://kr.hotels.com/graphql', json=params, headers=headers).json()
        except ExceptionReadTimeout:
            return dict(code=403, comments=[])

        result = []
        for resp_item in resp:
            print('##', resp_item)
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
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
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
            
        except Exception:
            print(traceback.print_exc())
            pass
        print('####', len(result))
        
        return dict(code=200, comments=result, score=score, count=count)
