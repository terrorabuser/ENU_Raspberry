import threading
from connection import DataManager
from display import DisplayController
from data import DBHandler, ContentHandler
from authorizate import MonitorAuthentication


if __name__ == "__main__":
    
    db = DBHandler()
    db.setup_db()

    manager = DataManager(db_handler=db)
    auth = MonitorAuthentication(manager)
    auth.screen_info()
    
    
    if auth.verification_mac():
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
        
        
