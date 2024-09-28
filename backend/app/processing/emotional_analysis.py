import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import AutoFeatureExtractor, ASTForAudioClassification
from transformers import ViTImageProcessor, ViTForImageClassification
import numpy as np
from tqdm import tqdm
import cv2

class Text_classificator:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model_checkpoint = 'seara/rubert-tiny2-ru-go-emotions'
        self.tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_checkpoint).to(self.device)

    def get_probs(self, text_scenes, batch_size=10):
        texts = {
            'id': [],
            'texts': []
        }
        for i, scene in enumerate(text_scenes):
            if scene['text'] != '':
                texts['id'].append(i)
                texts['texts'].append(scene['text'])


        ems = {
            'Злость': np.array([]),
            'Отвращение': np.array([]),
            'Страх': np.array([]),
            'Счастье': np.array([]),
            'Нейтрально': np.array([]),
            'Грусть': np.array([])
        }

        with torch.no_grad():
            for i in tqdm(range(0, len(texts['texts']), batch_size)):
                inputs = self.tokenizer(texts['texts'][i: i+batch_size], return_tensors='pt', truncation=True, padding=True).to(
                    self.device)
                proba = self.model(**inputs).logits
                logits = torch.nn.functional.softmax(proba[:, np.array([2, 11, 14, 13, 27, 25])], dim=1).cpu().numpy()

                for i, key in enumerate(ems.keys()):
                    ems[key] = np.concatenate([ems[key], logits[:, i]])

        s = set(list(range(len(text_scenes))))
        #indices = np.array(list(s.difference(set(texts['id']))))
        for i, key in enumerate(ems.keys()):
            arr = np.zeros(len(text_scenes))
            arr[np.array(texts['id'])] = ems[key]
            ems[key] = arr

        return ems


class Audio_classificator:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.feature_extractor = AutoFeatureExtractor.from_pretrained("abletobetable/spec_soul_ast")
        self.model = ASTForAudioClassification.from_pretrained("abletobetable/spec_soul_ast").to(self.device)

    def get_probs(self, audio_scenes, batch_size=10):

        ems = {
            'Злость': np.array([]),
            'Отвращение': np.array([]),
            'Страх': np.array([]),
            'Счастье': np.array([]),
            'Нейтрально': np.array([]),
            'Грусть': np.array([])
        }

        with torch.no_grad():
            for i in tqdm(range(0, len(audio_scenes))):
                try:
                    inputs = self.feature_extractor(audio_scenes[i], return_tensors='pt').to(self.device)
                    proba = self.model(**inputs).logits
                    logits = torch.nn.functional.softmax(proba[:, np.array([0, 1, 3, 4, 5, 6])]).cpu().numpy()[0]

                    for i, key in enumerate(ems.keys()):
                        ems[key] = np.concatenate([ems[key], np.array([logits[i]])])
                except:
                    for i, key in enumerate(ems.keys()):
                        ems[key] = np.concatenate([ems[key], np.array([0])])

        return ems

class Image_classificator:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.processor = ViTImageProcessor.from_pretrained('jhoppanne/Emotion-Image-Classification-V4')
        self.model = ViTForImageClassification.from_pretrained('jhoppanne/Emotion-Image-Classification-V4').to(self.device)

    def get_probs(self, image_scenes, batch_size=10):

        ems = {
            'Злость': np.array([]),
            'Отвращение': np.array([]),
            'Страх': np.array([]),
            'Счастье': np.array([]),
            'Нейтрально': np.array([]),
            'Грусть': np.array([])
        }

        with torch.no_grad():
            for i in tqdm(range(0, len(image_scenes), batch_size)):
                inputs = self.processor(image_scenes[i: i + batch_size], return_tensors='pt').to(self.device)
                proba = self.model(**inputs).logits
                logits = torch.nn.functional.softmax(proba[:, np.array([0, 2, 3, 4, 5, 6])], dim=1).cpu().numpy()

                for i, key in enumerate(ems.keys()):
                    ems[key] = np.concatenate([ems[key], logits[:, i]])

        return ems

class Emotional_analysis:
    def __init__(self):
        self.text_classifier = Text_classificator()
        self.audio_classifier = Audio_classificator()
        self.image_classifier = Image_classificator()

    def get_frames_from_scenes(self, scene_list, video_path):
        cap = cv2.VideoCapture(video_path)
        frames = [self.get_frames(scene, cap) for scene in scene_list]
        return frames

    def get_frames(self, scene, cap):
        first = scene[0].get_frames()
        last = scene[1].get_frames() - 1

        cap.set(cv2.CAP_PROP_POS_FRAMES, first)
        ret, frame = cap.read()
        frames = []
        frames.append(frame)
        cap.set(cv2.CAP_PROP_POS_FRAMES, last)
        ret, frame = cap.read()
        frames.append(frame)

        return frames

    def f(self, i):
        return self.keys[i]

    def get_emotionals(self, text_scenes, audio_scenes, scene_list, video_path):
        text_probs = self.text_classifier.get_probs(text_scenes)
        sound_probs = self.audio_classifier.get_probs(audio_scenes)
        images = self.get_frames_from_scenes(scene_list, video_path)
        first_image_probs = self.image_classifier.get_probs([i[0] for i in images])
        second_image_probs = self.image_classifier.get_probs([i[1] for i in images])

        mean = {}
        res = []
        for key in text_probs.keys():
            mean[key] = text_probs[key] + sound_probs[key] + first_image_probs[key] + second_image_probs[key]
            mean[key] = mean[key]/4
            res.append(mean[key])
        res = np.array(res)
        self.keys = list(mean.keys())
        indicies = res.argmax(axis=0)
        print('indicies', indicies)
        emotions = np.vectorize(self.f)(indicies)

        temp = []
        for key in text_probs.keys():
            temp.append(text_probs[key])
        temp = np.array(temp)
        indicies = temp.argmax(axis=0)
        text_emotions = np.vectorize(self.f)(indicies)

        temp = []
        for key in sound_probs.keys():
            temp.append(sound_probs[key])
        temp = np.array(temp)
        indicies = temp.argmax(axis=0)
        audio_emotions = np.vectorize(self.f)(indicies)

        temp = []
        for key in first_image_probs.keys():
            temp.append((first_image_probs[key] + second_image_probs[key]) / 2)
        temp = np.array(temp)
        indicies = temp.argmax(axis=0)
        image_emotions = np.vectorize(self.f)(indicies)

        temp = []
        for key in first_image_probs.keys():
            first_image = first_image_probs[key].mean()
            second_image = second_image_probs[key].mean()
            sound = sound_probs[key].mean()
            text = text_probs[key].mean()
            temp.append((first_image + second_image + sound + text) / 4)
        temp = np.array(temp)
        indicies = temp.argmax(axis=0)
        main_emotion = np.vectorize(self.f)(indicies)

        res = {
            'text_emotions': text_emotions,
            'audio_emotions': audio_emotions,
            'image_emotions': image_emotions,
            'scene_emotions': emotions,
            'main_emotion': main_emotion
        }

        return res