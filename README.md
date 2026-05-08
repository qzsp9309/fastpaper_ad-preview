import streamlit as st

# 페이지 설정 (와이드 모드)
st.set_page_config(page_title="Fastpaper Ad Preview", layout="wide")

# CSS로 인스타그램 느낌의 폰트와 스타일링 추가
st.markdown("""
    <style>
    .insta-card {
        border: 1px solid #dbdbdb;
        border-radius: 8px;
        padding: 20px;
        background-color: white;
    }
    .thumbnail-overlay {
        position: relative;
        text-align: center;
        color: white;
    }
    .overlay-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: rgba(0,0,0,0.5);
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. 상단 정보 섹션 ---
st.title("📢 포스팅 프리뷰")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("업로드 일정", "5월 12일 19:00")
with col2:
    st.write("**포스트 타입**")
    st.info("피드 + 스토리")
with col3:
    notice = "이번 포스팅은 톰보이 1999 무드를 강조했습니다." # 공란일 경우 처리 가능
    if notice:
        st.warning(f"기타 안내: {notice}")

st.divider()

# --- 2. 썸네일 및 슬라이드 섹션 ---
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("1) 썸네일 시뮬레이션")
    thumb_choice = st.radio("적용해볼 썸네일 선택", ["1안 (메인)", "2안 (서브)", "3안 (클로즈업)"], horizontal=True)
    
    st.subheader("3) 멘션 & 댓글")
    st.text_area("인스타그램 멘션", value="스튜디오 톰보이가 응답한 1999 🍀\n그 해 여름을 넘어...", height=150)
    st.code("#Tomboy #1999 #Dailylook", language=None) # 댓글 해시태그 영역

with right_col:
    st.subheader("2) 피드 미리보기")
    with st.container():
        # 인스타그램 카드 형태 구현
        st.markdown('<div class="insta-card">', unsafe_allow_html=True)
        
        # 첫 장(썸네일) 음영 처리 예시
        st.markdown(f"""
            <div class="thumbnail-overlay">
                <img src="이미지주소" style="width:100%">
                <div class="overlay-text">선택된 {thumb_choice} 적용 예시</div>
            </div>
        """, unsafe_allow_html=True)
        
        # 슬라이드 기능 (여기서는 단순 이미지 나열 대신 st.image 리스트로 구성 가능)
        st.markdown('</div>', unsafe_allow_html=True)
