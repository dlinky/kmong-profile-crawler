# 크몽 크롤러 프로젝트

크몽(Kmong) 플랫폼에서 판매자 프로필, 리뷰, 서비스 정보를 자동으로 수집하는 웹 크롤링 도구입니다.

## 📋 목차
- [전체 아키텍처](#전체-아키텍처)
- [클래스별 역할](#클래스별-역할)
- [설치 및 설정](#설치-및-설정)
- [데이터 수집 플로우](#데이터-수집-플로우)
- [기능별 사용법](#기능별-사용법)
- [문제 해결 가이드](#문제-해결-가이드)
- [알려진 이슈](#알려진-이슈)

## 🏗️ 전체 아키텍처

```
크몽 크롤러
├── BaseCrawler (기본 클래스)
│   ├── Selenium WebDriver 설정
│   ├── 데이터 저장 기능
│   └── 브라우저 관리
│
├── SellersCrawler (판매자 수집)
│   ├── 카테고리별 판매자 목록 크롤링
│   └── 페이지네이션 처리
│
└── ProfileCrawler (상세 정보 수집)
    ├── 판매자 프로필 정보
    ├── 리뷰 데이터 수집
    └── 서비스별 상세 정보
```

### 데이터 흐름
1. **카테고리 탐색** → 판매자 목록 수집
2. **판매자 프로필** → 상세 정보 추출
3. **리뷰 섹션** → 고객 리뷰 데이터
4. **서비스 페이지** → 가격, 패키지 정보

## 📦 클래스별 역할

### BaseCrawler
**역할**: 모든 크롤러의 기본 기능을 제공하는 부모 클래스

**주요 메서드**:
- `_setup_driver()`: Chrome WebDriver 초기화 및 옵션 설정
- `save_data(data, filename)`: 수집된 데이터를 CSV 파일로 저장
- `close()`: 브라우저 세션 종료

**핵심 설정**:
```python
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
```

### SellersCrawler
**역할**: 카테고리별 판매자 목록을 수집하는 클래스

**주요 메서드**:
- `crawl_category_sellers(category_id)`: 특정 카테고리의 모든 판매자 수집
- `crawl_multiple_categories(category_ids)`: 여러 카테고리 일괄 처리
- `_extract_sellers_from_page()`: 페이지별 판매자 정보 추출

**수집 데이터**:
- 판매자 이름
- 카테고리 ID
- 서비스 인덱스

### ProfileCrawler
**역할**: 판매자의 상세 프로필, 리뷰, 서비스 정보를 수집하는 클래스

**주요 메서드**:

#### 프로필 정보 수집
- `crawl_seller_profile(seller_name)`: 기본 프로필 정보 수집
- `_extract_introduction()`: 자기소개 추출
- `_extract_career()`: 경력사항 추출
- `_extract_skills()`: 보유 기술 추출
- `_extract_specialties()`: IT·프로그래밍 전문분야 추출

#### 리뷰 수집
- `crawl_reviews(seller_name, max_pages)`: 리뷰 데이터 수집
- `_extract_reviews_from_page()`: 페이지별 리뷰 추출
- `_go_to_next_review_page()`: 리뷰 페이지네이션

#### 서비스 정보 수집 (현재 이슈 있음)
- `crawl_services(seller_name)`: 판매자의 서비스 목록 수집
- `crawl_single_service(service_url)`: 개별 서비스 상세 정보
- `_extract_package_prices()`: 패키지별 가격 정보
- `_extract_skill_level()`: 기술 수준 정보
- `_extract_team_size()`: 팀 규모 정보

#### 통합 기능
- `crawl_seller_profile_complete()`: 프로필 + 리뷰 + 서비스 전체 수집

## 🚀 설치 및 설정

### 필수 요구사항
```bash
pip install selenium pandas
```

### Chrome WebDriver 설정
1. Chrome 브라우저 설치
2. ChromeDriver 다운로드 및 PATH 설정
3. 또는 `webdriver-manager` 사용:
```bash
pip install webdriver-manager
```

### 디렉토리 구조
```
project/
├── crawler.py
├── output/           # CSV 출력 파일들
├── requirements.txt
└── README.md
```

## 📊 데이터 수집 플로우

### 1. 판매자 목록 수집
```
카테고리 페이지 접근 → 서비스 카드 탐지 → 판매자명 추출 → 페이지네이션 → CSV 저장
```

### 2. 프로필 정보 수집
```
프로필 URL 생성 → 섹션별 정보 추출 → 구조화된 데이터 변환 → 저장
```

### 3. 리뷰 데이터 수집
```
프로필 페이지 → 리뷰 섹션 스크롤 → 페이지별 리뷰 추출 → 다음 페이지 이동 → 저장
```

### 4. 서비스 정보 수집 (현재 이슈)
```
서비스 탭 클릭 → 서비스 URL 목록 → 개별 서비스 페이지 → 패키지/가격 추출 → 저장
```

## 💻 기능별 사용법

### 기본 사용법

#### 1. 카테고리별 판매자 수집
```python
from crawler import SellersCrawler

# 크롤러 초기화
sellers_crawler = SellersCrawler()

# 단일 카테고리 크롤링
category_id = 661  # IT·프로그래밍
sellers = sellers_crawler.crawl_category_sellers(category_id)

# 여러 카테고리 크롤링
category_ids = [661, 662, 663]
all_sellers = sellers_crawler.crawl_multiple_categories(category_ids)

# 종료
sellers_crawler.close()
```

#### 2. 프로필 정보 수집
```python
from crawler import ProfileCrawler

# 크롤러 초기화
profile_crawler = ProfileCrawler()

# 단일 프로필 크롤링
profile_data = profile_crawler.crawl_seller_profile("seller_username")

# CSV에서 판매자 목록 읽어서 크롤링
profiles = profile_crawler.crawl_from_csv('output/category_661_sellers.csv', limit=10)

# 종료
profile_crawler.close()
```

#### 3. 리뷰 포함 크롤링
```python
# 프로필 + 리뷰 통합 수집
profile_with_reviews = profile_crawler.crawl_seller_profile_with_reviews(
    seller_name="seller_username", 
    max_review_pages=5
)

# 여러 판매자 리뷰 포함 크롤링
seller_names = ["seller1", "seller2", "seller3"]
all_data = profile_crawler.crawl_multiple_profiles_with_reviews(
    seller_names, 
    max_review_pages=3
)
```

#### 4. 전체 데이터 수집
```python
# 프로필 + 리뷰 + 서비스 통합 수집
complete_data = profile_crawler.crawl_seller_profile_complete(
    seller_name="seller_username",
    max_review_pages=2
)
```

### 고급 사용법

#### 배치 처리 예제
```python
def crawl_category_batch(category_id, max_profiles=50):
    """카테고리 전체 배치 처리"""
    
    # 1단계: 판매자 목록 수집
    sellers_crawler = SellersCrawler()
    sellers = sellers_crawler.crawl_category_sellers(category_id)
    sellers_crawler.close()
    
    # 2단계: 프로필 상세 정보 수집
    profile_crawler = ProfileCrawler()
    seller_names = [s['seller_name'] for s in sellers[:max_profiles]]
    
    profiles = profile_crawler.crawl_multiple_profiles_with_reviews(
        seller_names, 
        max_review_pages=2
    )
    profile_crawler.close()
    
    return profiles
```

## 🔧 수집되는 데이터 구조

### 판매자 기본 정보
```json
{
    "seller_name": "판매자명",
    "profile_url": "https://kmong.com/@seller_name",
    "introduction": "자기소개 텍스트",
    "career": ["경력1", "경력2"],
    "specialties": ["IT·프로그래밍", "세부분야1", "세부분야2"],
    "skills": ["기술1", "기술2"]
}
```

### 리뷰 데이터
```json
{
    "reviews": [
        {
            "review_date": "작성일자",
            "service_title": "서비스명",
            "work_period": "작업기간",
            "order_amount": "주문금액"
        }
    ],
    "total_reviews": 10
}
```

### 서비스 정보 (현재 이슈)
```json
{
    "services": [
        {
            "service_url": "서비스 URL",
            "packages": {
                "STANDARD": "기본 가격",
                "DELUXE": "디럭스 가격", 
                "PREMIUM": "프리미엄 가격"
            },
            "skill_level": "숙련도",
            "team_size": "팀 규모"
        }
    ],
    "total_services": 5
}
```

## 🛠️ 문제 해결 가이드

### 일반적인 문제들

#### 1. WebDriver 관련 오류
**증상**: `selenium.common.exceptions.WebDriverException`
**해결책**:
```bash
# ChromeDriver 업데이트
pip install --upgrade selenium
# 또는 webdriver-manager 사용
pip install webdriver-manager
```

#### 2. 요소를 찾을 수 없는 오류
**증상**: `NoSuchElementException`
**해결책**:
- `time.sleep()` 시간 증가
- `WebDriverWait` 사용
- XPath 선택자 재검토

#### 3. 페이지네이션 실패
**증상**: 무한 루프 또는 페이지 이동 실패
**해결책**:
- `max_attempts` 제한 설정 확인
- JavaScript 클릭 사용: `driver.execute_script("arguments[0].click();", element)`

### 서비스 수집 기능 이슈 해결

#### 현재 문제점
서비스별 정보 수집 기능에서 다음과 같은 문제들이 발생하고 있습니다:

1. **패키지 가격 추출 실패**
   - 동적 로딩으로 인한 요소 접근 어려움
   - 패키지 버튼 클릭 후 가격 정보 로딩 지연

2. **서비스 목록 URL 수집 불안정**
   - 서비스 탭 활성화 문제
   - 중복 URL 필터링 이슈

#### 권장 해결 방안

##### 1. 대기 시간 증가
```python
def _extract_package_prices(self):
    # 기존: time.sleep(2)
    time.sleep(5)  # 증가
    
    # WebDriverWait 활용
    WebDriverWait(self.driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "price-class"))
    )
```

##### 2. 더 안정적인 선택자 사용
```python
def _find_price_with_multiple_selectors(self):
    # 현재 여러 선택자를 시도하지만, 더 추가 필요
    price_selectors = [
        # 기존 선택자들...
        "//span[contains(@class, 'price') and contains(text(), '원')]",
        "//*[@data-testid='price-display']",
        "//div[contains(@class, 'package-price')]//span"
    ]
    
    for selector in price_selectors:
        try:
            element = self.driver.find_element(By.XPATH, selector)
            if element.text.strip():
                return element.text.strip()
        except:
            continue
    return ""
```

##### 3. 서비스 탭 활성화 개선
```python
def crawl_services(self, seller_name):
    try:
        self.driver.get(f"https://kmong.com/@{seller_name}")
        time.sleep(3)
        
        # 더 안정적인 탭 선택
        service_tabs = [
            "//button[contains(text(), '서비스')]",
            "//button[contains(text(), '포트폴리오')]", 
            "//a[contains(@href, 'portfolio')]",
            "//*[@role='tab' and contains(text(), '서비스')]"
        ]
        
        tab_clicked = False
        for tab_selector in service_tabs:
            try:
                tab = self.driver.find_element(By.XPATH, tab_selector)
                self.driver.execute_script("arguments[0].click();", tab)
                time.sleep(3)
                tab_clicked = True
                break
            except:
                continue
        
        if not tab_clicked:
            print("서비스 탭을 찾을 수 없음")
            
    except Exception as e:
        print(f"서비스 크롤링 실패: {e}")
```

##### 4. 동적 콘텐츠 대응
```python
def _wait_for_dynamic_content(self, selector, timeout=10):
    """동적 콘텐츠 로딩 대기"""
    try:
        WebDriverWait(self.driver, timeout).until(
            lambda driver: len(driver.find_elements(By.XPATH, selector)) > 0
        )
        return True
    except:
        return False
```

## 🎯 기능별 사용법

### 1. 기본 크롤링 워크플로우

```python
# 전체 워크플로우 예제
def main_workflow():
    # Step 1: 카테고리별 판매자 수집
    sellers_crawler = SellersCrawler()
    sellers = sellers_crawler.crawl_category_sellers(661)  # IT·프로그래밍
    sellers_crawler.close()
    
    # Step 2: 상위 N명 프로필 상세 수집
    profile_crawler = ProfileCrawler()
    top_sellers = [s['seller_name'] for s in sellers[:20]]
    
    profiles = profile_crawler.crawl_multiple_profiles_with_reviews(
        top_sellers, 
        max_review_pages=3
    )
    
    # Step 3: 서비스 정보 수집 (선택적)
    for seller_name in top_sellers[:5]:  # 소수만 테스트
        try:
            services = profile_crawler.crawl_services(seller_name)
            print(f"{seller_name}: {len(services)}개 서비스")
        except Exception as e:
            print(f"{seller_name} 서비스 수집 실패: {e}")
    
    profile_crawler.close()

if __name__ == "__main__":
    main_workflow()
```

### 2. CSV 기반 배치 처리

```python
# CSV에서 판매자 목록을 읽어와서 프로필 수집
def batch_from_csv(csv_path, limit=None):
    profile_crawler = ProfileCrawler()
    
    try:
        profiles = profile_crawler.crawl_from_csv(csv_path, limit=limit)
        print(f"총 {len(profiles)}명의 프로필 수집 완료")
        return profiles
    finally:
        profile_crawler.close()

# 사용 예
profiles = batch_from_csv('output/category_661_sellers.csv', limit=10)
```

### 3. 에러 복구 및 재시도

```python
def robust_crawl_with_retry(seller_names, max_retries=3):
    """재시도 로직이 포함된 안정적인 크롤링"""
    profile_crawler = ProfileCrawler()
    successful_profiles = []
    failed_sellers = []
    
    for seller_name in seller_names:
        retries = 0
        success = False
        
        while retries < max_retries and not success:
            try:
                profile = profile_crawler.crawl_seller_profile(seller_name)
                if profile and 'error' not in profile:
                    successful_profiles.append(profile)
                    success = True
                else:
                    retries += 1
                    time.sleep(5)  # 재시도 전 대기
                    
            except Exception as e:
                print(f"{seller_name} 시도 {retries + 1} 실패: {e}")
                retries += 1
                time.sleep(5)
        
        if not success:
            failed_sellers.append(seller_name)
    
    profile_crawler.close()
    return successful_profiles, failed_sellers
```

## ⚠️ 알려진 이슈

### 🔴 서비스 정보 수집 기능 문제

**현재 상태**: 부분적으로 작동하지 않음

**주요 이슈들**:

1. **패키지 가격 추출 실패**
   - 동적 로딩으로 인한 지연
   - 패키지 버튼 클릭 후 DOM 업데이트 대기 시간 부족
   - 가격 표시 요소의 XPath 변경

2. **서비스 탭 활성화 문제**
   - 일부 프로필에서 서비스 탭 클릭 실패
   - 탭 전환 후 콘텐츠 로딩 지연

3. **서비스 URL 수집 불안정**
   - 중복 URL 필터링 로직 개선 필요
   - href 속성 추출 시 상대/절대 경로 처리

**임시 해결책**:
- 서비스 정보 수집은 소량(5개 이하)으로 제한하여 테스트
- 대기 시간을 2배로 증가 (`time.sleep(5)`)
- 수동으로 서비스 URL을 미리 수집 후 개별 처리

### 🟡 기타 알려진 제한사항

1. **속도 제한**
   - 크몽 서버의 요청 제한으로 인한 지연 필요
   - 권장: 요청 간 2-3초 대기

2. **메모리 사용량**
   - 대량 데이터 수집 시 메모리 부족 가능
   - 권장: 배치 단위로 중간 저장

3. **브라우저 안정성**
   - 장시간 실행 시 브라우저 크래시 가능
   - 권장: 50-100개 프로필마다 브라우저 재시작

## 🔧 디버깅 및 모니터링

### 로그 출력 해석
```python
# 정상적인 로그 패턴
"카테고리 661, 페이지 1 크롤링 중..."
"현재 페이지에서 20개 서비스 발견"
"페이지 1에서 15명 수집"
"프로필 크롤링 완료: seller_name"

# 문제 상황 로그
"서비스 개수: 0개의 서비스"  # 카테고리 끝
"서비스 카드 찾기 실패"      # DOM 구조 변경
"가격을 찾을 수 없음"       # 서비스 정보 수집 실패
```

### 성능 모니터링
```python
import time

def timed_crawl(func, *args, **kwargs):
    """실행 시간 측정"""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    print(f"실행 시간: {end_time - start_time:.2f}초")
    return result

# 사용 예
profiles = timed_crawl(
    profile_crawler.crawl_multiple_profiles, 
    seller_names
)
```

## 📈 최적화 권장사항

### 1. 효율적인 데이터 수집 전략
```python
# 단계적 수집 접근법
def staged_collection():
    # 1단계: 판매자 목록만 빠르게 수집
    collect_seller_lists()
    
    # 2단계: 상위 판매자 프로필 우선 수집
    collect_top_profiles()
    
    # 3단계: 리뷰 데이터 수집
    collect_reviews_data()
    
    # 4단계: 서비스 정보 (문제 해결 후)
    # collect_service_details()
```

### 2. 메모리 관리
```python
# 대용량 데이터 처리 시
def memory_efficient_crawl(seller_names, batch_size=10):
    profile_crawler = ProfileCrawler()
    
    for i in range(0, len(seller_names), batch_size):
        batch = seller_names[i:i+batch_size]
        profiles = profile_crawler.crawl_multiple_profiles(batch)
        
        # 즉시 저장하고 메모리 해제
        profile_crawler.save_data(profiles, f'batch_{i//batch_size + 1}')
        del profiles  # 명시적 메모리 해제
    
    profile_crawler.close()
```

### 3. 오류 복구 전략
```python
def resilient_crawl(seller_names):
    profile_crawler = ProfileCrawler()
    results = []
    errors = []
    
    for seller_name in seller_names:
        try:
            profile = profile_crawler.crawl_seller_profile(seller_name)
            results.append(profile)
            
        except Exception as e:
            error_info = {
                'seller_name': seller_name,
                'error': str(e),
                'timestamp': time.time()
            }
            errors.append(error_info)
            
            # 오류 발생 시 브라우저 재시작
            try:
                profile_crawler.close()
                profile_crawler = ProfileCrawler()
            except:
                pass
    
    # 오류 로그 저장
    if errors:
        profile_crawler.save_data(errors, 'crawl_errors')
    
    profile_crawler.close()
    return results, errors
```

## 📝 개발 우선순위

### 즉시 해결 필요 (High Priority)
1. **서비스 정보 수집 기능 수정**
   - 패키지 가격 추출 로직 개선
   - 동적 콘텐츠 로딩 대기 시간 조정
   - 서비스 탭 활성화 안정성 향상

### 중기 개선 사항 (Medium Priority)
1. **에러 처리 강화**
   - 자동 재시도 메커니즘
   - 상세한 오류 로깅
   - 부분 실패 시 복구 로직

2. **성능 최적화**
   - 병렬 처리 도입
   - 불필요한 대기 시간 최적화
   - 메모리 사용량 개선

### 장기 목표 (Low Priority)
1. **모니터링 대시보드**
2. **설정 파일 기반 관리**
3. **API 인터페이스 추가**

## 🔍 사용 시 주의사항

1. **요청 제한 준수**: 크몽 서버에 과도한 부하를 주지 않도록 적절한 지연 시간 유지
2. **로봇 감지 회피**: User-Agent 설정 및 자연스러운 브라우징 패턴 유지
3. **데이터 백업**: 장시간 크롤링 시 중간 저장 필수
4. **법적 준수**: 크몽 이용약관 및 robots.txt 준수

## 📊 출력 파일 구조

### 생성되는 CSV 파일들

```
output/
├── category_{id}_sellers.csv          # 카테고리별 판매자 목록
├── profiles_batch_{n}.csv             # 프로필 배치별 저장
├── profiles_with_reviews_batch_{n}.csv # 리뷰 포함 프로필
├── all_profiles.csv                   # 전체 프로필 통합
└── crawl_errors.csv                   # 오류 로그
```

### CSV 파일 필드 설명

#### category_{id}_sellers.csv
| 필드 | 설명 | 예시 |
|------|------|------|
| seller_name | 판매자 사용자명 | "developer123" |
| service_index | 페이지 내 서비스 순서 | 1, 2, 3... |
| category_id | 카테고리 ID | 661 |

#### all_profiles.csv  
| 필드 | 설명 | 타입 |
|------|------|------|
| seller_name | 판매자명 | String |
| profile_url | 프로필 URL | String |
| introduction | 자기소개 | String |
| career | 경력사항 | List |
| specialties | IT 전문분야 | List |
| skills | 보유 기술 | List |
| reviews | 리뷰 데이터 | List |
| total_reviews | 총 리뷰 수 | Integer |
| services | 서비스 정보 | List |
| total_services | 총 서비스 수 | Integer |

## ⚙️ 설정 및 커스터마이징

### 환경 변수 설정
```python
# crawler_config.py
class CrawlerConfig:
    # 기본 대기 시간 (초)
    DEFAULT_WAIT = 3
    LONG_WAIT = 5
    
    # 페이지 제한
    MAX_PAGES_PER_CATEGORY = 100
    MAX_REVIEW_PAGES = 5
    
    # 배치 크기
    BATCH_SIZE = 10
    
    # 재시도 설정
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    
    # 출력 설정
    OUTPUT_DIR = 'output'
    ENCODING = 'utf-8-sig'
```

### 커스텀 크롤러 생성
```python
class CustomProfileCrawler(ProfileCrawler):
    def __init__(self, config=None):
        super().__init__()
        self.config = config or CrawlerConfig()
    
    def crawl_with_custom_fields(self, seller_name):
        """사용자 정의 필드 추가 크롤링"""
        profile_data = self.crawl_seller_profile(seller_name)
        
        # 추가 필드 수집
        profile_data.update({
            'response_time': self._extract_response_time(),
            'completion_rate': self._extract_completion_rate(),
            'rating_score': self._extract_rating_score()
        })
        
        return profile_data
```

## 🧪 테스트 및 검증

### 단위 테스트 예제
```python
import unittest
from crawler import SellersCrawler, ProfileCrawler

class TestCrawlerFunctions(unittest.TestCase):
    
    def setUp(self):
        self.sellers_crawler = SellersCrawler()
        self.profile_crawler = ProfileCrawler()
    
    def test_driver_setup(self):
        """WebDriver 정상 초기화 테스트"""
        self.assertIsNotNone(self.sellers_crawler.driver)
        self.assertEqual(self.sellers_crawler.driver.name, 'chrome')
    
    def test_single_profile_crawl(self):
        """단일 프로필 크롤링 테스트"""
        test_seller = "test_seller_name"
        profile = self.profile_crawler.crawl_seller_profile(test_seller)
        
        self.assertIn('seller_name', profile)
        self.assertEqual(profile['seller_name'], test_seller)
    
    def tearDown(self):
        self.sellers_crawler.close()
        self.profile_crawler.close()

# 실행
if __name__ == '__main__':
    unittest.main()
```

### 데이터 검증 스크립트
```python
def validate_crawled_data(csv_file_path):
    """수집된 데이터의 품질 검증"""
    import pandas as pd
    
    df = pd.read_csv(csv_file_path)
    
    validation_results = {
        'total_records': len(df),
        'missing_seller_names': df['seller_name'].isnull().sum(),
        'missing_profiles': df['profile_url'].isnull().sum(),
        'empty_introductions': (df['introduction'] == '').sum(),
        'average_reviews': df['total_reviews'].mean() if 'total_reviews' in df else 0
    }
    
    print("데이터 품질 검증 결과:")
    for key, value in validation_results.items():
        print(f"  {key}: {value}")
    
    return validation_results
```

## 🔄 지속적인 유지보수

### 정기 점검 사항
1. **XPath 선택자 유효성**: 크몽 사이트 구조 변경 시 업데이트 필요
2. **대기 시간 조정**: 사이트 응답 속도 변화에 따른 최적화
3. **오류율 모니터링**: 실패율이 높아지면 선택자 재검토

### 모니터링 스크립트
```python
def health_check_crawl():
    """크롤러 상태 확인"""
    test_cases = [
        ('카테고리 수집', lambda: SellersCrawler().crawl_category_sellers(661)),
        ('프로필 수집', lambda: ProfileCrawler().crawl_seller_profile('test_user')),
        ('리뷰 수집', lambda: ProfileCrawler().crawl_reviews('test_user', max_pages=1))
    ]
    
    results = {}
    for test_name, test_func in test_cases:
        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            
            results[test_name] = {
                'status': 'SUCCESS' if result else 'EMPTY',
                'duration': round(end_time - start_time, 2),
                'data_count': len(result) if isinstance(result, list) else 1
            }
        except Exception as e:
            results[test_name] = {
                'status': 'FAILED',
                'error': str(e)
            }
    
    return results
```

## 🚀 실제 운영 예제

### 프로덕션 크롤링 스크립트
```python
#!/usr/bin/env python3
"""
크몽 크롤러 메인 실행 스크립트
"""

import argparse
import logging
from datetime import datetime
from crawler import SellersCrawler, ProfileCrawler

def setup_logging():
    """로깅 설정"""
    log_filename = f"crawl_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='크몽 크롤러 실행')
    parser.add_argument('--category', type=int, default=661, help='카테고리 ID')
    parser.add_argument('--limit', type=int, help='수집할 프로필 수 제한')
    parser.add_argument('--reviews', action='store_true', help='리뷰 포함 수집')
    parser.add_argument('--services', action='store_true', help='서비스 정보 포함 수집')
    
    args = parser.parse_args()
    logger = setup_logging()
    
    try:
        logger.info(f"크롤링 시작 - 카테고리: {args.category}")
        
        # Step 1: 판매자 목록 수집
        sellers_crawler = SellersCrawler()
        sellers = sellers_crawler.crawl_category_sellers(args.category)
        sellers_crawler.close()
        
        logger.info(f"판매자 {len(sellers)}명 수집 완료")
        
        # Step 2: 프로필 상세 수집
        profile_crawler = ProfileCrawler()
        seller_names = [s['seller_name'] for s in sellers]
        
        if args.limit:
            seller_names = seller_names[:args.limit]
        
        if args.reviews:
            profiles = profile_crawler.crawl_multiple_profiles_with_reviews(seller_names)
        else:
            profiles = profile_crawler.crawl_multiple_profiles(seller_names)
        
        logger.info(f"프로필 {len(profiles)}개 수집 완료")
        
        # Step 3: 서비스 정보 수집 (선택적)
        if args.services:
            logger.warning("서비스 정보 수집은 현재 불안정할 수 있습니다")
            # 서비스 수집 로직...
        
        profile_crawler.close()
        logger.info("크롤링 완료")
        
    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main()
```

### 실행 명령어 예제
```bash
# 기본 프로필 수집
python crawler_main.py --category 661 --limit 20

# 리뷰 포함 수집
python crawler_main.py --category 661 --limit 10 --reviews

# 전체 데이터 수집 (서비스 포함)
python crawler_main.py --category 661 --limit 5 --reviews --services
```

## 📞 지원 및 기여

현재 서비스 정보 수집 기능에 이슈가 있으므로, 해당 부분의 개선에 기여해주시면 감사하겠습니다.

**주요 개선 영역**:
- `_extract_package_prices()` 메서드 안정성 향상
- `_get_service_list()` 메서드 URL 수집 로직 개선  
- 동적 콘텐츠 로딩 대기 시간 최적화

**기여 방법**:
1. 이슈 리포트: 구체적인 오류 상황과 로그 제공
2. 코드 개선: 서비스 수집 관련 메서드 수정 사항
3. 테스트: 다양한 판매자 프로필에서의 동작 검증