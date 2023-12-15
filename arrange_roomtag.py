from datamenity import arrange_room_tag
from datetime import datetime, timedelta

kst_now = datetime.utcnow() + timedelta(hours=9)
today = kst_now.replace(second=0, minute=0, hour=0, microsecond=0)
yesterday = today - timedelta(days=1)
arrange_room_tag(yesterday, today)