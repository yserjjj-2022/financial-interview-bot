# add_test_data.py
from modules.database import DatabaseManager, Question

def add_test_data():
    print("📝 Добавляем тестовые данные...")
    
    db = DatabaseManager()
    
    # Добавляем финансовый вопрос
    print("1. Добавляем финансовый вопрос...")
    financial_q_id = db.add_financial_question(
        text="Выберите наиболее подходящий инвестиционный продукт:",
        market_context="Ставка ЦБ: 16%, инфляция: 5.2%, волатильность рынка: высокая",
        option_a="Банковский депозит 15% годовых",
        option_b="Облигации федерального займа (ОФЗ)",
        option_a_details="Гарантированная доходность, страхование АСВ до 1.4 млн руб",
        option_b_details="Доходность 13-14%, возможность досрочной продажи"
    )
    print(f"✅ Финансовый вопрос добавлен с ID: {financial_q_id}")
    
    # Проверяем количество вопросов
    session = db.get_session()
    count = session.query(Question).count()
    print(f"✅ Всего вопросов в базе: {count}")
    
    # Получаем случайный вопрос
    random_q = db.get_random_question()
    if random_q:
        print(f"✅ Случайный вопрос: {random_q.text[:50]}...")
        print(f"   Тип: {random_q.question_type}")
        print(f"   Категория: {random_q.category}")
        print(f"   Продукт А: {random_q.option_a}")
        print(f"   Продукт Б: {random_q.option_b}")
        print(f"   Рыночный контекст: {random_q.market_context}")
    
    print("\n🎉 Тестовые данные добавлены успешно!")

if __name__ == "__main__":
    add_test_data()
