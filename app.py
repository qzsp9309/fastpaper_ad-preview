import streamlit as st
from PIL import Image
import os

# 페이지 설정
st.set_page_config(page_title="Fastpaper 콘텐츠 프리뷰", layout="wide")

# CSS: 인스타그램 느낌의 스타일링 및 레이아웃 조정
st.markdown("""
    <style>
    /* 전체 배경 및 폰트 */
    .main { background-color: #fafafa; }
    
    /* 인스타그램 목업 스타일 */
    .insta-preview {
        background-color: white;
        border: 1px solid #dbdbdb;
        border-radius: 12px;
        max-width: 450px;
        margin: auto;
        overflow: hidden;
    }
    .insta-header {
        padding: 12px;
        display: flex;
        align-items: center;
        font-weight: 600;
        font-size: 14px;
    }
    .insta-caption-area {
        padding: 12px;
        font-size: 14px;
        line-height: 1.5;
    }
    .hashtag-area {
        color: #00376b;
        padding: 0 12px 12px 12px;
        font-size: 13px;
    }
    /* 썸네일 음영 표시 */
    .thumbnail-overlay {
        position: relative;
    }
    .thumbnail-label {
        position: absolute;
        top: 10px;
        left: 10px;
        background: rgba(0,0,0,0.6);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# 좌측 입력창과 우측 프리뷰 창 분할
left_col, right_col = st.columns([1, 1.2])

with left_col:
    st.header("⚙️ 콘텐츠 세팅")

    # 1. 썸네일 시뮬레이션 (3개 후보)
    st.subheader("1) 썸네일 후보 업로드")
    thumb_files = st.file_uploader("썸네일 이미지 3개를 선택하세요 (JPG, PNG)", 
                                  type=['png', 'jpg', 'jpeg'], 
                                  accept_multiple_files=True,
                                  key="thumbs")
    
    # 2. 본문 소재 업로드 (이미지/영상)
    st.subheader("2) 본문 소재 업로드")
    content_files = st.file_uploader("본문에 들어갈 이미지/영상을 업로드하세요 (이름순 정렬)", 
                                    type=['png', 'jpg', 'jpeg', 'mp4', 'mov'], 
                                    accept_multiple_files=True,
                                    key="contents")
    
    # 파일 이름순 정렬
    if content_files:
        content_files = sorted(content_files, key=lambda x: x.name)

    # 3. 멘션 및 해시태그 기입
    st.subheader("3) 멘션 기입")
    mention_text = st.text_area("인스타그램 본문 문구를 입력하세요 (이모지 가능)", 
                               placeholder="여기에 문구를 입력하세요...",
                               height=300) # 길이 넉넉하게 조정

    st.subheader("4) 댓글 해시태그")
    hashtag_text = st.text_area("첫 번째 댓글에 들어갈 해시태그를 입력하세요", 
                               placeholder="#Fastpaper #Marketing #Daily",
                               height=100)

with right_col:
    st.header("📱 미리보기")
    
    # 인스타그램 목업 시작
    st.markdown('<div class="insta-preview">', unsafe_allow_html=True)
    
    # 상단 헤더 (가상의 계정 정보)
    st.markdown("""
        <div class="insta-header">
            <div style="width:32px; height:32px; background:#ddd; border-radius:50%; margin-right:10px;"></div>
            <span>fastpaper_official</span>
        </div>
    """, unsafe_allow_html=True)

    # 썸네일 선택 시뮬레이션
    if thumb_files:
        st.write("--- 썸네일 안 선택 ---")
        thumb_names = [f.name for f in thumb_files]
        selected_thumb_name = st.radio("시뮬레이션할 썸네일을 선택하세요", thumb_names, horizontal=True)
        
        # 선택된 썸네일 표시
        selected_thumb = next(f for f in thumb_files if f.name == selected_thumb_name)
        st.markdown('<div class="thumbnail-overlay">', unsafe_allow_html=True)
        st.image(selected_thumb, use_container_width=True)
        st.markdown('<div class="thumbnail-label">최종 선택 썸네일 적용 예시</div></div>', unsafe_allow_html=True)
    else:
        st.info("왼쪽에서 썸네일 이미지를 업로드하면 미리보기가 활성화됩니다.")

    # 본문 슬라이드 미리보기
    if content_files:
        st.write("--- 본문 슬라이드 (순서대로) ---")
        for i, f in enumerate(content_files):
            st.text(f"Slide {i+1}: {f.name}")
            if f.type.startswith('video'):
                st.video(f)
            else:
                st.image(f, use_container_width=True)

    # 멘션 표시
    if mention_text:
        st.markdown(f'<div class="insta-caption-area"><b>fastpaper_official</b> {mention_text.replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    # 해시태그 표시
    if hashtag_text:
        st.markdown(f'<div class="hashtag-area">{hashtag_text.replace("\n", " ")}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # 목업 끝
