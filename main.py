import socket
import tkinter as tk
import threading
from settings import PI_IP, PORT
from login_screen import build_login_screen
from main_screen import MainScreen

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((PI_IP, PORT))

    root = tk.Tk()
    root.title("Login")

    app_state = {"main_screen": None}

    def on_login_success(worker_name):
        login_frame.pack_forget()
        main_screen = MainScreen(root, client, worker_name)
        app_state["main_screen"] = main_screen
        main_screen.show()
        threading.Thread(target=listen_for_uid, daemon=True).start()

    def listen_for_uid():
        while True:
            try:
                data = client.recv(1024).decode()
                if app_state["main_screen"]:
                    app_state["main_screen"].add_item(data)
            except Exception as e:
                if app_state["main_screen"]:
                    app_state["main_screen"].add_item(f"Error: {e}")
                break

    login_frame = build_login_screen(root, client, on_login_success)
    login_frame.pack(padx=20, pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()