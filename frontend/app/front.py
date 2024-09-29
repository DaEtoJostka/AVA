import logging
import uuid

import requests
import streamlit as st
from config import cfg

from minio import S3Error, Minio
from infra.minio_client import MinioClient

# config
minio_client = MinioClient()
base_url = "http://localhost:8000/api/v1"

st.set_page_config(layout="wide")

st.sidebar.title("Navigation")
# Page navigation
page = st.sidebar.selectbox("Choose a page", ["Загрузка видео", "Анализ видео"])

if page == "Загрузка видео":
    st.title("Загрузка видео")

    uploaded_file = st.file_uploader("Выберите видеофайл", type=["mp4"])

    if uploaded_file:
        file_uuid = str(uuid.uuid4())
        minio_client.put_file("ava", file_uuid, uploaded_file)
        st.success(f"File {uploaded_file.name} uploaded successfully!")
        payload = {
            "url": file_uuid,
            "name": uploaded_file.name,
        }

        headers = {
            "Content-Type": "application/json",
        }

        response = requests.post(f'{base_url}/video', json=payload, headers=headers)

        st.write("Видео успешно загружено")
elif page == "Анализ видео":
    st.title("Анализ видео")

    # List uploaded videos
    # uploaded_videos = minio_client.list_files("ava")
    headers = {
        "Content-Type": "application/json",
    }

    response = requests.get(f'{base_url}/video', headers=headers)
    if response.status_code == 200 and (uploaded_videos := response.json()):
        video_map = {video['name']: video.get('detected_url') for video in uploaded_videos}
        print(video_map)
        if selected_video_name := st.selectbox("Select a video to play",
                                               [video_name for video_name, video_detected_url in video_map.items() if
                                                video_detected_url]):
            selected_video = minio_client.get_file('ava', video_map[selected_video_name], )

            st.video(selected_video.data)

            origin_video = video_map[selected_video_name].replace("_detected_compressed", "")

            scenes = requests.get(
                    f'{base_url}/video/scene?video_id={origin_video}',
                    headers=headers)
            if scenes.status_code == 200 and (scenes := scenes.json()):
                for scene in scenes:
                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        image = minio_client.get_file('ava',
                                                          origin_video + f'_scene_{scene["start_frame"]}_{scene["end_frame"]}.jpg', )
                        st.image(image.data, output_format='JPEG')
                    with col2:
                        st.write(scene["text"])
                    with col3:
                        c1, c2 = st.columns([1, 1.5])
                        with c1:
                            st.write('Эмоция в тексте: ')
                            st.write('Эмоция в аудио: ')
                            st.write('Эмоция в первом и последнем кадрах: ')
                            st.write('Мультимодальная эмоция в сцене: ')
                        with c2:
                            st.success(scene['text_emotion'])
                            st.success(scene['audio_emotion'])
                            st.success(scene['image_emotion'])
                            st.success(scene['scene_emotion'])
                    st.write('Эмоция в видео: ')
                st.success(scenes[0]['main_emotion'])
    else:
        st.warning("No videos uploaded yet!")
