import tkinter as tk

class MainScreen:
    def __init__(self, root, client, worker_name):
        self.client = client
        self.scanned_items = []
        self.popup = None

        self.frame = tk.Frame(root)

        tk.Label(self.frame, text=f"Logged in as: {worker_name}", font=("Helvetica", 18, "bold")).pack(pady=(10, 10))

        tk.Button(self.frame, text="Non-Scan Request", font=("Helvetica", 12),
                  command=self.request_non_scan_permission).pack(pady=10)
        tk.Button(self.frame, text="Restart NFC Scan", font=("Helvetica", 12), command=self.restart_nfc_scan).pack(
            pady=10)

        self.item_list_display = tk.Text(self.frame, height=20, width=70, font=("Helvetica", 14), state='disabled',
                                         wrap='word')
        self.item_list_display.pack(pady=10)

        self.total_label = tk.Label(self.frame, text="Total: €0.00", font=("Helvetica", 16, "bold"))
        self.total_label.pack(pady=(10, 0))

    def show(self):
        self.frame.pack(padx=20, pady=20)

    def add_item(self, item):
        if item.strip().upper() in ["APPROVED", "DENIED"]:
            self.update_popup_result(item)
            return

        self.scanned_items.append(item)
        self.update_item_list_display()
        self.update_total()

    def update_total(self):
        total = 0.0

        #Debug scanned items
        print("🔍 Scanned items:")
        for i in self.scanned_items:
            print(f"  → {i}")

        for item in self.scanned_items:
            # Expect format like: "Item found: Name, Price: $12.34, UID: 0x1234"
            # or "Non-Scan Item, Price: $5.00, UID: 0x00000000"
            try:
                if "price: €" in item.lower():
                    # Re-split using original string, but find the correct index first
                    start = item.lower().find("price: €")
                    sliced = item[start:]
                    price_str = sliced.split("€")[1].split(",")[0].strip()
                    print(f"✅ Extracted price: {price_str} from item: {item}")
                    total += float(price_str)
            except (IndexError, ValueError):
                print("Error parsing item price:", item)
                continue  # Skip if the format is wrong

        print(f"Total calculated: {total:.2f}")
        self.total_label.config(text=f"Total: €{total:.2f}")

    def update_item_list_display(self):
        self.item_list_display.config(state='normal')
        self.item_list_display.delete(1.0, tk.END)

        for idx, item in enumerate(self.scanned_items, start=1):
            self.item_list_display.insert(tk.END, f"{idx}. {item}\n")

        self.item_list_display.see(tk.END)
        self.item_list_display.config(state='disabled')

    def request_non_scan_permission(self):
        try:
            self.client.send("NONSCAN_REQUEST".encode())
            self.show_waiting_popup()
        except Exception as e:
            self.add_item(f"Error sending non-scan request: {e}")

    # TODO: Add check if popup isn't open when it should be (when clicked off earlier and won't open again)
    def show_waiting_popup(self):
        if self.popup:
            return  # Already open

        self.popup = tk.Toplevel(self.frame)
        self.popup.title("Approval Pending")

        label = tk.Label(self.popup, text="Waiting for approval from Android...", font=("Helvetica", 14))
        label.pack(padx=20, pady=20)

        self.popup_result_label = tk.Label(self.popup, text="", font=("Helvetica", 14, "bold"))
        self.popup_result_label.pack(pady=10)

    def prompt_price_for_non_scan_item(self):
        price_popup = tk.Toplevel(self.frame)
        price_popup.title("Enter Price for Non-Scan Item")

        tk.Label(price_popup, text="Enter price for Non-Scan Item:", font=("Helvetica", 14)).pack(pady=10)
        price_entry = tk.Entry(price_popup, font=("Helvetica", 14))
        price_entry.pack(pady=5)

        # TODO: Enter a check only points allowed
        def confirm_price():
            try:
                price = float(price_entry.get())
                if price <= 0:
                    raise ValueError("Price must be greater than 0.")

                # Add fixed non-scan item
                item = f"Non-Scan Item, Price: €{price:.2f}, UID: 0x00000000"
                self.scanned_items.append(item)
                self.update_item_list_display()
                self.update_total()
                price_popup.destroy()

            except ValueError:
                tk.Label(price_popup, text="Invalid price! Please enter a number > 0.", fg="red",
                         font=("Helvetica", 12)).pack()

        tk.Button(price_popup, text="Confirm", command=confirm_price, font=("Helvetica", 12)).pack(pady=10)

    def update_popup_result(self, result):
        if self.popup:
            self.popup_result_label.config(text=f"Response request: {result}")

            if result.strip().upper() == "APPROVED":
                self.popup.after(3000, self.popup.destroy)
                self.popup = None

                self.prompt_price_for_non_scan_item()

            elif result.strip().upper() == "DENIED":
                self.popup.after(3000, self.popup.destroy)
                self.popup = None

    def restart_nfc_scan(self):
        try:
            self.client.send("NFC_RESTART".encode())
        except Exception as e:
            self.add_item(f"Error restarting NFC scan: {e}")