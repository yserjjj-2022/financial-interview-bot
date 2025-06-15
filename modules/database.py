# modules/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, func, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os
import logging

Base = declarative_base()

class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    category = Column(String(100))
    difficulty = Column(Integer, default=1)
    explanation = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Поля для финансовых вопросов
    question_type = Column(String(50), default='text')
    market_context = Column(Text)
    option_a = Column(Text)
    option_b = Column(Text)
    option_a_details = Column(Text)
    option_b_details = Column(Text)

class Interview(Base):
    __tablename__ = 'interviews'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False)
    username = Column(String(100))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(20), default='active')
    
    # Связи
    responses = relationship("Response", back_populates="interview", cascade="all, delete-orphan")
    consultations = relationship("AIConsultation", back_populates="interview", cascade="all, delete-orphan")

class Response(Base):
    __tablename__ = 'responses'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    answer_text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Поля для финансовых решений
    selected_option = Column(String(10))
    consultations_count = Column(Integer, default=0)
    decision_confidence = Column(Integer)
    decision_reasoning = Column(Text)
    
    # Связи
    interview = relationship("Interview", back_populates="responses")
    question = relationship("Question")

class AIConsultation(Base):
    __tablename__ = 'ai_consultations'
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    user_query = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    consultation_type = Column(String(50))
    
    # Связи
    interview = relationship("Interview", back_populates="consultations")
    question = relationship("Question")

