import streamlit as st
import base64

# 페이지 설정
st.set_page_config(page_title="Fastpaper Instagram Preview", layout="wide")

# --- 1. CSS: 가로 슬라이드 및 세련된 디자인 ---
st.markdown("""
    <style>
    /* 인스타그램 스타일 가로 슬라이더 */
    .slide-container {
        display: flex;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        gap: 10px;
        padding-bottom: 15px;
        -webkit-overflow-scrolling: touch;
    }
    .slide-item {
        flex: 0 0 auto;
        scroll-snap-align: center;
        background: #000;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
    }
    .slide-item img, .slide-item video {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }
    /* 스크롤바 숨기기 */
    .slide-container::-webkit-scrollbar { display: none; }
    
    /* 인쇄 모드 최적화 (PDF 저장용) */
    @media print {
        .no-print { display: none !important; }
        .print-only { display: block !important; }
        .main { background: white !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 사이드바/좌측 세팅 ---
with st.sidebar if 'sidebar' in locals() else st.container(): # 왼쪽 영역
    if 'sidebar' not in locals():
        left_col, right_col = st.columns([1, 1.5])
    
    with left_col:
        st.title("⚙️ Setting")
        
        # 높이 조절 슬라이더
        img_height = st.slider("미리보기 이미지 높이 설정 (px)", 300, 800, 500)
        
        # 1. 썸네일 업로드
        st.subheader("1) 썸네일 후보 (3개)")
        thumb_files = st.file_uploader("썸네일 선택", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        
        # 2. 본문 소재 업로드
        st.subheader("2) 본문 소재 (이미지/영상)")
        content_files = st.file_uploader("본문 소재 선택", type=['png', 'jpg', 'jpeg', 'mp4', 'mov'], accept_multiple_files=True)
        if content_files:
            content_files = sorted(content_files, key=lambda x: x.name)

        # 3. 멘션 및 댓글
        mention_text = st.text_area("인스타그램 멘션", height=200)
        hashtag_text = st.text_area("댓글 해시태그", height=80)
        
        st.divider()
        # PDF 저장 버튼 (브라우저 인쇄창 호출)
        if st.button("📄 PDF 저장/인쇄 모드 실행"):
            st.write("콘트롤(Command) + P를 눌러 PDF로 저장하세요.")

# --- 3. 우측 미리보기 영역 ---
with right_col:
    st.title("📱 Instagram Preview")
    
    # 인스타그램 목업 박스
    with st.container():
        # 1) 썸네일 셀렉터
        if thumb_files:
            thumb_names = [f.name for f in thumb_files]
            selected_thumb_name = st.radio("시뮬레이션할 썸네일 선택", thumb_names, horizontal=True, key="thumb_radio")
            selected_thumb = next(f for f in thumb_files if f.name == selected_thumb_name)
            
            st.markdown("**[현재 적용된 썸네일]**")
            st.image(selected_thumb, width=200) # 작게 표시
            st.divider()

        # 2) 가로 슬라이더 (메인 소재)
        if content_files:
            st.markdown(f"**슬라이드 미리보기 (총 {len(content_files)}장) - 좌우로 밀어서 확인**")
            
            # HTML/CSS 기반 가로 슬라이더 생성
            slide_html = f'<div class="slide-container">'
            for f in content_files:
                # 파일을 base64로 변환하여 HTML에 삽입
                data = f.read()
                b64 = base64.b64encode(data).decode()
                mime = "video/mp4" if f.name.endswith(('mp4', 'mov')) else "image/jpeg"
                
                if "video" in mime:
                    tag = f'<video controls autoplay muted loop><source src="data:{mime};base64,{b64}"></video>'
                else:
                    tag = f'<img src="data:{mime};base64,{b64}">'
                
                slide_html += f'<div class="slide-item" style="width:{img_height}px; height:{img_height}px;">{tag}</div>'
            slide_html += '</div>'
            
            st.markdown(slide_html, unsafe_allow_html=True)
        else:
            st.info("파일을 업로드하면 슬라이드가 생성됩니다.")

        # 3) 멘션 및 댓글 영역
        st.markdown(f"""
            <div style="background: white; padding: 15px; border: 1px solid #eee; border-top: none;">
                <p><b>fastpaper_official</b> {mention_text.replace('\n', '<br>')}</p>
                <p style="color: #00376b;">{hashtag_text}</p>
            </div>
        """, unsafe_allow_html=True)
