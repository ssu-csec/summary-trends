import os
import requests
from pytrends.request import TrendReq
from openai import OpenAI
from googlesearch import search

from dotenv import load_dotenv

load_dotenv()

# OpenAI 클라이언트 설정
client = OpenAI(
    api_key=os.getenv("UPSTAGE_API_KEY"),  # 환경 변수에서 API 키 읽기
    base_url="https://api.upstage.ai/v1/solar"
)

# Google Trends 데이터 가져오기
def get_google_trends(country):
    pytrends = TrendReq()
    
    # 국가별 코드 설정
    country_code_map = {
        "US": "united_states",
        "KR": "south_korea",
        "JP": "japan",
        "HK": "hong_kong"
    }
    
    if country not in country_code_map:
        raise ValueError(f"Unsupported country code: {country}")
    
    country_code = country_code_map[country]
    trending_searches_df = pytrends.trending_searches(pn=country_code)
    
    return trending_searches_df.head(5).values.flatten().tolist()

# 뉴스 기사 및 블로그 검색
def search_news_and_blogs(keyword):
    query = f"{keyword} 뉴스 OR 블로그"
    search_results = search(query, num=5, stop=5)
    return search_results

# Solar API를 통해 트렌드 요약 및 이슈 설명 얻기
def summarize_trends_issues(trends, country):
    trend_issues = {}
    
    for trend in trends:
        # 뉴스 및 블로그 검색
        search_results = search_news_and_blogs(trend)
        search_results_text = "\n".join(search_results)
        
        # Solar API를 통해 요약 및 설명
        prompt = (
            f"다음은 '{trend}'에 대한 뉴스 기사 및 블로그 검색 결과입니다:\n\n"
            f"{search_results_text}\n\n"
            "이 트렌드가 왜 이슈가 되고 있는지 요약하고 설명해 주세요."
        )
        
        response = client.chat.completions.create(
            model="solar-1-mini-chat",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            stream=False,
        )
        
        trend_issues[trend] = response.choices[0].message.content
    
    return trend_issues

# 사용자 입력을 받아서 처리하는 함수
def process_user_input(user_input):
    # 국가별 키워드 맵핑
    country_keyword_map = {
        "한국": "KR",
        "미국": "US",
        "일본": "JP",
        "홍콩": "HK"
    }
    
    for country_keyword, country_code in country_keyword_map.items():
        if country_keyword in user_input:
            return country_code
    
    return None

# 메인 함수
def main():
    while True:
        # 사용자 입력 받기
        user_input = input("어느 나라의 트렌드를 알고 싶으신가요? (예: '한국의 현재 트렌드를 알려줘')\n")
        
        # 사용자 입력 처리
        country = process_user_input(user_input)
        
        if country:
            try:
                # Google Trends 데이터 가져오기
                trends = get_google_trends(country)
                
                if trends:
                    # 트렌드 요약 및 이슈 설명 얻기
                    trend_issues = summarize_trends_issues(trends, country)
                    
                    # 결과 출력
                    print(f"=== {country}의 트렌드 요약 및 설명 ===")
                    for trend, issue in trend_issues.items():
                        print(f"\n--- {trend} ---")
                        print(issue)
                else:
                    print(f"{country}의 트렌드를 가져오는 데 실패했습니다.")
            except ValueError as e:
                print(e)
        else:
            print("지원되지 않는 국가입니다. 한국, 미국, 일본, 홍콩 중에서 선택해 주세요.")

if __name__ == "__main__":
    main()
