import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="광고주 대시보드",
    page_icon="📊",
    layout="wide"
)

@st.cache_data(ttl=300)
def load_data():
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(st.secrets["SHEET_ID"]).worksheet(st.secrets["LOG_SHEET_NAME"])
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        if df.empty:
            return df
        
        df['기록일시'] = pd.to_datetime(df['기록일시'])
        return df
        
    except Exception as e:
        st.error(f"데이터 로드 실패: {str(e)}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("데이터가 없습니다")
    st.stop()

st.title("📊 광고주 대시보드")
st.caption(f"최종 업데이트: {df['기록일시'].max().strftime('%Y-%m-%d %H:%M')}")

st.sidebar.header("필터")
period = st.sidebar.selectbox("기간 선택", ["최근 4주", "최근 8주", "최근 12주", "전체"], index=0)

if period == "최근 4주":
    cutoff = datetime.now() - timedelta(weeks=4)
elif period == "최근 8주":
    cutoff = datetime.now() - timedelta(weeks=8)
elif period == "최근 12주":
    cutoff = datetime.now() - timedelta(weeks=12)
else:
    cutoff = df['기록일시'].min()

df_filtered = df[df['기록일시'] >= cutoff].copy()

col1, col2, col3, col4 = st.columns(4)
latest = df_filtered.iloc[-1]

with col1:
    st.metric("라이브 광고주 수", f"{latest['라이브_광고주수']:,}개")
with col2:
    st.metric("라이브 구독료 합계", f"{latest['라이브_구독료합계']:,.0f}원")
with col3:
    st.metric("준비중 광고주 수", f"{latest['준비중_광고주수']:,}개")
with col4:
    st.metric("준비중 구독료 합계", f"{latest['준비중_구독료합계']:,.0f}원")

st.divider()

st.subheader("주별 광고주 수 추이")
fig_count = go.Figure()
fig_count.add_trace(go.Scatter(
    x=df_filtered['주차'],
    y=df_filtered['라이브_광고주수'],
    mode='lines+markers',
    name='라이브',
    line=dict(color='#1f77b4', width=3),
    marker=dict(size=8)
))
fig_count.add_trace(go.Scatter(
    x=df_filtered['주차'],
    y=df_filtered['준비중_광고주수'],
    mode='lines+markers',
    name='준비중',
    line=dict(color='#ff7f0e', width=3),
    marker=dict(size=8)
))
fig_count.update_layout(
    height=400,
    hovermode='x unified',
    xaxis_title="주차",
    yaxis_title="광고주 수",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig_count, use_container_width=True)

st.subheader("주별 구독료 합계 추이")
fig_revenue = go.Figure()
fig_revenue.add_trace(go.Scatter(
    x=df_filtered['주차'],
    y=df_filtered['라이브_구독료합계'],
    mode='lines+markers',
    name='라이브',
    line=dict(color='#2ca02c', width=3),
    marker=dict(size=8)
))
fig_revenue.add_trace(go.Scatter(
    x=df_filtered['주차'],
    y=df_filtered['준비중_구독료합계'],
    mode='lines+markers',
    name='준비중',
    line=dict(color='#d62728', width=3),
    marker=dict(size=8)
))
fig_revenue.update_layout(
    height=400,
    hovermode='x unified',
    xaxis_title="주차",
    yaxis_title="구독료 합계 (원)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig_revenue, use_container_width=True)

with st.expander("원본 데이터 보기"):
    st.dataframe(df_filtered.sort_values('기록일시', ascending=False), use_container_width=True, hide_index=True)
