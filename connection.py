import threading
import socketio
import time
from config import SERVER_URL

class DataManager:
    def __init__(self, db_handler):
        self.sio = socketio.Client(logger=True, engineio_logger=True)
        self.mac_address = "AA:BB:CC:DD:EE:01"
        
        self.db_handler = db_handler
        
        self.max_attempts = 5
        self.initial_delay = 2
        self.cooldown_period = 15
        
        self.stop_event = threading.Event()

        self.sio.on("content", self.get_data)

    def connect(self):
        threading.Thread(target=self._connection_handler, daemon=True).start()
        

    def _connection_handler(self):
        while not self.stop_event.is_set():
            if not self.sio.connected:
                if self._connect_with_retry():
                    try:
                        self.sio.wait()
                    except Exception as e:
                        pass
                else:
                    time.sleep(self.cooldown_period)
            else: 
                time.sleep(1)

    def _connect_with_retry(self):
        attempt = 0
        print(SERVER_URL)
        delay = self.initial_delay

        while attempt < self.max_attempts:
            try:
                self.sio.connect(SERVER_URL, headers={"MacAddress": self.mac_address})
                return True
            except Exception as e:
                attempt += 1
                time.sleep(delay)
                delay *= 2
                
        return False

    def get_data(self, data):
        if isinstance(data, dict):
            self.db_handler.save_content(data)

        elif isinstance(data, list):
            for item in data:
                self.db_handler.save_content(item)
