import os
from config import FILE_TYPES
import cv2
import numpy as np
import requests
import time
import threading
from pdf2image import convert_from_path, convert_from_bytes
from io import BytesIO
import RPi.GPIO as GPIO

class DisplayController:
    def __init__(self, manager, content_handler, auth, reverse_logic=False):
        self.screen_on = True
        self.photo_opened = False
        self.relay_pin = 17
        self.reverse_logic = reverse_logic
        self.content_handler = content_handler
        self.manager = manager
        self.auth = auth
        self._setup_gpio()
        
    def get_file_type(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        for category, extensions in FILE_TYPES.items():
            if  ext in extensions:
                return category
        return None
    
    def send_monitor_status(self, sio, content, status_id):
         data = {
             'content_id': content['content_id'],
             'user_id': content['user_id'],
             'status_id': status_id
         }
         sio.emit('MonitorResponse', data)
    
    def _setup_gpio(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.relay_pin, GPIO.OUT)
        self.turn_off_screen()  # По умолчанию отключаем монитор при старте
    
    def turn_on(self):
        state = GPIO.HIGH if self.reverse_logic else GPIO.LOW
        GPIO.output(self.relay_pin, state)
        time.sleep(0.5)
        state = GPIO.LOW if self.reverse_logic else GPIO.HIGH
        GPIO.output(self.relay_pin, state)
        print(f"Монитор ВКЛЮЧЕН (пин {self.relay_pin} = {state})")
    
    def turn_off(self):
        state = GPIO.HIGH if self.reverse_logic else GPIO.LOW
        GPIO.output(self.relay_pin, state)
        time.sleep(0.5)
        state = GPIO.LOW if self.reverse_logic else GPIO.HIGH
        GPIO.output(self.relay_pin, state)
        print(f"Монитор ВЫКЛЮЧЕН (пин {self.relay_pin} = {state})")
        
    def turn_on_screen(self):
        if not self.screen_on:
            self.turn_on()
            self.screen_on = True
            
    def turn_off_screen(self):
        if self.screen_on:
            self.turn_off()
            self.screen_on = False

    def _display(self):
        threading.Thread(target=self.display, daemon=True).start()

    def display(self):
        print(f'{self.auth.screen_width} : {self.auth.screen_height}')
        cv2.namedWindow("Window", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        while True:
            file_dict = self.content_handler.active_content
            if not file_dict:
                self.turn_off_screen()
                black = np.zeros((self.auth.screen_height, self.auth.screen_width, 3), dtype=np.uint8)
                cv2.imshow("Window", black)
                if cv2.waitKey(1) == 27:
                    break
                time.sleep(1)
                continue
            
            self.turn_on_screen()
            
            for file_id, file_info in list(file_dict.items()):
                file_path = file_info.get('file_path')
                file_type = self.get_file_type(file_path)
                if file_type == 'image':
                    self._open_photo(file_info, self.manager.sio)
                    time.sleep(5)
                elif file_type == 'video':
                    self._open_video(file_info, self.manager.sio)
                elif file_type == 'pdf':
                    # self._open_pdf_slideshow(file_info, self.manager.sio)
                    pass
                else:
                    pass

    def _open_photo(self, file_info, display_time=5000):
        try:
            response = requests.get(file_info['file_path'])
            response.raise_for_status()
            image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            print(img.shape)
            print("RAZMER PHOTO")
            if img is None:
                print("PHOTO NETU!!!!")
            cv2.imshow("Window", img)
            self.photo_opened = True
            cv2.waitKey(1)
        except Exception as e:
            self.photo_opened = False
        finally:
            if self.photo_opened:
                self.photo_opened = False


    # def _open_pdf_slideshow(self, file_info, sio, delay=3):
    #     try:
    #         # self.send_monitor_status(sio, file_info, 1)
    #         pdf_url = file_info.get("file_path")
    #         if not pdf_url:
    #             print("PDF-ссылка не указана.")
    #             return

    #         response = requests.get(pdf_url)
    #         if response.status_code != 200:
    #             print(f"Ошибка при загрузке PDF: {response.status_code}")
    #             return

    #         pdf_bytes = BytesIO(response.content)

    #         pages = convert_from_bytes(pdf_bytes.read(), dpi=200, poppler_path=r"C:\poppler\Library\bin")
    #         if not pages:
    #             print("Не удалось получить страницы из PDF.")
    #             return

    #         cv2.namedWindow("Window", cv2.WINDOW_NORMAL)
    #         cv2.setWindowProperty("Window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    #         self.photo_opened = True

    #         current_page = 0
    #         num_pages = len(pages)

    #         while not self.stop_display:
    #             pil_image = pages[current_page]
    #             image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    #             cv2.imshow("Window", image)
    #             key = cv2.waitKey(delay * 1000)

    #             current_page = (current_page + 1) % num_pages

    #     except Exception as e:
    #         print("Ошибка при показе PDF-презентации:", e)
    #     finally:
    #         self.photo_opened = False
    #         cv2.destroyAllWindows()
    #         # self.send_monitor_status(sio, file_info, 2)

    def _open_video(self, file_info, sio):
        try:
            self.photo_opened = True
            video = cv2.VideoCapture(file_info['file_path'])
            fps = video.get(cv2.CAP_PROP_FPS) or 30
            delay = int(1000 / fps)
            ret, frame = video.read()
            while ret:
                cv2.imshow("Window", frame)
                if cv2.waitKey(delay) == 27:
                    self.stop_display = True
                    break
                ret, frame = video.read()
            video.release()
        except Exception as e:
            self.photo_opened = False
        finally:
            self.photo_opened = False

