import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="서울시 따릉이 데이터 분석", layout="wide")

# 1. 데이터베이스 연결 확인
DB_PATH = 'bicycle.db'

def get_connection():
    if not os.path.exists(DB_PATH):
        st.error(f"⚠️ '{DB_PATH}' 파일을 찾을 수 없습니다. 같은 폴더에 bicycle.db 파일을 넣어주세요!")
        st.stop()
    return sqlite3.connect(DB_PATH)

st.title("🚲 공공자전거 이용현황 대시보드")
st.info("데이터베이스의 실시간 통계 정보를 바탕으로 차트와 인사이트를 생성합니다.")

conn = get_connection()

# --- 차트 1: 월별 이용패턴 ---
st.header("1. 월별 이용패턴")
query1 = """
SELECT 대여일자, SUM(이용건수) as 총이용건수
FROM 이용정보
GROUP BY 대여일자
ORDER BY 대여일자
"""
df1 = pd.read_sql(query1, conn)

col1_1, col1_2 = st.columns([2, 1])
with col1_1:
    fig1 = px.line(df1, x='대여일자', y='총이용건수', markers=True, title="월별 따릉이 총 이용건수 추이")
    st.plotly_chart(fig1, use_container_width=True)

with col1_2:
    max_month = df1.loc[df1['총이용건수'].idxmax()]
    st.subheader("🔍 SQL & Insight")
    st.code(query1, language='sql')
    st.write(f"- 데이터 분석 결과, 이용량이 가장 많았던 달은 **{max_month['대여일자']}**입니다.")
    st.write(f"- 해당 월의 총 이용건수는 약 **{max_month['총이용건수']:,}건**에 달합니다.")

st.divider()

# --- 차트 2: 기온별 평균 이용량 (5도 구간) ---
st.header("2. 기온별 평균 이용량 (5도 단위)")
# 5도 구간을 만들기 위해 SQLite의 CAST와 산술 연산을 활용합니다.
query2 = """
SELECT 
    (CAST(g.평균기온/5 AS INT) * 5) || '도 ~ ' || (CAST(g.평균기온/5 AS INT) * 5 + 5) || '도' as 기온구간,
    AVG(i.이용건수) as 평균이용건수
FROM 이용정보 i
JOIN 기온 g ON i.대여일자 = g.년월
GROUP BY CAST(g.평균기온/5 AS INT)
ORDER BY CAST(g.평균기온/5 AS INT)
"""
df2 = pd.read_sql(query2, conn)

col2_1, col2_2 = st.columns([2, 1])
with col2_1:
    fig2 = px.bar(df2, x='기온구간', y='평균이용건수', color='평균이용건수', title="평균기온 구간별 자전거 이용량")
    st.plotly_chart(fig2, use_container_width=True)

with col2_2:
    best_temp = df2.loc[df2['평균이용건수'].idxmax()]
    st.subheader("🔍 SQL & Insight")
    st.code(query2, language='sql')
    st.write(f"- 분석 결과 **{best_temp['기온구간']}** 사이에서 가장 활발한 이용 양상을 보입니다.")
    st.write("- 기온이 너무 낮거나 높으면 이용량이 급감하므로 계절적 요인이 뚜렷하게 반영됩니다.")

st.divider()

# --- 차트 3: 인기 대여소 TOP 10 ---
st.header("3. 인기 대여소 TOP 10")
query3 = """
SELECT b.보관소명, SUM(i.이용건수) as 총이용건수
FROM 이용정보 i
JOIN 대여소 b ON i.대여소번호 = b.대여소번호
GROUP BY b.대여소번호
ORDER BY 총이용건수 DESC
LIMIT 10
"""
df3 = pd.read_sql(query3, conn)

col3_1, col3_2 = st.columns([2, 1])
with col3_1:
    fig3 = px.bar(df3, x='총이용건수', y='보관소명', orientation='h', color='총이용건수',
                 color_continuous_scale='Blues', title="이용건수 상위 10개 대여소")
    fig3.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig3, use_container_width=True)

with col3_2:
    top_station = df3.iloc[0]['보관소명']
    st.subheader("🔍 SQL & Insight")
    st.code(query3, language='sql')
    st.write(f"- 현재 전체 대여소 중 가장 이용객이 몰리는 곳은 **{top_station}**입니다.")
    st.write("- 상위 10개 대여소는 주로 교통 요충지나 자전거 도로가 잘 갖춰진 지역에 위치합니다.")

conn.close()