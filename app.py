
st.subheader('01-1  ·  4:5 영상 위 썸네일 합성')
st.caption('이미지 업로드 없이 영상과 제목만으로 제작합니다. 1080×1350(4:5) 출력 · 고화질 인코딩 · 원본 오디오 유지')

video_source = st.file_uploader(
    '원본 영상 (MP4 / MOV)',
    type=['mp4', 'mov'],
    key='overlay_video'
)

video_headline = st.text_area(
    '영상 제목',
    height=105,
    key='video_headline',
    placeholder='첫째 줄\n둘째 줄\n셋째 줄'
)

vg1, vg2 = st.columns(2, gap='small')
with vg1:
    video_gradient_top = st.checkbox(
        '상단 그라데이션', value=False, key='video_gradient_top'
    )
with vg2:
    video_gradient_bottom = st.checkbox(
        '하단 그라데이션', value=True, key='video_gradient_bottom'
    )

video_gradient_strength = st.slider(
    '영상 그라데이션 농도', 0, 255, 150,
    step=5, key='video_gradient_strength'
)

video_shadow = st.checkbox(
    '영상 제목 그림자', value=False, key='video_shadow'
)
video_shadow_strength = st.slider(
    '영상 그림자 농도', 0, 255, 120,
    step=5, key='video_shadow_strength',
    disabled=not video_shadow
)

if video_source is not None:
    if shutil.which('ffmpeg') is None:
        st.error(
            'FFmpeg가 필요합니다. '
            '배포 서버의 packages.txt에 ffmpeg를 추가해 주세요.'
        )
    elif not video_headline.strip():
        st.info('영상에 넣을 제목을 입력해 주세요.')
    else:
        if st.button(
            '🎬 4:5 영상 합성 시작',
            type='primary',
            key='render_video_button'
        ):
            with st.spinner('고화질 4:5 영상으로 합성 중입니다...'):
                try:
                    design = make_design_overlay(
                        video_headline,
                        '4:5',
                        video_gradient_top,
                        video_gradient_bottom,
                        video_gradient_strength,
                        video_shadow_strength if video_shadow else 0
                    )

                    overlay_buf = BytesIO()
                    design.save(overlay_buf, format='PNG')

                    output = render_video(
                        video_source.getvalue(),
                        Path(video_source.name).suffix.lower(),
                        overlay_buf.getvalue(),
                        '4:5'
                    )

                    st.session_state['rendered_video'] = output
                    st.session_state['rendered_video_name'] = (
                        'fastpaper_4x5_overlay.mp4'
                    )
                    st.session_state['rendered_video_signature'] = (
                        video_source.name,
                        video_source.size,
                        video_headline,
                        video_gradient_top,
                        video_gradient_bottom,
                        video_gradient_strength,
                        video_shadow,
                        video_shadow_strength
                    )
                except Exception as e:
                    st.error(f'영상 렌더링 실패: {e}')

        current_signature = (
            video_source.name,
            video_source.size,
            video_headline,
            video_gradient_top,
            video_gradient_bottom,
            video_gradient_strength,
            video_shadow,
            video_shadow_strength
        )

        if (
            st.session_state.get('rendered_video') is not None
            and st.session_state.get('rendered_video_signature')
            == current_signature
        ):
            st.success('영상 합성이 완료됐습니다.')
            st.download_button(
                '⬇ 합성 영상 MP4 다운로드',
                data=st.session_state['rendered_video'],
                file_name=st.session_state['rendered_video_name'],
                mime='video/mp4',
                key='video_overlay_download',
                use_container_width=True
            )
