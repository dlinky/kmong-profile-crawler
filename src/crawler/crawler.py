from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import json
from datetime import datetime
import time
import re
from bs4 import BeautifulSoup
import csv
from random import random

def log(message):
    print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {message}")
class BaseCrawler:
    def __init__(self):
        time.sleep(random())
        self.driver = self._setup_driver()

    def _setup_driver(self):
        options = Options()
        # options.add_argument('headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(2)

        return driver
    
    def _extract_with_soup(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            return soup
        except Exception as e:
            log(f"파싱 실패: {e}")
            return None
        
    def save_data(self, data, filename, columns=None):
        if not data:
            return
        
        df = pd.DataFrame(data, columns=columns)
        filepath = f'output/{filename}.csv'

        df.to_csv(filepath, mode='w', header=True, index=False, encoding='utf-8-sig')
        log(f"데이터 저장 완료: {filepath} ({len(data)}개 레코드)")
    
    def close(self):
        if self.driver:
            self.driver.quit()
    
class CategoryCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.driver.get("https://kmong.com/category/661")
        time.sleep(1)
    
    def _parse_service_amount(self):
        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'css-enj2mu')))
        service_amount = int(self.driver.find_element(By.CLASS_NAME, 'css-enj2mu').text.replace("개의 서비스",""))
        return service_amount
    
    def _extract_service_infos(self):
        info_list = []
        soup = self._extract_with_soup()
        if soup is None:
            return None
        service_list = soup.find_all("article", class_="edqw2x10")
        
        for service in service_list:
            title = service.find("span", class_="text-[14px] font-bold leading-[21px] text-gray-900 mb-1 line-clamp-2").text
            seller = service.find("span", "line-clamp-1 text-xs font-normal leading-[18px] text-gray-600").text
            link = service.find("a").attrs['href']
            # log([title, seller, link])
            info_list.append([title, seller, link])

        return info_list

    def crawl_category(self, category_id):
        service_list = []
        page_idx = 1
        service_amount = self._parse_service_amount()
        
        self.driver.get(f"https://kmong.com/category/{category_id}")

        while True:
            log(f"Page {page_idx}")

            # 서비스 목록 파싱
            WebDriverWait(self.driver, 10).until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'edqw2x10')))

            info_list = self._extract_service_infos()

            if isinstance(info_list, list):
                service_list.extend(info_list)
            else:
                log("파싱한 내용이 리스트가 아닙니다.")
            log(f"[{len(service_list)}/{service_amount}]")

            try:
                box = self.driver.find_element(By.CLASS_NAME, "e1t3wbc50")
                next_page_btn = box.find_elements(By.TAG_NAME, "button")[-1]
                if next_page_btn.is_enabled():
                    next_page_btn.click()
                else:
                    self.save_data(service_list, f"services_in_{category_id}")
                    return service_amount, service_list
            except Exception as e:
                log("단일 페이지입니다.")
                return service_amount, service_list

            time.sleep(0.5+random())
            page_idx += 1
        
    def save_result(self, all_service_infos):
        self.save_data(all_service_infos, "services", ['서비스명', '판매자', '링크'])

