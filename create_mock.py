import asyncio
import edge_tts

text = "Приветствую, сэр. Я готов к работе. Все системы функционируют в штатном режиме."
communicate = edge_tts.Communicate(text, "ru-RU-DmitryNeural", rate="+10%", pitch="-15Hz")
asyncio.run(communicate.save("jarvis_sample.wav"))
print("Создан заглушечный файл jarvis_sample.wav")
