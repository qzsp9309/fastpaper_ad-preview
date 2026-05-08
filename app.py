import streamlit as st
import base64

# 1. 페이지 설정
st.set_page_config(page_title="Fastpapermag Preview System", layout="wide")

# 2. CSS 스타일링 (4:5 비율 및 레이아웃 최적화)
st.markdown("""
    <style>
    /* 인스타그램 4:5 비율 그리드 설정 (위아래 여백 제거) */
    .content-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        background-color: #ffffff;
        padding: 20px 0;
    }
    .grid-item {
        width: calc(20% - 12px); /* 한 줄에 5개 */
        aspect-ratio: 4 / 5;    /* 4:5 비율 고정 */
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
        object-fit: cover; /* 4:5 영역에 꽉 채우기 (여백 방지) */
    }

    /* 썸네일 선택 영역 (높이 500px 및 좌측 정렬) */
    .thumb-preview-container {
        width: 100%;
        max-width: 400px; /* 너무 퍼지지 않게 폭 제한 */
        margin-bottom: 10px;
    }
    .thumb-img-box {
        width: 100%;
        height: 500px;
        background: #f0f0f0;
        border-radius: 8px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .thumb-img-box img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .thumb-text-left {
        text-align: left; /* 문구 좌측 정렬 */
        font-size: 14px;
        color: #333;
        line-height: 1.5;
        margin-top: 8px;
        white-space: pre-wrap; /* 줄바꿈 적용 */
    }

    /* 인스타그램 텍스트 스타일 */
    .insta-header {
        font-weight: bold;
        font-size: 18px;
        margin: 20px 0 10px 0;
        display: flex;
        align-items: center;
        font-family: sans-serif;
    }
    .profile-circle {
        width: 35px; height: 35px; border-radius: 50%;
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); 
        margin-right: 12px;
    }
    </style>
""", unsafe_allow_html=True)

if 'selected_thumb_idx' not in st.session_state:
    st.session_state.selected_thumb_idx = 0

# 3. 사이드바 입력창
with st.sidebar:
    st.title("📂 Editor")
    
    st.subheader("1) 썸네일 설정")
    thumb_files = st.file_uploader("썸네일 이미지 (최대 3개)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    # 썸네일 문구 입력 (3줄까지 고려하여 height 조절)
    thumb_texts = []
    for i in range(3):
        txt = st.text_area(f"{i+1}안 썸네일 문구 (최대 3줄)", key=f"thumb_txt_{i}", height=100)
        thumb_texts.append(txt)

    st.subheader("2) 본문 소재")
    content_files = st.file_uploader("이미지/영상 업로드", type=['png', 'jpg', 'jpeg', 'mp4', 'mov'], accept_multiple_files=True)
    if content_files:
        content_files = sorted(content_files, key=lambda x: x.name)

    st.subheader("3) 텍스트 입력")
    mention_text = st.text_area("본문 멘션", height=200)
    hashtag_text = st.text_area("댓글 해시태그", height=100)

# 4. 메인 미리보기 영역
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
            
            # 미리보기 이미지 (500px 고정) + 좌측 정렬 문구
            st.markdown(f"""
                <div class="thumb-preview-container">
                    <div class="thumb-img-box">
                        <img src="data:image/jpeg;base64,{t_b64}">
                    </div>
                    <div class="thumb-text-left">{thumb_texts[i]}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"{i+1}안 선택", key=f"btn_{i}", use_container_width=True):
                st.session_state.selected_thumb_idx = i
                st.rerun()
    st.divider()

# 5. 그리드 뷰 (4:5 비율)
st.markdown(f"""
    <div class="insta-header">
        <div class="profile-circle"></div>
        <span>fastpapermag</span>
    </div>
""", unsafe_allow_html=True)

combined_media = []
if thumb_files:
    combined_media.append(thumb_files[st.session_state.selected_thumb_idx])
if content_files:
    combined_media.extend(content_files)

if combined_media:
    grid_html = '<div class="content-grid">'
    for i, f in enumerate(combined_media):
        f.seek(0)
        data = f.read()
        b64 = base64.b64encode(data).decode()
        mime = "video/mp4" if f.name.endswith(('mp4', 'mov')) else "image/jpeg"
        
        # 'thumb' 라벨 제거됨
        if "video" in mime:
            tag = f'<video muted loop autoplay><source src="data:{mime};base64,{b64}"></video>'
        else:
            tag = f'<img src="data:{mime};base64,{b64}">'
        
        grid_html += f'<div class="grid-item">{tag}</div>'
    
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

# 6. 본문 텍스트 (줄바꿈 대응)
st.markdown(f"""
    <div style="padding: 25px 0; border-top: 1px solid #eee; font-family: sans-serif;">
        <p style="font-size: 16px; line-height: 1.6; white-space: pre-wrap;"><b>fastpapermag</b><br>{mention_text}</p>
        <div style="margin-top: 30px; padding: 20px; background: #fafafa; border-radius: 8px; border: 1px solid #f0f0f0;">
            <p style="color: #333; font-size: 14px; margin: 0; font-weight: bold;">댓글태그</p>
            <p style="color: #00376b; font-size: 14px; margin-top: 8px; white-space: pre-wrap;">{hashtag_text}</p>
        </div>
    </div>
""", unsafe_allow_html=True)
