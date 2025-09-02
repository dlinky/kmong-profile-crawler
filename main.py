import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.crawler.crawler import SellersCrawler, ProfileCrawler

def log(message):
    print(f"[{datetime.now().strftime("%H:%M:%S.%f")[:-3]}] {message}")

def main():
    choice = input("1. 카테고리 크롤링, 2. 프로필 크롤링, 3. 리뷰 크롤링, 4. 서비스 크롤링, 5. 전부다 : ")
    
    if choice in ['1', '5']:
        # 카테고리 크롤링
        log("=== 카테고리 크롤링 시작 ===")
        sellers_crawler = SellersCrawler()
        category_ids = [661, 663, 645, 605]
        
        try:
            all_sellers = sellers_crawler.crawl_multiple_categories(category_ids)
            sellers_crawler.save_data(all_sellers, 'all_sellers')
            log(f"카테고리 크롤링 완료: {len(all_sellers)}명")
        finally:
            sellers_crawler.close()
    
    if choice in ['2', '5']:
        # 프로필 크롤링 (limit 제거)
        log("=== 프로필 크롤링 시작 ===")
        profile_crawler = ProfileCrawler()
        
        try:
            profiles = profile_crawler.crawl_from_csv('output/all_sellers.csv')  # limit 제거
            log(f"프로필 크롤링 완료: {len(profiles)}명")
        finally:
            profile_crawler.close()

    if choice in ['3', '5']:
        # 리뷰 크롤링 (CSV에서 모든 판매자 처리)
        log("=== 리뷰 크롤링 시작 ===")
        profile_crawler = ProfileCrawler()

        try:
            # CSV에서 모든 판매자 읽어오기
            import pandas as pd
            df = pd.read_csv('output/all_sellers.csv')
            seller_names = df['seller_name'].unique().tolist()
            
            profiles = profile_crawler.crawl_multiple_profiles_with_reviews(
                seller_names,  # 모든 판매자 처리
                max_review_pages=10  # 리뷰 제한 없이 (큰 숫자)
            )
            profile_crawler.save_data(profiles, 'profiles_with_reviews')
            log(f"프로필+리뷰 크롤링 완료: {len(profiles)}명")
        finally:
            profile_crawler.close()

    if choice in ['4', '5']:
        # 프로필 + 리뷰 + 서비스 크롤링 (모든 판매자 처리)
        print("\n=== 서비스 크롤링 시작 ===")
        profile_crawler = ProfileCrawler()
        try:
            # CSV에서 모든 판매자 읽어오기
            import pandas as pd
            df = pd.read_csv('output/all_sellers.csv')
            seller_names = df['seller_name'].unique().tolist()
            
            all_data = []
            for i, seller in enumerate(seller_names, 1):
                print(f"전체 크롤링 {i}/{len(seller_names)}: {seller}")
                complete_data = profile_crawler.crawl_seller_profile_complete(
                    seller, 
                    max_review_pages=10  # 리뷰 제한 해제
                )
                all_data.append(complete_data)
                
                # 50개마다 중간 저장
                if i % 50 == 0:
                    profile_crawler.save_data(all_data[-50:], f'complete_profiles_batch_{i//50}')
            
            profile_crawler.save_data(all_data, 'complete_profiles')
            log(f"전체 크롤링 완료: {len(all_data)}명")
        finally:
            profile_crawler.close()

if __name__ == "__main__":
    main()