from src.crawler.crawler import SellersCrawler, ProfileCrawler

def main():
    choice = input("1. 카테고리 크롤링, 2. 프로필 크롤링, 3. 리뷰 크롤링, 4. 서비스 크롤링, 5. 전부다 : ")
    
    if choice in ['1', '5']:
        # 카테고리 크롤링
        print("=== 카테고리 크롤링 시작 ===")
        sellers_crawler = SellersCrawler()
        category_ids = [661, 663, 645, 605]
        
        try:
            all_sellers = sellers_crawler.crawl_multiple_categories(category_ids)
            sellers_crawler.save_data(all_sellers, 'all_sellers')
            print(f"카테고리 크롤링 완료: {len(all_sellers)}명")
        finally:
            sellers_crawler.close()
    
    if choice in ['2', '5']:
        # 프로필 크롤링
        print("\n=== 프로필 크롤링 시작 ===")
        profile_crawler = ProfileCrawler()
        
        try:
            profiles = profile_crawler.crawl_from_csv('output/all_sellers.csv', limit=3)
            print(f"프로필 크롤링 완료: {len(profiles)}명")
        finally:
            profile_crawler.close()

    if choice in ['3', '5']:
        # 리뷰 크롤링
        print("\n=== 프로필 크롤링 시작 ===")
        profile_crawler = ProfileCrawler()

        try:
            seller_names = ['두들코딩', '푸르미하우스', '트래픽최적화장인']  # 테스트용
            profiles = profile_crawler.crawl_multiple_profiles_with_reviews(
                seller_names, 
                max_review_pages=5
            )
            profile_crawler.save_data(profiles, 'profiles_with_reviews')
            print(f"프로필+리뷰 크롤링 완료: {len(profiles)}명")
        finally:
            profile_crawler.close()

    if choice in ['4', '5']:
        # 프로필 + 리뷰 + 서비스 크롤링
        profile_crawler = ProfileCrawler()
        try:
            # 전체 데이터 크롤링 (프로필 + 리뷰 + 서비스)
            seller_names = ['두들코딩', '푸르미하우스'] 
            
            all_data = []
            for seller in seller_names:
                complete_data = profile_crawler.crawl_seller_profile_complete(
                    seller, 
                    max_review_pages=5
                )
                all_data.append(complete_data)
            
            profile_crawler.save_data(all_data, 'complete_profiles')
            print(f"전체 크롤링 완료: {len(all_data)}명")
        finally:
            profile_crawler.close()

if __name__ == "__main__":
    main()