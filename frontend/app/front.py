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

            col1, col2 = st.columns([2, 1])

            with col1:
                st.video(selected_video.data)

                col_btn1, col_btn2, col_btn3, col_btn4 = st.tabs(["Сцены", "Либа звуков", "Либа символов", "Объекты"])
                with col_btn1:
                    st.button("Сцены")
                with col_btn2:
                    st.button("Либа звуков")
                with col_btn3:
                    st.button("Либа символов")
                with col_btn4:
                    st.button("Объекты")
                st.write("Ещё какая-то инфа. Например, здесь идут миниатюры сцен")
            with col2:
                st.text_input("Поиск", placeholder="Введите текст для поиска")
                st.text_area("Транскрипция", "{таймкод} - {говорящий} - {фраза}")
            #

    else:
        st.warning("No videos uploaded yet!")
