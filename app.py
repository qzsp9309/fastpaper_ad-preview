import base64
import html
import subprocess
import tempfile
import shutil
import os
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import streamlit.components.v1 as components

st.set_page_config(page_title="FASTPAPER Studio", layout="wide", initial_sidebar_state="collapsed")
BASE = Path(__file__).resolve().parent
FONT_PATH = BASE / 'assets' / 'fastpaperSans-Bold.ttf'
LOGO_PATH = BASE / 'assets' / 'fp_logo_white_w1920.png'
# PSD 원본의 텍스트/로고 레이어 바운딩 박스 기준 (px).
# 제목 font_size/line_step은 실제 레이어 글자폭/높이와 제공 폰트 렌더링을 대조해 보정한 값.
TEMPLATES = {
    # PSD 가이드: 마지막 줄의 실제 보이는 획 아래쪽을 고정, 이전 줄은 위로 쌓기.
    '4:5': {'size': (1080, 1350), 'font_size': 75, 'title_left': 97, 'ink_weight': 0.30,
            'last_bottom': 1135, 'line_step': 90, 'title_align': 'left',
            'logo_width': 203, 'logo_left': 439, 'logo_top': 1279},
    '9:16': {'size': (1080, 1920), 'font_size': 77, 'title_left': 72, 'ink_weight': 0.30,
             'last_bottom': 1454, 'line_step': 98, 'title_align': 'left',
             'logo_width': 216, 'logo_left': 85, 'logo_top': 290},
    '1:1': {'size': (1080, 1080), 'font_size': 60, 'title_left': 0, 'ink_weight': 0.30,
            'last_bottom': 908, 'line_step': 72, 'title_align': 'center',
            'logo_width': 162, 'logo_left': 460, 'logo_top': 1023},
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


def clean_insta_text(text):
    return (text or '').strip().replace('\xa0', ' ').replace('\u200b', '').replace('\t', ' ')


def image_data_uri(data, mime='image/png'):
    return f'data:{mime};base64,{base64.b64encode(data).decode("ascii")}'


def crop_cover(im, size):
    im = ImageOps.exif_transpose(im).convert('RGB')
    return ImageOps.fit(im, size, method=Image.Resampling.LANCZOS, centering=(.5, .5))


def make_design_overlay(headline, ratio='4:5', gradient_top=False,
                        gradient_bottom=True, gradient_strength=150,
                        title_shadow_strength=0):
    """배경 없는 RGBA: 영상과 이미지에 동일한 디자인을 합성."""
    t = TEMPLATES[ratio]
    W, H = t['size']
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
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
        gradient = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        gradient.putalpha(alpha.resize((W, H)))
        layer = Image.alpha_composite(layer, gradient)

    font = ImageFont.truetype(str(FONT_PATH), t['font_size'])
    lines = headline.strip().splitlines() if headline.strip() else []
    # 마지막 줄의 실제 잉크 아래쪽을 PSD 가이드에 고정한다.
    # 각 줄의 글자 모양에 따른 bbox 차이도 개별 보정한다.
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        bbox = font.getbbox(line, anchor='lt')
        ink_w = max(1, bbox[2] - bbox[0])
        ink_h = max(1, bbox[3] - bbox[1])
        mask = Image.new('L', (ink_w + 8, ink_h + 8), 0)
        ImageDraw.Draw(mask).text((4 - bbox[0], 4 - bbox[1]), line, font=font, fill=255, anchor='lt')
        ink_box = mask.getbbox()
        if ink_box is None:
            continue
        mask = mask.crop(ink_box)
        # 포토샵 대비 Pillow의 얇게 보이는 가장자리만 약하게 보정.
        # 전체 글자를 1px 팽창시키지 않고, 확장 마스크를 낮은 비율로 혼합한다.
        # 글자의 좌표/실제 아래 기준선은 이후 재계산하여 고정한다.
        weight = t.get('ink_weight', 0.0)
        if weight > 0:
            padded = ImageOps.expand(mask, border=1, fill=0)
            thickened = padded.filter(ImageFilter.MaxFilter(3))
            mask = Image.blend(padded, thickened, weight)
            actual = mask.getbbox()
            if actual:
                mask = mask.crop(actual)
        y_bottom = t['last_bottom'] - (len(lines) - 1 - index) * t['line_step']
        x = (W - mask.width) // 2 if t['title_align'] == 'center' else t['title_left']
        y = round(y_bottom - mask.height)
        if title_shadow_strength > 0:
            shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            shadow_ink = Image.new('RGBA', mask.size, (0, 0, 0, title_shadow_strength))
            shadow_ink.putalpha(mask.point(lambda a: round(a * title_shadow_strength / 255)))
            shadow.alpha_composite(shadow_ink, (x + 2, y + 3))
            layer = Image.alpha_composite(layer, shadow.filter(ImageFilter.GaussianBlur(5)))
        white = Image.new('RGBA', mask.size, 'white')
        white.putalpha(mask)
        layer.alpha_composite(white, (x, y))

    logo = Image.open(LOGO_PATH).convert('RGBA')
    logo_w = t['logo_width']
    logo_h = round(logo.height * logo_w / logo.width)
    logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
    layer.alpha_composite(logo, (t['logo_left'], t['logo_top']))
    return layer


def make_thumbnail(source, headline, ratio='4:5', gradient_top=False,
                   gradient_bottom=True, gradient_strength=150, title_shadow_strength=0):
    size = TEMPLATES[ratio]['size']
    base = crop_cover(Image.open(source), size).convert('RGBA')
    overlay = make_design_overlay(headline, ratio, gradient_top, gradient_bottom,
                                  gradient_strength, title_shadow_strength)
    result = Image.alpha_composite(base, overlay)
    buf = BytesIO()
    result.convert('RGB').save(buf, format='PNG', optimize=False)
    return buf.getvalue()


def get_video_frame(video_bytes, extension):
    """FFmpeg로 실제 영상의 첫 프레임을 추출."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / ('source' + extension)
        dst = Path(tmp) / 'frame.png'
        src.write_bytes(video_bytes)
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(src),
               '-frames:v', '1', str(dst)]
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if run.returncode != 0 or not dst.exists():
            raise RuntimeError(run.stderr[-1500:] or '첫 프레임 추출 실패')
        return dst.read_bytes()


def render_video(video_bytes, extension, overlay_png, ratio):
    """영상은 원본 FPS 유지, H.264 고화질 CRF 15, 오디오는 재인코딩 없이 복사."""
    if shutil.which('ffmpeg') is None:
        raise RuntimeError('FFmpeg가 설치되어 있지 않습니다.')
    W, H = TEMPLATES[ratio]['size']
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / ('source' + extension)
        png = Path(tmp) / 'overlay.png'
        dst = Path(tmp) / 'result.mp4'
        src.write_bytes(video_bytes)
        png.write_bytes(overlay_png)
        # 이미지와 동일한 중앙 cover crop. 화면 비율이 같으면 불필요한 crop 최소화.
        vf = (f'[0:v]scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,'
              f'crop={W}:{H},setsar=1,format=yuv420p[bg];'
              f'[1:v]format=rgba[fg];[bg][fg]overlay=0:0:shortest=1:format=auto,format=yuv420p[v]')
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(src),
               '-loop', '1', '-i', str(png), '-filter_complex', vf,
               '-map', '[v]', '-map', '0:a?', '-c:v', 'libx264', '-preset', 'slow',
               '-crf', '15', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
               '-c:a', 'copy', '-shortest', str(dst)]
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        if run.returncode != 0 or not dst.exists():
            raise RuntimeError(run.stderr[-2500:] or '영상 합성 실패')
        return dst.read_bytes()



# ---------------------------------------------------------
# 단일 화면 · 4개 작업 섹션
# ---------------------------------------------------------
st.markdown("""<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none !important;}
.block-container {max-width:1160px;padding-top:2rem;padding-bottom:4rem;}
.fp-head {font-size:1.9rem;font-weight:800;letter-spacing:-.05em;margin-bottom:0;}
.fp-sub {color:#777;font-size:.89rem;margin-bottom:1.3rem;}
.fp-card {background:#f7f7f7;border:1px solid #ececec;border-radius:12px;padding:12px;}
.fp-small-image {width:100%;max-width:245px;max-height:330px;object-fit:contain;display:block;margin:auto;border-radius:8px;}
.fp-candidate {width:100%;max-width:160px;max-height:205px;object-fit:contain;border-radius:7px;display:block;margin:0 auto;}
.fp-feed {display:flex;gap:10px;flex-wrap:wrap;align-items:flex-start;margin:12px 0;}
.fp-feed-img {width:135px;height:169px;object-fit:cover;border-radius:7px;border:1px solid #eee;}
.fp-feed-video {width:135px;height:169px;background:#202020;color:white;border-radius:7px;display:flex;align-items:center;justify-content:center;padding:10px;text-align:center;font-size:12px;overflow-wrap:anywhere;}
section[data-testid="stFileUploader"] {margin-bottom:.25rem;}
</style>""",unsafe_allow_html=True)

st.markdown('<div class="fp-head">FASTPAPER STUDIO</div><div class="fp-sub">썸네일 제작부터 인스타그램 게시물 확인까지 한 화면에서 작업</div>',unsafe_allow_html=True)

# 1. 썸네일 3안 독립 제작 및 선택
st.subheader('01  ·  썸네일 제작')
st.caption('1안 · 2안 · 3안을 각각 제작하고, 게시물 미리보기에 사용할 시안을 선택하세요.')

if 'selected_thumb_idx' not in st.session_state:
    st.session_state.selected_thumb_idx = 0

thumbnail_results = [None, None, None]
thumb_cols = st.columns(3, gap='medium')
for idx, col in enumerate(thumb_cols):
    with col:
        st.markdown(f'**{idx + 1}안**')
        ratio = st.selectbox('비율', ['4:5', '9:16', '1:1'], key=f'maker_ratio_{idx}')
        source = st.file_uploader('배경 이미지', type=['png','jpg','jpeg','webp'], key=f'maker_source_{idx}')
        headline = st.text_area('썸네일 제목', height=105, key=f'maker_headline_{idx}', placeholder='첫째 줄\n둘째 줄\n셋째 줄')
        g1, g2 = st.columns(2, gap='small')
        with g1:
            gradient_top = st.checkbox('상단', value=False, key=f'gradient_top_{idx}')
        with g2:
            gradient_bottom = st.checkbox('하단', value=True, key=f'gradient_bottom_{idx}')
        gradient_strength = st.slider('그라데이션 농도', 0, 255, 150, step=5, key=f'gradient_strength_{idx}')
        title_shadow_enabled = st.checkbox('제목 그림자', value=False, key=f'title_shadow_enabled_{idx}')
        title_shadow_strength = st.slider('그림자 농도', 0, 255, 120, step=5, key=f'title_shadow_strength_{idx}', disabled=not title_shadow_enabled)
        if source:
            try:
                rendered_thumb = make_thumbnail(
                    BytesIO(source.getvalue()), headline, ratio,
                    gradient_top=gradient_top,
                    gradient_bottom=gradient_bottom,
                    gradient_strength=gradient_strength,
                    title_shadow_strength=title_shadow_strength if title_shadow_enabled else 0,
                )
                thumbnail_results[idx] = rendered_thumb
                st.markdown(f'<div class="fp-card"><img class="fp-small-image" src="{image_data_uri(rendered_thumb)}"></div>', unsafe_allow_html=True)
                w, h = TEMPLATES[ratio]['size']
                st.caption(f'{w} × {h}px')
                st.download_button('⬇ PNG 다운로드', data=rendered_thumb, file_name=f'fastpaper_{idx+1}안_{w}x{h}.png', mime='image/png', key=f'thumb_download_{idx}', use_container_width=True)
            except Exception as e:
                st.error(f'이미지 생성 오류: {e}')
        else:
            st.caption('이미지를 올리면 미리보기가 표시됩니다.')

available_indices = [i for i, item in enumerate(thumbnail_results) if item is not None]
if available_indices:
    current = st.session_state.selected_thumb_idx
    if current not in available_indices:
        st.session_state.selected_thumb_idx = available_indices[0]
    selected = st.radio(
        '게시물 미리보기에 사용할 썸네일',
        options=available_indices,
        format_func=lambda i: f'{i+1}안',
        horizontal=True,
        key='selected_thumb_idx',
    )
    rendered = thumbnail_results[selected]
    st.caption(f'선택된 {selected+1}안이 아래 본문 소재 미리보기와 전체 이미지 저장에 반영됩니다.')
else:
    rendered = None

st.divider()
st.subheader('01-1  ·  영상 위 썸네일 합성')
st.caption('제작한 시안의 제목·그라데이션·로고를 투명 레이어로 영상 전체에 합성합니다. 원본 오디오는 유지합니다.')
video_source = st.file_uploader('원본 영상 (MP4 / MOV)', type=['mp4', 'mov'], key='overlay_video')
if video_source is not None:
    if not available_indices:
        st.info('위에서 먼저 썸네일 시안을 하나 제작해 주세요. 배경 이미지와 제목을 입력하면 됩니다.')
    else:
        video_idx = st.selectbox('영상에 적용할 시안', available_indices,
                                 format_func=lambda i: f'{i+1}안', key='video_design_idx')
        vr = st.session_state.get(f'maker_ratio_{video_idx}', '4:5')
        vh = st.session_state.get(f'maker_headline_{video_idx}', '')
        vt = st.session_state.get(f'gradient_top_{video_idx}', False)
        vb = st.session_state.get(f'gradient_bottom_{video_idx}', True)
        vs = st.session_state.get(f'gradient_strength_{video_idx}', 150)
        ve = st.session_state.get(f'title_shadow_enabled_{video_idx}', False)
        vss = st.session_state.get(f'title_shadow_strength_{video_idx}', 120) if ve else 0
        design = make_design_overlay(vh, vr, vt, vb, vs, vss)
        overlay_buf = BytesIO()
        design.save(overlay_buf, format='PNG')
        overlay_bytes = overlay_buf.getvalue()
        st.caption(f'적용 비율: {vr} · {TEMPLATES[vr]["size"][0]}×{TEMPLATES[vr]["size"][1]} · 중앙 기준 화면 맞춤')
        if shutil.which('ffmpeg') is None:
            st.error('FFmpeg가 필요합니다. 배포 서버에 FFmpeg를 설치해 주세요.')
        else:
            try:
                # 영상 전체를 재처리하지 않고 첫 프레임만 미리보기로 추출.
                frame = get_video_frame(video_source.getvalue(), Path(video_source.name).suffix.lower())
                preview = Image.alpha_composite(
                    crop_cover(Image.open(BytesIO(frame)), TEMPLATES[vr]['size']).convert('RGBA'), design)
                st.image(preview, caption='첫 프레임 합성 미리보기', width=320)
            except Exception as e:
                st.warning(f'미리보기 생성 실패: {e}')
            st.download_button('투명 디자인 레이어 PNG 다운로드', data=overlay_bytes,
                               file_name=f'fastpaper_overlay_{vr.replace(":", "x")}.png',
                               mime='image/png', key='overlay_png_download')
            if st.button('🎬 고화질 영상 렌더링 시작', type='primary', key='render_video_button'):
                with st.spinner('원본 영상의 화질과 FPS를 최대한 유지하며 렌더링 중입니다...'):
                    try:
                        output = render_video(video_source.getvalue(),
                                              Path(video_source.name).suffix.lower(), overlay_bytes, vr)
                        st.session_state['rendered_video'] = output
                        st.session_state['rendered_video_name'] = f'fastpaper_{vr.replace(":", "x")}_overlay.mp4'
                    except Exception as e:
                        st.error(f'영상 렌더링 실패: {e}')
            if 'rendered_video' in st.session_state:
                st.video(st.session_state['rendered_video'])
                st.download_button('⬇ 합성 영상 MP4 다운로드',
                                   data=st.session_state['rendered_video'],
                                   file_name=st.session_state['rendered_video_name'],
                                   mime='video/mp4', key='video_overlay_download')
st.divider()
# 2. 본문 소재
st.subheader('02  ·  본문 소재')
content_files=st.file_uploader('이미지 및 영상 업로드 · 여러 개 가능',type=['png','jpg','jpeg','webp','mp4','mov'],accept_multiple_files=True,key='content_files')
media=[]
if rendered is not None:
    media.append(('image',rendered))
for f in sorted(content_files or [],key=lambda x:x.name):
    if f.name.lower().endswith(('.mp4','.mov')):
        media.append(('video',f.name))
    else:
        media.append(('image',f.getvalue()))
if media:
    items=['<div class="fp-feed">']
    for typ,data in media:
        if typ=='image':
            items.append(f'<img class="fp-feed-img" src="{image_data_uri(data)}">')
        else:
            items.append(f'<div class="fp-feed-video">🎬 {html.escape(data)}</div>')
    items.append('</div>')
    st.markdown(''.join(items),unsafe_allow_html=True)
    st.caption(f'미리보기 · 총 {len(media)}개 소재 (영상은 파일명으로 표시)')
else:
    st.caption('본문 소재를 업로드하면 작은 카드로 한눈에 표시됩니다.')

st.divider()
# 3. 본문 멘션
st.subheader('03  ·  본문 멘션')
mention_text=st.text_area('게시물 본문',height=180,key='mention_text',label_visibility='collapsed',placeholder='게시물에 들어갈 멘션을 입력하세요.')

st.divider()
# 4. 댓글 해시태그
st.subheader('04  ·  댓글 해시태그')
hashtag_text=st.text_area('댓글 해시태그',height=110,key='hashtag_text',label_visibility='collapsed',placeholder='#fastpaper #패스트페이퍼')


st.divider()
st.subheader('05  ·  게시물 전체 이미지 저장')
st.caption('썸네일 · 본문 소재 · 멘션 · 해시태그를 하나의 이미지로 정리해 저장하거나 클립보드에 복사합니다. 영상은 파일명 카드로 표시됩니다.')

def make_page_snapshot(media, mention, hashtags):
    from PIL import Image, ImageDraw, ImageFont
    width = 1080
    margin = 66
    bg = (255,255,255)
    ink = (25,25,25)
    muted = (110,110,110)
    title_font = ImageFont.truetype(str(FONT_PATH), 43)
    body_font = ImageFont.truetype(str(FONT_PATH), 28)
    small_font = ImageFont.truetype(str(FONT_PATH), 23)
    header_font = ImageFont.truetype(str(FONT_PATH), 35)
    # 페이지 크기 사전 산정. 사진은 4:5 카드 5열로 배치.
    card_w = 178
    card_h = 224
    gap = 18
    rows = max(1,(len(media)+4)//5)
    text_lines = []
    for text in [mention, hashtags]:
        text_lines.append(wrap_lines(text, body_font, width-2*margin))
    height = 165 + rows*(card_h+gap) + 90 + sum(max(1,len(lines))*43+105 for lines in text_lines)+110
    page=Image.new('RGB',(width,height),bg)
    d=ImageDraw.Draw(page)
    d.text((margin,47),'FASTPAPER STUDIO',font=title_font,fill=ink)
    d.line((margin,115,width-margin,115),fill=(225,225,225),width=2)
    d.text((margin,137),'POST PREVIEW',font=small_font,fill=muted)
    y=185
    for i,(typ,data) in enumerate(media):
        col=i%5
        row=i//5
        x=margin+col*(card_w+gap)
        cy=y+row*(card_h+gap)
        if typ=='image':
            try:
                image=Image.open(BytesIO(data)).convert('RGB')
                image=ImageOps.fit(image,(card_w,card_h),method=Image.Resampling.LANCZOS)
                page.paste(image,(x,cy))
            except Exception:
                d.rectangle((x,cy,x+card_w,cy+card_h),fill=(235,235,235))
        else:
            d.rounded_rectangle((x,cy,x+card_w,cy+card_h),radius=8,fill=(40,40,40))
            d.text((x+14,cy+70),'VIDEO',font=small_font,fill='white')
            name=str(data)
            for j,line in enumerate(wrap_lines(name,small_font,card_w-25)[:3]):
                d.text((x+10,cy+110+j*29),line,font=small_font,fill='white')
    y+=rows*(card_h+gap)+38
    for label,lines in [('본문 멘션',text_lines[0]),('댓글 해시태그',text_lines[1])]:
        d.line((margin,y,width-margin,y),fill=(225,225,225),width=2)
        y+=23
        d.text((margin,y),label,font=header_font,fill=ink)
        y+=57
        for line in lines or ['']:
            d.text((margin,y),line,font=body_font,fill=ink)
            y+=43
        y+=45
    return page.crop((0,0,min(width,page.width),min(height,y+35)))

def wrap_lines(text,font,max_width):
    lines=[]
    for paragraph in (text or '').splitlines():
        if not paragraph:
            lines.append('')
            continue
        current=''
        for char in paragraph:
            attempt=current+char
            if font.getlength(attempt)>max_width and current:
                lines.append(current)
                current=char
            else:
                current=attempt
        lines.append(current)
    return lines

snapshot=make_page_snapshot(media,clean_insta_text(mention_text),clean_insta_text(hashtag_text))
out=BytesIO()
snapshot.save(out,format='PNG')
snapshot_bytes=out.getvalue()
st.download_button('📸 전체 이미지 저장 (PNG)',data=snapshot_bytes,file_name='fastpaper_post_preview.png',mime='image/png',use_container_width=True)

# 클립보드는 브라우저의 사용자 클릭 이벤트 안에서 직접 처리
snapshot_b64=base64.b64encode(snapshot_bytes).decode('ascii')
components.html(f"""
<div style="font-family:sans-serif;">
<button id="copy" style="width:100%;border:1px solid #ddd;background:#121212;color:white;border-radius:8px;padding:13px;cursor:pointer;font-weight:700;">📋 전체 이미지 클립보드 복사</button>
<div id="status" style="font-size:12px;color:#666;margin-top:5px;"></div>
</div>
<script>
const button=document.getElementById('copy');
const status=document.getElementById('status');
button.addEventListener('click',async()=>{{
  try {{
    if(!navigator.clipboard || !window.ClipboardItem) throw new Error('브라우저가 이미지 클립보드를 지원하지 않습니다. HTTPS 환경의 Chrome/Edge에서 이용해 주세요.');
    const raw=atob('{snapshot_b64}');
    const bytes=new Uint8Array(raw.length);
    for(let i=0;i<raw.length;i++) bytes[i]=raw.charCodeAt(i);
    const blob=new Blob([bytes],{{type:'image/png'}});
    await navigator.clipboard.write([new ClipboardItem({{'image/png':blob}})]);
    status.textContent='복사 완료! 원하는 곳에 Ctrl+V로 붙여넣으세요.';
  }} catch(e) {{
    status.textContent='복사 실패: '+e.message+' · 위 PNG 저장 버튼을 이용해 주세요.';
  }}
}});
</script>
""",height=95)
