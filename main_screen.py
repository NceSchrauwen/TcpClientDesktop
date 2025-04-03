import tkinter as tk

class MainScreen:
    def __init__(self, root, client, worker_name):
        self.client = client
        self.scanned_items = []

        self.frame = tk.Frame(root)

        tk.Label(self.frame, text=f"Logged in as: {worker_name}", font=("Helvetica", 18, "bold")).pack(pady=(10, 10))

        tk.Button(self.frame, text="Non-Scan Request", font=("Helvetica", 12), command=self.request_non_scan_permission).pack(pady=10)
        tk.Button(self.frame, text="Restart NFC Scan", font=("Helvetica", 12), command=self.restart_nfc_scan).pack(pady=10)

        self.item_list_display = tk.Text(self.frame, height=20, width=70, font=("Helvetica", 14), state='disabled', wrap='word')
        self.item_list_display.pack(pady=10)

    def show(self):
        self.frame.pack(padx=20, pady=20)

    def add_item(self, item):
        self.scanned_items.append(item)
        self.update_item_list_display()

    def update_item_list_display(self):
        self.item_list_display.config(state='normal')
        self.item_list_display.delete(1.0, tk.END)

        for idx, item in enumerate(self.scanned_items, start=1):
            self.item_list_display.insert(tk.END, f"{idx}. {item}\n\n")

        self.item_list_display.see(tk.END)
        self.item_list_display.config(state='disabled')

    def request_non_scan_permission(self):
        try:
            self.client.send("NONSCAN_REQUEST".encode())
        except Exception as e:
            self.add_item(f"Error sending non-scan request: {e}")

    def restart_nfc_scan(self):
        try:
            self.client.send("NFC_RESTART".encode())
        except Exception as e:
            self.add_item(f"Error restarting NFC scan: {e}")