# clean_output.py
import os
import shutil
from datetime import datetime

def clean_output_folder():
    """Очищает папку output от старых экспортированных файлов"""
    
    output_dir = 'output'
    
    if not os.path.exists(output_dir):
        print("📁 Папка output не существует")
        return
    
    files = os.listdir(output_dir)
    csv_files = [f for f in files if f.endswith('.csv')]
    
    if not csv_files:
        print("📁 В папке output нет CSV файлов для удаления")
        return
    
    print(f"🗑 Найдено {len(csv_files)} CSV файлов в папке output:")
    for file in csv_files:
        print(f"   - {file}")
    
    confirm = input("\nВы уверены, что хотите удалить все файлы? (y/N): ")
    
    if confirm.lower() in ['y', 'yes', 'да']:
        for file in csv_files:
            file_path = os.path.join(output_dir, file)
            os.remove(file_path)
            print(f"✅ Удален: {file}")
        
        print(f"\n🎉 Удалено {len(csv_files)} файлов из папки output")
    else:
        print("❌ Очистка отменена")

if __name__ == "__main__":
    clean_output_folder()
