import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collect_trend import get_shopping_insight, get_blog_search, get_shopping_search
import os
from datetime import datetime
import re
from collections import Counter

# 페이지 설정
st.set_page_config(page_title="Naver Shopping Intelligence", layout="wide")

st.title("📊 Naver Shopping Data Intelligence Dashboard")
st.markdown("네이버 API를 활용한 실시간 쇼핑 트렌드 및 시장 분석 대시보드입니다.")

# 사이드바 설정
st.sidebar.header("🔍 검색 설정")
keyword = st.sidebar.text_input("분석할 키워드", value="오메가3")
category_id = st.sidebar.text_input("카테고리 ID (쇼핑인사이트용)", value="50000008")

# 데이터 수집 버튼
if st.sidebar.button("데이터 수집 및 분석 시작"):
    with st.spinner(f"'{keyword}' 데이터를 수집 중입니다..."):
        # 데이터 수집
        trend_df = get_shopping_insight(keyword, category_id)
        blog_df = get_blog_search(keyword)
        shop_df = get_shopping_search(keyword)
        
        if trend_df is not None and blog_df is not None and shop_df is not None:
            st.success("데이터 수집 완료!")
            
            # 탭 구성
            tab1, tab2, tab3, tab4 = st.tabs(["📈 트렌드 분석", "📝 블로그 인사이트", "🛒 쇼핑 시장 분석", "📂 원본 데이터"])
            
            # --- [Tab 1] 트렌드 분석 ---
            with tab1:
                st.subheader("실시간 쇼핑 검색 트렌드")
                fig_trend = px.line(trend_df, x='period', y='ratio', title=f"'{keyword}' 검색 비중 추이", 
                                   labels={'period': '날짜', 'ratio': '상대적 검색량'},
                                   line_shape='spline', markers=True)
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # 트렌드 통계 (테이블 1)
                col1, col2, col3 = st.columns(3)
                col1.metric("최대 검색량", f"{trend_df['ratio'].max():.2f}")
                col2.metric("최소 검색량", f"{trend_df['ratio'].min():.2f}")
                col3.metric("평균 검색량", f"{trend_df['ratio'].mean():.2f}")
                
                st.write("### 일별 트렌드 상세 (표 1)")
                st.dataframe(trend_df.sort_values('period', ascending=False), use_container_width=True)

            # --- [Tab 2] 블로그 인사이트 ---
            with tab2:
                st.subheader("관련 블로그 키워드 분석")
                
                # 키워드 정제 및 추출
                def get_top_keywords(df):
                    text = " ".join(df['title'].astype(str) + " " + df['description'].astype(str))
                    text = re.sub(r'<[^>]+>', '', text)
                    words = [w for w in re.sub(r'[^가-힣\s]', '', text).split() if len(w) > 1 and w != keyword]
                    return Counter(words).most_common(15)
                
                top_words = get_top_keywords(blog_df)
                word_df = pd.DataFrame(top_words, columns=['키워드', '빈도'])
                
                fig_words = px.bar(word_df, x='키워드', y='빈도', title="블로그 주요 언급 키워드 Top 15", color='빈도')
                st.plotly_chart(fig_words, use_container_width=True)
                
                st.write("### 최신 블로그 포스트 (표 2)")
                # 테이블 클렌징
                blog_display = blog_df[['title', 'bloggername', 'postdate', 'link']].copy()
                blog_display['title'] = blog_display['title'].str.replace(r'<[^>]+>', '', regex=True)
                st.dataframe(blog_display, use_container_width=True)

            # --- [Tab 3] 쇼핑 시장 분석 ---
            with tab3:
                st.subheader("네이버 쇼핑 시장 분석")
                
                shop_df['lprice'] = pd.to_numeric(shop_df['lprice'], errors='coerce')
                
                col_left, col_right = st.columns(2)
                
                with col_left:
                    # 가격 분포 히스토그램 (시각화 3)
                    fig_price = px.histogram(shop_df, x='lprice', title="상품 가격대 분포", 
                                            labels={'lprice': '가격(원)'}, color_discrete_sequence=['indianred'])
                    st.plotly_chart(fig_price, use_container_width=True)
                
                with col_right:
                    # 브랜드 점유율 파이 차트 (시각화 4)
                    brand_counts = shop_df['brand'].value_counts().head(8)
                    fig_brand = px.pie(values=brand_counts.values, names=brand_counts.index, title="주요 브랜드 점유율 (Top 8)")
                    st.plotly_chart(fig_brand, use_container_width=True)
                
                # 브랜드별 가격 박스 플롯 (시각화 5)
                top_brands = brand_counts.index.tolist()
                brand_price_df = shop_df[shop_df['brand'].isin(top_brands)]
                fig_box = px.box(brand_price_df, x='brand', y='lprice', title="주요 브랜드별 가격 범위 비교",
                                labels={'brand': '브랜드', 'lprice': '가격(원)'}, color='brand')
                st.plotly_chart(fig_box, use_container_width=True)
                
                st.write("### 브랜드별 시장 성과 (표 4)")
                brand_stats = shop_df.groupby('brand').agg(
                    상품수=('productId', 'count'),
                    평균가격=('lprice', 'mean'),
                    최저가=('lprice', 'min'),
                    최고가=('lprice', 'max')
                ).sort_values('상품수', ascending=False).head(10)
                st.table(brand_stats)

            # --- [Tab 4] 원본 데이터 ---
            with tab4:
                st.subheader("수집 원본 데이터 탐색기")
                
                st.write(f"#### '{keyword}' 쇼핑 검색 원본 (표 3)")
                st.dataframe(shop_df, use_container_width=True)
                
                st.write("#### 데이터 요약 (표 5)")
                st.write(shop_df.describe())
                
                # CSV 다운로드 버튼
                csv = shop_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="쇼핑 데이터 CSV 다운로드",
                    data=csv,
                    file_name=f"{keyword}_shopping_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime='text/csv',
                )
        else:
            st.error("데이터를 불러오지 못했습니다. API 설정이나 키워드를 확인해주세요.")
else:
    st.info("사이드바에서 키워드를 입력하고 '수집 시작' 버튼을 눌러주세요.")
    
    # 기본 예시 데이터로 안내 (선택 사항)
    st.markdown("""
    ### 대시보드 활용 가이드
    1. 왼쪽 사이드바에 분석하고 싶은 **키워드**를 입력합니다. (예: 오메가3, 비타민D, 단백질 쉐이크 등)
    2. 해당 키워드의 네이버 쇼핑 **카테고리 ID**를 입력하면 정확한 트렌드 분석이 가능합니다.
    3. '분석 시작' 버튼을 클릭하면 실시간으로 데이터를 수집하여 시각화합니다.
    """)
