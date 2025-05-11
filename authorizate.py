import tkinter as tk
from tkinter import ttk
import requests
import os

API_LOGIN = "http://testsmart.enu.kz/api/login"
API_REGISTR = "http://testsmart.enu.kz/api/banner/monitor/add"
API_OPTIONS = "http://testsmart.enu.kz/api/public/banner/monitor/get"

class MonitorAuthentication:
    def __init__(self, manager):
        self.manager = manager
        self.root = tk.Tk()
        self.root.withdraw()
        self.mac_address = self.get_mac()
        self.screen_width = None
        self.screen_height = None

    def get_mac(self):
        for interface in os.listdir('/sys/class/net/'):
            if interface == "lo":
                continue
            try:
                with open(f'/sys/class/net/{interface}/operstate', 'r') as f:
                    state = f.read().strip()
                if state != "up":
                    continue

                with open(f'/sys/class/net/{interface}/address', 'r') as f:
                    mac = f.read().strip().upper()
                    if mac and mac != "00:00:00:00:00:00":
                        return mac
            except FileNotFoundError:
                continue
        return "MAC-адрес не найден"
            
    def verification_mac(self):
        self.screen_info()
        monitor_headers = {
            'Content-Type': 'application/json'
        }
        monitor_payload = {
            "page": 0,
            "rows": 1,
            "mac_address": self.mac_address,
            "floor": None,
            "building": None
        }
                
        monitor_response = requests.post(
                    API_OPTIONS,
                    json=monitor_payload,
                    headers=monitor_headers
                )
        
        if monitor_response.status_code == 200:
            monitor_data = monitor_response.json()
            monitors = monitor_data.get("monitors")

            if monitors:
                self.manager.connect()
                return True
            else:
                self.login_and_register()
                self.root.mainloop()
                return False
        # response = requests.get(API_OPTIONS, params={"mac_address": self.mac_address})
        # if response.status_code == 200:
        #     self.manager.connect()
        #     return True
        # else:
        #     self.login_and_register()
        #     self.root.mainloop()
        #     return False
    
    def screen_info(self):
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
    
    def login_and_register(self):
        self.screen_info()
        self.show_login_screen()

    def show_login_screen(self):
        self.login_win = tk.Toplevel(self.root)
        self.login_win.title("Авторизация")
        self.login_win.attributes('-type', 'dock')
        self.login_win.attributes('-fullscreen', True)
        self.login_win.attributes('-topmost', True)
        self.login_win.geometry(f"{self.screen_width}x{self.screen_height}+0+0")

        # Стиль
        style = ttk.Style(self.login_win)
        style.theme_use('clam')
        accent = '#5B8CFF'  # светло-синий
        style.configure('Accent.TButton',
                        font=('Arial', 20, 'bold'),
                        background=accent,
                        foreground='white',
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor='none',
                        padding=10)
        style.map('Accent.TButton',
                background=[('active', '#7DAEFF')],
                relief=[('pressed', 'flat'), ('!pressed', 'raised')])

        frame = tk.Frame(self.login_win, bg='black')
        frame.pack(expand=True, fill='both')

        tk.Label(frame, text="Username", fg="white", bg="black", font=("Arial", 18)).pack(pady=10)
        self.username_entry = ttk.Entry(frame, font=("Arial", 16))
        self.username_entry.pack(pady=5)
        self.username_entry.focus_set()

        tk.Label(frame, text="Password", fg="white", bg="black", font=("Arial", 18)).pack(pady=10)
        self.password_entry = ttk.Entry(frame, show='*', font=("Arial", 16))
        self.password_entry.pack(pady=5)

        self.message = tk.Label(frame, text="", fg="red", bg="black", font=("Arial", 14))
        self.message.pack(pady=10)

        ttk.Button(frame, text="Войти", style='Accent.TButton', command=self.authenticate).pack(pady=20)

    def authenticate(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Content-Type': 'application/json',
                'mode': 'no-cors',
                'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NfdXVpZCI6IjRlZGU1ODZiLWQ0MTYtNDJkMS1hNWYzLTZjNWMxYTIyNjY1OSIsImV4cCI6IjE3NDcyOTMxMzIiLCJzZXNzaW9uX3V1aWQiOiI2YTU0MGFmMS1iZGIwLTQwMzItOTc1OC1kODRkNjg4YWI2ZTEiLCJ1c2VyX2lkIjoiMTQyNjc1In0.JzfiDrdeOuNLh5B4GXH6n-JtlZ5Qz1MWEax4MChnzzY',
                'Origin': 'http://testsmart.enu.kz',
                'Connection': 'keep-alive',
                'Referer': 'http://testsmart.enu.kz/',
                'Cookie': '_ym_uid=1711018026458403413; _ym_d=1731040672; _ga_SE2CZ2FNMD=GS1.1.1724753698.1.0.1724754193.0.0.0; _ga=GA1.1.1396924448.1724753699; _ga_819GGM68GZ=GS2.1.s1746535198$o139$g1$t1746535690$j0$l0$h0; _pk_id.1.a6e6=5286dad9fd60a564.1740397520.; _pk_ses.1.a6e6=1; portainer_api_key=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsInJvbGUiOjEsInNjb3BlIjoiZGVmYXVsdCIsImZvcmNlQ2hhbmdlUGFzc3dvcmQiOmZhbHNlLCJleHAiOjE3NDY3MTcyMzQsImlhdCI6MTc0NjY4ODQzNCwianRpIjoiOGVjNjZkOWYtNDEzNC00MWM1LTk1NWQtZWY5OTEwYWNjYzRhIn0.OQ1rrV3JDE0hg12PT6IcthZLWpgyK48ZfgOqpfU_Pk4; _gorilla_csrf=MTc0NjY4ODQzNHxJbU4yU2xRMVQzUXhPV0p2V0VOaFpVZFVaRE5YZGtRMlFqVk5XWEZPWnpGRlJXMTZPSFJXWVcxalVXODlJZ289fA6g-YDqN3ft-iHx85t_M2TUraMbSWFHQFlprLZqX10n',
                'Priority': 'u=0'
            }

            response = requests.post(API_LOGIN, json={
                "username": username,
                "password": password,
                "session": None
            }, headers=headers)

            if response.status_code == 200:
                response_data = response.json()
                self.access_token = response_data.get("access_token")
                self.message.config(text='Успешный вход', fg='green')
                self.login_win.destroy()

                # --- второй запрос для получения информации о мониторе ---
                monitor_headers = {
                    'Content-Type': 'application/json'
                }
                monitor_payload = {
                    "page": 0,
                    "rows": 1,
                    "mac_address": self.mac_address,
                    "floor": None,
                    "building": None
                }

                monitor_response = requests.post(
                    API_OPTIONS,
                    json=monitor_payload,
                    headers=monitor_headers
                )

                if monitor_response.status_code == 200:
                    monitor_data = monitor_response.json()
                    monitors = monitor_data.get("monitors")

                    if monitors:
                        monitor = monitors[0]
                        building = monitor.get("building")
                        floor = monitor.get("floor")
                        notes = monitor.get("notes")
                        self.show_registration_screen(building, floor, notes)
                    else:
                        # Мониторов нет — пустой вызов
                        self.show_registration_screen()
                else:
                    self.message.config(text="Ошибка при получении данных монитора", fg="red")

            else:
                self.message.config(text="Неверный логин или пароль", fg="red")
        except Exception as e:
            self.message.config(text=f"Ошибка подключения: {e}", fg="red")
            
    def show_registration_screen(self, building=None, floor=None, notes=None):
        self.reg_win = tk.Toplevel(self.root)
        self.reg_win.title("Регистрация")
        self.reg_win.attributes('-type', 'dock')
        self.reg_win.attributes('-fullscreen', True)
        self.reg_win.attributes('-topmost', True)
        self.reg_win.geometry(f"{self.screen_width}x{self.screen_height}+0+0")

        frame = tk.Frame(self.reg_win)
        frame.pack(expand=True, fill='both', padx=20, pady=20)

        # MAC адрес
        tk.Label(frame, text="MAC адрес").pack()
        mac_entry = tk.Entry(frame)
        mac_entry.insert(0, self.mac_address)
        mac_entry.config(state='readonly')
        mac_entry.pack()

        # Разрешение экрана
        tk.Label(frame, text="Разрешение экрана").pack()
        res_entry = tk.Entry(frame)
        res_entry.insert(0, f"{self.screen_width}x{self.screen_height}")
        res_entry.config(state='readonly')
        res_entry.pack()

        # Корпус
        tk.Label(frame, text="Корпус").pack()
        building_var = tk.StringVar(value=building if building else "")
        building_entry = tk.Entry(frame, textvariable=building_var)
        building_entry.pack()

        # Этаж
        tk.Label(frame, text="Этаж").pack()
        floor_var = tk.StringVar(value=str(floor) if floor else "")
        floor_entry = tk.Entry(frame, textvariable=floor_var)
        floor_entry.pack()

        # Описание
        tk.Label(frame, text="Описание").pack()
        description_text = tk.Text(frame, height=5, width=40)
        if notes:
            description_text.insert('1.0', notes)
        description_text.pack()

        # Сообщение об ошибке
        message = tk.Label(frame, text="", fg="red")
        message.pack()

        def register():
            try:
                data = {
                    "building": building_var.get(),
                    "floor": int(floor_var.get()),
                    "notes": description_text.get("1.0", tk.END).strip(),
                    "resolution": f"{self.screen_width}x{self.screen_height}",
                    "mac_address": self.mac_address,
                }

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f'Bearer {self.access_token}'
                }

                response = requests.post(API_REGISTR, json=data, headers=headers)
                if response.status_code == 201:
                    message.config(text="Успешная регистрация", fg="green")
                    self.root.after(1000, self.root.quit)
                    self.reg_win.destroy()
                    self.manager.connect()
                else:
                    message.config(text=f"Ошибка: {response.status_code}\n{response.text}", fg="red")
            except Exception as e:
                message.config(text=f"Ошибка: {e}", fg="red")

        tk.Button(frame, text="Зарегистрировать", command=register).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = MonitorAuthentication(root)
    app.verification_mac()
    root.mainloop()