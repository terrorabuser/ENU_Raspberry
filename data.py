import sqlite3
import time
import os
import threading
from datetime import datetime
from config import DB_PATH

class DBHandler:
    def __init__(self):
        self.db_path = DB_PATH

    def setup_db(self):
        """Создание таблицы в БД, если она не существует, или создание новой базы данных"""
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            print(f"Старая база данных {self.db_path} удалена.")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''  
            CREATE TABLE IF NOT EXISTS content (
                content_id INTEGER PRIMARY KEY,
                file_path TEXT,
                start_time TEXT,
                end_time TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print(f"Новая база данных {self.db_path} создана.")

    def save_content(self, data):
        """Сохранение данных в БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO content
            (content_id, file_path, start_time, end_time)
            VALUES (?, ?, ?, ?)
        ''', (
            data["content_id"],
            data["file_path"],
            data["start_time"],
            data["end_time"]
        ))
        conn.commit()
        conn.close()
        print(f"Контент {data['content_id']} сохранён в БД")
        
    def get_available_content(self):
        """Поиск контента, подходящего для показа в данный момент"""
        current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM content
            WHERE start_time <= ? AND end_time >= ?
        ''', (current_time, current_time))
        content = cursor.fetchall()
        conn.close()

        # Преобразуем результат в список словарей
        return [{
            "content_id": row[0],
            "file_path": row[1],
            "start_time": row[2],
            "end_time": row[3]
        } for row in content]
            
class ContentHandler:
    def __init__(self, db_handler, manager):
        self.manager = manager
        self.db_handler = db_handler
        self.active_content = {}
        self.lock = threading.Lock()

    def send_monitor_status(self, content_id, status_id):
        data = {
            'content_id': content_id,
            'status_id': status_id
        }
        self.manager.sio.emit('MonitorResponse', data)

    def find_content_to_show(self):
        """Ищем и обновляем список подходящего контента"""
        available_content = self.db_handler.get_available_content()

        if not available_content:
            print("Подходящий контент не найден.")
            return

        print("Подходящий контент найден для показа:")

        for item in available_content:
            cid = item["content_id"]

            with self.lock:
                if cid not in self.active_content:
                    self.active_content[cid] = item
                    print(f"Добавлен Content ID: {cid}")
                    self.send_monitor_status(cid, 1)
                    self.start_timer_for_content(cid, item["end_time"])
                else:
                    print(f"Контент ID {cid} уже активен")

    def start_timer_for_content(self, content_id, end_time_str):
        """Запускает таймер на удаление контента после end_time"""
        current_time = datetime.strptime((datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'), '%Y-%m-%dT%H:%M:%S.%fZ')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        delay = (end_time - current_time).total_seconds()

        if delay > 0:
            print(f"Установлен таймер на {delay:.1f} сек для контента {content_id}")
            threading.Timer(delay, self.remove_content_by_id, args=(content_id,)).start()
        else:
            print(f"Контент {content_id} уже просрочен — удаляется сразу")
            self.send_monitor_status(content_id, 1)
            self.remove_content_by_id(content_id)

    def remove_content_by_id(self, content_id):
        """Удаляет контент из активного списка по завершению таймера"""
        with self.lock:
            if content_id in self.active_content:
                del self.active_content[content_id]
                self.send_monitor_status(content_id, 2)
                print(f"Контент {content_id} удалён из активного списка")

    def start_searching_for_content(self):
        """Запускает бесконечную проверку наличия нового контента"""
        while True:
            self.find_content_to_show()
            print("Ищем данные")
            # print(self.active_content)
            time.sleep(20)
            
    def find_content(self):
        threading.Thread(target=self.start_searching_for_content, daemon=True).start()
        