import torch
import torchaudio
import soundfile as sf
import time
import os

# PyTorch 2.6+ weights_only=True fix for Coqui TTS
_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _patched_load

# TorchAudio Nightly Windows fix (bypasses torchcodec/ffmpeg dlls)
def _patched_audio_load(filepath, **kwargs):
    data, samplerate = sf.read(filepath, dtype='float32')
    data = data.T if len(data.shape) > 1 else data.reshape(1, -1)
    return torch.tensor(data), samplerate
torchaudio.load = _patched_audio_load

from TTS.api import TTS

os.environ["COQUI_TOS_AGREED"] = "1"

print("PyTorch Version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

start = time.time()
print("Loading XTTS...")
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
print(f"Model loaded in: {time.time() - start:.2f} seconds")

start = time.time()
print("Generating audio...")
tts.tts_to_file(text="Тестирование Ист Экс Тэ Тэ Эс завершено успешно.", speaker_wav="jarvis_sample.wav", language="ru", file_path="test_output.wav")
print(f"Audio generated in: {time.time() - start:.2f} seconds")
