from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
import json
from datetime import datetime
import time
import re

def log(message):
    print(f"[{datetime.now().strftime("%H:%M:%S.%f")[:-3]}] {message}")

class BaseCrawler:
    def __init__(self):
        self.driver = self._setup_driver()
    
    def _setup_driver(self):
        """최적화된 드라이버 설정"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(2)  # 10초 → 2초로 단축
        return driver
    
    def _extract_with_beautifulsoup(self):
        """BeautifulSoup으로 빠른 HTML 파싱"""
        from bs4 import BeautifulSoup
        
        try:
            # 한 번에 전체 HTML 가져오기
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            return soup
        except Exception as e:
            log(f"BeautifulSoup 파싱 실패: {e}")
            return None
    
    def save_data(self, data, filename):
        """데이터 저장 - 덮어쓰기 모드"""
        if not data:
            return
            
        df = pd.DataFrame(data)
        filepath = f'output/{filename}.csv'
        
        # mode='w'로 변경하여 덮어쓰기
        df.to_csv(filepath, mode='w', header=True, index=False, encoding='utf-8-sig')
        log(f"데이터 저장 완료: {filepath} ({len(data)}개 항목)")
    
    def close(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()
            
class SellersCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.driver.get("https://kmong.com/category/661")
        time.sleep(1)
    
    def crawl_category_sellers(self, category_id):
        """카테고리의 모든 판매자 정보 수집"""
        all_sellers = []
        page = 1

        self.driver.get(f"https://kmong.com/category/{category_id}?page={page}")
        time.sleep(1)
        
        while True:
            log(f"카테고리 {category_id}, 페이지 {page} 크롤링 중...")
            
            # 페이지 접속
            url = f"https://kmong.com/category/{category_id}?page={page}"
            self.driver.get(url)
            time.sleep(1)
            
            # 서비스 개수 확인
            try:
                service_count_element = self.driver.find_element(
                    By.XPATH, "//*[@id='__next']/div/div/div/div/main/div/div[2]/p"
                )
                service_count_text = service_count_element.text
                log(f"서비스 개수: {service_count_text}")
                
                # "0개의 서비스"면 종료
                if "0개의 서비스" in service_count_text:
                    log(f"카테고리 {category_id} 크롤링 완료 (총 {len(all_sellers)}명)")
                    break
                    
            except Exception as e:
                log(f"서비스 개수 확인 실패: {e}")
                break
            
            # 해당 페이지의 판매자들 수집
            page_sellers = self._extract_sellers_from_page()
            
            if not page_sellers:
                log("더 이상 판매자가 없습니다.")
                break
                
            all_sellers.extend(page_sellers)
            log(f"페이지 {page}에서 {len(page_sellers)}명 수집")
            
            page += 1
            
            # 안전장치 (무한루프 방지)
            if page > 10000:  # 기존 100 → 10000으로 변경
                log("페이지 수가 10000을 초과했습니다. 종료합니다.")
                break
        
        return all_sellers
    
    def _extract_sellers_from_page(self):
        """현재 페이지에서 판매자 정보 추출"""
        sellers = []
        
        try:
            # 서비스 카드들 찾기
            service_cards = self.driver.find_elements(By.XPATH, "//*[@class='css-0 edqw2x10']")
            log(f"현재 페이지에서 {len(service_cards)}개 서비스 발견")
            
            for i, card in enumerate(service_cards):
                try:
                    # 판매자 이름 추출
                    seller_name_element = card.find_element(
                        By.XPATH, ".//*[@class='pt-2']//*[@class='mt-2 flex items-center gap-1']/span"
                    )
                    seller_name = seller_name_element.text.strip()
                    
                    if seller_name:
                        sellers.append({
                            'seller_name': seller_name,
                            'service_index': i + 1
                        })
                        
                except Exception as e:
                    log(f"서비스 {i+1}에서 판매자 이름 추출 실패: {e}")
                    continue
        
        except Exception as e:
            log(f"서비스 카드 찾기 실패: {e}")
        
        return sellers
    
    def crawl_multiple_categories(self, category_ids):
        """여러 카테고리 크롤링"""
        all_data = []
        
        for category_id in category_ids:
            log(f"\n=== 카테고리 {category_id} 시작 ===")
            
            try:
                sellers = self.crawl_category_sellers(category_id)
                
                # 카테고리 정보 추가
                for seller in sellers:
                    seller['category_id'] = category_id
                
                all_data.extend(sellers)
                
                # 중간 저장
                self.save_data(sellers, f'category_{category_id}_sellers')
                
            except Exception as e:
                log(f"카테고리 {category_id} 크롤링 실패: {e}")
                continue
            
            # 카테고리 간 잠시 대기
            time.sleep(3)
        
        return all_data

class ProfileCrawler(BaseCrawler):
    """개별 판매자 프로필 상세 정보 크롤링"""
    
    def __init__(self):
        super().__init__()
    
    def crawl_seller_profile(self, seller_name):
        """최적화된 프로필 크롤링"""
        profile_url = f"https://kmong.com/@{seller_name}"
        log(f"프로필 크롤링 시작: {seller_name}")
        
        try:
            self.driver.get(profile_url)
            time.sleep(1)  # 페이지 로딩만 대기
            
            # BeautifulSoup으로 한 번에 파싱
            soup = self._extract_with_beautifulsoup()
            if not soup:
                return {'seller_name': seller_name, 'error': 'HTML 파싱 실패'}
            
            profile_data = {
                'seller_name': seller_name,
                'profile_url': profile_url,
                'introduction': self._extract_introduction_fast(soup),
                'career': self._extract_career_fast(soup),
                'specialties': self._extract_specialties_fast(soup),
                'skills': self._extract_skills_fast(soup)
            }
            
            log(f"프로필 크롤링 완료: {seller_name}")
            return profile_data
            
        except Exception as e:
            log(f"프로필 크롤링 실패 - {seller_name}: {e}")
            return {'seller_name': seller_name, 'profile_url': profile_url, 'error': str(e)}
    
    def _extract_introduction_fast(self, soup):
        """빠른 자기소개 추출"""
        try:
            intro_element = soup.find(class_='ProfileDescriptionSection__desctiption')
            return intro_element.text.strip() if intro_element else ""
        except Exception as e:
            log(f"자기소개 추출 실패: {e}")
            return ""
    
    def _extract_section_data_fast(self, soup, section_title, tag_class):
        """빠른 섹션 데이터 추출"""
        try:
            section_titles = soup.find_all(class_="ProfileSectionTitle")
            
            for title in section_titles:
                if section_title in title.text.strip():
                    parent_div = title.parent.parent if title.parent else None
                    if parent_div:
                        tags = parent_div.find_all(class_=tag_class)
                        tag_texts = [tag.text.strip() for tag in tags if tag.text.strip()]
                        if tag_texts:
                            log(f"{section_title} 추출 완료: {len(tag_texts)}개")
                            return tag_texts
            return []
            
        except Exception as e:
            log(f"{section_title} 추출 실패: {e}")
            return []

    def _extract_career_fast(self, soup):
        """빠른 경력사항 추출"""
        return self._extract_section_data_fast(soup, "경력사항", "ProfileSkillSection__tag")

    def _extract_skills_fast(self, soup):
        """빠른 보유 기술 추출"""
        return self._extract_section_data_fast(soup, "보유 기술", "ProfileSkillSection__tag")

    def _extract_specialties_fast(self, soup):
        """빠른 전문분야 추출"""
        try:
            specialty_sections = soup.find_all(class_="ProfileSkillSection__specialty")
            
            for specialty in specialty_sections:
                full_text = specialty.text.strip()
                if "IT·프로그래밍" in full_text:
                    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                    
                    it_found = False
                    tags = []
                    
                    for line in lines:
                        if "IT·프로그래밍" in line:
                            it_found = True
                            continue
                        
                        if it_found:
                            if line and not (line.startswith('·') and '·' in line and len(line) < 20):
                                if '·' in line and len(line) < 20:
                                    break
                                tags.append(line)
                    
                    if tags:
                        log(f"IT·프로그래밍 태그들: {tags}")
                        return tags
            
            return []
            
        except Exception as e:
            log(f"전문분야 추출 실패: {e}")
            return []
    
    def crawl_multiple_profiles(self, seller_names):
        """여러 판매자 프로필 크롤링"""
        all_profiles = []
        
        for i, seller_name in enumerate(seller_names, 1):
            log(f"\n=== 프로필 {i}/{len(seller_names)}: {seller_name} ===")
            
            profile_data = self.crawl_seller_profile(seller_name)
            all_profiles.append(profile_data)
            
            # 중간 저장 간격을 더 자주 (10개 → 50개)
            if i % 50 == 0:
                self.save_data(all_profiles[-50:], f'profiles_batch_{i//50}')
            
            # 요청 간격 조절
            time.sleep(1)
        
        return all_profiles
    
    def crawl_from_csv(self, csv_file_path, limit=None):
        """CSV 파일에서 판매자명을 읽어와서 프로필 크롤링"""
        try:
            df = pd.read_csv(csv_file_path)
            seller_names = df['seller_name'].unique().tolist()  # 중복 제거
            
            # limit 기본값을 None으로 설정하여 전체 처리
            if limit:
                seller_names = seller_names[:limit]
                log(f"제한 모드: {limit}명만 크롤링합니다")
            else:
                log(f"전체 모드: {len(seller_names)}명 크롤링합니다")
            
            profiles = self.crawl_multiple_profiles(seller_names)
            
            # 전체 결과 저장
            self.save_data(profiles, 'all_profiles')
            
            return profiles
            
        except Exception as e:
            log(f"CSV 파일 읽기 실패: {e}")
            return []

    def crawl_reviews(self, seller_name, max_pages=20):  # 5 → 20으로 증가
        """리뷰 크롤링 - 리뷰 섹션 스크롤 포함"""
        profile_url = f"https://kmong.com/@{seller_name}"
        
        try:
            self.driver.get(profile_url)
            time.sleep(1)
            
            # 리뷰 섹션으로 스크롤
            try:
                review_section = self.driver.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__list-group")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", review_section)
                time.sleep(1)
                log("리뷰 섹션으로 스크롤 완료")
            except:
                log("리뷰 섹션을 찾을 수 없음")
                return []
            
            # 리뷰 크롤링 진행
            all_reviews = []
            pages_crawled = 0
            
            while pages_crawled < max_pages:
                current_page = pages_crawled + 1
                log(f"리뷰 페이지 {current_page} 크롤링 중...")
                
                page_reviews = self._extract_reviews_from_page()
                
                if not page_reviews:
                    log("더 이상 리뷰가 없습니다.")
                    break
                    
                all_reviews.extend(page_reviews)
                log(f"페이지 {current_page}에서 {len(page_reviews)}개 리뷰 수집")
                pages_crawled += 1
                
                if pages_crawled < max_pages:
                    if not self._go_to_next_review_page():
                        break
            
            return all_reviews
            
        except Exception as e:
            log(f"리뷰 크롤링 실패: {e}")
            return []

    def _extract_reviews_from_page(self):
        """최적화된 리뷰 추출"""
        reviews = []
        
        try:
            soup = self._extract_with_beautifulsoup()
            if not soup:
                return []
            
            review_cards = soup.find_all(class_="RatingList")
            log(f"리뷰 {len(review_cards)}개 발견")
            
            for i, card in enumerate(review_cards):
                try:
                    date_element = card.find(class_="RatingList__rating-user-info")
                    date_info = date_element.text.strip() if date_element else ""
                    
                    service_info = self._extract_service_info_fast(card)
                    
                    review_data = {
                        'review_date': date_info,
                        'service_title': service_info.get('title', ''),
                        'work_period': service_info.get('period', ''),
                        'order_amount': service_info.get('amount', '')
                    }
                    
                    reviews.append(review_data)
                    
                except Exception as e:
                    log(f"개별 리뷰 {i+1} 추출 실패: {e}")
                    continue
            
            return reviews
            
        except Exception as e:
            log(f"리뷰 추출 실패: {e}")
            # 기존 Selenium 방식으로 폴백
            return self._extract_reviews_from_page_selenium()

    def _extract_reviews_from_page_selenium(self):
        """기존 Selenium 방식 리뷰 추출 (폴백용)"""
        reviews = []
        
        try:
            # 리뷰 섹션 내에서만 검색
            review_section = self.driver.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__list-group")
            
            # 해당 섹션 내의 리뷰들만 추출
            review_cards = review_section.find_elements(By.CLASS_NAME, "RatingList")
            log(f"리뷰 섹션에서 {len(review_cards)}개 리뷰 발견")
            
            for i, card in enumerate(review_cards):
                try:
                    # 1. 리뷰 작성 일시
                    date_info = card.find_element(By.CLASS_NAME, "RatingList__rating-user-info").text.strip()
                    
                    # 2. 서비스 정보
                    service_info = self._extract_service_info_selenium(card)
                    
                    review_data = {
                        'review_date': date_info,
                        'service_title': service_info.get('title', ''),
                        'work_period': service_info.get('period', ''),
                        'order_amount': service_info.get('amount', '')
                    }
                    
                    reviews.append(review_data)
                    log(f"  리뷰 {i+1}: {review_data['service_title'][:30]}...")
                    
                except Exception as e:
                    log(f"개별 리뷰 {i+1} 추출 실패: {e}")
                    continue
                    
        except Exception as e:
            log(f"리뷰 섹션에서 리뷰 추출 실패: {e}")
        
        return reviews
    
    def _extract_service_info_fast(self, card_soup):
        """빠른 서비스 정보 추출"""
        service_info = {'title': '', 'period': '', 'amount': ''}
        
        try:
            title_element = card_soup.find(class_="RatingList__buyer-selling-service-gig-info-title")
            if title_element:
                service_info['title'] = title_element.text.strip()
            
            if title_element and title_element.find_next_sibling('span'):
                service_info['period'] = title_element.find_next_sibling('span').text.strip()
            
            amount_elements = card_soup.find_all('span')
            for span in amount_elements:
                text = span.text.strip()
                if '원' in text and ',' in text:
                    service_info['amount'] = text
                    break
            
            return service_info
            
        except Exception as e:
            log(f"서비스 정보 추출 실패: {e}")
            return service_info

    def _extract_service_info_selenium(self, card):
        """기존 Selenium 방식 서비스 정보 추출"""
        service_info = {'title': '', 'period': '', 'amount': ''}
        
        try:
            # 서비스 정보 전체 컨테이너
            service_container = card.find_element(By.CLASS_NAME, "RatingList__buyer-selling-service-gig-info")
            
            # 서비스명과 작업 기간을 감싸는 wrap
            info_wrap = service_container.find_element(By.CLASS_NAME, "RatingList__buyer-selling-service-gig-info-wrap")
            
            # 서비스명
            try:
                service_title = info_wrap.find_element(By.CLASS_NAME, "RatingList__buyer-selling-service-gig-info-title")
                service_info['title'] = service_title.text.strip()
                
                # 작업 기간 (서비스명 바로 다음 span)
                try:
                    period_span = service_title.find_element(By.XPATH, "./following-sibling::span")
                    service_info['period'] = period_span.text.strip()
                except Exception as e:
                    log(f"작업 기간 추출 실패: {e}")
                    
            except Exception as e:
                log(f"서비스명 추출 실패: {e}")
            
            # 주문금액 (info_wrap 다음 div 안의 span)
            try:
                amount_div = info_wrap.find_element(By.XPATH, "./following-sibling::div")
                amount_span = amount_div.find_element(By.TAG_NAME, "span")
                service_info['amount'] = amount_span.text.strip()
            except Exception as e:
                log(f"주문금액 추출 실패: {e}")
                
        except Exception as e:
            log(f"서비스 정보 컨테이너 찾기 실패: {e}")
        
        return service_info

    def _go_to_next_review_page(self):
        """리뷰 다음 페이지 이동 - 페이지네이션 없는 경우 처리"""
        try:
            # 리뷰 섹션을 매번 새로 찾기
            review_section = self.driver.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__list-group")
            
            # 페이지네이션이 있는지 먼저 확인
            try:
                pagination = review_section.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__pagination")
            except:
                log("리뷰 페이지네이션이 없음 (1페이지만 존재)")
                return False
            
            # 현재 페이지 번호 확인 (디버깅용)
            try:
                active_page = pagination.find_element(By.XPATH, ".//li[contains(@class, 'active')]/a")
                current_page_num = active_page.text
                log(f"현재 리뷰 페이지: {current_page_num}")
            except:
                log("현재 페이지 번호 확인 불가")
            
            # ">" 버튼 찾기
            next_buttons = pagination.find_elements(By.XPATH, ".//li/a[text()='>']")
            
            if not next_buttons:
                log("리뷰 '>' 버튼을 찾을 수 없음")
                return False
            
            next_button = next_buttons[0]
            parent_li = next_button.find_element(By.XPATH, "./..")
            
            # 상태 확인 강화
            li_class = parent_li.get_attribute("class") or ""
            tabindex = next_button.get_attribute("tabindex") or "0"
            
            log(f"버튼 상태 - class: '{li_class}', tabindex: '{tabindex}'")
            
            if "disabled" in li_class or tabindex == "-1":
                log("리뷰 다음 페이지 버튼이 비활성화됨")
                return False
            
            # 클릭 전 잠시 대기
            time.sleep(0.5)
            
            # JavaScript 클릭
            self.driver.execute_script("arguments[0].click();", next_button)
            log("리뷰 다음 페이지 버튼 클릭")
            
            # 페이지 변경 대기 - 더 긴 시간
            time.sleep(1)
            
            # 페이지 변경 확인
            try:
                new_section = self.driver.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__list-group")
                new_pagination = new_section.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__pagination")
                new_active = new_pagination.find_element(By.XPATH, ".//li[contains(@class, 'active')]/a")
                new_page_num = new_active.text
                log(f"새 리뷰 페이지: {new_page_num}")
                
                if new_page_num == current_page_num:
                    log("경고: 페이지가 변경되지 않음")
                    return False
                    
            except Exception as e:
                log(f"페이지 변경 확인 실패: {e}")
            
            # 새 리뷰 데이터 로딩 대기
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: len(driver.find_elements(By.CLASS_NAME, "RatingList")) > 0
                )
                log("새 리뷰 데이터 로딩 확인")
            except:
                log("새 리뷰 데이터 로딩 대기 시간 초과")
            
            return True
            
        except Exception as e:
            log(f"리뷰 다음 페이지 이동 실패: {e}")
            return False

    def crawl_seller_profile_with_reviews(self, seller_name, max_review_pages=10):  # 3 → 10으로 증가
        """프로필 + 리뷰 통합 크롤링"""
        log(f"\n=== {seller_name} 프로필 + 리뷰 크롤링 시작 ===")
        
        # 기본 프로필 정보 크롤링
        profile_data = self.crawl_seller_profile(seller_name)
        
        # 리뷰 크롤링 추가
        try:
            reviews = self.crawl_reviews(seller_name, max_pages=max_review_pages)
            profile_data['reviews'] = reviews
            profile_data['total_reviews'] = len(reviews)
            log(f"리뷰 크롤링 완료: {len(reviews)}개")
        except Exception as e:
            log(f"리뷰 크롤링 실패: {e}")
            profile_data['reviews'] = []
            profile_data['total_reviews'] = 0
        
        return profile_data

    def crawl_multiple_profiles_with_reviews(self, seller_names, max_review_pages=10):  # 2 → 10으로 증가
        """여러 판매자 프로필 + 리뷰 크롤링"""
        all_profiles = []
        
        for i, seller_name in enumerate(seller_names, 1):
            log(f"\n=== 프로필 {i}/{len(seller_names)}: {seller_name} ===")
            
            profile_data = self.crawl_seller_profile_with_reviews(seller_name, max_review_pages)
            all_profiles.append(profile_data)
            
            # 중간 저장 (50개씩)
            if i % 50 == 0:
                self.save_data(all_profiles[-50:], f'profiles_with_reviews_batch_{i//50}')
            
            # 요청 간격 조절 (리뷰까지 크롤링하면 시간이 더 걸림)
            time.sleep(3)
        
        return all_profiles

    def crawl_services(self, seller_name, max_service_pages=10, max_services=None):
        """판매자의 서비스 정보 크롤링 - 예외 처리 강화"""
        profile_url = f"https://kmong.com/@{seller_name}"
        
        try:
            self.driver.get(profile_url)
            time.sleep(1)
            
            # 서비스 탭 활성화
            service_tab_activated = self._activate_service_tab()
            if not service_tab_activated:
                log("서비스 탭 활성화 실패 - 서비스가 없거나 접근 불가")
                return []
            
            # 서비스 목록 URLs 수집 (페이지네이션 포함)
            service_urls = self._get_service_list(max_pages=max_service_pages)
            
            if not service_urls:
                log("서비스 URL을 찾을 수 없음")
                return []
            
            log(f"총 {len(service_urls)}개 서비스 처리 예정")
            
            # 각 서비스 상세 정보 수집
            all_services = []
            for i, service_url in enumerate(service_urls, 1):
                log(f"서비스 {i}/{len(service_urls)} 처리: {service_url}")
                
                service_data = self.crawl_single_service(service_url)
            if service_data:
                all_services.append(service_data)
            
            time.sleep(2)  # 서비스 간 대기
        
            return all_services
        
        except Exception as e:
            log(f"서비스 크롤링 실패: {e}")
            return []

    def _activate_service_tab(self):
        """서비스 탭 활성화 - 더 많은 선택자 시도"""
        service_tab_selectors = [
            "//button[contains(text(), '서비스') or contains(text(), 'Services')]",
            "//a[contains(text(), '포트폴리오') or contains(text(), 'Portfolio')]", 
            "//*[@role='tab'][contains(text(), '서비스')]",
            "//button[contains(@class, 'tab') and contains(text(), '서비스')]",
            "//div[contains(@class, 'tab')]//button[contains(text(), '서비스')]",
            "//*[contains(@class, 'ProfileTab')]//button[contains(text(), '서비스')]"
        ]
        time.sleep(1)
        
        for i, selector in enumerate(service_tab_selectors):
            try:
                log(f"서비스 탭 선택자 {i+1} 시도: {selector}")
                tab = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                self.driver.execute_script("arguments[0].click();", tab)
                time.sleep(2)
                
                # 서비스 목록이 로딩되었는지 확인
                try:
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: len(driver.find_elements(By.XPATH, "//a[contains(@href, '/gig/')]")) > 0
                    )
                    log(f"서비스 탭 활성화 성공 (선택자 {i+1})")
                    return True
                except:
                    log(f"서비스 탭 클릭했으나 서비스 목록 로딩 안됨 (선택자 {i+1})")
                    continue
                    
            except Exception as e:
                log(f"서비스 탭 선택자 {i+1} 실패: {e}")
                continue
        
        # 마지막 시도: 서비스가 아예 없는 경우 확인
        try:
            # 서비스 섹션이 존재하는지 확인
            service_sections = self.driver.find_elements(
                By.XPATH, "//*[contains(@class, 'ProfileServiceListSection') or contains(text(), '서비스')]"
            )
            if not service_sections:
                log("이 판매자는 서비스를 제공하지 않습니다")
                return False
        except:
            pass
        
        log("서비스 탭 활성화 실패")
        return False

    def _get_service_list(self, max_pages=10):  # 5 → 10으로 증가
        """서비스 목록 URLs 수집 - 페이지네이션 포함"""
        all_service_urls = []
        current_page = 1
        
        try:
            # 서비스 섹션으로 스크롤
            service_section = self.driver.find_element(By.CLASS_NAME, "ProfileServiceListSection")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", service_section)
            time.sleep(1)
            log("서비스 섹션으로 스크롤 완료")
        except:
            log("서비스 섹션을 찾을 수 없음")
        
        while current_page <= max_pages:
            log(f"서비스 목록 페이지 {current_page} 수집 중...")
            
            try:
                # 현재 페이지의 서비스 URLs 수집
                page_urls = self._extract_service_urls_from_page()
                
                if not page_urls:
                    log("더 이상 서비스가 없습니다.")
                    break
                
                # 중복 제거하면서 추가
                new_urls = [url for url in page_urls if url not in all_service_urls]
                all_service_urls.extend(new_urls)
                
                log(f"페이지 {current_page}에서 {len(new_urls)}개 새 서비스 발견")
                
                # 다음 페이지로 이동
                if current_page < max_pages:
                    if not self._go_to_next_service_page():
                        break
                
                current_page += 1
                
            except Exception as e:
                log(f"서비스 페이지 {current_page} 수집 실패: {e}")
                break
        
        log(f"총 {len(all_service_urls)}개 서비스 URL 수집 완료")
        return all_service_urls

    def _extract_service_urls_from_page(self):
        """현재 페이지에서 서비스 URLs 추출"""
        service_urls = []
        
        try:
            # 서비스 카드들에서 URL 추출
            service_cards = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/gig/')]")
            
            for card in service_cards:
                url = card.get_attribute('href')
                if url and url not in service_urls:
                    service_urls.append(url)
            
            # 대안: 다른 선택자 시도
            if not service_urls:
                service_links = self.driver.find_elements(By.XPATH, "//div[@class='css-0 edqw2x10']//a")
                for link in service_links:
                    href = link.get_attribute('href')
                    if href and '/gig/' in href:
                        service_urls.append(href)
            
            return service_urls
            
        except Exception as e:
            log(f"서비스 URL 추출 실패: {e}")
            return []

    def _go_to_next_service_page(self):
        """서비스 다음 페이지로 이동 - 페이지네이션 없는 경우 처리"""
        try:
            # 서비스 섹션에서 페이지네이션 찾기
            try:
                service_section = self.driver.find_element(By.CLASS_NAME, "ProfileServiceListSection")
            except:
                log("서비스 섹션을 찾을 수 없음")
                return False
            
            try:
                pagination = service_section.find_element(By.CLASS_NAME, "ProfileServiceListSection__pagination")
            except:
                log("서비스 페이지네이션이 없음 (1페이지만 존재)")
                return False
            
            # ">" 버튼 찾기
            next_buttons = pagination.find_elements(By.XPATH, ".//li/a[text()='>']")
            
            if not next_buttons:
                log("서비스 '>' 버튼을 찾을 수 없음")
                return False
            
            next_button = next_buttons[0]
            parent_li = next_button.find_element(By.XPATH, "./..")
            
            # disabled 상태 확인
            li_class = parent_li.get_attribute("class") or ""
            tabindex = next_button.get_attribute("tabindex") or "0"
            
            if "disabled" in li_class or tabindex == "-1":
                log("서비스 다음 페이지 버튼이 비활성화됨")
                return False
            
            # JavaScript 클릭
            self.driver.execute_script("arguments[0].click();", next_button)
            log("서비스 다음 페이지 버튼 클릭")
            
            # 페이지 변경 대기
            time.sleep(1)
            
            # 새 서비스 데이터 로딩 확인
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: len(driver.find_elements(By.XPATH, "//a[contains(@href, '/gig/')]")) > 0
                )
                log("새 서비스 페이지 로딩 완료")
                return True
            except:
                log("새 서비스 페이지 로딩 확인 실패")
                return False
                
        except Exception as e:
            log(f"서비스 다음 페이지 이동 실패: {e}")
            return False

    def _extract_package_info_fast(self):
        """빠른 패키지 정보 추출"""
        try:
            # BeautifulSoup으로 한 번에 파싱
            soup = self._extract_with_beautifulsoup()
            if not soup:
                return {}
            
            aside = soup.find('aside')
            if not aside:
                return {}
            
            # 패키지 버튼들 확인
            package_buttons = aside.find_all('button', class_=lambda x: x and 'flex h-[50px] w-[119px]' in x)
            
            if not package_buttons:
                # 단일 패키지 처리
                return self._extract_single_package_info_fast(aside)
            else:
                # 다중 패키지의 경우 Selenium 필요 (버튼 클릭)
                return self._extract_multiple_packages_info(self.driver.find_element(By.TAG_NAME, "aside"), 
                                                        self.driver.find_elements(By.XPATH, ".//button[contains(@class, 'flex h-[50px] w-[119px]')]"))
            
        except Exception as e:
            log(f"패키지 정보 추출 실패: {e}")
            return {}

    def _extract_single_package_info_fast(self, aside_soup):
        """빠른 단일 패키지 정보 추출"""
        try:
            # 가격
            price_element = aside_soup.find('div', class_=lambda x: x and 'text-[18px]' in x and 'font-bold' in x)
            price = price_element.text.strip() if price_element else ""
            
            # 제목
            title_element = aside_soup.find('p', class_=lambda x: x and 'text-[14px]' in x and 'font-bold' in x)
            title = title_element.text.strip() if title_element else ""
            
            # 설명
            desc_element = aside_soup.find('p', class_=lambda x: x and 'whitespace-pre-wrap' in x)
            description = desc_element.text.strip() if desc_element else ""
            
            # 상세 정보
            details = self._extract_package_details_fast(aside_soup)
            
            return {
                'SINGLE': {
                    'price': price,
                    'title': title, 
                    'description': description,
                    'details': details
                }
            }
            
        except Exception as e:
            log(f"단일 패키지 추출 실패: {e}")
            return {}

    def _extract_multiple_packages_info(self, aside, package_buttons):
        """다중 패키지 정보 추출"""
        packages = {}
        package_types = ['STANDARD', 'DELUXE', 'PREMIUM']
        
        # 모든 패키지 콘텐츠 div들 찾기
        content_divs = aside.find_elements(
            By.XPATH, ".//div[contains(@class, 'w-full rounded-b-lg border border-gray-300')]"
        )
        
        for i, (button, content_div) in enumerate(zip(package_buttons, content_divs)):
            try:
                package_name = package_types[i] if i < len(package_types) else f'PACKAGE_{i+1}'
                
                # 버튼 클릭하여 해당 패키지 활성화
                self.driver.execute_script("arguments[0].click();", button)
                time.sleep(1)
                
                # 현재 활성화된 패키지 정보 추출
                package_info = self._extract_active_package_info(aside)
                
                if package_info:
                    packages[package_name] = package_info
                    log(f"{package_name} 패키지 정보 추출 완료")
                
            except Exception as e:
                log(f"{package_name} 패키지 추출 실패: {e}")
                continue
        
        return packages

    def _extract_active_package_info(self, aside):
        """현재 활성화된 패키지의 정보 추출"""
        try:
            # 현재 표시된 (block 상태) 콘텐츠 div 찾기
            active_content = aside.find_element(
                By.XPATH, ".//div[contains(@class, 'w-full rounded-b-lg border border-gray-300') and contains(@class, 'block')]"
            )
            
            # 가격 추출
            price_element = active_content.find_element(
                By.XPATH, ".//div[contains(@class, 'text-[18px] font-bold leading-[27px]')]"
            )
            price = price_element.text.strip()
            
            # 패키지 제목 추출
            title_element = active_content.find_element(
                By.XPATH, ".//p[contains(@class, 'text-[14px] font-bold text-gray-800')]"
            )
            title = title_element.text.strip()
            
            # 패키지 설명 추출
            description_element = active_content.find_element(
                By.XPATH, ".//p[contains(@class, 'whitespace-pre-wrap text-sm leading-[21px]')]"
            )
            description = description_element.text.strip()
            
            # 상세 정보 추출
            details = self._extract_package_details_selenium(active_content)
            
            return {
                'price': price,
                'title': title,
                'description': description,
                'details': details
            }
            
        except Exception as e:
            log(f"활성 패키지 정보 추출 실패: {e}")
            return None

    def _extract_package_details_fast(self, container_soup):
        """빠른 패키지 상세 정보 추출"""
        details = {
            'included_features': [],
            'specifications': {}
        }
        
        try:
            # 그리드 컨테이너 내 모든 flex 아이템들
            flex_items = container_soup.find_all('div', class_=lambda x: x and 'flex basis-1/2' in x)
            
            for item in flex_items:
                try:
                    p_tags = item.find_all('p', class_=lambda x: x and 'text-sm' in x)
                    if len(p_tags) >= 1:
                        left_text = p_tags[0].text.strip()
                        
                        # SVG 체크마크 확인
                        if item.find('svg'):
                            details['included_features'].append(left_text)
                        elif len(p_tags) >= 2:
                            right_text = p_tags[1].text.strip()
                            details['specifications'][left_text] = right_text
                        else:
                            details['included_features'].append(left_text)
                            
                except Exception as e:
                    continue
            
            return details
            
        except Exception as e:
            log(f"패키지 상세 정보 추출 실패: {e}")
            return details

    def _extract_package_details_selenium(self, container):
        """Selenium 방식 패키지 상세 정보 추출"""
        details = {
            'included_features': [],  # 체크 표시된 항목들
            'specifications': {}      # 키-값 쌍 항목들
        }
        
        try:
            # 그리드 컨테이너 찾기
            grid_container = container.find_element(
                By.XPATH, ".//div[contains(@class, 'mt-4 grid grid-cols-1 gap-x-4')]"
            )
            
            # 모든 flex 아이템들 찾기
            flex_items = grid_container.find_elements(
                By.XPATH, ".//div[contains(@class, 'flex basis-1/2 items-center justify-between py-0.5')]"
            )
            
            for item in flex_items:
                try:
                    # 왼쪽 텍스트 (항목명)
                    left_text = item.find_element(
                        By.XPATH, ".//p[contains(@class, 'text-sm')]"
                    ).text.strip()
                    
                    # 오른쪽 요소 확인 (SVG 체크마크 또는 값)
                    try:
                        # 체크마크 SVG 있는지 확인
                        svg_check = item.find_element(By.XPATH, ".//svg")
                        details['included_features'].append(left_text)
                        log(f"포함 기능: {left_text}")
                        
                    except:
                        # SVG가 없으면 값이 있는 항목
                        try:
                            right_text = item.find_elements(
                                By.XPATH, ".//p[contains(@class, 'text-sm')]"
                            )[1].text.strip()  # 두 번째 p 태그
                            
                            details['specifications'][left_text] = right_text
                            log(f"상세 정보: {left_text} = {right_text}")
                            
                        except:
                            # 값을 찾을 수 없는 경우 포함 기능으로 분류
                            details['included_features'].append(left_text)
                            
                except Exception as e:
                    log(f"개별 항목 추출 실패: {e}")
                    continue
            
            return details
            
        except Exception as e:
            log(f"패키지 상세 정보 추출 실패: {e}")
            return details

    def crawl_single_service(self, service_url):
        """최적화된 서비스 크롤링"""
        try:
            self.driver.get(service_url)
            time.sleep(1)  # 페이지 로딩만 대기
            
            service_data = {
                'service_url': service_url,
                'packages': self._extract_package_info_fast(),  # 빠른 추출
                'skill_level': self._extract_skill_level_fast(),
                'team_size': self._extract_team_size_fast()
            }
            
            return service_data
            
        except Exception as e:
            log(f"서비스 페이지 크롤링 실패: {e}")
            return None

    def _extract_skill_level_fast(self):
        """빠른 기술 수준 추출"""
        try:
            soup = self._extract_with_beautifulsoup()
            if not soup:
                return ""
            
            info_box = soup.find('div', id='10')
            if not info_box:
                return ""
            
            # 기술/수준 관련 텍스트 찾기
            skill_elements = info_box.find_all(string=lambda text: text and ('기술' in text or '수준' in text))
            
            for element in skill_elements:
                parent = element.parent
                if parent:
                    # 다음 span 태그에서 값 찾기
                    next_span = parent.find_next('span')
                    if next_span and next_span.text.strip():
                        return next_span.text.strip()
            
            return ""
            
        except Exception as e:
            log(f"기술 수준 추출 실패: {e}")
            return ""

    def _extract_team_size_fast(self):
        """빠른 팀 규모 추출"""
        try:
            soup = self._extract_with_beautifulsoup()
            if not soup:
                return ""
            
            info_box = soup.find('div', id='10')
            if not info_box:
                return ""
            
            # 팀/규모 관련 텍스트 찾기
            team_elements = info_box.find_all(string=lambda text: text and ('팀' in text or '규모' in text))
            
            for element in team_elements:
                parent = element.parent
                if parent:
                    next_span = parent.find_next('span')
                    if next_span and next_span.text.strip():
                        return next_span.text.strip()
            
            return ""
            
        except Exception as e:
            log(f"팀 규모 추출 실패: {e}")
            return ""

    def crawl_seller_profile_complete(self, seller_name, max_review_pages=10):  # 2 → 10으로 증가
        """프로필 + 리뷰 + 서비스 통합 크롤링"""
        log(f"\n=== {seller_name} 전체 데이터 크롤링 시작 ===")
        
        # 1. 기본 프로필 정보
        profile_data = self.crawl_seller_profile(seller_name)
        
        # 2. 리뷰 크롤링
        try:
            reviews = self.crawl_reviews(seller_name, max_pages=max_review_pages)
            profile_data['reviews'] = reviews
            profile_data['total_reviews'] = len(reviews)
            log(f"리뷰 크롤링 완료: {len(reviews)}개")
        except Exception as e:
            log(f"리뷰 크롤링 실패: {e}")
            profile_data['reviews'] = []
            profile_data['total_reviews'] = 0
        
        # 3. 서비스 크롤링
        try:
            services = self.crawl_services(seller_name)
            profile_data['services'] = services
            profile_data['total_services'] = len(services)
            log(f"서비스 크롤링 완료: {len(services)}개")
        except Exception as e:
            log(f"서비스 크롤링 실패: {e}")
            profile_data['services'] = []
            profile_data['total_services'] = 0
        
        return profile_data