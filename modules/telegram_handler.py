# modules/telegram_handler.py
import telebot
from telebot import types
import os
import pytz
from datetime import datetime
from dotenv import load_dotenv
from modules.database import DatabaseManager, Interview, Response

load_dotenv()

class TelegramHandler:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env файле")
        
        self.bot = telebot.TeleBot(self.bot_token)
        self.db = DatabaseManager()
        self.moscow_tz = pytz.timezone('Europe/Moscow')
        
        # Словари для отслеживания состояний пользователей
        self.waiting_for_text_answer = {}
        self.waiting_for_ai_consultation = {}
        
        self.setup_handlers()
    
    def get_moscow_time(self):
        return datetime.now(self.moscow_tz)
    
    def utc_to_moscow(self, utc_datetime):
        if utc_datetime is None:
            return None
        if utc_datetime.tzinfo is None:
            utc_datetime = pytz.utc.localize(utc_datetime)
        return utc_datetime.astimezone(self.moscow_tz)
    
    def format_duration(self, start_time, end_time):
        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())
        if total_seconds < 0:
            return "0 мин 0 сек"
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes} мин {seconds} сек"
    
    def send_long_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        """Безопасная отправка длинных сообщений с разбивкой на части"""
        MAX_LENGTH = 4000  # Оставляем запас для форматирования
        
        if len(text) <= MAX_LENGTH:
            self.bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
        else:
            # Разбиваем на части по абзацам или предложениям
            parts = []
            current_part = ""
            
            # Разбиваем по абзацам
            paragraphs = text.split('\n\n')
            
            for paragraph in paragraphs:
                if len(current_part + paragraph) <= MAX_LENGTH:
                    current_part += paragraph + '\n\n'
                else:
                    if current_part:
                        parts.append(current_part.strip())
                        current_part = paragraph + '\n\n'
                    else:
                        # Если даже один абзац слишком длинный
                        while len(paragraph) > MAX_LENGTH:
                            parts.append(paragraph[:MAX_LENGTH])
                            paragraph = paragraph[MAX_LENGTH:]
                        current_part = paragraph + '\n\n'
            
            if current_part:
                parts.append(current_part.strip())
            
            # Отправляем каждую часть
            for i, part in enumerate(parts):
                if i == 0:
                    # Первая часть
                    self.bot.send_message(chat_id, part, parse_mode=parse_mode)
                elif i == len(parts) - 1:
                    # Последняя часть с кнопками
                    self.bot.send_message(chat_id, f"**Продолжение:**\n\n{part}", 
                                        parse_mode=parse_mode, reply_markup=reply_markup)
                else:
                    # Промежуточные части
                    self.bot.send_message(chat_id, f"**Продолжение:**\n\n{part}", parse_mode=parse_mode)
    
    def get_gigachat_response(self, user_query, question_id):
        """Получает ответ от реального GigaChat API"""
        try:
            # Получаем контекст вопроса из базы данных
            session = self.db.get_session()
            from modules.database import Question
            question = session.query(Question).filter(Question.id == question_id).first()
            
            if not question:
                return "❌ Не удалось найти информацию о вопросе для консультации."
            
            # Импортируем GigaChatHandler
            from modules.gigachat_handler import GigaChatHandler
            
            # Создаем обработчик GigaChat
            giga_handler = GigaChatHandler()
            
            # Формируем контекст для ИИ
            question_context = {
                'question_text': question.text,
                'market_context': question.market_context,
                'option_a': question.option_a,
                'option_a_details': question.option_a_details,
                'option_b': question.option_b,
                'option_b_details': question.option_b_details
            }
            
            # Получаем ответ от GigaChat
            ai_response = giga_handler.get_financial_advice(user_query, question_context)
            
            return f"💡 **Консультация GigaChat:**\n\n{ai_response}"
            
        except Exception as e:
            print(f"❌ Ошибка получения ответа от GigaChat: {e}")
            return f"""
❌ **Ошибка консультации**

К сожалению, сейчас не удается получить ответ от ИИ-консультанта.

Ваш вопрос: "{user_query}"

**Общие рекомендации:**
• При выборе финансовых продуктов учитывайте свои цели и отношение к риску
• Сравнивайте реальную доходность (номинальная доходность - инфляция)  
• Диверсифицируйте инвестиции между разными типами активов

Попробуйте задать вопрос позже.
"""
    
    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start_interview(message):
            user_id = str(message.from_user.id)
            username = message.from_user.username or message.from_user.first_name
            session = self.db.get_session()

            # Очищаем все состояния ожидания
            if user_id in self.waiting_for_text_answer:
                del self.waiting_for_text_answer[user_id]
            if user_id in self.waiting_for_ai_consultation:
                del self.waiting_for_ai_consultation[user_id]

            # Завершаем все старые активные интервью пользователя
            active_interviews = session.query(Interview).filter(
                Interview.user_id == user_id,
                Interview.status == 'active'
            ).all()
            for interview in active_interviews:
                interview.status = 'restarted'
                interview.completed_at = datetime.utcnow()
            session.commit()

            # Создаем новое интервью
            new_interview = Interview(
                user_id=user_id,
                username=username,
                started_at=datetime.utcnow()
            )
            session.add(new_interview)
            session.commit()

            welcome_text = f"""
🎤 **Добро пожаловать в финансовое интервью!**

Привет, {username}! Я буду задавать вам вопросы о выборе финансовых продуктов в различных рыночных условиях.

**Как это работает:**
• Вопросы идут по порядку
• Вопросы с выбором: выберите продукт А или Б
• Текстовые вопросы: напишите ваш ответ
• 💡 **Можете консультироваться с реальным GigaChat по любому вопросу**
• Ваши ответы сохраняются для исследования

**Команды:**
/start - начать/перезапустить интервью
/end - завершить интервью
/status - показать прогресс
/help - справка

Готовы начать?
            """
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📝 Начать интервью", callback_data="get_question"))
            self.bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')
        
        @self.bot.callback_query_handler(func=lambda call: call.data == "get_question")
        def get_question_callback(call):
            user_id = str(call.from_user.id)
            self.send_next_question(call.message.chat.id, user_id)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('choose_'))
        def handle_choice(call):
            user_id = str(call.from_user.id)
            choice_data = call.data.split('_')
            option = choice_data[1]  # A или B
            question_id = int(choice_data[2])
            
            session = self.db.get_session()
            interview = session.query(Interview).filter(
                Interview.user_id == user_id,
                Interview.status == 'active'
            ).first()
            
            if interview:
                existing_response = session.query(Response).filter(
                    Response.interview_id == interview.id,
                    Response.question_id == question_id
                ).first()
                
                if existing_response:
                    self.bot.send_message(call.message.chat.id, 
                        "⚠️ Вы уже отвечали на этот вопрос!")
                    return
                
                # Подсчитываем количество консультаций для этого вопроса
                from modules.database import AIConsultation
                consultations_count = session.query(AIConsultation).filter(
                    AIConsultation.interview_id == interview.id,
                    AIConsultation.question_id == question_id
                ).count()
                
                response = Response(
                    interview_id=interview.id,
                    question_id=question_id,
                    selected_option=option,
                    answer_text=f"Выбран продукт {option}",
                    consultations_count=consultations_count,
                    timestamp=datetime.utcnow()
                )
                session.add(response)
                session.commit()
                
                from modules.database import Question
                question = session.query(Question).filter(Question.id == question_id).first()
                if question:
                    chosen_product = question.option_a if option == 'A' else question.option_b
                    self.bot.send_message(call.message.chat.id, 
                        f"✅ **Ваш выбор сохранен!**\n\n"
                        f"Вы выбрали: **{chosen_product}**", 
                        parse_mode='Markdown')
                
                self.send_next_question(call.message.chat.id, user_id)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('skip_'))
        def handle_skip(call):
            user_id = str(call.from_user.id)
            question_id = int(call.data.split('_')[1])
            
            session = self.db.get_session()
            interview = session.query(Interview).filter(
                Interview.user_id == user_id,
                Interview.status == 'active'
            ).first()
            
            if interview:
                # Очищаем состояния ожидания
                if user_id in self.waiting_for_text_answer:
                    del self.waiting_for_text_answer[user_id]
                if user_id in self.waiting_for_ai_consultation:
                    del self.waiting_for_ai_consultation[user_id]
                
                # Сохраняем пропущенный ответ
                response = Response(
                    interview_id=interview.id,
                    question_id=question_id,
                    answer_text="[Вопрос пропущен]",
                    timestamp=datetime.utcnow()
                )
                session.add(response)
                session.commit()
                
                self.bot.send_message(call.message.chat.id, "⏭ Вопрос пропущен.")
                self.send_next_question(call.message.chat.id, user_id)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('consult_'))
        def handle_consultation_request(call):
            user_id = str(call.from_user.id)
            question_id = int(call.data.split('_')[1])
            
            # Устанавливаем состояние ожидания консультации
            self.waiting_for_ai_consultation[user_id] = question_id
            
            consult_text = """
💡 **Консультация с GigaChat**

Задайте свой вопрос о финансовых продуктах, и реальный ИИ GigaChat поможет вам разобраться!

**Примеры вопросов:**
• "Какой продукт безопаснее?"
• "Что лучше при высокой инфляции?"
• "Объясни разницу между продуктами"
• "Какая доходность более выгодна?"
• "Как защититься от рисков?"
• "Рассчитай реальную доходность"

📝 **Напишите ваш вопрос следующим сообщением.**
            """
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("❌ Отмена консультации", callback_data=f"cancel_consult_{question_id}"))
            self.bot.send_message(call.message.chat.id, consult_text, reply_markup=markup, parse_mode='Markdown')
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_consult_'))
        def cancel_consultation(call):
            user_id = str(call.from_user.id)
            
            # Очищаем состояние ожидания консультации
            if user_id in self.waiting_for_ai_consultation:
                del self.waiting_for_ai_consultation[user_id]
            
            self.bot.send_message(call.message.chat.id, 
                "❌ Консультация отменена. Выберите один из продуктов или задайте вопрос заново.")
        
        @self.bot.callback_query_handler(func=lambda call: call.data == "end_interview")
        def confirm_end_interview(call):
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("✅ Да, завершить", callback_data="confirm_end"),
                types.InlineKeyboardButton("❌ Продолжить позже", callback_data="cancel_end")
            )
            self.bot.send_message(
                call.message.chat.id,
                "🤔 **Подтверждение завершения**\n\nВы уверены, что хотите завершить интервью?",
                reply_markup=markup,
                parse_mode='Markdown'
            )
        
        @self.bot.callback_query_handler(func=lambda call: call.data == "confirm_end")
        def handle_confirm_end(call):
            user_id = str(call.from_user.id)
            
            # Очищаем все состояния ожидания
            if user_id in self.waiting_for_text_answer:
                del self.waiting_for_text_answer[user_id]
            if user_id in self.waiting_for_ai_consultation:
                del self.waiting_for_ai_consultation[user_id]
            
            session = self.db.get_session()
            interview = session.query(Interview).filter(
                Interview.user_id == user_id,
                Interview.status == 'active'
            ).first()
            
            if interview:
                completed_at = datetime.utcnow()
                interview.status = 'completed'
                interview.completed_at = completed_at
                session.commit()
                
                responses_count = session.query(Response).filter(
                    Response.interview_id == interview.id
                ).count()
                
                choice_a_count = session.query(Response).filter(
                    Response.interview_id == interview.id,
                    Response.selected_option == 'A'
                ).count()
                
                choice_b_count = session.query(Response).filter(
                    Response.interview_id == interview.id,
                    Response.selected_option == 'B'
                ).count()
                
                # Подсчитываем консультации
                from modules.database import AIConsultation
                consultations_count = session.query(AIConsultation).filter(
                    AIConsultation.interview_id == interview.id
                ).count()
                
                started_msk = self.utc_to_moscow(interview.started_at)
                completed_msk = self.utc_to_moscow(completed_at)
                duration_str = self.format_duration(interview.started_at, completed_at)
                
                from modules.database import Question
                total_questions = session.query(Question).filter(Question.is_active == True).count()
                
                stats_text = f"""
🎉 **Интервью успешно завершено!**

📊 **Ваша статистика:**

📝 **Ответы:**
• Отвечено на вопросов: {responses_count} из {total_questions}
• Выбрано продуктов А: {choice_a_count}
• Выбрано продуктов Б: {choice_b_count}

💡 **Консультации с GigaChat:**
• Всего консультаций: {consultations_count}

⏱ **Время (МСК):**
• Длительность: {duration_str}
• Начато: {started_msk.strftime('%d.%m.%Y %H:%M:%S')}
• Завершено: {completed_msk.strftime('%d.%m.%Y %H:%M:%S')}

🙏 **Спасибо за участие в исследовании!**

Ваши ответы и взаимодействие с GigaChat помогут нам лучше понять, как люди принимают финансовые решения.

---
Для начала нового интервью используйте /start
                """
                self.bot.send_message(call.message.chat.id, stats_text, parse_mode='Markdown')
            else:
                self.bot.send_message(call.message.chat.id, "❌ Активное интервью не найдено.")
        
        @self.bot.callback_query_handler(func=lambda call: call.data == "cancel_end")
        def handle_cancel_end(call):
            self.bot.send_message(
                call.message.chat.id,
                "👍 **Хорошо!**\n\nВы можете продолжить интервью позже или начать новое с помощью /start",
                parse_mode='Markdown'
            )
        
        @self.bot.message_handler(commands=['end'])
        def end_command(message):
            user_id = str(message.from_user.id)
            
            # Очищаем все состояния ожидания
            if user_id in self.waiting_for_text_answer:
                del self.waiting_for_text_answer[user_id]
            if user_id in self.waiting_for_ai_consultation:
                del self.waiting_for_ai_consultation[user_id]
            
            session = self.db.get_session()
            interview = session.query(Interview).filter(
                Interview.user_id == user_id,
                Interview.status == 'active'
            ).first()
            
            if interview:
                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton("✅ Да, завершить", callback_data="confirm_end"),
                    types.InlineKeyboardButton("❌ Продолжить", callback_data="cancel_end")
                )
                self.bot.send_message(
                    message.chat.id,
                    "🤔 **Завершение интервью**\n\nВы уверены, что хотите завершить текущее интервью?",
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    "❌ У вас нет активного интервью для завершения.\n\nДля начала нового интервью используйте /start"
                )
        
        @self.bot.message_handler(commands=['status'])
        def status_command(message):
            user_id = str(message.from_user.id)
            session = self.db.get_session()
            interview = session.query(Interview).filter(
                Interview.user_id == user_id,
                Interview.status == 'active'
            ).first()
            
            if interview:
                answered, total = self.db.get_interview_progress(interview.id)
                started_msk = self.utc_to_moscow(interview.started_at)
                current_time = datetime.utcnow()
                duration_str = self.format_duration(interview.started_at, current_time)
                
                # Проверяем состояния ожидания
                waiting_status = ""
                if user_id in self.waiting_for_text_answer:
                    waiting_status += "\n⏳ Ожидается ответ на текстовый вопрос"
                if user_id in self.waiting_for_ai_consultation:
                    waiting_status += "\n💡 Ожидается вопрос для GigaChat"
                
                # Подсчитываем консультации
                from modules.database import AIConsultation
                consultations_count = session.query(AIConsultation).filter(
                    AIConsultation.interview_id == interview.id
                ).count()
                
                status_text = f"""
📊 **Статус интервью:**

🟢 **Интервью активно**
📝 Прогресс: {answered}/{total} вопросов
💡 Консультаций с GigaChat: {consultations_count}
⏱ Длительность: {duration_str}
🆔 ID интервью: {interview.id}
📅 Начато: {started_msk.strftime('%d.%m.%Y %H:%M:%S')} (МСК){waiting_status}

Для завершения используйте /end
                """
            else:
                status_text = """
📊 **Статус интервью:**

🔴 **Нет активного интервью**

Для начала нового интервью используйте /start
                """
            self.bot.send_message(message.chat.id, status_text, parse_mode='Markdown')
        
        @self.bot.message_handler(commands=['help'])
        def help_command(message):
            help_text = """
🆘 **Справка по боту-интервьюеру**

**Доступные команды:**
/start - начать новое интервью
/end - завершить текущее интервью
/status - показать прогресс интервью
/help - показать эту справку

**Как проходит интервью:**
• Вопросы показываются по порядку
• Вопросы с выбором: выберите продукт А или Б
• Текстовые вопросы: напишите ваш ответ текстом
• 💡 **Консультации с GigaChat:** нажмите кнопку и задайте вопрос
• Можете пропустить текстовые вопросы
• Ваши ответы автоматически сохраняются

**Консультации с GigaChat:**
• Доступны для любого вопроса с выбором
• Задавайте конкретные вопросы о продуктах
• GigaChat учитывает рыночный контекст
• Все консультации сохраняются для анализа

**Завершение интервью:**
• Команда /end в любой момент
• Кнопка "Завершить интервью" когда вопросы закончатся
• Подтверждение перед завершением
• Подробная статистика включая консультации

**Особенности:**
• Нельзя ответить на один вопрос дважды
• Можно начать новое интервью в любой момент
• Все время отображается по московскому часовому поясу
• Все данные используются только для исследования
            """
            self.bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
        
        # ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ (ответы на вопросы и консультации с GigaChat)
        @self.bot.message_handler(func=lambda message: True)
        def handle_text_message(message):
            user_id = str(message.from_user.id)
            
            # Проверяем, ожидается ли текстовый ответ на вопрос
            if user_id in self.waiting_for_text_answer:
                question_id = self.waiting_for_text_answer[user_id]
                
                session = self.db.get_session()
                interview = session.query(Interview).filter(
                    Interview.user_id == user_id,
                    Interview.status == 'active'
                ).first()
                
                if interview:
                    # Проверяем, не отвечал ли уже на этот вопрос
                    existing_response = session.query(Response).filter(
                        Response.interview_id == interview.id,
                        Response.question_id == question_id
                    ).first()
                    
                    if existing_response:
                        self.bot.send_message(message.chat.id, 
                            "⚠️ Вы уже отвечали на этот вопрос!")
                        del self.waiting_for_text_answer[user_id]
                        return
                    
                    # Сохраняем текстовый ответ
                    response = Response(
                        interview_id=interview.id,
                        question_id=question_id,
                        answer_text=message.text,
                        timestamp=datetime.utcnow()
                    )
                    session.add(response)
                    session.commit()
                    
                    # Удаляем из состояния ожидания
                    del self.waiting_for_text_answer[user_id]
                    
                    self.bot.send_message(message.chat.id, 
                        f"✅ **Ваш ответ сохранен!**\n\n"
                        f"Ответ: _{message.text}_", 
                        parse_mode='Markdown')
                    
                    # Переходим к следующему вопросу
                    self.send_next_question(message.chat.id, user_id)
                else:
                    # Интервью не найдено
                    del self.waiting_for_text_answer[user_id]
                    self.bot.send_message(message.chat.id, 
                        "❌ Активное интервью не найдено. Используйте /start")
            
            # Проверяем, ожидается ли вопрос для GigaChat-консультации
            elif user_id in self.waiting_for_ai_consultation:
                question_id = self.waiting_for_ai_consultation[user_id]
                user_query = message.text
                
                session = self.db.get_session()
                interview = session.query(Interview).filter(
                    Interview.user_id == user_id,
                    Interview.status == 'active'
                ).first()
                
                if interview:
                    # Отправляем сообщение о том, что запрос обрабатывается
                    processing_msg = self.bot.send_message(message.chat.id, 
                        "🤔 Обращаюсь к GigaChat, это может занять несколько секунд...")
                    
                    # Получаем ответ от GigaChat
                    ai_response = self.get_gigachat_response(user_query, question_id)
                    
                    # Сохраняем консультацию в базу данных
                    try:
                        consultation_id = self.db.save_consultation(
                            interview_id=interview.id,
                            question_id=question_id,
                            user_query=user_query,
                            ai_response=ai_response,
                            consultation_type="gigachat_advice"
                        )
                        
                        # Удаляем сообщение о обработке
                        try:
                            self.bot.delete_message(message.chat.id, processing_msg.message_id)
                        except:
                            pass  # Игнорируем ошибки удаления сообщения
                        
                        # ИСПРАВЛЕНО: Используем безопасную отправку длинных сообщений
                        self.send_long_message(message.chat.id, ai_response, parse_mode='Markdown')
                        
                        # Предлагаем продолжить
                        markup = types.InlineKeyboardMarkup()
                        markup.row(
                            types.InlineKeyboardButton("🅰️ Выбрать А", callback_data=f"choose_A_{question_id}"),
                            types.InlineKeyboardButton("🅱️ Выбрать Б", callback_data=f"choose_B_{question_id}")
                        )
                        markup.add(types.InlineKeyboardButton("💡 Еще вопрос к GigaChat", callback_data=f"consult_{question_id}"))
                        
                        self.bot.send_message(message.chat.id, 
                            "Теперь выберите один из продуктов или задайте еще один вопрос:",
                            reply_markup=markup)
                        
                        # Удаляем из состояния ожидания консультации
                        del self.waiting_for_ai_consultation[user_id]
                        
                    except Exception as e:
                        print(f"❌ Ошибка сохранения консультации: {e}")
                        try:
                            self.bot.delete_message(message.chat.id, processing_msg.message_id)
                        except:
                            pass
                        # ИСПРАВЛЕНО: Используем безопасную отправку для ошибок
                        self.send_long_message(message.chat.id, 
                            f"{ai_response}\n\n❌ Ошибка сохранения консультации в базу данных.")
                        del self.waiting_for_ai_consultation[user_id]
                else:
                    # Интервью не найдено
                    del self.waiting_for_ai_consultation[user_id]
                    self.bot.send_message(message.chat.id, 
                        "❌ Активное интервью не найдено. Используйте /start")
            
            else:
                # Пользователь не в состоянии ожидания
                self.bot.send_message(message.chat.id, 
                    "🤔 Я не понимаю это сообщение. Используйте /help для справки или /start для начала интервью.")
    
    def send_next_question(self, chat_id, user_id):
        session = self.db.get_session()
        interview = session.query(Interview).filter(
            Interview.user_id == user_id,
            Interview.status == 'active'
        ).first()
        
        if not interview:
            self.bot.send_message(chat_id, "❌ Активное интервью не найдено. Используйте /start")
            return
        
        question = self.db.get_next_question_for_interview(interview.id)
        
        if question:
            answered, total = self.db.get_interview_progress(interview.id)
            progress_text = f"📊 Прогресс: {answered}/{total} вопросов"
            
            if question.question_type == 'choice':
                # Финансовый вопрос с выбором
                question_text = f"""
{progress_text}

❓ **Вопрос {answered + 1}:**
{question.text}

📊 **Рыночная ситуация:**
{question.market_context}

**Варианты для выбора:**

🅰️ **Продукт А:** {question.option_a}
_{question.option_a_details}_

🅱️ **Продукт Б:** {question.option_b}
_{question.option_b_details}_
                """
                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton("🅰️ Выбрать А", callback_data=f"choose_A_{question.id}"),
                    types.InlineKeyboardButton("🅱️ Выбрать Б", callback_data=f"choose_B_{question.id}")
                )
                markup.add(types.InlineKeyboardButton("💡 Консультация с GigaChat", callback_data=f"consult_{question.id}"))
                self.bot.send_message(chat_id, question_text, reply_markup=markup, parse_mode='Markdown')
                
            elif question.question_type == 'text':
                # Текстовый вопрос
                question_text = f"""
{progress_text}

❓ **Вопрос {answered + 1}:**
{question.text}

📝 **Напишите ваш ответ следующим сообщением.**
                """
                
                # Устанавливаем состояние ожидания текстового ответа
                self.waiting_for_text_answer[user_id] = question.id
                
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("⏭ Пропустить вопрос", callback_data=f"skip_{question.id}"))
                self.bot.send_message(chat_id, question_text, reply_markup=markup, parse_mode='Markdown')
        else:
            # Все вопросы пройдены
            answered, total = self.db.get_interview_progress(interview.id)
            end_text = f"""
🎉 **Поздравляем!**

Вы ответили на все {total} вопросов в нашем финансовом интервью!

📊 **Ваш результат: {answered}/{total}**

Теперь вы можете завершить интервью и посмотреть подробную статистику ваших финансовых решений и консультаций с GigaChat.
            """
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Завершить интервью", callback_data="end_interview"))
            self.bot.send_message(chat_id, end_text, reply_markup=markup, parse_mode='Markdown')
    
    def start_polling(self):
        print("🤖 Telegram бот с GigaChat запущен!")
        try:
            self.bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"❌ Ошибка infinity_polling: {e}")
            raise
