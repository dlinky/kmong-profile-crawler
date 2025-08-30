from src.crawler.crawler import SellersCrawler, ProfileCrawler

def main():
    choice = input("1. 카테고리 크롤링, 2. 프로필 크롤링, 3. 둘 다: ")
    
    if choice in ['1', '3']:
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
    
    if choice in ['2', '3']:
        # 프로필 크롤링
        print("\n=== 프로필 크롤링 시작 ===")
        profile_crawler = ProfileCrawler()
        
        try:
            profiles = profile_crawler.crawl_from_csv('output/all_sellers.csv')
            print(f"프로필 크롤링 완료: {len(profiles)}명")
        finally:
            profile_crawler.close()

if __name__ == "__main__":
    main()