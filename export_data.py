# export_data.py
import csv
from datetime import datetime
import pytz
import os
from modules.database import DatabaseManager, Interview, Response, Question, AIConsultation

def export_to_csv():
    print("📤 Экспорт данных в CSV файлы...")
    
    db = DatabaseManager()
    session = db.get_session()
    moscow_tz = pytz.timezone('Europe/Moscow')
    
    def utc_to_moscow_str(utc_dt):
        if utc_dt and utc_dt.tzinfo is None:
            utc_dt = pytz.utc.localize(utc_dt)
        return utc_dt.astimezone(moscow_tz).strftime('%Y-%m-%d %H:%M:%S') if utc_dt else ''
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 Создана папка: {output_dir}")
    
    # 1. ЭКСПОРТ ИНТЕРВЬЮ
    interviews = session.query(Interview).all()
    with open(f'{output_dir}/interviews_{timestamp}.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'User_ID', 'Username', 'Status', 'Started_At', 'Completed_At', 'Duration_Minutes'])
        
        for interview in interviews:
            duration_minutes = ''
            if interview.completed_at:
                duration = interview.completed_at - interview.started_at
                duration_minutes = round(duration.total_seconds() / 60, 2)
            
            writer.writerow([
                interview.id,
                interview.user_id,
                interview.username,
                interview.status,
                utc_to_moscow_str(interview.started_at),
                utc_to_moscow_str(interview.completed_at),
                duration_minutes
            ])
    
    print(f"✅ Интервью экспортированы в {output_dir}/interviews_{timestamp}.csv")
    
    # 2. ЭКСПОРТ ОТВЕТОВ
    responses = session.query(Response).join(Question).all()
    with open(f'{output_dir}/responses_{timestamp}.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Response_ID', 'Interview_ID', 'Question_ID', 'Question_Text', 'Question_Type', 
                        'Selected_Option', 'Answer_Text', 'Consultations_Count', 'Timestamp'])
        
        for response in responses:
            question = session.query(Question).filter(Question.id == response.question_id).first()
            writer.writerow([
                response.id,
                response.interview_id,
                response.question_id,
                question.text if question else '',
                question.question_type if question else '',
                response.selected_option or '',
                response.answer_text or '',
                response.consultations_count or 0,
                utc_to_moscow_str(response.timestamp)
            ])
    
    print(f"✅ Ответы экспортированы в {output_dir}/responses_{timestamp}.csv")
    
    # 3. ЭКСПОРТ КОНСУЛЬТАЦИЙ
    consultations = session.query(AIConsultation).all()
    with open(f'{output_dir}/consultations_{timestamp}.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Consultation_ID', 'Interview_ID', 'Question_ID', 'User_Query', 
                        'AI_Response', 'Consultation_Type', 'Timestamp'])
        
        for consultation in consultations:
            writer.writerow([
                consultation.id,
                consultation.interview_id,
                consultation.question_id,
                consultation.user_query,
                consultation.ai_response,
                consultation.consultation_type or '',
                utc_to_moscow_str(consultation.timestamp)
            ])
    
    print(f"✅ Консультации экспортированы в {output_dir}/consultations_{timestamp}.csv")
    
    # 4. ЭКСПОРТ СВОДНОЙ СТАТИСТИКИ
    with open(f'{output_dir}/summary_stats_{timestamp}.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Metric', 'Value'])
        
        total_interviews = session.query(Interview).count()
        completed_interviews = session.query(Interview).filter(Interview.status == 'completed').count()
        total_responses = session.query(Response).count()
        total_consultations = session.query(AIConsultation).count()
        
        # Статистика по выборам
        choice_a_count = session.query(Response).filter(Response.selected_option == 'A').count()
        choice_b_count = session.query(Response).filter(Response.selected_option == 'B').count()
        
        writer.writerow(['Total_Interviews', total_interviews])
        writer.writerow(['Completed_Interviews', completed_interviews])
        writer.writerow(['Total_Responses', total_responses])
        writer.writerow(['Total_Consultations', total_consultations])
        writer.writerow(['Choice_A_Count', choice_a_count])
        writer.writerow(['Choice_B_Count', choice_b_count])
        
        if choice_a_count + choice_b_count > 0:
            choice_a_percent = (choice_a_count / (choice_a_count + choice_b_count)) * 100
            choice_b_percent = (choice_b_count / (choice_a_count + choice_b_count)) * 100
            writer.writerow(['Choice_A_Percent', round(choice_a_percent, 2)])
            writer.writerow(['Choice_B_Percent', round(choice_b_percent, 2)])
    
    print(f"✅ Сводная статистика экспортирована в {output_dir}/summary_stats_{timestamp}.csv")
    print(f"\n📊 Все файлы сохранены в папке {output_dir}/ с меткой времени: {timestamp}")

if __name__ == "__main__":
    export_to_csv()
