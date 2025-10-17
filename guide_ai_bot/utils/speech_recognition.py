import os
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which
from typing import Optional

from guide_ai_bot.utils.logger import get_logger

logger = get_logger(__name__)

class SpeechToText:
    """
    Утилита для распознавания речи из голосовых сообщений
    """
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Устанавливаем порог чувствительности для шума
        self.recognizer.energy_threshold = 400
    
    async def convert_ogg_to_wav(self, ogg_file_path: str) -> str:
        """
        Конвертирует OGG файл в WAV формат
        """
        try:
            # Загружаем аудио файл
            audio = AudioSegment.from_ogg(ogg_file_path)
            
            # Создаем временный файл для WAV
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
                audio.export(temp_wav.name, format='wav')
                return temp_wav.name
        except Exception as e:
            logger.error(f"Ошибка при конвертации OGG в WAV: {e}")
            raise
    
    async def recognize_speech_from_file(self, file_path: str) -> Optional[str]:
        """
        Распознает речь из аудиофайла и возвращает текст
        """
        try:
            # Определяем формат файла по расширению
            if file_path.lower().endswith('.ogg'):
                # Конвертируем OGG в WAV, так как speech_recognition лучше работает с WAV
                wav_file_path = await self.convert_ogg_to_wav(file_path)
                
                # Используем временный WAV файл для распознавания
                with sr.AudioFile(wav_file_path) as source:
                    audio = self.recognizer.record(source)
            else:
                # Для WAV файлов используем напрямую
                with sr.AudioFile(file_path) as source:
                    audio = self.recognizer.record(source)
            
            # Пытаемся распознать речь с помощью Google Web Speech API
            try:
                text = self.recognizer.recognize_google(audio, language="ru-RU")
                logger.info(f"Распознанный текст: {text}")
                return text
            except sr.UnknownValueError:
                logger.warning("Не удалось распознать речь в аудио файле")
                return "Не удалось распознать речь в сообщении"
            except sr.RequestError as e:
                logger.error(f"Ошибка запроса к сервису распознавания речи: {e}")
                return "Сервис распознавания речи временно недоступен"
        
        except Exception as e:
            logger.error(f"Ошибка при распознавании речи: {e}")
            return "Ошибка при обработке голосового сообщения"
        
        finally:
            # Удаляем временный WAV файл, если он был создан
            if 'wav_file_path' in locals() and os.path.exists(wav_file_path):
                os.unlink(wav_file_path)
    
    async def recognize_speech_from_telegram_voice(self, voice_file_path: str) -> Optional[str]:
        """
        Распознает речь из голосового сообщения Telegram
        """
        return await self.recognize_speech_from_file(voice_file_path)