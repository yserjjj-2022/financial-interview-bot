# modules/gigachat_handler.py
import os
from dotenv import load_dotenv
from gigachat import GigaChat
import logging

load_dotenv()

class GigaChatHandler:
    def __init__(self):
        self.credentials = os.getenv('GIGACHAT_CREDENTIALS')
        if not self.credentials:
            raise ValueError("GIGACHAT_CREDENTIALS не найден в .env файле")
        
        self.giga = GigaChat(
            credentials=self.credentials,
            scope="GIGACHAT_API_PERS",
            model="GigaChat",
            verify_ssl_certs=False
        )
        
        # Настройка логирования
        self.logger = logging.getLogger(__name__)
    
    def get_financial_advice(self, user_query, question_context):
        """
        Получает финансовую консультацию от GigaChat
        
        Args:
            user_query (str): Вопрос пользователя
            question_context (dict): Контекст вопроса с продуктами и рыночной ситуацией
        
        Returns:
            str: Ответ GigaChat
        """
        try:
            # Формируем промпт для GigaChat
            prompt = self._build_financial_prompt(user_query, question_context)
            
            # Отправляем запрос
            response = self.giga.chat(prompt)
            
            # Извлекаем текст ответа
            ai_response = response.choices[0].message.content
            
            self.logger.info(f"GigaChat ответил на вопрос: {user_query[:50]}...")
            return ai_response
            
        except Exception as e:
            self.logger.error(f"Ошибка GigaChat: {e}")
            return self._get_fallback_response(user_query)
    
    def _build_financial_prompt(self, user_query, question_context):
        """Строит промпт для GigaChat с финансовым контекстом"""
        
        prompt = f"""Ты - профессиональный финансовый консультант. Дай подробную консультацию по финансовым продуктам.

КОНТЕКСТ ВОПРОСА:
{question_context.get('question_text', '')}

РЫНОЧНАЯ СИТУАЦИЯ:
{question_context.get('market_context', '')}

ПРОДУКТ А: {question_context.get('option_a', '')}
Детали: {question_context.get('option_a_details', '')}

ПРОДУКТ Б: {question_context.get('option_b', '')}
Детали: {question_context.get('option_b_details', '')}

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {user_query}

ТРЕБОВАНИЯ К ОТВЕТУ:
- Дай конкретные рекомендации с учетом рыночной ситуации
- Объясни риски и преимущества каждого продукта
- Используй расчеты реальной доходности, если уместно
- Ответ должен быть понятным для обычного человека
- НЕ ПРЕВЫШАЙ 300 СЛОВ - это критично для Telegram
- Структурируй ответ кратко и по пунктам
- Используй эмодзи для лучшего восприятия

Ответ:"""
        
        return prompt
    
    def _get_fallback_response(self, user_query):
        """Возвращает резервный ответ при ошибке GigaChat"""
        return f"""
💡 **Консультация временно недоступна**

К сожалению, сейчас не удается получить ответ от ИИ-консультанта.

Ваш вопрос: "{user_query}"

**Общие рекомендации:**
• При выборе финансовых продуктов учитывайте свои цели и отношение к риску
• Сравнивайте реальную доходность (номинальная доходность - инфляция)
• Диверсифицируйте инвестиции между разными типами активов
• Консультируйтесь с финансовыми консультантами при крупных решениях

Попробуйте задать вопрос позже.
"""

    def test_connection(self):
        """Тестирует подключение к GigaChat"""
        try:
            response = self.giga.chat("Привет! Ответь кратко.")
            return True, response.choices[0].message.content
        except Exception as e:
            return False, str(e)
