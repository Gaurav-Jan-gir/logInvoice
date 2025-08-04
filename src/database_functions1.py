import mysql.connector
from mysql.connector import Error
import pandas as pd
import time

class Database:
    
    def __init__(self, host, user, password, db):
        self.db = self.connect(host, user, password, db)
        if self.db:
            self.cursor = self.db.cursor(dictionary=True)
            self.create_tables()
        else:
            self.cursor = None

    def connect(self, host, user, password, db):
        try:
            connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=db
            )
            if connection.is_connected():
                print("Connected to MySQL database")
                return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None

    def create_tables(self):
        try:
            self.cursor.execute("SHOW TABLES LIKE 'invoices'")
            invoices_table_exists = self.cursor.fetchone()
            
            self.cursor.execute("SHOW TABLES LIKE 'invoice_items'")
            items_table_exists = self.cursor.fetchone()
            
            create_invoices_table = """
            CREATE TABLE IF NOT EXISTS invoices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                invoice_number VARCHAR(255) UNIQUE,
                invoice_date DATE,
                sender_info TEXT,
                billed_to VARCHAR(255),
                address TEXT,
                total_amount DECIMAL(10, 2),
                currency VARCHAR(10) DEFAULT 'USD',
                original_filename VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            create_invoice_items_table = """
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                invoice_id INT,
                item_description VARCHAR(255),
                quantity INT,
                unit_price DECIMAL(10, 2),
                total DECIMAL(10, 2),
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
            );
            """
            self.cursor.execute(create_invoices_table)
            self.cursor.execute(create_invoice_items_table)
            self.db.commit()

            if items_table_exists:
                self.cursor.execute("SHOW COLUMNS FROM invoice_items")
                items_columns = [row['Field'] for row in self.cursor.fetchall()]

                if 'invoice_id' not in items_columns:
                    print("Adding missing invoice_id column to invoice_items table...")
                    self.cursor.execute("ALTER TABLE invoice_items ADD COLUMN invoice_id INT")

                    if 'invoice_data_id' in items_columns:
                        print("Migrating data from invoice_data_id to invoice_id...")
                        self.cursor.execute("UPDATE invoice_items SET invoice_id = invoice_data_id WHERE invoice_data_id IS NOT NULL")
                    
                    self.db.commit()

                if 'item_description' not in items_columns and 'item_name' not in items_columns:
                    print("Adding missing item_description column to invoice_items table...")
                    self.cursor.execute("ALTER TABLE invoice_items ADD COLUMN item_description VARCHAR(255)")
                    self.db.commit()

                if 'total' not in items_columns and 'total_price' not in items_columns:
                    print("Adding missing total column to invoice_items table...")
                    self.cursor.execute("ALTER TABLE invoice_items ADD COLUMN total DECIMAL(10, 2)")
                    self.db.commit()

            if not invoices_table_exists:
                print("Tables created successfully.")
            else:
                print("Tables already exist.")

            self.cursor.execute("DESCRIBE invoices")
            columns = [row['Field'] for row in self.cursor.fetchall()]
            
            required_columns = {
                'invoice_number': 'VARCHAR(255) UNIQUE',
                'invoice_date': 'DATE',
                'sender_info': 'TEXT',
                'billed_to': 'VARCHAR(255)',
                'address': 'TEXT',
                'total_amount': 'DECIMAL(10, 2)',
                'currency': 'VARCHAR(10) DEFAULT "USD"',
                'original_filename': 'VARCHAR(255)',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            }
            
            for col_name, col_definition in required_columns.items():
                if col_name not in columns:
                    print(f"Adding missing {col_name} column...")
                    self.cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_definition}")
                    self.db.commit()
                
            print("Tables created or already exist.")
        except Error as e:
            print(f"Error creating tables: {e}")

    def log_invoice_data(self, parsed_data, filename):
        if not self.db or not self.db.is_connected():
            print("Database not connected.")
            return None

        invoice_number = parsed_data.get('invoice_number')
        if not invoice_number:
            print(f"Skipping entry for {filename} due to missing invoice number.")
            invoice_number = f"UNKNOWN_{filename}_{int(time.time())}"

        self.cursor.execute("SELECT id FROM invoices WHERE invoice_number = %s", (invoice_number,))
        if self.cursor.fetchone():
            print(f"Invoice {invoice_number} already exists. Skipping.")
            return None

        try:
            query = """
            INSERT INTO invoices (invoice_number, invoice_date, sender_info, billed_to, address, total_amount, currency, original_filename)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                invoice_number, parsed_data.get('date'), parsed_data.get('sender_info'),
                parsed_data.get('billed_to'), parsed_data.get('address'),
                parsed_data.get('total_amount'), parsed_data.get('currency', 'USD'), filename
            )
            
            self.cursor.execute(query, values)
            invoice_id = self.cursor.lastrowid

            items_df = parsed_data.get('items')
            if items_df is not None and not items_df.empty:
                self.cursor.execute("SHOW COLUMNS FROM invoice_items")
                columns = [row['Field'] for row in self.cursor.fetchall()]

                fk_col = 'invoice_id' if 'invoice_id' in columns else (
                    'invoice_data_id' if 'invoice_data_id' in columns else 'id'
                )
                item_col = 'item_description' if 'item_description' in columns else (
                    'item_name' if 'item_name' in columns else 'description'
                )
                total_col = 'total' if 'total' in columns else (
                    'total_price' if 'total_price' in columns else 'amount'
                )
                
                print(f"[DEBUG] Using columns: {fk_col}, {item_col}, quantity, unit_price, {total_col}")

                items_sql = f"INSERT INTO invoice_items ({fk_col}, {item_col}, quantity, unit_price, {total_col}) VALUES (%s, %s, %s, %s, %s)"
                
                for _, row in items_df.iterrows():
                    item_values = (invoice_id, row['Item'], row['Quantity'], row['Unit Price'], row['Total'])
                    self.cursor.execute(items_sql, item_values)

            self.db.commit()
            print(f"Successfully logged invoice ID: {invoice_id}")
            return invoice_id
        except Error as e:
            print(f"Error logging invoice to DB: {e}")
            self.db.rollback()
            return None
        
    def get_invoices(self, date_in="", time_in="", date_out="", time_out=""):
        if not self.db or not self.db.is_connected():
            return "Database not connected."

        try:

            try:
                self.cursor.execute("SHOW COLUMNS FROM invoice_items")
                columns = [row['Field'] for row in self.cursor.fetchall()]

                item_col = 'item_description' if 'item_description' in columns else 'item_name'
                total_col = 'total' if 'total' in columns else 'total_price'

                fk_col = 'invoice_id' if 'invoice_id' in columns else 'invoice_data_id'
                
                query = f"""
                SELECT 
                    i.id as invoice_id,
                    i.invoice_number,
                    i.invoice_date,
                    i.sender_info,
                    i.billed_to,
                    i.address,
                    i.total_amount,
                    'INR' as currency,
                    ii.{item_col} as item_description,
                    ii.quantity,
                    ii.unit_price,
                    ii.{total_col} as total_price,
                    i.created_at
                FROM invoices i
                LEFT JOIN invoice_items ii ON i.id = ii.{fk_col}
                """
            except Exception as schema_e:
                query = """
                SELECT 
                    i.id as invoice_id,
                    i.invoice_number,
                    i.invoice_date,
                    i.sender_info,
                    i.billed_to,
                    i.address,
                    i.total_amount,
                    'INR' as currency,
                    NULL as item_description,
                    NULL as quantity,
                    NULL as unit_price,
                    NULL as total_price,
                    i.created_at
                FROM invoices i
                """
            
            params = []
            conditions = []

            if date_in:
                try:
                    final_time_in = time_in if time_in else "00:00:00"
                    start_dt = f"{pd.to_datetime(date_in, format='%d-%m-%Y').date()} {final_time_in}"
                    conditions.append("i.created_at >= %s")
                    params.append(start_dt)
                except (ValueError, TypeError):
                    return "Invalid date format for 'Date In'. Please use DD-MM-YYYY."

            if date_out:
                try:
                    final_time_out = time_out if time_out else "23:59:59"
                    end_dt = f"{pd.to_datetime(date_out, format='%d-%m-%Y').date()} {final_time_out}"
                    conditions.append("i.created_at <= %s")
                    params.append(end_dt)
                except (ValueError, TypeError):
                    return "Invalid date format for 'Date Out'. Please use DD-MM-YYYY."

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY i.created_at DESC, i.id"
            
            self.cursor.execute(query, tuple(params))
            results = self.cursor.fetchall()

            if not results:
                return "No invoices found for the specified period."

            formatted_output = []
            current_invoice_id = None
            
            for row in results:
                invoice_id = row.get('invoice_id')
                invoice_number = row.get('invoice_number')
                invoice_date = row.get('invoice_date')
                sender_info = row.get('sender_info')
                billed_to = row.get('billed_to')
                address = row.get('address')
                total_amount = row.get('total_amount')
                currency = row.get('currency')
                item_description = row.get('item_description')
                quantity = row.get('quantity')
                unit_price = row.get('unit_price')
                total_price = row.get('total_price')
                created_at = row.get('created_at')
                
                if current_invoice_id != invoice_id:
                    if current_invoice_id is not None:
                        formatted_output.append("-" * 80)
                    
                    formatted_output.append(f"INVOICE #{invoice_number or 'N/A'}")
                    formatted_output.append(f"Date: {invoice_date or 'N/A'}")
                    formatted_output.append(f"Billed To: {billed_to or 'N/A'}")
                    formatted_output.append(f"Address: {address or 'N/A'}")
                    formatted_output.append(f"Sender: {sender_info or 'N/A'}")
                    formatted_output.append(f"Total Amount: {currency or ''} {total_amount or '0.00'}")
                    formatted_output.append(f"Created: {created_at}")
                    formatted_output.append("")
                    formatted_output.append("ITEMS:")
                    formatted_output.append(f"{'Item Name':<30} {'Qty':<8} {'Unit Price':<12} {'Total Price':<12}")
                    formatted_output.append("-" * 70)
                    current_invoice_id = invoice_id
                
                if item_description:
                    safe_quantity = quantity or 0
                    try:
                        safe_unit_price = float(unit_price) if unit_price is not None else 0.00
                    except (ValueError, TypeError):
                        safe_unit_price = 0.00
                    try:
                        safe_total_price = float(total_price) if total_price is not None else 0.00
                    except (ValueError, TypeError):
                        safe_total_price = 0.00
                    formatted_output.append(f"{item_description:<30} {safe_quantity:<8} {safe_unit_price:<12.2f} {safe_total_price:<12.2f}")
            
            if formatted_output:
                formatted_output.append("-" * 80)
            
            return "\n".join(formatted_output) if formatted_output else "No invoice data found."
            
        except Error as e:
            return f"Error fetching invoices: {e}"
        
    def execute_raw_query(self, query):
        if not self.db or not self.db.is_connected():
            return "Database not connected."
        
        try:
            self.cursor.execute(query)

            if query.strip().lower().startswith(('select', 'show', 'desc', 'explain')):
                result = self.cursor.fetchall()
                if not result:
                    return "Query executed successfully, but returned no results."

                return pd.DataFrame(result).to_string()
            
            else:
                self.db.commit()
                return f"Query executed successfully. Rows affected: {self.cursor.rowcount}"

        except Error as e:
            self.db.rollback()
            return f"Error executing query: {e}"
        
    def get_summary(self):
        if not self.db or not self.db.is_connected():
            return "Database not connected."
        
        try:
            summary_lines = []

            self.cursor.execute("SELECT COUNT(*) as total FROM invoices")
            total_invoices = self.cursor.fetchone()['total']
            summary_lines.append(f"Total Invoices Logged: {total_invoices}")

            self.cursor.execute("SELECT SUM(total_amount) as total_sum FROM invoices")

            total_sum = self.cursor.fetchone()['total_sum'] or 0.0
            summary_lines.append(f"Total Value of All Invoices: ${total_sum:,.2f}")

            summary_lines.append("\n--- Most Recent Invoices ---")
            self.cursor.execute(
                "SELECT invoice_number, total_amount, created_at FROM invoices ORDER BY created_at DESC LIMIT 5"
            )
            recent_invoices = self.cursor.fetchall()

            if not recent_invoices:
                summary_lines.append("No invoices found.")
            else:
                for inv in recent_invoices:
                    date_str = inv['created_at'].strftime('%Y-%m-%d')
                    summary_lines.append(f"  - #{inv['invoice_number']} (${inv['total_amount']}) on {date_str}")
            
            return "\n".join(summary_lines)

        except Error as e:
            return f"Error generating summary: {e}"
            
    def close(self):
        if self.db and self.db.is_connected():
            self.db.close()
            print("Database connection closed.")
    
    def fetch_invoices(self, date_in="", time_in="", date_out="", time_out=""):
        """Wrapper method for get_invoices to maintain compatibility"""
        return self.get_invoices(date_in, time_in, date_out, time_out)
    
    def execute_query(self, query):
        """Wrapper method for execute_raw_query to maintain compatibility"""
        return self.execute_raw_query(query)
    
    def get_export_data(self):
        """
        Get structured data for Excel export including invoices and items
        Returns dictionary with invoices_data and items_data
        """
        if not self.db or not self.db.is_connected():
            return None
        
        try:
            # Check available columns in invoice_items table
            self.cursor.execute("SHOW COLUMNS FROM invoice_items")
            item_columns = [row['Field'] for row in self.cursor.fetchall()]
            
            item_col = 'item_description' if 'item_description' in item_columns else 'item_name'
            total_col = 'total' if 'total' in item_columns else 'total_price'
            fk_col = 'invoice_id' if 'invoice_id' in item_columns else 'invoice_data_id'
            
            # Query for invoices summary
            invoices_query = """
            SELECT 
                i.id,
                i.invoice_number,
                i.invoice_date,
                i.sender_info,
                i.billed_to,
                i.address,
                i.total_amount,
                i.original_filename,
                i.created_at
            FROM invoices i
            ORDER BY i.created_at DESC
            """
            
            # Query for detailed invoice items
            items_query = f"""
            SELECT 
                i.invoice_number,
                i.invoice_date,
                i.billed_to,
                i.total_amount as invoice_total,
                ii.{item_col} as item_description,
                ii.quantity,
                ii.unit_price,
                ii.{total_col} as item_total,
                i.created_at
            FROM invoices i
            LEFT JOIN invoice_items ii ON i.id = ii.{fk_col}
            ORDER BY i.created_at DESC, ii.id
            """
            
            # Execute queries
            self.cursor.execute(invoices_query)
            invoices_data = self.cursor.fetchall()
            
            self.cursor.execute(items_query)
            items_data = self.cursor.fetchall()
            
            return {
                'invoices_data': invoices_data,
                'items_data': items_data
            }
            
        except Exception as e:
            print(f"Error getting export data: {e}")
            return None

    def get_detailed_export_data(self):
        """
        Get detailed item-level data for Excel export with specific column format:
        Invoice No. | Date | Receiver | Receiver_Address | Sender | Sender_Address | Item_Name | Item_Quantity | Unit_Price | Total_Price
        """
        if not self.db or not self.db.is_connected():
            return None
        
        try:
            # Check available columns in invoice_items table
            self.cursor.execute("SHOW COLUMNS FROM invoice_items")
            item_columns = [row['Field'] for row in self.cursor.fetchall()]
            
            item_col = 'item_description' if 'item_description' in item_columns else 'item_name'
            total_col = 'total' if 'total' in item_columns else 'total_price'
            fk_col = 'invoice_id' if 'invoice_id' in item_columns else 'invoice_data_id'
            
            # Query for detailed invoice items with exact column mapping
            detailed_query = f"""
            SELECT 
                i.invoice_number as Invoice_No,
                i.invoice_date as Date,
                i.billed_to as Receiver,
                i.address as Receiver_Address,
                i.sender_info as Sender,
                '' as Sender_Address,
                ii.{item_col} as Item_Name,
                ii.quantity as Item_Quantity,
                ii.unit_price as Unit_Price,
                ii.{total_col} as Total_Price,
                i.currency as Currency
            FROM invoices i
            LEFT JOIN invoice_items ii ON i.id = ii.{fk_col}
            WHERE ii.{item_col} IS NOT NULL
            ORDER BY i.created_at DESC, ii.id
            """
            
            # Execute query
            self.cursor.execute(detailed_query)
            detailed_data = self.cursor.fetchall()
            
            return detailed_data
            
        except Exception as e:
            print(f"Error getting detailed export data: {e}")
            return None
    