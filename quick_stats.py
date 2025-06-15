# quick_stats.py
from modules.database import DatabaseManager, Interview, Response, Question, AIConsultation

def quick_stats():
    print("⚡ БЫСТРАЯ СТАТИСТИКА")
    print("=" * 30)
    
    db = DatabaseManager()
    session = db.get_session()
    
    # Основные цифры
    interviews = session.query(Interview).count()
    completed = session.query(Interview).filter(Interview.status == 'completed').count()
    responses = session.query(Response).count()
    consultations = session.query(AIConsultation).count()
    
    print(f"🎤 Интервью: {interviews} (завершено: {completed})")
    print(f"📝 Ответов: {responses}")
    print(f"💡 Консультаций: {consultations}")
    
    # Статистика выборов
    choice_a = session.query(Response).filter(Response.selected_option == 'A').count()
    choice_b = session.query(Response).filter(Response.selected_option == 'B').count()
    
    if choice_a + choice_b > 0:
        print(f"\n📊 Выборы продуктов:")
        print(f"   Продукт А: {choice_a} ({choice_a/(choice_a+choice_b)*100:.1f}%)")
        print(f"   Продукт Б: {choice_b} ({choice_b/(choice_a+choice_b)*100:.1f}%)")
    
    # Последние активности
    last_interview = session.query(Interview).order_by(Interview.started_at.desc()).first()
    if last_interview:
        print(f"\n🕐 Последнее интервью: {last_interview.username} ({last_interview.status})")
    
    print("=" * 30)

if __name__ == "__main__":
    quick_stats()
