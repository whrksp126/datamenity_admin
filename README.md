# datamenity-admin
데이터메니티 어드민


## Prerequisite
sudo apt-get install python-dev libmysqlclient-dev  python3-dev build-essential python3-virtualenv xvfb 

sudo apt-get install libpq-dev (postgres 때문)

sudo apt-get install google-chrome-stable

virtualenv .venv -ppython3


## OTA 추가시, Enum  타입 수정
ALTER TABLE room CHANGE ota_type ota_type enum('GOODCHOICE','BOOKING','EXPEDIA','AGODA','INTERPARK','YANOLJA','DAILY', 'HOTELS', 'TRIP', 'WINGS', 'KENSINGTON', 'IKYU', 'RAKUTEN', 'JALAN') NOT NULL;


## AWS 설정 필요 -> Elastic IP 교체를 위함
sudo apt install awscli
aws configure
key-id : 입력
accesskey : 입력
region : ap-northeast-2
format : json
