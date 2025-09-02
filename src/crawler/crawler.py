from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
import json
import time
import re

class BaseCrawler:
    def __init__(self):
        self.driver = self._setup_driver()
    
    def _setup_driver(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        return driver
    
    def save_data(self, data, filename):
        """데이터 저장 - 덮어쓰기 모드"""
        if not data:
            return
            
        df = pd.DataFrame(data)
        filepath = f'output/{filename}.csv'
        
        # mode='w'로 변경하여 덮어쓰기
        df.to_csv(filepath, mode='w', header=True, index=False, encoding='utf-8-sig')
        print(f"데이터 저장 완료: {filepath} ({len(data)}개 항목)")
    
    def close(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()
            
class SellersCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.driver.get("https://kmong.com/category/661")
        time.sleep(3)
    
    def crawl_category_sellers(self, category_id):
        """카테고리의 모든 판매자 정보 수집"""
        all_sellers = []
        page = 1

        self.driver.get(f"https://kmong.com/category/{category_id}?page={page}")
        time.sleep(5)
        
        while True:
            print(f"카테고리 {category_id}, 페이지 {page} 크롤링 중...")
            
            # 페이지 접속
            url = f"https://kmong.com/category/{category_id}?page={page}"
            self.driver.get(url)
            time.sleep(3)
            
            # 서비스 개수 확인
            try:
                service_count_element = self.driver.find_element(
                    By.XPATH, "//*[@id='__next']/div/div/div/div/main/div/div[2]/p"
                )
                service_count_text = service_count_element.text
                print(f"서비스 개수: {service_count_text}")
                
                # "0개의 서비스"면 종료
                if "0개의 서비스" in service_count_text:
                    print(f"카테고리 {category_id} 크롤링 완료 (총 {len(all_sellers)}명)")
                    break
                    
            except Exception as e:
                print(f"서비스 개수 확인 실패: {e}")
                break
            
            # 해당 페이지의 판매자들 수집
            page_sellers = self._extract_sellers_from_page()
            
            if not page_sellers:
                print("더 이상 판매자가 없습니다.")
                break
                
            all_sellers.extend(page_sellers)
            print(f"페이지 {page}에서 {len(page_sellers)}명 수집")
            
            page += 1
            
            # 안전장치 (무한루프 방지)
            if page > 100:
                print("페이지 수가 100을 초과했습니다. 종료합니다.")
                break
        
        return all_sellers
    
    def _extract_sellers_from_page(self):
        """현재 페이지에서 판매자 정보 추출"""
        sellers = []
        
        try:
            # 서비스 카드들 찾기
            service_cards = self.driver.find_elements(By.XPATH, "//*[@class='css-0 edqw2x10']")
            print(f"현재 페이지에서 {len(service_cards)}개 서비스 발견")
            
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
                    print(f"서비스 {i+1}에서 판매자 이름 추출 실패: {e}")
                    continue
        
        except Exception as e:
            print(f"서비스 카드 찾기 실패: {e}")
        
        return sellers
    
    def crawl_multiple_categories(self, category_ids):
        """여러 카테고리 크롤링"""
        all_data = []
        
        for category_id in category_ids:
            print(f"\n=== 카테고리 {category_id} 시작 ===")
            
            try:
                sellers = self.crawl_category_sellers(category_id)
                
                # 카테고리 정보 추가
                for seller in sellers:
                    seller['category_id'] = category_id
                
                all_data.extend(sellers)
                
                # 중간 저장
                self.save_data(sellers, f'category_{category_id}_sellers')
                
            except Exception as e:
                print(f"카테고리 {category_id} 크롤링 실패: {e}")
                continue
            
            # 카테고리 간 잠시 대기
            time.sleep(5)
        
        return all_data

class ProfileCrawler(BaseCrawler):
    """개별 판매자 프로필 상세 정보 크롤링"""
    
    def __init__(self):
        super().__init__()
    
    def crawl_seller_profile(self, seller_name):
        """개별 판매자 프로필 크롤링"""
        profile_url = f"https://kmong.com/@{seller_name}"
        print(f"프로필 크롤링 시작: {seller_name} ({profile_url})")
        
        try:
            self.driver.get(profile_url)
            time.sleep(3)
            
            # 페이지 로딩 확인
            time.sleep(3)
            
            profile_data = {
                'seller_name': seller_name,
                'profile_url': profile_url,
                'introduction': self._extract_introduction(),
                'career': self._extract_career(),
                'specialties': self._extract_specialties(),
                'skills': self._extract_skills()
            }
            
            print(f"프로필 크롤링 완료: {seller_name}")
            return profile_data
            
        except Exception as e:
            print(f"프로필 크롤링 실패 - {seller_name}: {e}")
            return {
                'seller_name': seller_name,
                'profile_url': profile_url,
                'error': str(e)
            }
    
    def _extract_introduction(self):
        """자기소개 추출"""
        try:
            intro_element = self.driver.find_element(
                By.XPATH, "//*[@class='ProfileDescriptionSection__desctiption']"
            )
            return intro_element.text.strip()
        except Exception as e:
            print(f"자기소개 추출 실패: {e}")
            return ""
    
    def _extract_career(self):
        """경력사항 추출"""
        print("경력사항 추출")
        return self._extract_section_data("경력사항", "ProfileSkillSection__tag")
    
    def _extract_skills(self):
        """보유 기술 추출"""
        print("보유 기술 추출")
        return self._extract_section_data("보유 기술", "ProfileSkillSection__tag")

    def _extract_section_data(self, section_title, tag_class):
        try:
            section_titles = self.driver.find_elements(By.CLASS_NAME, "ProfileSectionTitle")
            
            for title in section_titles:
                if section_title in title.text.strip():
                    print(f"{section_title} 섹션 발견")
                    
                    # XPath 패턴 분석:
                    # 제목: .../div[1]/div[1]  
                    # 내용: .../div[1]/div[2]/div
                    # 즉, div[1] → div[2]로 이동해서 태그들 찾기
                    
                    try:
                        # 제목의 부모 요소 (div[1])
                        parent_div = title.find_element(By.XPATH, "./..")
                        
                        # 형제 요소인 div[2] 찾기  
                        content_div = parent_div.find_element(By.XPATH, "./div[2]")
                        
                        # 그 안의 모든 태그들 찾기
                        tags = content_div.find_elements(By.CLASS_NAME, tag_class)
                        
                        tag_texts = [tag.text.strip() for tag in tags if tag.text.strip()]
                        print(f"{section_title} 추출 완료: {len(tag_texts)}개 - {tag_texts}")
                        return tag_texts
                        
                    except Exception as e:
                        print(f"{section_title} 태그 추출 실패: {e}")
                        
                        # 대안: 더 넓은 범위에서 태그 찾기
                        try:
                            # 제목 다음 형제 요소들에서 모든 태그 검색
                            next_sibling = title.find_element(By.XPATH, "./following-sibling::*")
                            tags = next_sibling.find_elements(By.CLASS_NAME, tag_class)
                            tag_texts = [tag.text.strip() for tag in tags if tag.text.strip()]
                            print(f"{section_title} 대안 방법으로 추출: {tag_texts}")
                            return tag_texts
                        except:
                            return []
            
            print(f"{section_title} 섹션을 찾을 수 없습니다.")
            return []
            
        except Exception as e:
            print(f"{section_title} 추출 실패: {e}")
            return []

    def _extract_specialties(self):
        """전문분야 및 상세분야 추출 (IT·프로그래밍만) - 구조 기반 수정"""
        try:
            section_titles = self.driver.find_elements(By.CLASS_NAME, "ProfileSectionTitle")
            
            for title in section_titles:
                if "전문분야" in title.text:
                    print("전문분야 섹션 발견")
                    
                    # 전문분야 섹션 전체 컨테이너 찾기
                    section_container = title.find_element(By.XPATH, "./../../..")
                    
                    # IT·프로그래밍 제목을 가진 div 찾기
                    it_titles = section_container.find_elements(By.CLASS_NAME, "ProfileSkillSection__title")
                    
                    for it_title in it_titles:
                        title_text = it_title.text.strip()
                        print(f"전문분야 제목 발견: '{title_text}'")
                        
                        if "IT" in title_text and "프로그래밍" in title_text:
                            print(f"IT·프로그래밍 전문분야 발견: {title_text}")
                            
                            try:
                                # IT·프로그래밍 제목 다음에 오는 태그들 찾기
                                # 방법 1: 다음 형제 요소들에서 태그 찾기
                                next_elements = it_title.find_elements(By.XPATH, "./following-sibling::*")
                                
                                all_tags = []
                                for element in next_elements:
                                    # 다음 ProfileSkillSection__title이 나오면 중단
                                    if "ProfileSkillSection__title" in element.get_attribute("class"):
                                        break
                                    
                                    # 태그들 찾기
                                    tags = element.find_elements(By.CLASS_NAME, "ProfileSkillSection__tag")
                                    for tag in tags:
                                        tag_text = tag.text.strip()
                                        if tag_text:
                                            all_tags.append(tag_text)
                                
                                if all_tags:
                                    print(f"IT·프로그래밍 태그들: {all_tags}")
                                    return all_tags
                                
                                # 방법 2: 부모 요소에서 태그들 찾기 (바로 다음)
                                parent = it_title.find_element(By.XPATH, "./..")
                                tags = parent.find_elements(By.CLASS_NAME, "ProfileSkillSection__tag")
                                if tags:
                                    tag_texts = [tag.text.strip() for tag in tags if tag.text.strip()]
                                    print(f"부모에서 찾은 IT·프로그래밍 태그들: {tag_texts}")
                                    return tag_texts
                                    
                            except Exception as e:
                                print(f"IT 프로그래밍 태그 추출 실패: {e}")
                    
                    # 대안: 텍스트 파싱으로 추출
                    print("대안 방법: 텍스트 파싱 시도")
                    specialties = section_container.find_elements(By.CLASS_NAME, "ProfileSkillSection__specialty")
                    
                    for specialty in specialties:
                        full_text = specialty.text.strip()
                        if "IT·프로그래밍" in full_text:
                            lines = full_text.split('\n')
                            
                            # IT·프로그래밍 이후의 줄들 추출
                            it_found = False
                            tags = []
                            
                            for line in lines:
                                line = line.strip()
                                if "IT·프로그래밍" in line:
                                    it_found = True
                                    continue
                                
                                if it_found:
                                    # 다음 전문분야가 나오면 중단
                                    if line and not line.startswith('·') and '·' in line and len(line) < 20:
                                        break
                                    if line:
                                        tags.append(line)
                            
                            if tags:
                                print(f"텍스트 파싱으로 추출한 IT·프로그래밍 태그들: {tags}")
                                return tags
            
            print("IT·프로그래밍 전문분야를 찾을 수 없습니다.")
            return []
            
        except Exception as e:
            print(f"전문분야 추출 실패: {e}")
            return []
    
    def crawl_multiple_profiles(self, seller_names):
        """여러 판매자 프로필 크롤링"""
        all_profiles = []
        
        for i, seller_name in enumerate(seller_names, 1):
            print(f"\n=== 프로필 {i}/{len(seller_names)}: {seller_name} ===")
            
            profile_data = self.crawl_seller_profile(seller_name)
            all_profiles.append(profile_data)
            
            # 중간 저장
            if i % 10 == 0:
                self.save_data(all_profiles[-10:], f'profiles_batch_{i//10}')
            
            # 요청 간격 조절
            time.sleep(2)
        
        return all_profiles
    
    def crawl_from_csv(self, csv_file_path, limit=None):
        """CSV 파일에서 판매자명을 읽어와서 프로필 크롤링"""
        try:
            df = pd.read_csv(csv_file_path)
            seller_names = df['seller_name'].unique().tolist()  # 중복 제거
            
            # 개발 단계에서 제한 적용
            if limit:
                seller_names = seller_names[:limit]
                print(f"개발 모드: {limit}명만 크롤링합니다")
            
            print(f"CSV에서 {len(seller_names)}명의 판매자 크롤링 예정")
            
            profiles = self.crawl_multiple_profiles(seller_names)
            
            # 전체 결과 저장
            self.save_data(profiles, 'all_profiles')
            
            return profiles
            
        except Exception as e:
            print(f"CSV 파일 읽기 실패: {e}")
            return []

    def crawl_reviews(self, seller_name, max_pages=5):
        """리뷰 크롤링 - 리뷰 섹션 스크롤 포함"""
        profile_url = f"https://kmong.com/@{seller_name}"
        
        try:
            self.driver.get(profile_url)
            time.sleep(3)
            
            # 리뷰 섹션으로 스크롤
            try:
                review_section = self.driver.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__list-group")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", review_section)
                time.sleep(2)
                print("리뷰 섹션으로 스크롤 완료")
            except:
                print("리뷰 섹션을 찾을 수 없음")
                return []
            
            # 리뷰 크롤링 진행
            all_reviews = []
            pages_crawled = 0
            
            while pages_crawled < max_pages:
                current_page = pages_crawled + 1
                print(f"리뷰 페이지 {current_page} 크롤링 중...")
                
                page_reviews = self._extract_reviews_from_page()
                
                if not page_reviews:
                    print("더 이상 리뷰가 없습니다.")
                    break
                    
                all_reviews.extend(page_reviews)
                print(f"페이지 {current_page}에서 {len(page_reviews)}개 리뷰 수집")
                pages_crawled += 1
                
                if pages_crawled < max_pages:
                    if not self._go_to_next_review_page():
                        break
            
            return all_reviews
            
        except Exception as e:
            print(f"리뷰 크롤링 실패: {e}")
            return []

    def _extract_reviews_from_page(self):
        """리뷰 섹션에서만 리뷰 추출"""
        reviews = []
        
        try:
            # 리뷰 섹션 내에서만 검색
            review_section = self.driver.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__list-group")
            
            # 해당 섹션 내의 리뷰들만 추출
            review_cards = review_section.find_elements(By.CLASS_NAME, "RatingList")
            print(f"리뷰 섹션에서 {len(review_cards)}개 리뷰 발견")
            
            for i, card in enumerate(review_cards):
                try:
                    # 1. 리뷰 작성 일시
                    date_info = card.find_element(By.CLASS_NAME, "RatingList__rating-user-info").text.strip()
                    
                    # 2. 서비스 정보
                    service_info = self._extract_service_info(card)
                    
                    review_data = {
                        'review_date': date_info,
                        'service_title': service_info.get('title', ''),
                        'work_period': service_info.get('period', ''),
                        'order_amount': service_info.get('amount', '')
                    }
                    
                    reviews.append(review_data)
                    print(f"  리뷰 {i+1}: {review_data['service_title'][:30]}...")
                    
                except Exception as e:
                    print(f"개별 리뷰 {i+1} 추출 실패: {e}")
                    continue
                    
        except Exception as e:
            print(f"리뷰 섹션에서 리뷰 추출 실패: {e}")
            # 대안: 전체 페이지에서 검색
            try:
                review_cards = self.driver.find_elements(By.CLASS_NAME, "RatingList")
                print(f"전체 페이지에서 {len(review_cards)}개 리뷰 발견 (대안)")
                # 위와 동일한 추출 로직 적용
            except:
                print("전체 페이지에서도 리뷰를 찾을 수 없음")
        
        return reviews

    def _extract_service_info(self, card):
        """서비스 정보 추출"""
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
                    print(f"작업 기간 추출 실패: {e}")
                    
            except Exception as e:
                print(f"서비스명 추출 실패: {e}")
            
            # 주문금액 (info_wrap 다음 div 안의 span)
            try:
                amount_div = info_wrap.find_element(By.XPATH, "./following-sibling::div")
                amount_span = amount_div.find_element(By.TAG_NAME, "span")
                service_info['amount'] = amount_span.text.strip()
            except Exception as e:
                print(f"주문금액 추출 실패: {e}")
                
        except Exception as e:
            print(f"서비스 정보 컨테이너 찾기 실패: {e}")
        
        return service_info

    def _get_next_available_page(self, current_page):
        """다음으로 갈 수 있는 페이지 번호 찾기 - 단순화된 로직"""
        # 단순히 다음 페이지 번호를 반환
        # 실제 페이지 존재 여부는 _go_to_review_page에서 확인
        return current_page + 1

    def _go_to_review_page(self, target_page):
        """특정 페이지로 이동 - 실제 페이지네이션 패턴에 맞춘 로직"""
        try:
            pagination = self.driver.find_element(By.CLASS_NAME, "pagination")
            
            # 1. 먼저 목표 페이지가 직접 보이는지 확인
            direct_links = pagination.find_elements(By.XPATH, f".//li[@class='page-item']/a[text()='{target_page}']")
            
            if direct_links and len(direct_links) > 0:
                # 직접 클릭 가능
                direct_links[0].click()
                time.sleep(2)
                print(f"페이지 {target_page} 직접 이동 성공")
                return True
            
            # 2. 목표 페이지가 안 보이면 현재 상황 분석
            current_active = None
            try:
                active_page = pagination.find_element(By.XPATH, ".//li[contains(@class, 'active')]/a")
                current_active = int(active_page.text)
                print(f"현재 활성 페이지: {current_active}, 목표: {target_page}")
            except:
                print("현재 활성 페이지를 찾을 수 없음")
            
            # 3. ">" 버튼으로 앞으로 이동
            max_attempts = 10  # 무한루프 방지
            attempts = 0
            
            while attempts < max_attempts:
                attempts += 1
                
                # ">" 버튼 찾기
                next_buttons = pagination.find_elements(By.XPATH, ".//li/a[text()='>']")
                if not next_buttons:
                    print("'>' 버튼을 찾을 수 없음")
                    break
                
                next_button = next_buttons[0]
                parent_li = next_button.find_element(By.XPATH, "./..")
                
                # disabled 체크
                if "disabled" in parent_li.get_attribute("class"):
                    print("'>' 버튼이 비활성화됨")
                    break
                
                # ">" 클릭
                next_button.click()
                time.sleep(3)
                print(f"'>' 클릭 시도 {attempts}")
                
                # 페이지네이션 다시 가져오기
                try:
                    pagination = self.driver.find_element(By.CLASS_NAME, "pagination")
                except:
                    print("페이지네이션을 다시 찾을 수 없음")
                    break
                
                # 목표 페이지가 이제 보이는지 확인
                target_links = pagination.find_elements(By.XPATH, f".//li[@class='page-item']/a[text()='{target_page}']")
                if target_links:
                    target_links[0].click()
                    time.sleep(2)
                    print(f"페이지 {target_page} 이동 성공 (시도 {attempts}회)")
                    return True
                
                # 현재 페이지가 목표보다 크면 너무 멀리 간 것
                try:
                    current_active = pagination.find_element(By.XPATH, ".//li[contains(@class, 'active')]/a")
                    current_num = int(current_active.text)
                    if current_num >= target_page:
                        print(f"목표 페이지 {target_page}를 지나쳤음 (현재: {current_num})")
                        break
                except:
                    pass
            
            print(f"페이지 {target_page} 이동 실패")
            return False
            
        except Exception as e:
            print(f"페이지 {target_page} 이동 중 오류: {e}")
            return False

    def _go_to_next_review_page(self):
        """리뷰 다음 페이지 이동 - 안정성 강화"""
        try:
            # 리뷰 섹션을 매번 새로 찾기
            review_section = self.driver.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__list-group")
            
            # 현재 페이지 번호 확인 (디버깅용)
            try:
                current_pagination = review_section.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__pagination")
                active_page = current_pagination.find_element(By.XPATH, ".//li[contains(@class, 'active')]/a")
                current_page_num = active_page.text
                print(f"현재 리뷰 페이지: {current_page_num}")
            except:
                print("현재 페이지 번호 확인 불가")
            
            # 페이지네이션을 매번 새로 찾기 (DOM 재생성 대응)
            pagination = review_section.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__pagination")
            next_buttons = pagination.find_elements(By.XPATH, ".//li/a[text()='>']")
            
            if not next_buttons:
                print("리뷰 '>' 버튼을 찾을 수 없음")
                return False
            
            next_button = next_buttons[0]
            parent_li = next_button.find_element(By.XPATH, "./..")
            
            # 상태 확인 강화
            li_class = parent_li.get_attribute("class") or ""
            tabindex = next_button.get_attribute("tabindex") or "0"
            
            print(f"버튼 상태 - class: '{li_class}', tabindex: '{tabindex}'")
            
            if "disabled" in li_class or tabindex == "-1":
                print("리뷰 다음 페이지 버튼이 비활성화됨")
                return False
            
            # 클릭 전 잠시 대기
            time.sleep(1)
            
            # JavaScript 클릭
            self.driver.execute_script("arguments[0].click();", next_button)
            print("리뷰 다음 페이지 버튼 클릭")
            
            # 페이지 변경 대기 - 더 긴 시간
            time.sleep(2)
            
            # 페이지 변경 확인
            try:
                new_section = self.driver.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__list-group")
                new_pagination = new_section.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__pagination")
                new_active = new_pagination.find_element(By.XPATH, ".//li[contains(@class, 'active')]/a")
                new_page_num = new_active.text
                print(f"새 리뷰 페이지: {new_page_num}")
                
                if new_page_num == current_page_num:
                    print("경고: 페이지가 변경되지 않음")
                    return False
                    
            except Exception as e:
                print(f"페이지 변경 확인 실패: {e}")
            
            # 새 리뷰 데이터 로딩 대기
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: len(driver.find_elements(By.CLASS_NAME, "RatingList")) > 0
                )
                print("새 리뷰 데이터 로딩 확인")
            except:
                print("새 리뷰 데이터 로딩 대기 시간 초과")
            
            return True
            
        except Exception as e:
            print(f"리뷰 다음 페이지 이동 실패: {e}")
            return False

    def crawl_seller_profile_with_reviews(self, seller_name, max_review_pages=3):
        """프로필 + 리뷰 통합 크롤링"""
        print(f"\n=== {seller_name} 프로필 + 리뷰 크롤링 시작 ===")
        
        # 기본 프로필 정보 크롤링
        profile_data = self.crawl_seller_profile(seller_name)
        
        # 리뷰 크롤링 추가
        try:
            reviews = self.crawl_reviews(seller_name, max_pages=max_review_pages)
            profile_data['reviews'] = reviews
            profile_data['total_reviews'] = len(reviews)
            print(f"리뷰 크롤링 완료: {len(reviews)}개")
        except Exception as e:
            print(f"리뷰 크롤링 실패: {e}")
            profile_data['reviews'] = []
            profile_data['total_reviews'] = 0
        
        return profile_data

    def crawl_multiple_profiles_with_reviews(self, seller_names, max_review_pages=2):
        """여러 판매자 프로필 + 리뷰 크롤링"""
        all_profiles = []
        
        for i, seller_name in enumerate(seller_names, 1):
            print(f"\n=== 프로필 {i}/{len(seller_names)}: {seller_name} ===")
            
            profile_data = self.crawl_seller_profile_with_reviews(seller_name, max_review_pages)
            all_profiles.append(profile_data)
            
            # 중간 저장 (10개씩)
            if i % 10 == 0:
                self.save_data(all_profiles[-10:], f'profiles_with_reviews_batch_{i//10}')
            
            # 요청 간격 조절 (리뷰까지 크롤링하면 시간이 더 걸림)
            time.sleep(3)
        
        return all_profiles

    def _go_to_next_service_page(self):
        """서비스 다음 페이지로 이동 - 리뷰 로직 기반"""
        try:
            # 서비스 섹션에서 페이지네이션 찾기
            service_section = self.driver.find_element(By.CLASS_NAME, "ProfileServiceListSection")
            pagination = service_section.find_element(By.CLASS_NAME, "ProfileServiceListSection__pagination")
            
            # ">" 버튼 찾기
            next_buttons = pagination.find_elements(By.XPATH, ".//li/a[text()='>']")
            
            if not next_buttons:
                print("서비스 '>' 버튼을 찾을 수 없음")
                return False
            
            next_button = next_buttons[0]
            parent_li = next_button.find_element(By.XPATH, "./..")
            
            # disabled 상태 확인
            li_class = parent_li.get_attribute("class") or ""
            tabindex = next_button.get_attribute("tabindex") or "0"
            
            if "disabled" in li_class or tabindex == "-1":
                print("서비스 다음 페이지 버튼이 비활성화됨")
                return False
            
            # JavaScript 클릭
            self.driver.execute_script("arguments[0].click();", next_button)
            print("서비스 다음 페이지 버튼 클릭")
            
            # 페이지 변경 대기
            time.sleep(3)
            
            # 새 서비스 데이터 로딩 확인
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: len(driver.find_elements(By.XPATH, "//a[contains(@href, '/gig/')]")) > 0
                )
                print("새 서비스 페이지 로딩 완료")
                return True
            except:
                print("새 서비스 페이지 로딩 확인 실패")
                return False
                
        except Exception as e:
            print(f"서비스 다음 페이지 이동 실패: {e}")
            return False
            
    def crawl_services(self, seller_name, max_service_pages=3, max_services=10):
        """판매자의 서비스 정보 크롤링 - 페이지네이션 포함"""
        profile_url = f"https://kmong.com/@{seller_name}"
        
        try:
            self.driver.get(profile_url)
            time.sleep(3)
            
            # 서비스 탭 클릭
            service_tab_activated = self._activate_service_tab()
            if not service_tab_activated:
                print("서비스 탭 활성화 실패")
                return []
            
            # 서비스 목록 URLs 수집 (페이지네이션 포함)
            service_urls = self._get_service_list(max_pages=max_service_pages)
            
            if not service_urls:
                print("서비스 URL을 찾을 수 없음")
                return []
            
            # 제한된 수의 서비스만 처리 (너무 많으면 시간 오래 걸림)
            if max_services:
                service_urls = service_urls[:max_services]
            
            # 각 서비스 상세 정보 수집
            all_services = []
            for i, service_url in enumerate(service_urls, 1):
                print(f"서비스 {i}/{len(service_urls)} 처리: {service_url}")
                
                service_data = self.crawl_single_service(service_url)
                if service_data:
                    all_services.append(service_data)
                
                time.sleep(2)  # 서비스 간 대기
            
            return all_services
            
        except Exception as e:
            print(f"서비스 크롤링 실패: {e}")
            return []

    def _activate_service_tab(self):
        """서비스 탭 활성화"""
        service_tab_selectors = [
            "//button[contains(text(), '서비스') or contains(text(), 'Services')]",
            "//a[contains(text(), '포트폴리오') or contains(text(), 'Portfolio')]",
            "//*[@role='tab'][contains(text(), '서비스')]"
        ]
        
        for selector in service_tab_selectors:
            try:
                tab = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                self.driver.execute_script("arguments[0].click();", tab)
                time.sleep(3)
                
                # 서비스 목록이 로딩되었는지 확인
                WebDriverWait(self.driver, 10).until(
                    lambda driver: len(driver.find_elements(By.XPATH, "//a[contains(@href, '/gig/')]")) > 0
                )
                
                print("서비스 탭 활성화 성공")
                return True
                
            except:
                continue
        
        print("서비스 탭 활성화 실패")
        return False

    def _get_service_list(self, max_pages=5):
        """서비스 목록 URLs 수집 - 페이지네이션 포함"""
        all_service_urls = []
        current_page = 1
        
        try:
            # 서비스 섹션으로 스크롤
            service_section = self.driver.find_element(By.CLASS_NAME, "ProfileServiceListSection")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", service_section)
            time.sleep(2)
            print("서비스 섹션으로 스크롤 완료")
        except:
            print("서비스 섹션을 찾을 수 없음")
        
        while current_page <= max_pages:
            print(f"서비스 목록 페이지 {current_page} 수집 중...")
            
            try:
                # 현재 페이지의 서비스 URLs 수집
                page_urls = self._extract_service_urls_from_page()
                
                if not page_urls:
                    print("더 이상 서비스가 없습니다.")
                    break
                
                # 중복 제거하면서 추가
                new_urls = [url for url in page_urls if url not in all_service_urls]
                all_service_urls.extend(new_urls)
                
                print(f"페이지 {current_page}에서 {len(new_urls)}개 새 서비스 발견")
                
                # 다음 페이지로 이동
                if current_page < max_pages:
                    if not self._go_to_next_service_page():
                        break
                
                current_page += 1
                
            except Exception as e:
                print(f"서비스 페이지 {current_page} 수집 실패: {e}")
                break
        
        print(f"총 {len(all_service_urls)}개 서비스 URL 수집 완료")
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
            print(f"서비스 URL 추출 실패: {e}")
            return []
            
    def _extract_package_info(self):
        """패키지별 상세 정보 추출 - 완전 개선된 버전"""
        try:
            # aside 요소 찾기 (페이지에 하나만 있음)
            aside = self.driver.find_element(By.TAG_NAME, "aside")
            
            # 패키지 버튼들 확인
            package_buttons = aside.find_elements(
                By.XPATH, ".//button[contains(@class, 'flex h-[50px] w-[119px]')]"
            )
            
            if not package_buttons:
                # 단일 패키지 처리
                print("단일 패키지 감지")
                return self._extract_single_package_info(aside)
            else:
                # 다중 패키지 처리
                print(f"{len(package_buttons)}개 패키지 감지")
                return self._extract_multiple_packages_info(aside, package_buttons)
                
        except Exception as e:
            print(f"패키지 정보 추출 실패: {e}")
            return {}

    def _extract_single_package_info(self, aside):
        """단일 패키지 정보 추출"""
        try:
            # 가격 추출
            price_element = aside.find_element(
                By.XPATH, ".//div[contains(@class, 'text-[18px] font-bold leading-[27px]')]"
            )
            price = price_element.text.strip()
            
            # 패키지 제목 추출
            title_element = aside.find_element(
                By.XPATH, ".//p[contains(@class, 'text-[14px] font-bold text-gray-800')]"
            )
            title = title_element.text.strip()
            
            # 패키지 설명 추출
            description_element = aside.find_element(
                By.XPATH, ".//p[contains(@class, 'whitespace-pre-wrap text-sm leading-[21px]')]"
            )
            description = description_element.text.strip()
            
            # 상세 정보 추출
            details = self._extract_package_details(aside)
            
            return {
                'SINGLE': {
                    'price': price,
                    'title': title,
                    'description': description,
                    'details': details
                }
            }
            
        except Exception as e:
            print(f"단일 패키지 추출 실패: {e}")
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
                time.sleep(2)
                
                # 현재 활성화된 패키지 정보 추출
                package_info = self._extract_active_package_info(aside)
                
                if package_info:
                    packages[package_name] = package_info
                    print(f"{package_name} 패키지 정보 추출 완료")
                
            except Exception as e:
                print(f"{package_name} 패키지 추출 실패: {e}")
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
            details = self._extract_package_details(active_content)
            
            return {
                'price': price,
                'title': title,
                'description': description,
                'details': details
            }
            
        except Exception as e:
            print(f"활성 패키지 정보 추출 실패: {e}")
            return None

    def _extract_package_details(self, container):
        """패키지 상세 정보 추출 (체크박스 항목들 + 키-값 쌍들)"""
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
                        print(f"포함 기능: {left_text}")
                        
                    except:
                        # SVG가 없으면 값이 있는 항목
                        try:
                            right_text = item.find_elements(
                                By.XPATH, ".//p[contains(@class, 'text-sm')]"
                            )[1].text.strip()  # 두 번째 p 태그
                            
                            details['specifications'][left_text] = right_text
                            print(f"상세 정보: {left_text} = {right_text}")
                            
                        except:
                            # 값을 찾을 수 없는 경우 포함 기능으로 분류
                            details['included_features'].append(left_text)
                            
                except Exception as e:
                    print(f"개별 항목 추출 실패: {e}")
                    continue
            
            return details
            
        except Exception as e:
            print(f"패키지 상세 정보 추출 실패: {e}")
            return details

    def _extract_package_prices(self):
        """기존 메서드를 새로운 패키지 추출 메서드로 대체"""
        package_info = self._extract_package_info()
        
        # 기존 형식과의 호환성을 위해 가격만 추출
        prices = {}
        for package_name, info in package_info.items():
            if isinstance(info, dict) and 'price' in info:
                prices[package_name] = info['price']
        
        return prices

    # 전체 서비스 정보에 패키지 상세 정보 포함하도록 수정
    def crawl_single_service(self, service_url):
        """개별 서비스 페이지 크롤링 - 패키지 상세 정보 포함"""
        try:
            self.driver.get(service_url)
            time.sleep(3)
            
            service_data = {
                'service_url': service_url,
                'packages': self._extract_package_info(),  # 상세 정보 포함
                'skill_level': self._extract_skill_level(),
                'team_size': self._extract_team_size()
            }
            
            return service_data
            
        except Exception as e:
            print(f"서비스 페이지 크롤링 실패: {e}")
            return None

    def _extract_skill_level(self):
        """기술 수준 추출"""
        try:
            # id="10" 박스 찾기
            info_box = self.driver.find_element(By.XPATH, "//div[@id='10']")
            
            # 기술 수준 제목 찾기
            skill_titles = info_box.find_elements(By.XPATH, ".//*[contains(text(), '기술') or contains(text(), '수준') or contains(text(), 'Skill')]")
            
            for title in skill_titles:
                try:
                    # 제목 바로 밑의 값 찾기
                    value_span = title.find_element(By.XPATH, "./following-sibling::div/div/div/span")
                    skill_level = value_span.text.strip()
                    print(f"기술 수준: {skill_level}")
                    return skill_level
                except:
                    # 다른 구조 시도
                    try:
                        parent = title.find_element(By.XPATH, "./..")
                        value_span = parent.find_element(By.XPATH, ".//span")
                        skill_level = value_span.text.strip()
                        print(f"기술 수준: {skill_level}")
                        return skill_level
                    except:
                        continue
            
            print("기술 수준을 찾을 수 없음")
            return ""
            
        except Exception as e:
            print(f"기술 수준 추출 실패: {e}")
            return ""

    def _extract_team_size(self):
        """팀 규모 추출"""
        try:
            # id="10" 박스 찾기
            info_box = self.driver.find_element(By.XPATH, "//div[@id='10']")
            
            # 팀 규모 제목 찾기
            team_titles = info_box.find_elements(By.XPATH, ".//*[contains(text(), '팀') or contains(text(), '규모') or contains(text(), 'Team')]")
            
            for title in team_titles:
                try:
                    # 제목 바로 밑의 값 찾기
                    value_span = title.find_element(By.XPATH, "./following-sibling::div/div/div/span")
                    team_size = value_span.text.strip()
                    print(f"팀 규모: {team_size}")
                    return team_size
                except:
                    # 다른 구조 시도
                    try:
                        parent = title.find_element(By.XPATH, "./..")
                        value_span = parent.find_element(By.XPATH, ".//span")
                        team_size = value_span.text.strip()
                        print(f"팀 규모: {team_size}")
                        return team_size
                    except:
                        continue
            
            print("팀 규모를 찾을 수 없음")
            return ""
            
        except Exception as e:
            print(f"팀 규모 추출 실패: {e}")
            return ""

    def crawl_seller_profile_complete(self, seller_name, max_review_pages=2):
        """프로필 + 리뷰 + 서비스 통합 크롤링"""
        print(f"\n=== {seller_name} 전체 데이터 크롤링 시작 ===")
        
        # 1. 기본 프로필 정보
        profile_data = self.crawl_seller_profile(seller_name)
        
        # 2. 리뷰 크롤링
        try:
            reviews = self.crawl_reviews(seller_name, max_pages=max_review_pages)
            profile_data['reviews'] = reviews
            profile_data['total_reviews'] = len(reviews)
            print(f"리뷰 크롤링 완료: {len(reviews)}개")
        except Exception as e:
            print(f"리뷰 크롤링 실패: {e}")
            profile_data['reviews'] = []
            profile_data['total_reviews'] = 0
        
        # 3. 서비스 크롤링
        try:
            services = self.crawl_services(seller_name)
            profile_data['services'] = services
            profile_data['total_services'] = len(services)
            print(f"서비스 크롤링 완료: {len(services)}개")
        except Exception as e:
            print(f"서비스 크롤링 실패: {e}")
            profile_data['services'] = []
            profile_data['total_services'] = 0
        
        return profile_data