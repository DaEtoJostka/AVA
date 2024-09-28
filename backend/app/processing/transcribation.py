from scenedetect import detect, AdaptiveDetector, split_video_ffmpeg
import numpy as np
import librosa
import whisper_timestamped as whisper
import torch


def get_scenes(video_path: str) -> list:
    scene_list = detect(video_path, AdaptiveDetector())
    return scene_list

class Transcribation:
    def __init__(self, model_name='openai/whisper-small'):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.device = device
        self.model = whisper.load_model(model_name, device=self.device)

    def get_audio_scenes(self, video_path, scene_list):
        audio, sr = librosa.load(video_path)

        audio_scenes = []
        min_seconds = 2
        for start_time, end_time in scene_list:

            start_frame = int(start_time.get_seconds() * sr)
            end_frame = int(end_time.get_seconds() * sr)

            if end_time.get_seconds() - start_time.get_seconds() > min_seconds:
                audio_scene = audio[start_frame:end_frame]
                audio_scenes.append(audio_scene)
            else:
                audio_scenes.append(np.array([]))
        return audio_scenes

    def return_uniq_words_ratio(self, res):
        words = res['text'].split(' ')
        values, counts = np.unique(np.array(words), return_counts=True)
        return len(values) / len(words)

    def get_texts(self, audio_scenes):
        results = []
        for i in range(len(audio_scenes)):
            if audio_scenes[i].shape[0] != 0:
                results.append(whisper.transcribe(self.model, audio_scenes[i]))
            else:
                results.append({'text': '', 'segments': []})
        return results

    def get_transcribation_inf(self, video_path, scene_list):
        audio_scenes = self.get_audio_scenes(video_path, scene_list)
        texts = self.get_texts(audio_scenes)
        for i in range(len(texts)):
            if self.return_uniq_words_ratio(texts[i]) < 0.2:
                texts[i]['text'] = ''
                texts[i]['segments'] = []
        out = {
            'audio_scenes': audio_scenes,
            'text_scenes': texts
        }
        return out
