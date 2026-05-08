import streamlit as st
import base64

# 페이지 설정
st.set_page_config(page_title="Fastpapermag Preview System", layout="wide")

# --- 1. CSS & JavaScript (고해상도 캡처 및 스타일링) ---
st.markdown("""
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <script>
    function saveCapture() {
        const element = document.querySelector("#capture-area");
        html2canvas(element, {
            scale: 2, // 고해상도 설정을 위해 스케일 업
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
    /* 가로 슬라이더 스타일 */
    .slide-container {
        display: flex;
        overflow-x: auto;
        gap: 10px;
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
    }
    .slide-item img, .slide-item video {
        max-height: 100%;
        object-fit: contain;
    }
    /* 캡처를 위한 전체 영역 스타일 */
    #capture-area {
        background: white;
        padding: 40px;
        width: fit-content;
        min-width: 1000px;
    }
    .insta-header {
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
    }
    .profile-circle {
        width: 35px; height: 35px; border-radius: 50%;
        background: #eee; margin-right: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. 사이드바 (설정창) ---
with st.sidebar:
    st.title("🚀 Fastpapermag Editor")
    
    # 1. 썸네일 업로드
    st.subheader("1) 썸네일 후보")
    thumb_files = st.file_uploader("썸네일 이미지 선택", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    # 2. 본문 소재 업로드
    st.subheader("2) 본문 소재")
    content_files = st.file_uploader("이미지/영상 선택", type=['png', 'jpg', 'jpeg', 'mp4', 'mov'], accept_multiple_files=True)
    if content_files:
        content_files = sorted(content_files, key=lambda x: x.name)

    # 3. 멘션 및 댓글
    st.subheader("3) 텍스트 입력")
    mention_text = st.text_area("본문 멘션", height=150)
    hashtag_text = st.text_area("댓글 태그", height=80)
    
    st.divider()
    # 캡처 버튼
    if st.button("📸 고해상도 JPG 다운로드 (2,000px급)"):
        st.components.v1.html("<script>saveCapture();</script>")

# --- 3. 메인 미리보기 영역 ---
left_col, right_col = st.columns([0.1, 0.9]) # 여백 조절

with right_col:
    # 썸네일 선택 라디오 (미리보기 위에 위치)
    selected_thumb = None
    if thumb_files:
        thumb_names = [f.name for f in thumb_files]
        choice = st.radio("미리보기에 적용할 썸네일 선택", thumb_names, horizontal=True)
        selected_thumb = next(f for f in thumb_files if f.name == choice)

    # 🖼️ 캡처 대상 영역 시작
    st.markdown('<div id="capture-area">', unsafe_allow_html=True)
    
    # 계정 정보 (fastpapermag)
    st.markdown(f"""
        <div class="insta-header">
            <div class="profile-circle"></div>
            <span>fastpapermag</span>
        </div>
    """, unsafe_allow_html=True)

    # 슬라이드 구성 (썸네일 + 본문)
    combined_media = []
    if selected_thumb:
        combined_media.append(selected_thumb)
    if content_files:
        combined_media.extend(content_files)

    if combined_media:
        # 가로 높이 500px 고정 슬라이더
        slide_html = '<div class="slide-container">'
        for i, f in enumerate(combined_media):
            f.seek(0) # 파일 포인터 초기화
            data = f.read()
            b64 = base64.b64encode(data).decode()
            mime = "video/mp4" if f.name.endswith(('mp4', 'mov')) else "image/jpeg"
            
            # 첫 번째 이미지(선택된 썸네일)에만 표시 추가
            label = '<div style="position:absolute; top:10px; left:10px; background:rgba(0,0,0,0.5); color:white; padding:2px 6px; font-size:12px;">Thumbnail</div>' if i == 0 and selected_thumb else ""
            
            if "video" in mime:
                tag = f'<video muted><source src="data:{mime};base64,{b64}"></video>'
            else:
                tag = f'<img src="data:{mime};base64,{b64}">'
            
            slide_html += f'<div class="slide-item" style="height:500px; position:relative;">{label}{tag}</div>'
        slide_html += '</div>'
        st.markdown(slide_html, unsafe_allow_html=True)
    else:
        st.info("왼쪽에서 파일을 업로드해 주세요.")

    # 하단 텍스트 영역
    st.markdown(f"""
        <div style="padding: 20px 0; border-top: 1px solid #eee;">
            <p style="font-size: 16px;"><b>fastpapermag</b> {mention_text.replace('\\n', '<br>')}</p>
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px dashed #ddd;">
                <p style="color: #666; font-size: 14px;"><b>댓글태그</b><br>{hashtag_text.replace('\\n', '<br>')}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True) # 캡처 영역 끝
