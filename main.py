import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.crawler.crawler import CategoryCrawler, ProfileCrawler
from datetime import datetime
import time
import pandas as pd

from multiprocessing import Pool

def log(message):
    print(f"[{datetime.now().strftime("%H:%M:%S.%f")[:-3]}] {message}")

def get_seller_names():
    df = pd.read_csv('./output/services.csv')
    seller_names = df['판매자'].unique()
    return seller_names

def crawl_profiles(seller_names=None):
    profile_crawler = ProfileCrawler(seller_names=seller_names)
    profiles = []

    for seller_idx, seller_name in enumerate(profile_crawler.seller_names):
        log(f"{seller_name} [{seller_idx+1}/{len(profile_crawler.seller_names)}]")
        profile = profile_crawler.crawl_profile(seller_name)
        profiles.append(profile)

    return profiles

def main():
    choice = input("1. 카테고리별 판매자 크롤링\n2. 판매자별 프로필, 리뷰 크롤링\n3. 서비스 정보 크롤링\n4. 데이터 정제\n5. All-in-One\n: ")
    process_count = 3
    # process_count = input("가동할 프로세스 수를 입력하세요(기본=1) :")
    try:
        process_count = int(process_count)
    except:
        if process_count == "":
            process_count = 1
        else:
            log(f"프로세스 수는 숫자를 입력해야 합니다.")
            return

    if choice in ['1', '5']:
        log("=== 카테고리별 판매자 크롤링 시작 ===")
        category_ids = input("검색할 카테고리 id를 입력하세요 (기본값 : [605, 661, 663, 645])\n: ")
        if category_ids == "":
            category_ids = [605, 661, 663, 645]

        category_crawler = CategoryCrawler()

        all_service_infos = []
        try:
            for category_id in category_ids:
                service_amount, service_list = category_crawler.crawl_category(category_id)
                all_service_infos.extend(service_list)
                log(f"카테고리 {category_id} : 총 {service_amount}개 서비스 수집 완료")
            
            category_crawler.save_result(all_service_infos)
        except Exception as e:
            log(f"카테고리 크롤링 실패: {e}")
    elif choice in ['2', '5']:
        log("=== 판매자별 프로필, 리뷰 크롤링 시작 ===")
        merged_profiles = []
        seller_names = get_seller_names()
        chunk_size = len(seller_names) // process_count
        seller_name_chunks = []
        for i in range(process_count):
            start_idx = i*chunk_size
            if i==process_count - 1:
                end_idx = len(seller_names)
            else:
                end_idx = (i+1)*chunk_size
            seller_name_chunks.append(seller_names[start_idx:end_idx])

        if process_count > 1:
            pool = Pool(processes=process_count)
            results = pool.map(crawl_profiles, seller_name_chunks)
            for result in results:
                merged_profiles.extend(result)
        else:
            merged_profiles = crawl_profiles()

        df = pd.DataFrame(merged_profiles)
        print(df)
        df.to_csv('output/profiles.csv', mode='w', header=True, index=False, encoding='utf-8-sig')
        log(f"판매자 {len(seller_names)}명 : 총 {len(merged_profiles)}개 프로필 수집 완료")
        
    else:
        log(f"에러입니다.")

if __name__ == "__main__":
    main()