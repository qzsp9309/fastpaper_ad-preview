import streamlit as st
import base64

# 1. 페이지 설정
st.set_page_config(page_title="Fastpapermag Preview System", layout="wide")

# 2. CSS 스타일링 (4:5 비율 및 레이아웃 최적화)
st.markdown("""
    <style>
    /* 인스타그램 4:5 비율 그리드 설정 */
    .content-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        background-color: #ffffff;
        padding: 20px 0;
    }
    .grid-item {
        width: calc(20% - 12px); 
        aspect-ratio: 4 / 5;
        background: #000;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #eee;
        overflow: hidden;
    }
    .grid-item img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    /* 썸네일 선택 영역 (500px 높이 & 4:5 가로폭 고정) */
    .thumb-selection-wrapper {
        width: 400px; /* 500px 높이 기준 4:5 비율 너비 */
        margin-bottom: 20px;
    }
    .thumb-img-box {
        width: 100%;
        height: 500px;
        background: #f0f0f0;
        border-radius: 8px;
        overflow: hidden;
    }
    .thumb-img-box img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .thumb-text-left {
        text-align: left;
        font-size: 14px;
        color: #333;
        line-height: 1.5;
        margin: 10px 0;
        white-space: pre-wrap;
    }

    /* 인스타그램 헤더 스타일 */
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
    
    thumb_texts = []
    for i in range(3):
        txt = st.text_area(f"{i+1}안 썸네일 문구", key=f"thumb_txt_{i}", height=80)
        thumb_texts.append(txt)

    st.subheader("2) 본문 소재")
    content_files = st.file_uploader("이미지/영상 업로드", type=['png', 'jpg', 'jpeg', 'mp4', 'mov'], accept_multiple_files=True)
    if content_files:
        content_files = sorted(content_files, key=lambda x: x.name)

    st.subheader("3) 텍스트 입력")
    mention_text = st.text_area("본문 멘션", height=150)
    hashtag_text = st.text_area("댓글 해시태그", height=80)

# 4. 메인 미리보기 영역
if thumb_files:
    st.subheader("🎯 썸네일 안 선택")
    cols = st.columns(len(thumb_files))
    
    for i in range(len(thumb_files)):
        with cols[i]:
            f = thumb_files[i]
            f.seek(0)
            t_data = f.read()
            t_b64 = base64.b64encode(t_data).decode()
            
            # 썸네일 이미지 박스 + 문구를 포함한 래퍼 (폭 400px 고정)
            st.markdown(f"""
                <div class="thumb-selection-wrapper">
                    <div class="thumb-img-box">
                        <img src="data:image/jpeg;base64,{t_b64}">
                    </div>
                    <div class="thumb-text-left">{thumb_texts[i]}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # 버튼도 이미지 폭(400px)에 맞춰 정렬됨
            if st.button(f"{i+1}안 선택", key=f"btn_{i}", use_container_width=False):
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
        
        # 영상 파일도 img 태그를 사용하여 미리보기 이미지로만 노출 (부하 감소)
        # 브라우저가 영상 데이터의 첫 프레임을 이미지처럼 처리하도록 함
        mime = "video/mp4" if f.name.endswith(('mp4', 'mov')) else "image/jpeg"
        
        # 영상인 경우 캡션에 비디오 아이콘 등을 띄울 수 있으나, 요청대로 이미지형태로만 노출
        tag = f'<img src="data:{mime};base64,{b64}">'
        
        grid_html += f'<div class="grid-item">{tag}</div>'
    
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

# 6. 본문 텍스트
st.markdown(f"""
    <div style="padding: 25px 0; border-top: 1px solid #eee; font-family: sans-serif;">
        <p style="font-size: 16px; line-height: 1.6; white-space: pre-wrap;"><b>fastpapermag</b><br>{mention_text}</p>
        <div style="margin-top: 30px; padding: 20px; background: #fafafa; border-radius: 8px; border: 1px solid #f0f0f0;">
            <p style="color: #333; font-size: 14px; margin: 0; font-weight: bold;">댓글태그</p>
            <p style="color: #00376b; font-size: 14px; margin-top: 8px; white-space: pre-wrap;">{hashtag_text}</p>
        </div>
    </div>
""", unsafe_allow_html=True)
