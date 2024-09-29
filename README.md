![Цифровой прорыв](https://drive.google.com/uc?id=1AkP94tbG0tFtfhNZNN8FjYguUF2lKlS-)

# AVA

AVA (Automatic video analyser) - многофункциональная система для разметки видео

## Стек

Python, PyTorch, YOLOv8, SceneDetect, Polars, Whisper-Small, RuBert-tiny-ru, AST, VisionTranformer, OpenCV, Dramatiq, Streamlit, PostgreSQL, pgVector, SQLAlchemy,  Docker, MinIO

## Описание возможностей

- **Детекция объектов в видео**. Детекция более 1000 объектов *(backend/app/processing/detecting)*
- **Разбивка на сцены**. Разбивка на сцены по резким переходам между кадрами *(backend/app/processing/transcribation)*
- **Транскрибация**. Для решения проблемы мультиязычной транскрибации аудиозапись была разбита согласно
сценам. Следуя гипотезе о том, что в одной сцене с большой вероятностью будет один язык, 
мы транскрибируем в текст только часть аудио,
которая соотвествует одной сцене. Таким образом, удаётся сохранить мультиязысность.
Также для каждого слова выводится его местоположение в аудио сцене. *(backend/app/processing/transcribation)*
- **Эмоции**. Мультимодальность сцен позволяет находить эмоции в тексте, аудио, картинках, затем и в общем в сцене.
Что позволяет не обучать модель для распознавания эмоций на видео или создать свой датасет эмоций в видео.
*(backend/app/processing/emotional_analysis)*

## Возможности, не реализованные, но включенные в систему
- **Мультимодальная векторная база данных** для поиска по аудио, тексту, изображениям, видео.
Такая база данных позволяет осуществлять поиск сцен по базе данных или непосредственно в видео или поиск видео в базе данных.
Каждая модальность векторизуется. Далее путём сравнения эмбеддинга входящей информации
разной модальности с эмбеддингами в базе данных можно найти наиболее релевантный материал

## Видео для теста
[Видео](https://drive.google.com/file/d/1i_ZFyPIR_t8fJAr1f0ZYcdlL6jOMukyM/view?usp=sharing)

## Запуск

Запускать ячейки кода нужно в отдельных терминалах

```docker compose up postgres```

```docker compose up redis```

```docker compose up minio```

``` commandline
    pip install -r alembic/requirements.txt
    pip install -r backend/app/requirements.txt
    pip install -r frontend/requirements.txt
    pip install -r requirements.txt
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

``` commandline
    cd backend/app
    python -m fastapi run server.py
```

``` commandline
    cd backend/app
    python -m dramatiq worker --processes 1 --threads 1
```
``` commandline
    cd frontend
    python -m streamlit run app/front.py --server.port 8502
```
``` commandline
    cd alembic
    python -m alembic upgrade head
```

Далее в localhost:8502 можно увидеть интерфейс и с ним работать