class ProfileCrawler(BaseCrawler):
    def __init__(self, seller_names=None):
        super().__init__()
        self.driver.get("https://kmong.com/category/661")
        time.sleep(1)
        if seller_names is not None:
            self.seller_names = seller_names
        else:
            self.seller_names = self._get_seller_names()
        log(f"{len(self.seller_names)}명의 판매자 정보를 수집합니다.")

    def _get_seller_names(self):
        df = pd.read_csv('./output/services.csv')
        seller_names = df['판매자'].unique()
        return seller_names
    
    def crawl_profile(self, seller_name):
        profile_url = f"https://kmong.com/@{seller_name}"
        self.driver.get(profile_url)
        time.sleep(0.7+random())

        soup = self._extract_with_soup()

        career, specialties, skills = self._extract_spec(soup)

        profile_data = {
            'seller_name': seller_name,
            'profile_url': profile_url,
            'introduction': self._extract_introduction(soup),
            'career': career,
            'specialties': specialties,
            'skills': skills,
            'total_jobs': self._extract_total_jobs(soup),
            'reviews': self._extract_reviews(),
            'portfolios': self._extract_portfolios(seller_name)
        }
        return profile_data
    
    def _extract_introduction(self, soup):
        try:
            intro_element = soup.find('div', 'ProfileDescriptionSection__desctiption')
            if intro_element:
                # log(f"자기소개 추출 성공")
                return intro_element.text.strip()
            else:
                log(f"자기소개 추출 실패: 자기소개 텍스트가 없습니다.")
                return ""
        except Exception as e:
            log(f"자기소개 추출 실패: {e}")
            return ""

    def _extract_spec(self, soup):
        spec_div = soup.find('div', 'DescriptionDetailSection')
        career = self._extract_section_data(spec_div, '경력사항')
        specialties = self._extract_section_data(spec_div, "전문분야 및 상세분야")
        skills = self._extract_section_data(spec_div, '보유 기술')

        return career, specialties, skills

    def _extract_section_data(self, div, section_title):
        try:
            if section_title == "전문분야 및 상세분야":
                specialty_dict = {}
                root_div = div.find('div', 'ProfileSkillSection__specialty')
                title_divs = root_div.find_all('div', 'ProfileSkillSection__title')
                for title_div in title_divs:
                    title = title_div.text.strip()
                    parent_div = title_div.parent
                    if parent_div:
                        tags = parent_div.find_all('div', 'ProfileSkillSection__tag')
                        tag_texts = [tag.text.strip() for tag in tags if tag.text.strip()]
                        specialty_dict[title] = tag_texts
                        if tag_texts:
                            # log(f"{title} 추출 완료 : {len(tag_texts)}개")
                            pass
                        else:
                            log(f"{title}: 태그 내용이 없습니다.")
                    else:
                        log(f"{title}: 부모 div를 찾을 수 없습니다.")
                specialty_len = 0
                for specialties in specialty_dict.values():
                    specialty_len += len(specialties)
                # log(f"{section_title} 추출 완료: {specialty_len}개")
                return specialty_dict

            else:
                title_divs = div.find_all('div', 'ProfileSectionTitle')
                for title_div in title_divs:
                    if title_div.text.strip() == section_title:
                        parent_div = title_div.parent
                        if parent_div:
                            tags = parent_div.find_all('div', 'ProfileSkillSection__tag')
                            tag_texts = [tag.text.strip() for tag in tags if tag.text.strip()]
                            if tag_texts:
                                # log(f"{section_title} 추출 완료: {len(tag_texts)}개")
                                return tag_texts
            pass
        except Exception as e:
            log(f"{section_title} 추출 불가 : {e}")

    def _extract_total_jobs(self, soup):
        try:
            profile_div = soup.find('div', 'ProfileInformationSection__section')
            description_divs = profile_div.find_all('span', 'ProfileInformationSection__section-infomation-description')
            for description_div in description_divs:
                # log(f"총 작업 수 : {description_div.text}")
                if "개" in description_div.text.strip():
                    return description_div.text.strip().replace("개","")
        except Exception as e:
            log(f"총 작업 수를 찾을 수 없습니다. : {e}")

    def _extract_reviews(self):
        reviews = []

        try:
            while True:
                try:

                    soup = self._extract_with_soup()
                    cards = soup.find_all('div', 'RatingList')
                    for card in cards:
                        date = card.find('span', 'RatingList__rating-user-info').text[:8]

                        service_div = card.find('div', 'RatingList__buyer-selling-service-gig-info')
                        service_title = service_div.select_one('*:nth-child(1) > *:nth-child(1)').text.strip()
                        period = service_div.select_one('*:nth-child(1) > *:nth-child(2)').text.strip().replace("| ", "")
                        price = service_div.select_one('*:nth-child(2)').text.strip().replace("주문 금액 범위 : ", "")
                        reviews.append([date, service_title, period, price])
            
                except Exception as e:
                    log(f"리뷰 추출 실패 : {e}")
                    return None
                
                try:
                    review_section = self.driver.find_element(By.CLASS_NAME, "ProfileRateEvaluationSection__list-group")
                    pagination = review_section.find_element(By.CLASS_NAME, "pagination")
                    next_button = pagination.find_element(By.XPATH, './li[last()]/a')
                    if next_button.get_attribute("tabindex") == "-1":
                        return reviews
                    else:
                        self.driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(1)
                except Exception as e:
                    log(f"단일 페이지입니다.")
                    return reviews
        except Exception as e:
            log(f"리뷰 추출 실패 : {e}")
            return None

    def _extract_portfolios(self, seller_name):
        self.driver.get(f"https://kmong.com/@{seller_name}/portfolios")
        try:
            portfolios = []
            blank_page_tag = self.driver.find_element(By.TAG_NAME, "b")
            if blank_page_tag.text=="404":
                log(f"포트폴리오가 없습니다.")
                return None
            
            soup = self._extract_with_soup()
            if soup:
                cards = soup.find_all('arcticle')
                for card in cards:
                    portfolio = {'title', 'hashtag', 'link'}
                    portfolio['link'] = card.find('a').attrs['href']
                    card_texts = card.find_all('p')
                    if isinstance(card_texts, list) and len(card_texts)==2:
                        portfolio['title'] = card_texts[0]
                        portfolio['hashtag'] = card_texts[1]
                    portfolios.append(portfolio)
            return portfolios
                
        except Exception as e:
            log(f"포트폴리오 추출 실패 : {e}")
            return None
    
    def save_result(self, all_service_infos):
        self.save_data(all_service_infos, "sellers", ['판매자', '주소', '소개', '경력', '전문분야', '보유 기술', '총 작업 수', '서비스', '리뷰'])