"""Generate a sample WAV for every installed piper voice so you can pick one.

    python voice_samples.py

Writes voice_samples/<voice>.wav, then prints how to switch. Set the winner in
jarvis_config.json as "PIPER_VOICE": "<name>".
"""
import io
import sys
import time
import wave
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

JARVIS_DIR = Path(__file__).parent
MODELS_DIR = JARVIS_DIR / "piper_models"
OUT_DIR = JARVIS_DIR / "voice_samples"

TEXT = ("Системы на связи, сэр. Процессор загружен на семь процентов, "
        "оперативной памяти свободно четырнадцать гигабайт. Чем могу помочь?")


def synth(model_path: Path, length_scale: float) -> tuple[bytes, float]:
    from piper import PiperVoice, SynthesisConfig
    voice = PiperVoice.load(str(model_path))
    t0 = time.perf_counter()
    chunks = list(voice.synthesize(TEXT, syn_config=SynthesisConfig(length_scale=length_scale)))
    elapsed = time.perf_counter() - t0
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(chunks[0].sample_rate)
        for c in chunks:
            wf.writeframes(c.audio_int16_bytes)
    return buf.getvalue(), elapsed


def main():
    OUT_DIR.mkdir(exist_ok=True)
    models = sorted(MODELS_DIR.glob("ru_RU-*.onnx"))
    if not models:
        print(f"Нет моделей в {MODELS_DIR}")
        return

    print(f"Текст: {TEXT}\n")
    for m in models:
        name = m.stem.replace("ru_RU-", "").replace("-medium", "")
        for scale, tag in ((1.0, ""), (1.15, "-slow")):
            try:
                data, elapsed = synth(m, scale)
                out = OUT_DIR / f"{name}{tag}.wav"
                out.write_bytes(data)
                secs = len(data) / (22050 * 2)
                print(f"  {out.name:20s} синтез {elapsed*1000:5.0f}мс, длительность {secs:.1f}с")
            except Exception as e:
                print(f"  {name}{tag}: ошибка — {e}")

    print(f"\nОбразцы здесь: {OUT_DIR}")
    print('Послушайте и впишите победителя в jarvis_config.json:')
    print('    "PIPER_VOICE": "ruslan",          (dmitri / ruslan / denis / irina)')
    print('    "PIPER_LENGTH_SCALE": "1.15"      (если нравится вариант -slow)')


if __name__ == "__main__":
    main()
