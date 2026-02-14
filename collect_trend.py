import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

def get_headers():
    return {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
        "Content-Type": "application/json"
    }

def save_to_csv(df, title, category_name):
    """
    파일명 규칙: {내용}_{구분}_{날짜}.csv
    """
    today = datetime.now().strftime("%Y%m%d")
    folder_path = "naverapieda/data"
    os.makedirs(folder_path, exist_ok=True)
    
    filename = f"{category_name}_{title}_{today}.csv"
    file_path = os.path.join(folder_path, filename)
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"Saved: {file_path}")

def get_shopping_insight(category_name, category_id):
    """
    네이버 쇼핑인사이트 API를 통한 최근 1년 트렌드 수집
    """
    url = "https://openapi.naver.com/v1/datalab/shopping/categories"
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "date",
        "category": [{"name": category_name, "param": [category_id]}],
        "device": "",
        "ages": [],
        "gender": ""
    }
    
    response = requests.post(url, headers=get_headers(), data=json.dumps(body))
    if response.status_code == 200:
        data = response.json()
        if 'results' in data and data['results']:
            # 단일 카테고리 정보 추출
            result = data['results'][0]
            df = pd.DataFrame(result['data'])
            return df
    else:
        print(f"Error Shopping Insight: {response.status_code}")
    return None

def get_blog_search(keyword):
    """
    네이버 블로그 검색 API 수집
    """
    url = f"https://openapi.naver.com/v1/search/blog.json?query={keyword}&display=100"
    
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        items = response.json().get('items', [])
        return pd.DataFrame(items)
    else:
        print(f"Error Blog Search: {response.status_code}")
    return None

def get_shopping_search(keyword):
    """
    네이버 쇼핑 검색 API 수집
    """
    url = f"https://openapi.naver.com/v1/search/shop.json?query={keyword}&display=100"
    
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        items = response.json().get('items', [])
        return pd.DataFrame(items)
    else:
        print(f"Error Shopping Search: {response.status_code}")
    return None

def main():
    if not CLIENT_ID or not CLIENT_SECRET or "YOUR_CLIENT_ID" in CLIENT_ID:
        print("API 키가 설정되지 않았습니다. .env 파일을 확인해 주세요.")
        return

    targets = [
        {"name": "오메가3", "id": "50000008"}, # 건강식품 > 영양제 > 오메가3
        {"name": "비타민d", "id": "50007042"}, # 식품 > 건강식품 > 비타민제 > 비타민D
        {"name": "선글라스", "id": "50000183"} # 패션잡화 > 패션소품 > 선글라스
    ]
    
    for target in targets:
        print(f"--- Collecting data for: {target['name']} ---")
        # 트렌드 수집 및 저장
        trend_df = get_shopping_insight(target['name'], target['id'])
        if trend_df is not None:
            save_to_csv(trend_df, "트렌드", target['name'])
            
        # 블로그 수집 및 저장
        blog_df = get_blog_search(target['name'])
        if blog_df is not None:
            save_to_csv(blog_df, "블로그", target['name'])
            
        # 쇼핑 수집 및 저장
        shop_df = get_shopping_search(target['name'])
        if shop_df is not None:
            save_to_csv(shop_df, "쇼핑", target['name'])

if __name__ == "__main__":
    main()
