import threading
from connection import DataManager
from display import DisplayController
from data import DBHandler, ContentHandler
from authorizate import MonitorAuthentication
from auto_launch import setup_autostart
        
if __name__ == "__main__":
    setup_autostart()
    db = DBHandler()
    db.setup_db()

    manager = DataManager(db_handler=db)
    auth = MonitorAuthentication(manager)
    auth.screen_info()
    
    if True:
        manager.connect()
        
        content = ContentHandler(db, manager)
        content.find_content()
    
        images = DisplayController(manager, content, auth)
        images.display()
        
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Завершение программы")
        
        
