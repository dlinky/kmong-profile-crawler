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
        """데이터 저장"""
        if not data:
            return

        df = pd.DataFrame(data)
        df.to_csv(f'output/{filename}.csv', mode='a', header=not pd.io.common.file_exists(f'output/{filename}.csv'), index=False, encoding='utf-8-sig')
    
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
    
    def _extract_specialties(self):
        """전문분야 및 상세분야 추출 (IT·프로그래밍만)"""
        print("전문분야 추출")
        try:
            # 전문분야 섹션 찾기
            section_titles = self.driver.find_elements(By.CLASS_NAME, "ProfileSectionTitle")
            
            for title in section_titles:
                if "전문분야 및 상세분야" in title.text:
                    # 형제 요소에서 전문분야들 찾기
                    parent = title.find_element(By.XPATH, "./..")
                    specialties = parent.find_elements(By.CLASS_NAME, "ProfileSkillSection__specialty")
                    
                    for specialty in specialties:
                        specialty_title = specialty.text.strip()
                        if "IT·프로그래밍" in specialty_title:
                            print(f"IT·프로그래밍 전문분야 발견: {specialty_title}")
                            # 해당 전문분야의 태그들 추출
                            try:
                                # 전문분야 다음의 태그들 찾기
                                parent_section = specialty.find_element(By.XPATH, "./../../..")
                                tags = parent_section.find_elements(By.CLASS_NAME, "ProfileSkillSection__tag")
                                tag_texts = [tag.text.strip() for tag in tags if tag.text.strip()]
                                return tag_texts
                            except Exception as e:
                                print(f"전문분야 태그 추출 실패: {e}")
                                return []
            
            print("IT·프로그래밍 전문분야를 찾을 수 없습니다.")
            return []
            
        except Exception as e:
            print(f"전문분야 추출 실패: {e}")
            return []
    
    def _extract_section_data(self, section_title, tag_class):
        """섹션별 데이터 추출 공통 함수"""
        try:
            # 섹션 제목들 찾기
            section_titles = self.driver.find_elements(By.CLASS_NAME, "ProfileSectionTitle")
            
            for title in section_titles:
                if section_title in title.text:
                    print(f"{section_title} 섹션 발견")
                    # 형제 요소에서 태그들 찾기
                    parent = title.find_element(By.XPATH, "./..")
                    try:
                        tag_group = parent.find_element(By.CLASS_NAME, "ProfileSkillSection_tag-group")
                        tags = tag_group.find_elements(By.CLASS_NAME, tag_class)
                        tag_texts = [tag.text.strip() for tag in tags if tag.text.strip()]
                        print(f"{section_title} 추출 완료: {len(tag_texts)}개")
                        return tag_texts
                    except Exception as e:
                        print(f"{section_title} 태그 추출 실패: {e}")
                        return []
            
            print(f"{section_title} 섹션을 찾을 수 없습니다.")
            return []
            
        except Exception as e:
            print(f"{section_title} 추출 실패: {e}")
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
    
    def crawl_from_csv(self, csv_file_path):
        """CSV 파일에서 판매자명을 읽어와서 프로필 크롤링"""
        try:
            df = pd.read_csv(csv_file_path)
            seller_names = df['seller_name'].unique().tolist()  # 중복 제거
            print(f"CSV에서 {len(seller_names)}명의 판매자 발견")
            
            profiles = self.crawl_multiple_profiles(seller_names)
            
            # 전체 결과 저장
            self.save_data(profiles, 'all_profiles')
            
            return profiles
            
        except Exception as e:
            print(f"CSV 파일 읽기 실패: {e}")
            return []