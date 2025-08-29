# 프로그램 설명
크몽에 등록된 사업자들의 카테고리 종류 및 수익구조를 분석하여, 사용자가 앞으로 어떤 방향으로 개발을 준비해야 할지 판단할 데이터를 수집/처리

# 0. 폴더 구조
kmong_profile_crawler/
├── src/
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── base_crawler.py
│   │   ├── profile_crawler.py
│   │   └── data_extractor.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── processor.py
│   │   └── analyzer.py
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       └── helpers.py
├── output/
├── logs/
├── requirements.txt
└── main.py

# 1. 데이터 수집
## 1. 검색 패턴 분석
1. IT·프로그래밍 영역에서 관심 분야인 프로그램 --> 완성형 프로그램 스토어, 업무 자동화, 크롤링·스크래핑, 일반 프로그램 카테고리의 서비스를 수집
완성형 프로그램 스토어 : https://kmong.com/category/661
업무 자동화 : https://kmong.com/category/663
크롤링·스크래핑 : https://kmong.com/category/645
일반 프로그램 : https://kmong.com/category/605

페이지 : https://kmong.com/category/645?page=2

해당 페이지의 서비스 갯수 : //*[@id="__next"]/div/div/div/div/main/div/div[2]/p

while 반복 돌리다가 서비스 갯수가 0개로 뜨면 멈춤

2. 각 서비스의 전문가 이름(ID)를 수집하고, 고유값 추출
박스 : //*[@id="__next"]/div/div/div/div/main/div/div[3]/div[1]
개별 박스 : /article[i]
개별 박스 내 아이디 위치 : /a/div[2]/div[n]/span
** div[n] 부분이 문제. 리뷰가 있으면 3, 아니면 4임. 3으로 검색해서 "원"이 있으면 4를 찾는걸로 하면 될듯.

찾고 나면 해당 개발자 주소는 https://kmong.com/@[아이디] 형식으로 들어가면 됨

3. 프로필 들어가서 정보 수집

자기소개 : //*[@class="ProfileDescriptionSection__desctiption"]

경력 관련 섹션 : //*[@class="DescriptionDetailSection"]
제목 : /[@class="ProfileSectionTitle"]
내용 : /[@class="ProfileSkillSection__tag"]
