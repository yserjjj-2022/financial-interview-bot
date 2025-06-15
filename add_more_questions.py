# add_more_questions.py
from modules.database import DatabaseManager

def add_multiple_questions():
    db = DatabaseManager()
    
    questions = [
        {
            "text": "Выберите инструмент для краткосрочных инвестиций:",
            "market_context": "Ставка ЦБ: 16%, краткосрочная волатильность высокая",
            "option_a": "Краткосрочные депозиты до 3 месяцев",
            "option_b": "Краткосрочные облигации",
            "option_a_details": "Ставка 14-15%, полная гарантия возврата",
            "option_b_details": "Доходность 12-13%, возможность досрочной продажи"
        },
        {
            "text": "Выберите стратегию в условиях высокой инфляции:",
            "market_context": "Инфляция 5.2%, реальные ставки близки к нулю",
            "option_a": "Валютные депозиты",
            "option_b": "Индексируемые облигации",
            "option_a_details": "Защита от девальвации рубля",
            "option_b_details": "Защита от инфляции, привязка к индексу цен"
        }
    ]
    
    for i, q in enumerate(questions, 1):
        question_id = db.add_financial_question(**q)
        print(f"✅ Вопрос {i} добавлен с ID: {question_id}")

if __name__ == "__main__":
    add_multiple_questions()
