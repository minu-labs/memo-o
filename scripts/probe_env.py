import PySide6, sounddevice as sd, faster_whisper, ctranslate2
print(PySide6.__version__, faster_whisper.__version__, "cuda:", ctranslate2.get_cuda_device_count())
print(sd.query_devices())
print("default:", sd.default.device)
