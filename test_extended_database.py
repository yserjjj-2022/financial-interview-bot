# test_extended_database.py
from modules.database import DatabaseManager, Question, Interview, Response, AIConsultation

def test_extended_database():
    print("🔍 Тестирование расширенной структуры БД...")
    
    try:
        # Создаем менеджер БД
        db = DatabaseManager()
        
        # Создаем таблицы
        print("1. Создание таблиц...")
        db.create_tables()
        
        # Проверяем все таблицы
        session = db.get_session()
        
        tables_to_check = [
            ('questions', Question),
            ('interviews', Interview), 
            ('responses', Response),
            ('ai_consultations', AIConsultation)
        ]
        
        print("2. Проверка созданных таблиц...")
        for table_name, model_class in tables_to_check:
            try:
                count = session.query(model_class).count()
                print(f"✅ Таблица {table_name}: {count} записей")
            except Exception as e:
                print(f"❌ Ошибка с таблицей {table_name}: {e}")
        
        print("\n🎉 Тестирование завершено успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_extended_database()
