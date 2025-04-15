import socket
import tkinter as tk
import threading
import time
from tkinter import messagebox

from settings import PI_IP, PORT
from login_screen import build_login_screen
from main_screen import MainScreen

def main():
    last_pong_time = [time.time()]

    def start_login_screen():
        nonlocal client
        try:
            client.close()
        except:
            pass

        # 🧽 Clean up any previous login frame
        if app_state["login_frame"]:
            try:
                app_state["login_frame"].destroy()
            except:
                pass
            app_state["login_frame"] = None

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((PI_IP, PORT))
        except Exception as e:
            print(f"❌ Could not reconnect to server: {e}")
            messagebox.showerror("Connection Error", "Could not connect to the server. Please try again later.")
            return  # Exit early — don't try to build login screen if Pi is dead

        login_frame = build_login_screen(root, client, on_login_success)
        login_frame.pack(padx=20, pady=20)
        app_state["login_frame"] = login_frame

    def on_login_success(worker_name):
        last_pong_time[0] = time.time() # Start the timer for PONG after login
        app_state["login_frame"].pack_forget()  # HIDE the login screen

        main_screen = MainScreen(root, client, worker_name, on_logout)
        app_state["main_screen"] = main_screen
        main_screen.show()

        threading.Thread(target=listen_for_uid, daemon=True).start()
        threading.Thread(target=ping_server_loop, daemon=True).start()

    def ping_server_loop():
        while app_state["main_screen"]:
            try:
                client.send("PING".encode())
            except Exception as e:
                print("❌ Lost connection during idle state (send failed). Auto-logging out.")
                logout_due_to_disconnect()
                break

            # Check if last pong is older than 6 seconds
            if time.time() - last_pong_time[0] > 6:
                print("❌ No PONG received in over 6 seconds. Auto-logging out.")
                logout_due_to_disconnect()
                break

            time.sleep(1)  # Check every second

    def logout_due_to_disconnect():
        if app_state["main_screen"]:
            try:
                app_state["main_screen"].frame.pack_forget()
            except:
                pass
            app_state["main_screen"] = None
            messagebox.showwarning("Disconnected", "Connection to the server was lost. Please log in again.")
            start_login_screen()

    def on_logout():
        app_state["main_screen"].frame.pack_forget()
        app_state["main_screen"] = None
        start_login_screen()


    def listen_for_uid():
        while True:
            try:
                client.settimeout(None)  # No timeout here
                data = client.recv(1024).decode().strip()

                if data == "PONG":
                    print("✅ Received PONG from server.")
                    nonlocal last_pong_time
                    last_pong_time[0] = time.time()
                    continue

                if app_state["main_screen"]:
                    app_state["main_screen"].add_item(data)

            except Exception as e:
                print("❌ Lost connection during active data stream.")
                if app_state["main_screen"]:
                    try:
                        app_state["main_screen"].add_item(f"Disconnected: {e}")
                        app_state["main_screen"].frame.pack_forget()
                    except:
                        pass
                    app_state["main_screen"] = None

                messagebox.showwarning("Disconnected", "Connection to the server was lost. Please log in again.")
                start_login_screen()
                break

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((PI_IP, PORT))

    root = tk.Tk()
    root.title("Login")

    app_state = {
        "main_screen": None,
        "login_frame": None,
    }

    start_login_screen()
    root.mainloop()

if __name__ == "__main__":
    main()