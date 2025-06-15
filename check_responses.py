# check_responses.py
from modules.database import DatabaseManager, Interview, Response, Question, AIConsultation

def check_database_responses():
    print("🔍 Проверяем сохраненные ответы в базе данных...")
    
    db = DatabaseManager()
    session = db.get_session()
    
    # Проверяем количество записей в каждой таблице
    print("\n📊 Статистика базы данных:")
    
    questions_count = session.query(Question).count()
    interviews_count = session.query(Interview).count()
    responses_count = session.query(Response).count()
    consultations_count = session.query(AIConsultation).count()
    
    print(f"   Вопросов: {questions_count}")
    print(f"   Интервью: {interviews_count}")
    print(f"   Ответов: {responses_count}")
    print(f"   Консультаций: {consultations_count}")
    
    # Показываем все интервью
    print("\n🎤 Все интервью:")
    interviews = session.query(Interview).all()
    for interview in interviews:
        print(f"   ID: {interview.id} | User: {interview.user_id} | Username: {interview.username}")
        print(f"   Начато: {interview.started_at} | Статус: {interview.status}")
    
    # Показываем все ответы
    print("\n💬 Все ответы:")
    responses = session.query(Response).all()
    for response in responses:
        print(f"   ID: {response.id} | Interview: {response.interview_id} | Question: {response.question_id}")
        print(f"   Выбор: {response.selected_option} | Ответ: {response.answer_text}")
        print(f"   Время: {response.timestamp}")
        print("   ---")
    
    # Показываем детальную информацию о последнем интервью
    if interviews:
        last_interview = interviews[-1]
        print(f"\n🔍 Детали последнего интервью (ID: {last_interview.id}):")
        
        # Ответы этого интервью
        interview_responses = session.query(Response).filter(
            Response.interview_id == last_interview.id
        ).all()
        
        print(f"   Количество ответов: {len(interview_responses)}")
        
        for resp in interview_responses:
            # Получаем вопрос
            question = session.query(Question).filter(Question.id == resp.question_id).first()
            if question:
                print(f"   Вопрос: {question.text[:50]}...")
                print(f"   Выбран продукт: {resp.selected_option}")
                if question.selected_option == 'A':
                    print(f"   Выбранный продукт: {question.option_a}")
                elif resp.selected_option == 'B':
                    print(f"   Выбранный продукт: {question.option_b}")
    
    print("\n✅ Проверка завершена!")

if __name__ == "__main__":
    check_database_responses()
