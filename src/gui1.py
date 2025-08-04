from gui_functions1 import *
from tkinter import filedialog, ttk
from tkinter import *
import threading

def save_file_dialog(filetypes):
    file_path = filedialog.asksaveasfilename(filetypes=filetypes)
    return file_path

class Widgets:
    def __init__(self):
        self.entries = []
        self.buttons = []
        self.labels = []
        self.messages = []
        self.texts = []
        self.checkboxes = []

    def clear(self):
        self.entries.clear()
        self.buttons.clear()
        self.labels.clear()
        self.messages.clear()
        self.texts.clear()
        self.checkboxes.clear()

class GUI:
    def __init__(self, root):
        self.root = root
        self.widgets = Widgets()
        self.frame = Frame(self.root)
        self.frame.pack(fill=BOTH, expand=True, padx = 20, pady= 20)
        self.status_space = (0, 0)
        self.active_gui = None
        self.mail, self.db = load_remembered_settings()
        self.fetch_thread = None
        self.stop_fetch_event = threading.Event()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.widgets.clear()
        self.status_space = (-1, -1)
        self.active_gui = None

    def clear_status_message(self):
        if self.status_space == (-1, -1):
            return
        for i in range(len(self.widgets.messages) - 1, -1, -1):
            grid_info = self.widgets.messages[i].grid_info()
            row, col = grid_info.get('row'), grid_info.get('column')
            if row is not None and col is not None and row == self.status_space[0] and col == self.status_space[1]:
                self.widgets.messages[i].grid_remove()
                self.widgets.messages.pop(i)
                return
            
    def on_close(self):
        if hasattr(self, 'fetch_thread') and self.fetch_thread and self.fetch_thread.is_alive():
            print("Stopping periodic fetching thread...")
            self.stop_fetch_event.set()
            self.fetch_thread.join(timeout=1.0)

        if self.mail:
            try:
                print("Logging out from email server...")
                self.mail.logout()
            except Exception as e:
                print(f"Error during email logout: {e}")

        if self.db:
            print("Closing database connection...")
            self.db.close()

        self.root.destroy()
            
    def start_gui(self):
        self.clear_frame()
        self.root.title("Invoice Data Extractor")
        self.active_gui = "start_gui"
        self.status_space = (6, 0)

        self.widgets.labels.append(ttk.Label(self.frame, text="Invoice Data Extractor", font=("Arial", 18, "bold")))
        self.widgets.labels[-1].grid(row=0, column=0, pady=(0, 20))

        if not self.mail:
            self.widgets.buttons.append(Button(self.frame, text="Connect Email", width=20, command=self.email_login_gui))
        else:
            self.widgets.buttons.append(Button(self.frame, text="Disconnect Email", width=20, command=self.disconnect_email))
        self.widgets.buttons[-1].grid(row=1, column=0, pady=(0, 10))

        if not self.db:
            self.widgets.buttons.append(Button(self.frame, text="Connect Database", width=20, command=self.database_login_gui))
        else:
            self.widgets.buttons.append(Button(self.frame, text="Disconnect Database", width=20, command=self.disconnect_database))
        self.widgets.buttons[-1].grid(row=2, column=0, pady=(0, 10))

        self.widgets.buttons.append(Button(self.frame, text="Fetch & Log Invoices", width=20, command=self.fetch_log_gui))
        self.widgets.buttons[-1].grid(row=3, column=0, pady=(0, 10))

        self.widgets.buttons.append(Button(self.frame, text="Database Viewer", width=20, command=self.database_viewer_gui))
        self.widgets.buttons[-1].grid(row=4, column=0, pady=(0, 10))

        self.widgets.buttons.append(Button(self.frame, text="Exit", width=20, command=self.on_close))
        self.widgets.buttons[-1].grid(row=5, column=0, pady=(0, 10))

        self.widgets.messages.append(Message(self.frame, text = " "))
        self.widgets.messages[-1].grid(row=6, column=0, pady=(10, 0))

    def email_login_gui(self):
        self.clear_frame()
        self.root.title("Email Login")
        self.active_gui = "email_login_gui"
        self.status_space = (5, 0)

        self.widgets.labels.append(ttk.Label(self.frame, text="Email Login", font=("Arial", 18, "bold")))
        self.widgets.labels[-1].grid(row=0, column=0, columnspan=3, pady=(0, 20))
        self.widgets.labels.append(ttk.Label(self.frame, text="Email Address:"))
        self.widgets.labels[-1].grid(row=1, column=0, pady=(0, 10))
        self.widgets.entries.append(Entry(self.frame, width=30))
        self.widgets.entries[-1].grid(row=1, column=1,columnspan=2, pady=(0, 10))
        self.widgets.labels.append(ttk.Label(self.frame, text="Password:"))
        self.widgets.labels[-1].grid(row=2, column=0, pady=(0, 10))
        self.widgets.entries.append(Entry(self.frame, show='*', width=30))
        self.widgets.entries[-1].grid(row=2, column=1, columnspan=2, pady=(0, 10))
        check = BooleanVar()
        self.widgets.checkboxes.append(Checkbutton(self.frame, text="Remember Email", variable=check))
        self.widgets.checkboxes[-1].grid(row=3, column=0, columnspan=3, pady=(0, 10), sticky=EW)
        self.widgets.buttons.append(Button(self.frame, text="Connect", command=lambda : self.connect_email(check)))
        self.widgets.buttons[-1].grid(row=4, column=0, pady=(0, 10), sticky=EW, padx = 10)
        self.widgets.buttons.append(Button(self.frame, text="Help", command=self.help_email_gui))
        self.widgets.buttons[-1].grid(row=4, column=1, pady=(0, 10), sticky=EW, padx = 10)
        self.widgets.buttons.append(Button(self.frame, text="Back", command=self.start_gui))
        self.widgets.buttons[-1].grid(row=4, column=2, pady=(0, 10), sticky=EW, padx = 10)
        self.widgets.messages.append(Message(self.frame, text=" "))
        self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))

    def connect_email(self, check):
        email_address = self.widgets.entries[0].get().strip()
        password = self.widgets.entries[1].get().strip()
        if not validate_email(email_address):
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="Invalid Email Address", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        try:
            if check:
                store_mail(email_address, password)
            self.mail = get_email_object(email_address, password)
            self.start_gui()
        except Exception as e:
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text=f"Error connecting to email: {str(e)}", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            self.mail = None
            return

    def help_email_gui(self):
        email_address = self.widgets.entries[0].get().strip()
        if not validate_email(email_address):
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="Invalid Email Address", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        self.clear_frame()
        self.root.title("Email Login Help")
        self.active_gui = "email_login_help_gui"
        self.status_space = (4, 0)
        self.widgets.labels.append(ttk.Label(self.frame, text= "Email Login Help",font=("Arial", 18, "bold")))
        self.widgets.labels[-1].grid(row= 0, column = 0, columnspan = 3, padx = 20, pady = (10,0))
        text_help = get_email_help(email_address)
        self.widgets.texts.append(Text(self.frame, width= 40, height= 20))
        self.widgets.texts[-1].insert(END, text_help)
        self.widgets.texts[-1].config(state=DISABLED)
        self.widgets.texts[-1].config(wrap=WORD)
        self.widgets.texts[-1].grid(row = 1, column = 0, columnspan = 3,rowspan = 3 ,padx = 20, pady = (10,0))
        self.widgets.buttons.append(Button(self.frame, text = "Back", command=self.email_login_gui))
        self.widgets.buttons[-1].grid(row = 4, column = 1, sticky = EW, padx = 20, pady = (10,0))
        print("Help Email GUI")

    def disconnect_email(self):
        try:
            if self.mail.state == 'SELECTED':
                self.mail.close()
            self.mail.logout()
        except Exception as e:
            print(f"Error during email disconnect: {e}")
        finally:
            self.mail = None
            store_mail(None, None)
            self.start_gui()  
        return

    def database_login_gui(self):
        self.clear_frame()
        self.root.title("SQL Database Login")
        self.active_gui = "database_login_gui"
        self.status_space = (7, 0)
        self.widgets.labels.append(ttk.Label(self.frame, text="SQL Database Login", font=("Arial", 18, "bold")))
        self.widgets.labels[-1].grid(row=0, column=0, columnspan=3, pady=(0, 20))
        self.widgets.labels.append(ttk.Label(self.frame, text="Host:"))
        self.widgets.labels[-1].grid(row=1, column=0, pady=(0, 10))
        self.widgets.entries.append(Entry(self.frame, width=30))
        self.widgets.entries[-1].grid(row=1, column=1, columnspan=2, pady=(0, 10))
        self.widgets.labels.append(ttk.Label(self.frame, text="User:"))
        self.widgets.labels[-1].grid(row=2, column=0, pady=(0, 10))
        self.widgets.entries.append(Entry(self.frame, width=30))
        self.widgets.entries[-1].grid(row=2, column=1, columnspan=2, pady=(0, 10))
        self.widgets.labels.append(ttk.Label(self.frame, text="Password:"))
        self.widgets.labels[-1].grid(row=3, column=0, pady=(0, 10))
        self.widgets.entries.append(Entry(self.frame, show='*', width=30))
        self.widgets.entries[-1].grid(row=3, column=1, columnspan=2, pady=(0, 10))
        self.widgets.labels.append(ttk.Label(self.frame, text="Database:"))
        self.widgets.labels[-1].grid(row=4, column=0, pady=(0, 10))
        self.widgets.entries.append(Entry(self.frame, width=30))
        self.widgets.entries[-1].grid(row=4, column=1, columnspan=2, pady=(0, 10))
        check = BooleanVar()
        self.widgets.checkboxes.append(Checkbutton(self.frame, text="Remember Database", variable=check))
        self.widgets.checkboxes[-1].grid(row=5, column=0, columnspan=3, pady=(0, 10), sticky=EW)
        self.widgets.buttons.append(Button(self.frame, text="Connect", command=lambda : self.connect_database(check)))
        self.widgets.buttons[-1].grid(row=6, column=0, pady=(0, 10), sticky=EW, padx=10)
        self.widgets.buttons.append(Button(self.frame, text="Help", command=self.help_database_gui))
        self.widgets.buttons[-1].grid(row=6, column=1, pady=(0, 10), sticky=EW, padx=10)
        self.widgets.buttons.append(Button(self.frame, text="Back", command=self.start_gui))
        self.widgets.buttons[-1].grid(row=6, column=2, pady=(0, 10), sticky=EW, padx=10)
        self.widgets.messages.append(Message(self.frame, text=" "))
        self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))

    def connect_database(self, check):
        host = self.widgets.entries[0].get().strip()
        user = self.widgets.entries[1].get().strip()
        password = self.widgets.entries[2].get().strip()
        db = self.widgets.entries[3].get().strip()
        if not db or db == "":
            db = "Invoice Logger"
        if not host or not user:
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="Please fill User and Host fields", width=60))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        try:
            if check:
                store_db(host, user, password, db)
            db_config = {'host': host, 'user': user, 'password': password, 'database': db}
            self.db = get_db(db_config)
            self.start_gui()
        except Exception as e:
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text=f"Error connecting to database: {str(e)}", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            self.db = None
            return
        
    def help_database_gui(self):
        self.clear_frame()
        self.root.title("Database Login Help")
        self.active_gui = "database_login_help_gui"
        self.status_space = (4, 0)
        self.widgets.labels.append(ttk.Label(self.frame, text="Database Login Help", font=("Arial", 18, "bold")))
        self.widgets.labels[-1].grid(row=0, column=0, columnspan=3, padx=20, pady=(10, 0))
        help_text = get_database_help()
        self.widgets.texts.append(Text(self.frame, width=40, height=20))
        self.widgets.texts[-1].insert(END, help_text)
        self.widgets.texts[-1].config(state=DISABLED)
        self.widgets.texts[-1].config(wrap=WORD)
        self.widgets.texts[-1].grid(row=1, column=0, columnspan=3, rowspan=3, padx=20, pady=(10, 0))
        self.widgets.buttons.append(Button(self.frame, text="Back", command=self.database_login_gui))
        self.widgets.buttons[-1].grid(row=4, column=1, sticky=EW, padx=20, pady=(10, 0))

    def disconnect_database(self):
        if self.db:
            self.db.close()
            self.db = None
            store_db(None, None, None, None)
            self.start_gui()  
        else:
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="No Database Connection to Disconnect", width=80))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))

    def fetch_log_gui(self):
        if not self.mail:
            self.widgets.messages.append(Message(self.frame, text="Please connect to Email first", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        if not self.db:
            self.widgets.messages.append(Message(self.frame, text="Please connect to Database first", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        self.clear_frame()
        self.root.title("Fetch & Log Invoices")
        self.active_gui = "fetch_log_gui"
        self.status_space = (3, 0)

        self.widgets.labels.append(ttk.Label(self.frame, text="Fetch & Log Invoices", font=("Arial", 18, "bold")))
        self.widgets.labels[-1].grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        self.widgets.labels.append(ttk.Label(self.frame, text="Fetch Interval (in minutes):"))
        self.widgets.labels[-1].grid(row=1, column=0, pady=(0, 10))
        self.widgets.entries.append(Entry(self.frame, width=10))
        self.widgets.entries[-1].grid(row=1, column=1,columnspan = 2, pady=(0, 10))
        self.widgets.entries[-1].insert(0, "30")  
        self.widgets.buttons.append(Button(self.frame, text="Fetch Invoices Now", command=self.fetch_invoices))
        self.widgets.buttons[-1].grid(row=2, column=1, sticky=EW, padx=20, pady=(10, 0))
        if hasattr(self, 'fetch_thread') and self.fetch_thread and self.fetch_thread.is_alive():
            self.widgets.buttons.append(Button(self.frame, text="Stop Fetching", command=self.stop_fetching))
            self.widgets.buttons[-1].grid(row=2, column=2, sticky=EW, padx=20, pady=(10, 0))
        else:
            self.widgets.buttons.append(Button(self.frame, text="Start Fetching", command=self.start_fetching))
            self.widgets.buttons[-1].grid(row=2, column=2, sticky=EW, padx=20, pady=(10, 0))
        self.widgets.buttons.append(Button(self.frame, text="Retry Old Invoices", command=self.retry_old_invoices))
        self.widgets.buttons[-1].grid(row=2, column=3, sticky=EW, padx=20, pady=(10, 0))
        self.widgets.buttons.append(Button(self.frame, text="Back", command=self.start_gui))
        self.widgets.buttons[-1].grid(row=2, column=4, sticky=EW, padx=20, pady=(10, 0))
        self.widgets.messages.append(Message(self.frame, text=" "))
        self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))

    def fetch_invoices(self):
        self.clear_status_message()
        res = log_invoice(self.mail,self.db)
        if not res:
            self.widgets.messages.append(Message(self.frame, text="Failed to log invoice", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        self.widgets.messages.append(Message(self.frame, text=res, width=400))
        self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))

    def retry_old_invoices(self):
        if not self.db:
            self.widgets.messages.append(Message(self.frame, text="Please connect to Database first", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        
        self.clear_status_message()
        self.widgets.messages.append(Message(self.frame, text="Processing old invoices... Please wait.", width=400))
        self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
        self.root.update()  # Update GUI to show message
        
        res = process_old_invoices(self.db)
        
        self.clear_status_message()
        if not res:
            self.widgets.messages.append(Message(self.frame, text="No old invoices found to retry", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        self.widgets.messages.append(Message(self.frame, text=res, width=400))
        self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))

    def start_fetching(self):
        if hasattr(self, 'fetch_thread') and self.fetch_thread and self.fetch_thread.is_alive():
            self.widgets.messages[-1].config(text="Periodic fetching is already running.")
            return

        interval_str = self.widgets.entries[0].get().strip()
        if not interval_str.isdigit() or int(interval_str) <= 0:
            self.widgets.messages[-1].config(text="Invalid Fetch Interval. Must be a positive integer.")
            return

        interval_seconds = int(interval_str) * 60
        self.stop_fetch_event.clear()

        self.fetch_thread = threading.Thread(
            target=log_invoices_periodically,
            args=(self.mail, self.db, interval_seconds, self.stop_fetch_event)
        )
        
        self.fetch_thread.daemon = True 
        self.fetch_thread.start()

        self.fetch_log_gui()
        self.widgets.messages[-1].config(text=f"Started periodic fetching every {interval_str} minutes.")

    def stop_fetching(self):
        if hasattr(self, 'fetch_thread') and self.fetch_thread is not None and self.fetch_thread.is_alive():
            self.stop_fetch_event.set()
            self.fetch_thread.join(timeout=1)
            self.fetch_log_gui()
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="Fetching stopped", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
        else:
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="No fetching in progress", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
    
    def database_viewer_gui(self):
        self.clear_frame()
        self.root.title("Database Viewer")
        self.active_gui = "database_viewer_gui"
        self.status_space = (6, 0)
        
        self.widgets.labels.append(ttk.Label(self.frame, text="Database Viewer", font=("Arial", 18, "bold")))
        self.widgets.labels[-1].grid(row=0, column=0, columnspan=3, pady=(0, 20))
        if not self.db:
            self.widgets.messages.append(Message(self.frame, text="Please connect to Database first", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        self.widgets.buttons.append(Button(self.frame, text="View Invoices", command=self.view_invoices))
        self.widgets.buttons[-1].grid(row=1, column=1, pady=(0, 10), sticky=EW)
        self.widgets.buttons.append(Button(self.frame, text="Use SQL Queries(Advanced)", command=self.sql_query_gui))
        self.widgets.buttons[-1].grid(row=2, column=1, pady=(0, 10), sticky=EW)
        self.widgets.buttons.append(Button(self.frame, text="View Summary", command=self.view_summary))
        self.widgets.buttons[-1].grid(row=3, column=1, pady=(0, 10), sticky=EW)
        self.widgets.buttons.append(Button(self.frame, text="Export to Excel", command=self.export_to_excel))
        self.widgets.buttons[-1].grid(row=4, column=1, pady=(0, 10), sticky=EW)
        self.widgets.buttons.append(Button(self.frame, text="Back", command=self.start_gui))
        self.widgets.buttons[-1].grid(row=5, column=1, pady=(0, 10), sticky=EW)
        self.widgets.messages.append(Message(self.frame, text=" "))
        self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))

    def export_to_excel(self):
        if not self.db:
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="Please connect to Database first", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        
        # Get file path from dialog
        file_path = save_file_dialog([("Excel Files", "*.xlsx"), ("All Files", "*.*")])
        if not file_path:  # User cancelled the dialog
            return
            
        try:
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="Exporting invoices... Please wait.", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            self.root.update()  # Update GUI to show message
            
            export_status = export_invoices_to_excel(self.db, file_path)
            
            self.clear_status_message()
            if export_status and not export_status.startswith("Error") and not export_status.startswith("No"):
                self.widgets.messages.append(Message(self.frame, text=export_status, width=400))
                self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            else:
                self.widgets.messages.append(Message(self.frame, text=f"Export failed: {export_status}", width=400))
                self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
        except Exception as e:
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text=f"Error exporting invoices: {str(e)}", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))

    def view_invoices(self):
        self.clear_frame()
        self.root.title("Database Viewer")
        self.active_gui = "database_viewer_gui"
        self.status_space = (7, 0)
        self.widgets.labels.append(ttk.Label(self.frame, text="View Invoices", font=("Arial", 18, "bold")))
        self.widgets.labels[-1].grid(row=0, column=0, columnspan=3, pady=(0, 20))
        invoices_text = get_invoices_from_db(self.db)
        self.widgets.texts.append(Text(self.frame, width=80, height=20))
        self.widgets.texts[-1].grid(row=1, column=0, columnspan=3, pady=(0, 20))
        self.widgets.texts[-1].insert(END, invoices_text)
        self.widgets.texts[-1].config(state=DISABLED)
        self.widgets.labels.append(ttk.Label(self.frame, text="Date in (DD-MM-YYYY) [Leave empty for all]:"))
        self.widgets.labels[-1].grid(row=2, column=0, pady=(0, 10))
        self.widgets.entries.append(Entry(self.frame, width=20))
        self.widgets.entries[-1].grid(row=2, column=1, pady=(0, 10))
        self.widgets.labels.append(ttk.Label(self.frame, text="Time in (HH:MM:SS) [Optional]:"))
        self.widgets.labels[-1].grid(row=3, column=0, pady=(0, 10))
        self.widgets.entries.append(Entry(self.frame, width=20))
        self.widgets.entries[-1].grid(row=3, column=1, pady=(0, 10))
        self.widgets.labels.append(ttk.Label(self.frame, text="Date out (DD-MM-YYYY) [Leave empty for all]:"))
        self.widgets.labels[-1].grid(row=4, column=0, pady=(0, 10))
        self.widgets.entries.append(Entry(self.frame, width=20))
        self.widgets.entries[-1].grid(row=4, column=1, pady=(0, 10))
        self.widgets.labels.append(ttk.Label(self.frame, text="Time out (HH:MM:SS) [Optional]:"))
        self.widgets.labels[-1].grid(row=5, column=0, pady=(0, 10))
        self.widgets.entries.append(Entry(self.frame, width=20))
        self.widgets.entries[-1].grid(row=5, column=1, pady=(0, 10))
        self.widgets.buttons.append(Button(self.frame, text="Fetch Invoices", command=self.fetch_invoices_from_db))
        self.widgets.buttons[-1].grid(row=6, column=0, pady=(10, 0), sticky=EW, padx=10)
        self.widgets.buttons.append(Button(self.frame, text="Back", command=self.database_viewer_gui))
        self.widgets.buttons[-1].grid(row=6, column=1, pady=(10, 0), sticky=EW, padx=10)
        self.widgets.messages.append(Message(self.frame, text=" "))
        self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))

    def fetch_invoices_from_db(self):
        date_in = self.widgets.entries[0].get().strip()
        time_in = self.widgets.entries[1].get().strip()
        date_out = self.widgets.entries[2].get().strip()
        time_out = self.widgets.entries[3].get().strip()
        
        # Validate date/time format only if they are provided
        if not validate_date_time(date_in, time_in):
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="Invalid Date In/Time In Format. Use DD-MM-YYYY for date and HH:MM:SS for time", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
            
        if not validate_date_time(date_out, time_out):
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="Invalid Date Out/Time Out Format. Use DD-MM-YYYY for date and HH:MM:SS for time", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        
        invoices_text = get_invoices_from_db(self.db, date_in, time_in, date_out, time_out)
        if not invoices_text:
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="No Invoices Found", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        
        self.clear_status_message()
        self.widgets.texts[-1].config(state=NORMAL)
        self.widgets.texts[-1].delete(1.0, END)
        self.widgets.texts[-1].insert(END, invoices_text)
        self.widgets.texts[-1].config(state=DISABLED)

    def sql_query_gui(self):
        self.clear_frame()
        self.root.title("SQL Query Interface")
        self.active_gui = "sql_query_gui"
        self.status_space = (5, 0)

        self.widgets.labels.append(ttk.Label(self.frame, text="SQL Query Interface", font=("Arial", 18, "bold")))
        self.widgets.labels[-1].grid(row=0, column=0, columnspan=3, pady=(0, 20))
        if not self.db:
            self.widgets.messages.append(Message(self.frame, text="Please connect to Database first", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        self.widgets.labels.append(ttk.Label(self.frame, text="Enter SQL Query:"))
        self.widgets.labels[-1].grid(row=1, column=0, pady=(0, 10))
        self.widgets.texts.append(Text(self.frame, width=80, height=10))
        self.widgets.texts[-1].grid(row=1, column=1, columnspan=2, pady=(0, 10))
        self.widgets.buttons.append(Button(self.frame, text="Execute Query", command=self.execute_sql_query))
        self.widgets.buttons[-1].grid(row=2, column=1, pady=(10, 0), sticky=EW)
        self.widgets.buttons.append(Button(self.frame, text="Back", command=self.database_viewer_gui))
        self.widgets.buttons[-1].grid(row=2, column=2, pady=(10, 0), sticky=EW)
        self.widgets.messages.append(Message(self.frame, text=" "))
        self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))

    def execute_sql_query(self):
        query = self.widgets.texts[0].get(1.0, END).strip()
        if not query:
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="Please enter a SQL query", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        try:
            result = execute_query(self.db, query)
            if isinstance(result, str):
                self.clear_status_message()
                self.widgets.messages.append(Message(self.frame, text=result, width=400))
                self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            else:
                self.clear_status_message()
                self.widgets.texts[-1].config(state=NORMAL)
                self.widgets.texts[-1].delete(1.0, END)
                self.widgets.texts[-1].insert(END, result)
                self.widgets.texts[-1].config(state=DISABLED)
        except Exception as e:
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text=f"Error executing query: {str(e)}", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))

    def view_summary(self):
        self.clear_frame()
        self.root.title("Database Summary")
        self.active_gui = "database_summary_gui"
        self.status_space = (5, 0)

        self.widgets.labels.append(ttk.Label(self.frame, text="Database Summary", font=("Arial", 18, "bold")))
        self.widgets.labels[-1].grid(row=0, column=0, columnspan=3, pady=(0, 20))
        if not self.db:
            self.widgets.messages.append(Message(self.frame, text="Please connect to Database first", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        summary_text = get_database_summary(self.db)
        if not summary_text:
            self.clear_status_message()
            self.widgets.messages.append(Message(self.frame, text="No Summary Available", width=400))
            self.widgets.messages[-1].grid(row=self.status_space[0], column=self.status_space[1], columnspan=3, pady=(10, 0))
            return
        self.widgets.texts.append(Text(self.frame, width=80, height=20))
        self.widgets.texts[-1].insert(END, summary_text)
        self.widgets.texts[-1].config(state=DISABLED)
        self.widgets.texts[-1].grid(row=1, column=0, columnspan=3, pady=(0, 20))
        self.widgets.buttons.append(Button(self.frame, text="Back", command=self.database_viewer_gui))
        self.widgets.buttons[-1].grid(row=2, column=1, pady=(10, 0), sticky=EW)


if __name__ == "__main__":
    root = Tk()
    gui = GUI(root)
    gui.start_gui()
    root.mainloop()
