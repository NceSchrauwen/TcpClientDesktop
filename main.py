import socket
import tkinter as tk
import threading
import time
from tkinter import messagebox
from settings import PI_IP, PORT
from login_screen import build_login_screen
from main_screen import MainScreen

def main():
    global client
    client = None
    last_pong_time = [time.time()]
    should_exit = threading.Event()

    def start_login_screen():
        global client
        try:
            if client:
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
            # Only show error if not intentional logout
            if not app_state.get("intentional_logout", False):
                messagebox.showerror("Connection Error", "Could not connect to the server. Please check your connection.")
            return  # Exit early — don't try to build login screen if Pi is dead

        login_frame = build_login_screen(root, client, on_login_success)
        login_frame.pack(padx=20, pady=20)
        app_state["login_frame"] = login_frame

        app_state["intentional_logout"] = False  # Reset the flag only when starting the login screen
        should_exit.clear() # Clear the exit flag to allow threads to run when logging in again

    def on_login_success(worker_name):
        last_pong_time[0] = time.time()  # Start the timer for PONG after login
        app_state["login_frame"].pack_forget()  # HIDE the login screen

        main_screen = MainScreen(root, client, worker_name, on_logout)
        app_state["main_screen"] = main_screen
        main_screen.show()

        uid_thread = threading.Thread(target=listen_for_uid, args=(client,), daemon=True)
        ping_thread = threading.Thread(target=ping_server_loop, args=(client,), daemon=True)

        app_state["uid_thread"] = uid_thread
        app_state["ping_thread"] = ping_thread

        uid_thread.start()
        ping_thread.start()

    def ping_server_loop(client):
        while app_state["main_screen"] and not should_exit.is_set():
            try:
                client.send("PING".encode())
            except Exception as e:
                if app_state.get("intentional_logout") or should_exit.is_set():
                    print("ℹ️ Ping loop exiting after intentional logout.")
                    break

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
        app_state["intentional_logout"] = False  # Set the flag to indicate unintentional logout
        if app_state["main_screen"]:
            try:
                app_state["main_screen"].frame.pack_forget()
            except:
                pass
            app_state["main_screen"] = None
            messagebox.showwarning("Disconnected", "Connection to the server was lost. Please log in again. (logout due to disconnect)")
            start_login_screen()

    def on_logout():
        app_state["intentional_logout"] = True
        should_exit.set()

        try:
            if app_state["uid_thread"] and app_state["uid_thread"].is_alive():
                app_state["uid_thread"].join(timeout=2)
            if app_state["ping_thread"] and app_state["ping_thread"].is_alive():
                app_state["ping_thread"].join(timeout=2)
        except Exception as e:
            print(f"Error joining threads: {e}")

        try:
            client.sendall("LOGOUT".encode())
        except:
            pass

        try:
            app_state["main_screen"].frame.pack_forget()
        except:
            pass
        app_state["main_screen"] = None
        app_state["uid_thread"] = None
        app_state["ping_thread"] = None
        start_login_screen()

    def listen_for_uid(client_socket):
        client_socket.settimeout(0.5)

        while not should_exit.is_set():
            try:
                if app_state.get("intentional_logout"):
                    print("ℹ️ Exiting UID listener due to intentional logout.")
                    break

                data = client_socket.recv(1024).decode().strip()

                if data == "PONG":
                    print("✅ Received PONG from server.")
                    nonlocal last_pong_time
                    last_pong_time[0] = time.time()
                    continue

                if app_state["main_screen"]:
                    app_state["main_screen"].add_item(data)

            except socket.timeout:
                continue

            except (OSError, ConnectionResetError) as e:
                if app_state.get("intentional_logout") or should_exit.is_set():
                    print("ℹ️ UID listener socket error after intentional logout. Ignoring.")
                    break
                print("❌ Lost connection during active data stream.")
                break

            except Exception as e:
                if app_state.get("intentional_logout") or should_exit.is_set():
                    print("ℹ️ UID listener caught general exception after logout. Ignoring.")
                    break
                print(f"❌ Unexpected error in UID listener: {e}")
                break

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((PI_IP, PORT))

    root = tk.Tk()
    root.title("Login")

    app_state = {
        "main_screen": None,
        "login_frame": None,
        "intentional_logout": False,  # Flag to track if logout was intentional
        "should_exit": should_exit,
        "ping_thread": None,
        "uid_thread": None,
    }

    start_login_screen()
    root.mainloop()

if __name__ == "__main__":
    main()