class DatabaseManager:
    def __init__(self, db_url=None):
        if not db_url:
            user = os.getenv('USER')
            db_url = f'postgresql://{user}@localhost/interview_bot_db'
        
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False)
        self.session = None
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def create_tables(self):
        """Создает все таблицы в базе данных"""
        try:
            Base.metadata.create_all(self.engine)
            self.logger.info("✅ Таблицы созданы успешно")
            print("✅ Таблицы созданы")
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания таблиц: {e}")
            print(f"❌ Ошибка создания таблиц: {e}")
            raise
        
    def get_session(self):
        """Получает сессию для работы с БД"""
        if not self.session:
            try:
                Session = sessionmaker(bind=self.engine)
                self.session = Session()
                self.logger.debug("Сессия базы данных создана")
            except Exception as e:
                self.logger.error(f"❌ Ошибка создания сессии: {e}")
                print(f"❌ Ошибка создания сессии: {e}")
                raise
        return self.session
    
    def close_session(self):
        """Закрывает текущую сессию"""
        if self.session:
            try:
                self.session.close()
                self.session = None
                self.logger.debug("Сессия базы данных закрыта")
            except Exception as e:
                self.logger.error(f"❌ Ошибка закрытия сессии: {e}")
    
    def add_financial_question(self, text, market_context, option_a, option_b, 
                              option_a_details, option_b_details, category="financial_choice"):
        """Добавляет вопрос с выбором финансовых продуктов"""
        # Валидация данных
        if not text or not market_context or not option_a or not option_b:
            raise ValueError("Обязательные поля (text, market_context, option_a, option_b) не могут быть пустыми")
        
        try:
            session = self.get_session()
            question = Question(
                text=text.strip(),
                category=category,
                question_type='choice',
                market_context=market_context.strip(),
                option_a=option_a.strip(),
                option_b=option_b.strip(),
                option_a_details=option_a_details.strip() if option_a_details else None,
                option_b_details=option_b_details.strip() if option_b_details else None
            )
            session.add(question)
            session.commit()
            
            self.logger.info(f"✅ Финансовый вопрос добавлен с ID: {question.id}")
            return question.id
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"❌ Ошибка добавления финансового вопроса: {e}")
            raise
    
    def add_text_question(self, text, category="general", explanation=None):
        """Добавляет обычный текстовый вопрос"""
        if not text:
            raise ValueError("Текст вопроса не может быть пустым")
        
        try:
            session = self.get_session()
            question = Question(
                text=text.strip(),
                category=category,
                question_type='text',
                explanation=explanation.strip() if explanation else None
            )
            session.add(question)
            session.commit()
            
            self.logger.info(f"✅ Текстовый вопрос добавлен с ID: {question.id}")
            return question.id
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"❌ Ошибка добавления текстового вопроса: {e}")
            raise
    
    def get_next_question_for_interview(self, interview_id):
        """Получает следующий неотвеченный вопрос для конкретного интервью"""
        try:
            session = self.get_session()
            
            # Получаем ID вопросов, на которые уже ответили в этом интервью
            answered_question_ids = session.query(Response.question_id).filter(
                Response.interview_id == interview_id
            ).scalar_subquery()
            
            # Находим первый неотвеченный вопрос (по порядку ID)
            next_question = session.query(Question).filter(
                Question.is_active == True,
                Question.id.notin_(answered_question_ids)
            ).order_by(Question.id).first()
            
            return next_question
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения следующего вопроса: {e}")
            return None
    
    def get_interview_progress(self, interview_id):
        """Получает прогресс интервью"""
        try:
            session = self.get_session()
            
            total_questions = session.query(Question).filter(Question.is_active == True).count()
            answered_questions = session.query(Response).filter(
                Response.interview_id == interview_id
            ).count()
            
            return answered_questions, total_questions
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения прогресса интервью: {e}")
            return 0, 0
    
    def save_consultation(self, interview_id, question_id, user_query, ai_response, consultation_type="product_advice"):
        """Сохраняет консультацию с ИИ"""
        if not user_query or not ai_response:
            raise ValueError("Запрос пользователя и ответ ИИ не могут быть пустыми")
        
        try:
            session = self.get_session()
            consultation = AIConsultation(
                interview_id=interview_id,
                question_id=question_id,
                user_query=user_query.strip(),
                ai_response=ai_response.strip(),
                consultation_type=consultation_type
            )
            session.add(consultation)
            session.commit()
            
            # Обновляем счетчик консультаций в ответе (если ответ уже существует)
            response = session.query(Response).filter(
                Response.interview_id == interview_id,
                Response.question_id == question_id
            ).first()
            
            if response:
                response.consultations_count = session.query(AIConsultation).filter(
                    AIConsultation.interview_id == interview_id,
                    AIConsultation.question_id == question_id
                ).count()
                session.commit()
            
            self.logger.info(f"✅ Консультация сохранена с ID: {consultation.id}")
            return consultation.id
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"❌ Ошибка сохранения консультации: {e}")
            raise
    
    def get_random_question(self, category=None):
        """Получает случайный вопрос (для совместимости со старым кодом)"""
        try:
            session = self.get_session()
            query = session.query(Question).filter(Question.is_active == True)
            if category:
                query = query.filter(Question.category == category)
            return query.order_by(func.random()).first()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения случайного вопроса: {e}")
            return None
    
    def get_question_by_id(self, question_id):
        """Получает вопрос по ID"""
        try:
            session = self.get_session()
            return session.query(Question).filter(Question.id == question_id).first()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения вопроса по ID: {e}")
            return None
    
    def get_interview_by_user_id(self, user_id, status='active'):
        """Получает интервью пользователя по статусу"""
        try:
            session = self.get_session()
            return session.query(Interview).filter(
                Interview.user_id == user_id,
                Interview.status == status
            ).first()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения интервью пользователя: {e}")
            return None
    
    def get_interview_statistics(self, interview_id):
        """Получает подробную статистику интервью"""
        try:
            session = self.get_session()
            
            # Основная информация об интервью
            interview = session.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                return None
            
            # Статистика ответов
            responses = session.query(Response).filter(Response.interview_id == interview_id).all()
            
            # Подсчет выборов
            choice_a_count = sum(1 for r in responses if r.selected_option == 'A')
            choice_b_count = sum(1 for r in responses if r.selected_option == 'B')
            
            # Статистика консультаций
            consultations_count = session.query(AIConsultation).filter(
                AIConsultation.interview_id == interview_id
            ).count()
            
            # Общее количество вопросов
            total_questions = session.query(Question).filter(Question.is_active == True).count()
            
            return {
                'interview': interview,
                'responses_count': len(responses),
                'choice_a_count': choice_a_count,
                'choice_b_count': choice_b_count,
                'consultations_count': consultations_count,
                'total_questions': total_questions,
                'completion_rate': len(responses) / total_questions if total_questions > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения статистики интервью: {e}")
            return None
    
    def deactivate_question(self, question_id):
        """Деактивирует вопрос (помечает как неактивный)"""
        try:
            session = self.get_session()
            question = session.query(Question).filter(Question.id == question_id).first()
            
            if question:
                question.is_active = False
                session.commit()
                self.logger.info(f"✅ Вопрос {question_id} деактивирован")
                return True
            else:
                self.logger.warning(f"⚠️ Вопрос {question_id} не найден")
                return False
                
        except Exception as e:
            session.rollback()
            self.logger.error(f"❌ Ошибка деактивации вопроса: {e}")
            return False
    
    def get_all_questions(self, active_only=True):
        """Получает все вопросы"""
        try:
            session = self.get_session()
            query = session.query(Question)
            
            if active_only:
                query = query.filter(Question.is_active == True)
                
            return query.order_by(Question.id).all()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения всех вопросов: {e}")
            return []
    
    def cleanup_old_interviews(self, days_old=30):
        """Удаляет старые завершенные интервью"""
        try:
            from datetime import timedelta
            session = self.get_session()
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_interviews = session.query(Interview).filter(
                Interview.status.in_(['completed', 'restarted']),
                Interview.completed_at < cutoff_date
            ).all()
            
            count = len(old_interviews)
            
            for interview in old_interviews:
                session.delete(interview)
            
            session.commit()
            self.logger.info(f"✅ Удалено {count} старых интервью")
            return count
            
        except Exception as e:
            if hasattr(self, 'session') and self.session:
                self.session.rollback()
            self.logger.error(f"❌ Ошибка очистки старых интервью: {e}")
            return 0
    
    def __del__(self):
        """Деструктор - закрывает сессию при удалении объекта"""
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
        except:
            pass  # Игнорируем все ошибки в деструкторе
