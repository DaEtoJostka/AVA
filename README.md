![Цифровой прорыв](https://drive.google.com/file/d/1AkP94tbG0tFtfhNZNN8FjYguUF2lKlS-/view?usp=sharing)

# AVA

AVA (Automatic video analyser) - многофункционалная система для разметки видео

## Описание возможностей

- **Детекция объектов в видео**. Детекция производится с помощью YOLOv10
- **Разбивка на сцены**. Разбивка производится с помощью библиотеки scenedetection
- **Транскрибация**. Для решения проблемы мультиязычной транскрибации аудиозапись была разбита согласно
сценам. Следуя гипотезе о том, что в одной сцене с большой вероятностью будет один язык, мы транскрибируем в текст только часть аудио,
которая соотвествует одной сцене. Таким образом, удаётся сохранить мультиязысность.
Также для каждого слова выводится его местоположение в аудио сцене.
- **Эмоции**. Мультимодальность сцен позволяет находить эмоции в тексте, аудио, картинках, затем и в общем в сцене.
Что позволяет н обучать модель для распознавания эмоций на видео или создать свой датасет эмоций в видео.

## Возможности, не реализованные, но включенные в систему
- **Мультимодальная векторная база данных** для поиска по аудио, тексту, изображениям, видео.
Такая база данных позволяет осуществлять поиск сцен по базе данных или непосредственно в видео или поиск видео в базе данных.
Каждая модальность векторизуется. Далее путём сравнения эмбеддинга входящей информации разной модальности с эмбеддингами в базе данных можно найти наиболее релевантный материал

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