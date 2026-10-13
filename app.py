import base64
import html
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

st.set_page_config(page_title="Fastpapermag Preview System", layout="wide")
BASE = Path(__file__).resolve().parent
FONT_PATH = BASE / 'assets' / 'fastpaperSans-Bold.ttf'
LOGO_PATH = BASE / 'assets' / 'fp_logo_white_w1920.png'
TEMPLATES = {
    '4:5': {'size': (1080, 1350), 'font_size': 72, 'title_left': 95, 'title_bottom': 1130, 'line_gap': 8, 'logo_width': 205, 'logo_bottom': 40, 'logo_top': 0, 'logo_left': 0, 'title_align': 'left', 'logo_position': 'bottom'},
    '9:16': {'size': (1080, 1920), 'font_size': 82, 'title_left': 66, 'title_bottom': 1450, 'line_gap': 8, 'logo_width': 220, 'logo_bottom': 0, 'logo_top': 285, 'logo_left': 74, 'title_align': 'left', 'logo_position': 'top'},
    '1:1': {'size': (1080, 1080), 'font_size': 64, 'title_left': 0, 'title_bottom': 920, 'line_gap': 8, 'logo_width': 160, 'logo_bottom': 27, 'logo_top': 0, 'logo_left': 0, 'title_align': 'center', 'logo_position': 'bottom'},
}

st.markdown('''<style>
.main {background-color:#fff}
.content-grid {display:flex;flex-wrap:wrap;gap:12px;background:#fff;padding:20px 0}
.grid-item {width:calc(20% - 12px);aspect-ratio:4/5;background:#000;display:flex;align-items:center;justify-content:center;border:1px solid #eee;overflow:hidden}
.grid-item img {width:100%;height:100%;object-fit:cover}
.thumb-img-box {width:100%;aspect-ratio:4/5;background:#f0f0f0;border-radius:8px;overflow:hidden}
.thumb-img-box img {width:100%;height:100%;object-fit:cover}
.thumb-text-left {text-align:left;font-size:14px;color:#333;line-height:1.6;margin:10px 0;white-space:pre-wrap;overflow-wrap:anywhere}
.insta-header {font-weight:bold;font-size:18px;margin:20px 0 10px;display:flex;align-items:center;font-family:sans-serif}
.profile-circle {width:35px;height:35px;border-radius:50%;background:linear-gradient(45deg,#f09433 0%,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888 100%);margin-right:12px}
.insta-text-container {border-top:1px solid #eee;padding-top:15px;margin-top:0}
.insta-text-box {font-family:sans-serif;font-size:16px;line-height:1.8;white-space:pre-wrap;overflow-wrap:anywhere;margin-top:0!important;padding-top:0!important}
.hashtag-box {background:#fafafa;padding:20px;border-radius:8px;border:1px solid #f0f0f0;margin-top:20px}
</style>''', unsafe_allow_html=True)

if 'selected_thumb_idx' not in st.session_state:
    st.session_state.selected_thumb_idx = 0


def clean_insta_text(text):
    return (text or '').strip().replace('\xa0', ' ').replace('\u200b', '').replace('\t', ' ')


def image_data_uri(data, mime='image/png'):
    return f'data:{mime};base64,{base64.b64encode(data).decode("ascii")}'


def crop_cover(im, size):
    im = ImageOps.exif_transpose(im).convert('RGB')
    return ImageOps.fit(im, size, method=Image.Resampling.LANCZOS, centering=(.5, .5))


