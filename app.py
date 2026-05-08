import streamlit as st
import base64

# 1. 페이지 설정
st.set_page_config(page_title="Fastpapermag Preview System", layout="wide")

# 2. CSS 스타일링 (4:5 비율 및 레이아웃)
st.markdown("""
    <style>
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
    .thumb-selection-wrapper {
        width: 400px;
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
        line-height: 1.6;
        margin: 10px 0;
        white-space: pre-wrap;
        word-break: break-all;
    }
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
    /* 텍스트 영역 스타일 */
    .insta-text-box {
        font-family: sans-serif;
        font-size: 16px;
        line-height: 1.8;
        white-space: pre-wrap;
        word-break: break-all;
        margin-bottom: 20px;
    }
    .hashtag-box {
        background-color: #fafafa;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #f0f0f0;
    }
    </style>
""", unsafe_allow_html=True)

if 'selected_thumb_idx' not in st.session_state:
    st.session_state.selected_thumb_idx = 0

# 3. 텍스트 클리닝 함수
def clean_insta_text(text):
    if not text: return ""
    return text.strip().replace('\xa0', ' ').replace('\u200b', '').replace('\t', ' ')

# 4. 사이드바 입력창
with st.sidebar:
    st.title("📂 Editor")
    thumb_files = st.file_uploader("썸네일 이미지 (최대 3개)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    thumb_texts = [st.text_area(f"{i+1}안 썸네일 문구", key=f"t_txt_{i}", height=100) for i in range(3)]
    content_files = st.file_uploader("본문 소재", type=['png', 'jpg', 'jpeg', 'mp4', 'mov'], accept_multiple_files=True)
    mention_text = st.text_area("본문 멘션", height=200)
    hashtag_text = st.text_area("댓글 해시태그", height=100)

# 5. 썸네일 선택 영역
if thumb_files:
    st.subheader("🎯 썸네일 안 선택")
    cols = st.columns(len(thumb_files))
    for i in range(len(thumb_files)):
        with cols[i]:
            f = thumb_files[i]
            f.seek(0)
            t_b64 = base64.b64encode(f.read()).decode()
            st.markdown(f"""
                <div class="thumb-selection-wrapper">
                    <div class="thumb-img-box"><img src="data:image/jpeg;base64,{t_b64}"></div>
                    <div class="thumb-text-left">{clean_insta_text(thumb_texts[i])}</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"{i+1}안 선택", key=f"btn_{i}", use_container_width=True):
                st.session_state.selected_thumb_idx = i
                st.rerun()
    st.divider()

# 6. 미리보기 헤더 및 그리드
st.markdown(f'<div class="insta-header"><div class="profile-circle"></div><span>fastpapermag</span></div>', unsafe_allow_html=True)

combined_media = []
if thumb_files: combined_media.append(thumb_files[st.session_state.selected_thumb_idx])
if content_files: combined_media.extend(sorted(content_files, key=lambda x: x.name))

if combined_media:
    grid_html = '<div class="content-grid">'
    for f in combined_media:
        f.seek(0)
        b64 = base64.b64encode(f.read()).decode()
        mime = "video/mp4" if f.name.endswith(('mp4', 'mov')) else "image/jpeg"
        grid_html += f'<div class="grid-item"><img src="data:{mime};base64,{b64}"></div>'
    st.markdown(grid_html + '</div>', unsafe_allow_html=True)

# 7. 본문 멘션 섹션 (독립 실행)
st.markdown(f"""
    <div style="border-top: 1px solid #eee; padding-top: 20px;">
        <div class="insta-text-box">
            <b>fastpapermag</b><br>
            {clean_insta_text(mention_text)}
        </div>
    </div>
""", unsafe_allow_html=True)

# 8. 댓글 해시태그 섹션 (독립 실행 - 섞일 일 없음)
if hashtag_text:
    st.markdown(f"""
        <div class="hashtag-box">
            <p style="color: #333; font-size: 14px; margin: 0 0 10px 0; font-weight: bold;">댓글태그</p>
            <div style="color: #00376b; font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-break: break-all;">
                {clean_insta_text(hashtag_text)}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
