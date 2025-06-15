# run_bot.py
from modules.telegram_handler import TelegramHandler

def main():
    try:
        bot_handler = TelegramHandler()
        bot_handler.start_polling()
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