def make_thumbnail(source, headline, ratio='4:5', gradient=True, logo_shadow=False,
                   font_size=None, title_bottom=None, title_left=None, line_gap=None,
                   logo_width=None, logo_bottom=None, gradient_strength=150,
                   logo_top=None, logo_left=None, gradient_top=False, gradient_bottom=None):
    t = TEMPLATES[ratio]
    W, H = t['size']
    font_size = t['font_size'] if font_size is None else font_size
    title_bottom = t['title_bottom'] if title_bottom is None else title_bottom
    title_left = t['title_left'] if title_left is None else title_left
    line_gap = t['line_gap'] if line_gap is None else line_gap
    logo_width = t['logo_width'] if logo_width is None else logo_width
    logo_bottom = t['logo_bottom'] if logo_bottom is None else logo_bottom
    logo_top = t['logo_top'] if logo_top is None else logo_top
    logo_left = t['logo_left'] if logo_left is None else logo_left

    base = crop_cover(Image.open(source), (W, H)).convert('RGBA')
    # 상단 / 하단 그라데이션을 독립적으로 설정
    if gradient_bottom is None:
        gradient_bottom = gradient
    if gradient_top or gradient_bottom:
        alpha = Image.new('L', (1, H), 0)
        for y in range(H):
            opacity = 0
            if gradient_bottom:
                progress = max(0., min(1., (y - H * .49) / (H * .51)))
                opacity = max(opacity, round(gradient_strength * progress ** 1.5))
            if gradient_top:
                progress = max(0., min(1., (H * .42 - y) / (H * .42)))
                opacity = max(opacity, round(gradient_strength * progress ** 1.5))
            alpha.putpixel((0, y), opacity)
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        overlay.putalpha(alpha.resize((W, H)))
        base = Image.alpha_composite(base, overlay)

    font = ImageFont.truetype(str(FONT_PATH), font_size)
    lines = headline.strip().splitlines() if headline.strip() else []
    if lines:
        d = ImageDraw.Draw(base)
        line_h = font_size + line_gap
        top = title_bottom - len(lines) * line_h
        for i, line in enumerate(lines):
            if TEMPLATES[ratio]['title_align'] == 'center':
                d.text((W // 2, top + i * line_h), line, font=font, fill='white', anchor='mt')
            else:
                d.text((title_left, top + i * line_h), line, font=font, fill='white', anchor='lt')

    logo = Image.open(LOGO_PATH).convert('RGBA')
    logo_height = round(logo.height * logo_width / logo.width)
    logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
    if TEMPLATES[ratio]['logo_position'] == 'top':
        x, y = logo_left, logo_top
    else:
        x, y = (W - logo_width) // 2, H - logo_bottom - logo_height
    if logo_shadow:
        shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        alpha = logo.getchannel('A').point(lambda v: round(v * .7))
        dark = Image.new('RGBA', logo.size, (0, 0, 0, 0))
        dark.putalpha(alpha)
        shadow.alpha_composite(dark, (x + 2, y + 3))
        shadow = shadow.filter(ImageFilter.GaussianBlur(7))
        base = Image.alpha_composite(base, shadow)
    base.alpha_composite(logo, (x, y))
    buf = BytesIO()
    base.convert('RGB').save(buf, format='PNG', optimize=False)
    return buf.getvalue()


# 원래 앱의 입력 및 미리보기 구조 유지
with st.sidebar:
    st.title('📂 Editor')
    thumb_files = st.file_uploader('썸네일 이미지 (최대 3개)', type=['png','jpg','jpeg'], accept_multiple_files=True)
    thumb_texts = [st.text_area(f'{i+1}안 썸네일 문구', key=f't_txt_{i}', height=100) for i in range(3)]
    content_files = st.file_uploader('본문 소재', type=['png','jpg','jpeg','mp4','mov'], accept_multiple_files=True)
    mention_text = st.text_area('본문 멘션', height=400)
    hashtag_text = st.text_area('댓글 해시태그', height=100)

st.header('🖼️ FASTPAPER 썸네일 제작')
st.caption('4:5 · 9:16 · 1:1 / fastpaperSans Bold / PNG 출력')
with st.expander('썸네일 자동 제작', expanded=True):
    ratio = st.radio('썸네일 비율', ['4:5', '9:16', '1:1'], horizontal=True, key='maker_ratio')
    settings = TEMPLATES[ratio]
    width, height = settings['size']
    st.caption(f'출력: {width} × {height}px')
    left, right = st.columns([1, 1])
    with left:
        source = st.file_uploader('배경 이미지', type=['png','jpg','jpeg','webp'], key='maker_source')
        headline = st.text_area('썸네일 제목 (줄바꿈 직접 입력)', height=135, key='maker_headline', placeholder='얼굴합 난리났다는\n고윤정 X 디디에 두보\n화보 공개')
        c1, c2 = st.columns(2)
        with c1:
            gradient_bottom = st.checkbox('하단 검은 그라데이션', value=True)
        with c2:
            logo_shadow = st.checkbox('로고 그림자', value=False)
        gradient_top = st.checkbox('상단 검은 그라데이션', value=False)
        with st.expander('위치 / 크기 미세 조정'):
            font_size = st.slider('제목 글자 크기', 32, 120, settings['font_size'], key=f'font_{ratio}')
            if settings['title_align'] == 'left':
                title_left = st.slider('제목 왼쪽 위치 (px)', 0, 350, settings['title_left'], key=f'left_{ratio}')
            else:
                title_left = 0
                st.caption('1:1 제목은 가로 중앙 정렬입니다.')
            title_bottom = st.slider('제목 마지막 줄 하단 기준 (px)', 300, height - 50, settings['title_bottom'], key=f'bottom_{ratio}')
            line_gap = st.slider('줄 간격 추가 (px)', -12, 36, settings['line_gap'], key=f'gap_{ratio}')
            logo_width = st.slider('로고 너비 (px)', 100, 350, settings['logo_width'], key=f'logo_width_{ratio}')
            if settings['logo_position'] == 'top':
                logo_top = st.slider('로고 위쪽 위치 (px)', 0, 550, settings['logo_top'], key=f'logo_top_{ratio}')
                logo_left = st.slider('로고 왼쪽 위치 (px)', 0, 350, settings['logo_left'], key=f'logo_left_{ratio}')
                logo_bottom = 0
            else:
                logo_bottom = st.slider('로고 하단 여백 (px)', 0, 140, settings['logo_bottom'], key=f'logo_bottom_{ratio}')
                logo_top = 0
                logo_left = 0
            gradient_strength = st.slider('그라데이션 강도', 0, 230, 150)
    with right:
        if source:
            try:
                source.seek(0)
                rendered = make_thumbnail(
                    source, headline, ratio, gradient_bottom, logo_shadow,
                    font_size, title_bottom, title_left, line_gap,
                    logo_width, logo_bottom, gradient_strength,
                    logo_top, logo_left, gradient_top=gradient_top,
                    gradient_bottom=gradient_bottom
                )
                st.image(rendered, caption=f'{ratio} 썸네일 미리보기', use_container_width=True)
                st.download_button('⬇️ 썸네일 PNG 다운로드', data=rendered,
                                   file_name=f'fastpaper_thumbnail_{width}x{height}.png',
                                   mime='image/png', use_container_width=True)
                st.session_state.generated_thumb = rendered
            except Exception as e:
                st.error(f'썸네일 생성 실패: {e}')
        else:
            st.session_state.pop('generated_thumb', None)
            st.info('왼쪽에서 배경 이미지를 업로드하면 자동으로 미리보기가 생성됩니다.')

# 선택할 썸네일 후보: 업로드된 이미지 + 제작한 이미지
candidates = []
if thumb_files:
    for i, f in enumerate(thumb_files[:3]):
        candidates.append({'name': f'{i+1}안', 'data': f.getvalue(), 'text': thumb_texts[i]})
if source and 'generated_thumb' in st.session_state:
    candidates.append({'name': '자동 제작', 'data': st.session_state.generated_thumb, 'text': headline})

if candidates:
    st.subheader('🎯 썸네일 안 선택')
    cols = st.columns(len(candidates))
    for i, item in enumerate(candidates):
        with cols[i]:
            uri = image_data_uri(item['data'])
            st.markdown(f'<div class="thumb-img-box"><img src="{uri}"></div><div class="thumb-text-left">{html.escape(clean_insta_text(item["text"]))}</div>', unsafe_allow_html=True)
            if st.button(f'{item["name"]} 선택', key=f'btn_{i}', use_container_width=True):
                st.session_state.selected_thumb_idx = i
                st.rerun()
    st.divider()

st.markdown('<div class="insta-header"><div class="profile-circle"></div><span>fastpapermag</span></div>', unsafe_allow_html=True)
combined_media = []
if candidates:
    idx = min(st.session_state.selected_thumb_idx, len(candidates) - 1)
    combined_media.append(('image', candidates[idx]['data']))
if content_files:
    for f in sorted(content_files, key=lambda x: x.name):
        if f.name.lower().endswith(('.mp4', '.mov')):
            # 영상은 그리드에 플레이스홀더로 표시 (원본처럼 img로 렌더링되지 않는 문제 방지)
            combined_media.append(('video', f.name))
        else:
            combined_media.append(('image', f.getvalue()))

if combined_media:
    grid_html = '<div class="content-grid">'
    for typ, val in combined_media:
        if typ == 'image':
            grid_html += f'<div class="grid-item"><img src="{image_data_uri(val)}"></div>'
        else:
            grid_html += f'<div class="grid-item" style="color:#fff;font-size:13px;text-align:center;padding:8px">🎬 {html.escape(val)}</div>'
    st.markdown(grid_html + '</div>', unsafe_allow_html=True)

st.markdown(f'<div class="insta-text-container"><div class="insta-text-box">{html.escape(clean_insta_text(mention_text))}</div></div>', unsafe_allow_html=True)
if hashtag_text:
    st.markdown(f'<div class="hashtag-box"><p style="color:#333;font-size:14px;margin:0 0 10px;font-weight:bold">댓글태그</p><div style="color:#00376b;font-size:14px;line-height:1.6;white-space:pre-wrap;overflow-wrap:anywhere">{html.escape(clean_insta_text(hashtag_text))}</div></div>', unsafe_allow_html=True)
