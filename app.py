import streamlit as st
import base64

# 페이지 설정
st.set_page_config(page_title="Fastpapermag Preview System", layout="wide")

# --- 1. CSS (스타일링 최적화) ---
st.markdown("""
    <style>
    /* 1. 그리드 레이아웃 (한 줄에 5개) */
    .content-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px; /* 여백 최소화 */
        background-color: #ffffff;
        padding: 10px 0;
    }
    .grid-item {
        width: 100%;
        background: #000;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #eee;
        overflow: hidden;
    }
    .grid-item img, .grid-item video {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }
    
    /* 2. 썸네일 선택 영역 (여백 제거) */
    .thumb-image-container {
        width: 100%;
        height: 300px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f9f9f9;
        margin-bottom: 5px;
    }
    .thumb-image-container img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }

    /* 3. 인스타그램 헤더 및 텍스트 스타일 */
    .insta-header {
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        font-family: sans-serif;
    }
    .profile-circle {
        width: 35px; height: 35px; border-radius: 50%;
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); 
        margin-right: 12px;
    }
    .thumb-caption {
        font-size: 14px;
        color: #555;
        margin-top: 5px;
        text-align: center;
        min-height: 20px;
    }
    </style>
""", unsafe_allow_html=True)

if 'selected_thumb_idx' not in st.session_state:
    st.session_state.selected_thumb_idx = 0

# --- 2. 사이드바 (데이터 입력) ---
with st.sidebar:
    st.title("📂 Fastpapermag Editor")
    
    st.subheader("1) 썸네일 설정")
    thumb_files = st.file_uploader("썸네일 이미지 (최대 3개)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    # 썸네일 문구 입력창 (최대 3개)
    thumb_texts = []
    for i in range(3):
        txt = st.text_input(f"{i+1}안 썸네일 문구", key=f"thumb_txt_{i}")
        thumb_texts.append(txt)

    st.subheader("2) 본문 소재")
    content_files = st.file_uploader("이미지/영상 업로드", type=['png', 'jpg', 'jpeg', 'mp4', 'mov'], accept_multiple_files=True)
    if content_files:
        content_files = sorted(content_files, key=lambda x: x.name)

    st.subheader("3) 텍스트 입력")
    mention_text = st.text_area("본문 멘션", height=150)
    hashtag_text = st.text_area("댓글 해시태그", height=80)

# --- 3. 메인 미리보기 영역 ---

# 3-1. 상단 썸네일 셀렉터
if thumb_files:
    st.subheader("🎯 썸네일 안 선택")
    num_thumbs = len(thumb_files)
    cols = st.columns(num_thumbs)
    
    for i in range(num_thumbs):
        with cols[i]:
            f = thumb_files[i]
            f.seek(0)
            t_data = f.read()
            t_b64 = base64.b64encode(t_data).decode()
            
            # 썸네일 이미지 노출 (여백 최소화)
            st.markdown(f"""
                <div class="thumb-image-container">
                    <img src="data:image/jpeg;base64,{t_b64}">
                </div>
            """, unsafe_allow_html=True)
            
            # 버튼 및 문구 노출
            if st.button(f"{i+1}안 선택", key=f"btn_{i}", use_container_width=True):
                st.session_state.selected_thumb_idx = i
                st.rerun()
            
            # 썸네일 문구 노출 (내용이 있을 때만)
            if i < len(thumb_texts) and thumb_texts[i]:
                st.markdown(f'<div class="thumb-caption">{thumb_texts[i]}</div>', unsafe_allow_html=True)
    st.divider()

# 3-2. 그리드 미리보기 영역
st.container()
st.markdown(f"""
    <div class="insta-header">
        <div class="profile-circle"></div>
        <span>fastpapermag</span>
    </div>
""", unsafe_allow_html=True)

# 소재 병합
combined_media = []
if thumb_files:
    combined_media.append(thumb_files[st.session_state.selected_thumb_idx])
if content_files:
    combined_media.extend(content_files)

if combined_media:
    # 한 줄에 5개씩 배치되는 그리드 시작
    st.markdown('<div class="content-grid">', unsafe_allow_html=True)
    
    # 5개씩 끊어서 행 생성 (Streamlit의 특성상 HTML 스트링으로 한꺼번에 구성)
    grid_html = ""
    for i, f in enumerate(combined_media):
        f.seek(0)
        data = f.read()
        b64 = base64.base64encode(data).decode()
        mime = "video/mp4" if f.name.endswith(('mp4', 'mov')) else "image/jpeg"
        
        if "video" in mime:
            tag = f'<video muted loop autoplay><source src="data:{mime};base64,{b64}"></video>'
        else:
            tag = f'<img src="data:{mime};base64,{b64}">'
        
        # 높이는 500px 유지하되 너비는 그리드에 맞춤
        grid_html += f'<div class="grid-item" style="height:500px;">{tag}</div>'
    
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)
else:
    st.info("파일을 업로드하면 그리드 뷰가 생성됩니다.")

# 텍스트 영역
st.markdown(f"""
    <div style="padding: 25px 0; border-top: 1px solid #eee; font-family: sans-serif;">
        <p style="font-size: 16px; line-height: 1.6;"><b>fastpapermag</b> {mention_text.replace('\\n', '<br>')}</p>
        <div style="margin-top: 30px; padding: 20px; background: #fafafa; border-radius: 8px;">
            <p style="color: #333; font-size: 14px; margin: 0; font-weight: bold;">댓글태그</p>
            <p style="color: #00376b; font-size: 14px; margin-top: 8px;">{hashtag_text.replace('\\n', '<br>')}</p>
        </div>
    </div>
""", unsafe_allow_html=True)
