import streamlit as st
import base64

# 페이지 설정
st.set_page_config(page_title="Fastpapermag Preview System", layout="wide")

# --- 1. CSS & JavaScript (고해상도 캡처 및 UI 스타일링) ---
st.markdown("""
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
    function saveCapture() {
        const element = document.querySelector("#capture-area");
        html2canvas(element, {
            scale: 2,
            useCORS: true,
            backgroundColor: "#ffffff"
        }).then(canvas => {
            const link = document.createElement('a');
            link.download = 'fastpapermag_preview.jpg';
            link.href = canvas.toDataURL('image/jpeg', 0.9);
            link.click();
        });
    }
    </script>
    <style>
    /* 썸네일 후보 카드 스타일 */
    .thumb-card {
        border: 2px solid #eee;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        background: white;
    }
    .thumb-card.selected {
        border-color: #FF4B4B;
        background: #FFF5F5;
    }
    
    /* 가로 슬라이더 스타일 (메인) */
    .slide-container {
        display: flex;
        overflow-x: auto;
        gap: 15px;
        padding: 20px;
        background-color: #ffffff;
    }
    .slide-item {
        flex: 0 0 auto;
        background: #000;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #eee;
        border-radius: 4px;
        overflow: hidden;
    }
    .slide-item img, .slide-item video {
        max-height: 100%;
        object-fit: contain;
    }
    
    #capture-area {
        background: white;
        padding: 40px;
        width: fit-content;
        min-width: 1100px;
    }
    .insta-header {
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        font-family: sans-serif;
    }
    .profile-circle {
        width: 38px; height: 38px; border-radius: 50%;
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); 
        margin-right: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화 (선택된 썸네일 인덱스 저장)
if 'selected_thumb_idx' not in st.session_state:
    st.session_state.selected_thumb_idx = 0

# --- 2. 사이드바 (데이터 입력) ---
with st.sidebar:
    st.title("📂 Data Input")
    st.subheader("1) 이미지/영상 업로드")
    thumb_files = st.file_uploader("썸네일 후보 (최대 3개)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    content_files = st.file_uploader("본문 슬라이드 소스", type=['png', 'jpg', 'jpeg', 'mp4', 'mov'], accept_multiple_files=True)
    
    if content_files:
        content_files = sorted(content_files, key=lambda x: x.name)

    st.subheader("2) 텍스트 입력")
    mention_text = st.text_area("본문 멘션", height=150, placeholder="내용을 입력하세요...")
    hashtag_text = st.text_area("댓글 해시태그", height=80, placeholder="#태그 #입력")
    
    st.divider()
    if st.button("📸 결과물 JPG 다운로드"):
        st.components.v1.html("<script>saveCapture();</script>")

# --- 3. 메인 프리뷰 영역 ---
# 3-1. 썸네일 셀렉터 (상단 배치)
if thumb_files:
    st.subheader("🎯 썸네일 안 선택")
    cols = st.columns(len(thumb_files))
    for i, f in enumerate(thumb_files):
        with cols[i]:
            # 300px 높이로 썸네일 표시
            st.image(f, height=300, use_column_width=True)
            if st.button(f"{i+1}안 선택", key=f"btn_{i}", use_container_width=True):
                st.session_state.selected_thumb_idx = i
                st.rerun()
    st.divider()

# 3-2. 메인 미리보기 (캡처 영역)
st.markdown('<div id="capture-area">', unsafe_allow_html=True)

# 계정 헤더
st.markdown(f"""
    <div class="insta-header">
        <div class="profile-circle"></div>
        <span>fastpapermag</span>
    </div>
""", unsafe_allow_html=True)

# 미디어 병합 (선택된 썸네일 + 본문)
combined_media = []
if thumb_files:
    combined_media.append(thumb_files[st.session_state.selected_thumb_idx])
if content_files:
    combined_media.extend(content_files)

if combined_media:
    slide_html = '<div class="slide-container">'
    for i, f in enumerate(combined_media):
        f.seek(0)
        data = f.read()
        b64 = base64.b64encode(data).decode()
        mime = "video/mp4" if f.name.endswith(('mp4', 'mov')) else "image/jpeg"
        
        # 썸네일 표기 레이블
        label = '<div style="position:absolute; top:15px; left:15px; background:#FF4B4B; color:white; padding:4px 10px; font-size:12px; font-weight:bold; border-radius:4px;">SELECTED THUMBNAIL</div>' if i == 0 and thumb_files else ""
        
        if "video" in mime:
            tag = f'<video muted><source src="data:{mime};base64,{b64}"></video>'
        else:
            tag = f'<img src="data:{mime};base64,{b64}">'
        
        # 높이 500px 고정
        slide_html += f'<div class="slide-item" style="height:500px; position:relative;">{label}{tag}</div>'
    slide_html += '</div>'
    st.markdown(slide_html, unsafe_allow_html=True)
else:
    st.info("사이드바에서 파일을 업로드하면 프리뷰가 생성됩니다.")

# 텍스트 영역
st.markdown(f"""
    <div style="padding: 25px 0; border-top: 1px solid #eee; font-family: sans-serif;">
        <p style="font-size: 16px; line-height: 1.6;"><b>fastpapermag</b> {mention_text.replace('\\n', '<br>')}</p>
        <div style="margin-top: 30px; padding: 20px; background: #fafafa; border-radius: 8px;">
            <p style="color: #555; font-size: 14px; margin: 0;"><b>댓글태그</b></p>
            <p style="color: #00376b; font-size: 14px; margin-top: 8px;">{hashtag_text.replace('\\n', '<br>')}</p>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
