import base64
import html
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import streamlit.components.v1 as components

st.set_page_config(page_title="FASTPAPER Studio", layout="wide", initial_sidebar_state="collapsed")
BASE = Path(__file__).resolve().parent
FONT_PATH = BASE / 'assets' / 'fastpaperSans-Bold.ttf'
LOGO_PATH = BASE / 'assets' / 'fp_logo_white_w1920.png'
TEMPLATES = {
    '4:5': {'size': (1080, 1350), 'font_size': 72, 'title_left': 95, 'title_bottom': 1130, 'line_gap': 8, 'logo_width': 205, 'logo_bottom': 40, 'logo_top': 0, 'logo_left': 0, 'title_align': 'left', 'logo_position': 'bottom'},
    '9:16': {'size': (1080, 1920), 'font_size': 80, 'title_left': 69, 'title_bottom': 1474, 'line_gap': 15, 'logo_width': 216, 'logo_bottom': 0, 'logo_top': 290, 'logo_left': 85, 'title_align': 'left', 'logo_position': 'top'},
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
                   logo_top=None, logo_left=None, gradient_top=False, gradient_bottom=None, title_shadow_strength=0):
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
        # 제목 그림자: 텍스트만 별도 레이어에 그린 뒤 블러 적용
        if title_shadow_strength > 0:
            shadow_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            for i, line in enumerate(lines):
                if TEMPLATES[ratio]['title_align'] == 'center':
                    pos, anchor = (W // 2 + 2, top + i * line_h + 3), 'mt'
                else:
                    pos, anchor = (title_left + 2, top + i * line_h + 3), 'lt'
                shadow_draw.text(pos, line, font=font,
                                 fill=(0, 0, 0, title_shadow_strength), anchor=anchor)
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(5))
            base = Image.alpha_composite(base, shadow_layer)
            d = ImageDraw.Draw(base)
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

# 1. 썸네일 제작
st.subheader('01  ·  썸네일 제작')
ratio = st.segmented_control('비율 선택', ['4:5','9:16','1:1'], default='4:5', key='maker_ratio')
ratio = ratio or '4:5'
t = TEMPLATES[ratio]
w,h=t['size']
edit_col,preview_col = st.columns([1.3,1],gap='large')
with edit_col:
    source=st.file_uploader('배경 이미지',type=['png','jpg','jpeg','webp'],key='maker_source')
    headline=st.text_area('썸네일 제목 · 줄바꿈 직접 입력',height=115,key='maker_headline',placeholder='첫째 줄\n둘째 줄\n셋째 줄')
    g1,g2=st.columns(2)
    with g1: gradient_top=st.checkbox('상단 그라데이션',value=False)
    with g2: gradient_bottom=st.checkbox('하단 그라데이션',value=True)
    gradient_strength=st.slider('그라데이션 농도',min_value=0,max_value=255,value=150,step=5,help='상단과 하단에 동일하게 적용됩니다.')
    title_shadow_enabled=st.checkbox('제목 그림자',value=False)
    title_shadow_strength=st.slider('제목 그림자 농도',min_value=0,max_value=255,value=120,step=5,disabled=not title_shadow_enabled) if title_shadow_enabled else 0
    # 디자인 좌표/폰트/로고 크기는 비율별 템플릿 값으로 고정
    font_size=t['font_size']
    title_left=t['title_left']
    title_bottom=t['title_bottom']
    line_gap=t['line_gap']
    logo_width=t['logo_width']
    logo_top=t['logo_top']
    logo_left=t['logo_left']
    logo_bottom=t['logo_bottom']

rendered=None
with preview_col:
    st.caption(f'미리보기 · {w} × {h}px')
    if source:
        try:
            source.seek(0)
            rendered=make_thumbnail(source,headline,ratio,gradient_bottom,False,
                font_size,title_bottom,title_left,line_gap,logo_width,logo_bottom,gradient_strength,
                logo_top,logo_left,gradient_top=gradient_top,gradient_bottom=gradient_bottom,
                title_shadow_strength=title_shadow_strength)
            st.markdown(f'<div class="fp-card"><img class="fp-small-image" src="{image_data_uri(rendered)}"></div>',unsafe_allow_html=True)
            st.download_button('⬇ 썸네일 PNG 다운로드',data=rendered,file_name=f'fastpaper_{w}x{h}.png',mime='image/png',use_container_width=True)
        except Exception as e:
            st.error(f'이미지 생성 오류: {e}')
    else:
        st.info('배경 이미지를 올리면 이곳에 작은 미리보기가 표시됩니다.')

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
