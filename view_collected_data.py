# view_collected_data.py
from modules.database import DatabaseManager, Interview, Response, Question, AIConsultation
from datetime import datetime
import pytz
import os

def view_all_data():
    print("📊 АНАЛИЗ СОБРАННЫХ ДАННЫХ")
    print("=" * 50)
    
    db = DatabaseManager()
    session = db.get_session()
    moscow_tz = pytz.timezone('Europe/Moscow')
    
    def utc_to_moscow(utc_dt):
        if utc_dt and utc_dt.tzinfo is None:
            utc_dt = pytz.utc.localize(utc_dt)
        return utc_dt.astimezone(moscow_tz) if utc_dt else None
    
    # 1. ОБЩАЯ СТАТИСТИКА
    print("\n🔢 ОБЩАЯ СТАТИСТИКА:")
    
    total_interviews = session.query(Interview).count()
    completed_interviews = session.query(Interview).filter(Interview.status == 'completed').count()
    active_interviews = session.query(Interview).filter(Interview.status == 'active').count()
    total_responses = session.query(Response).count()
    total_consultations = session.query(AIConsultation).count()
    total_questions = session.query(Question).filter(Question.is_active == True).count()
    
    print(f"   Всего интервью: {total_interviews}")
    print(f"   Завершенных: {completed_interviews}")
    print(f"   Активных: {active_interviews}")
    print(f"   Всего ответов: {total_responses}")
    print(f"   Консультаций с ИИ: {total_consultations}")
    print(f"   Активных вопросов: {total_questions}")
    
    # 2. ДЕТАЛИ ИНТЕРВЬЮ
    print("\n🎤 ДЕТАЛИ ВСЕХ ИНТЕРВЬЮ:")
    interviews = session.query(Interview).order_by(Interview.started_at.desc()).all()
    
    for i, interview in enumerate(interviews, 1):
        started_msk = utc_to_moscow(interview.started_at)
        completed_msk = utc_to_moscow(interview.completed_at) if interview.completed_at else None
        
        # Подсчитываем ответы и консультации для этого интервью
        responses_count = session.query(Response).filter(Response.interview_id == interview.id).count()
        consultations_count = session.query(AIConsultation).filter(AIConsultation.interview_id == interview.id).count()
        
        duration = ""
        if interview.completed_at:
            dur = interview.completed_at - interview.started_at
            minutes = int(dur.total_seconds() // 60)
            seconds = int(dur.total_seconds() % 60)
            duration = f"{minutes}м {seconds}с"
        
        print(f"\n   {i}. ID: {interview.id} | User: {interview.user_id}")
        print(f"      Username: {interview.username}")
        print(f"      Статус: {interview.status}")
        print(f"      Начато: {started_msk.strftime('%d.%m.%Y %H:%M:%S') if started_msk else 'N/A'}")
        print(f"      Завершено: {completed_msk.strftime('%d.%m.%Y %H:%M:%S') if completed_msk else 'Не завершено'}")
        print(f"      Длительность: {duration if duration else 'В процессе'}")
        print(f"      Ответов: {responses_count}/{total_questions}")
        print(f"      Консультаций: {consultations_count}")
    
    # 3. АНАЛИЗ ОТВЕТОВ НА ВОПРОСЫ
    print("\n📝 АНАЛИЗ ОТВЕТОВ ПО ВОПРОСАМ:")
    questions = session.query(Question).filter(Question.is_active == True).order_by(Question.id).all()
    
    for question in questions:
        responses = session.query(Response).filter(Response.question_id == question.id).all()
        
        if question.question_type == 'choice':
            choice_a = len([r for r in responses if r.selected_option == 'A'])
            choice_b = len([r for r in responses if r.selected_option == 'B'])
            
            print(f"\n   Вопрос {question.id}: {question.text[:60]}...")
            print(f"   Тип: {question.question_type}")
            print(f"   Всего ответов: {len(responses)}")
            print(f"   Выбор А ({question.option_a}): {choice_a}")
            print(f"   Выбор Б ({question.option_b}): {choice_b}")
            
            if len(responses) > 0:
                percent_a = (choice_a / len(responses)) * 100
                percent_b = (choice_b / len(responses)) * 100
                print(f"   Процентное соотношение: А={percent_a:.1f}% | Б={percent_b:.1f}%")
        
        elif question.question_type == 'text':
            print(f"\n   Вопрос {question.id}: {question.text[:60]}...")
            print(f"   Тип: {question.question_type}")
            print(f"   Всего ответов: {len(responses)}")
            
            # Показываем несколько примеров ответов
            for j, response in enumerate(responses[:3], 1):
                if response.answer_text and response.answer_text != "[Вопрос пропущен]":
                    print(f"     Ответ {j}: {response.answer_text[:100]}...")
    
    # 4. АНАЛИЗ КОНСУЛЬТАЦИЙ С ИИ
    print("\n💡 АНАЛИЗ КОНСУЛЬТАЦИЙ С ИИ:")
    consultations = session.query(AIConsultation).order_by(AIConsultation.timestamp.desc()).all()
    
    if consultations:
        # Группируем по типам консультаций
        consultation_types = {}
        for cons in consultations:
            cons_type = cons.consultation_type or 'unknown'
            if cons_type not in consultation_types:
                consultation_types[cons_type] = 0
            consultation_types[cons_type] += 1
        
        print(f"   Всего консультаций: {len(consultations)}")
        print("   По типам:")
        for cons_type, count in consultation_types.items():
            print(f"     {cons_type}: {count}")
        
        print("\n   Последние 5 консультаций:")
        for i, cons in enumerate(consultations[:5], 1):
            timestamp_msk = utc_to_moscow(cons.timestamp)
            question = session.query(Question).filter(Question.id == cons.question_id).first()
            
            print(f"\n     {i}. Время: {timestamp_msk.strftime('%d.%m %H:%M') if timestamp_msk else 'N/A'}")
            print(f"        Вопрос к ИИ: {cons.user_query[:80]}...")
            print(f"        К вопросу: {question.text[:50] if question else 'N/A'}...")
            print(f"        Ответ ИИ: {cons.ai_response[:100]}...")
    else:
        print("   Консультаций пока нет")
    
    # 5. ЭКСПОРТ ДАННЫХ
    print("\n📤 ЭКСПОРТ ДАННЫХ:")
    print("   Для экспорта в CSV используйте: python export_data.py")
    print("   Файлы будут сохранены в папку: output/")
    
    # Проверяем, есть ли уже экспортированные файлы
    if os.path.exists('output'):
        csv_files = [f for f in os.listdir('output') if f.endswith('.csv')]
        if csv_files:
            print(f"   Найдено {len(csv_files)} экспортированных файлов:")
            for file in sorted(csv_files)[-5:]:  # Показываем последние 5
                print(f"     - {file}")
    
    print("\n" + "=" * 50)
    print("✅ Анализ завершен!")

if __name__ == "__main__":
    view_all_data()
