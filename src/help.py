

def get_email_help_text(domain):
    if domain == 'gmail.com':
        help_text = """Steps to connect Gmail:

1. Enable 2-Factor Authentication:
   - Go to Google Account settings
   - Security → 2-Step Verification → Turn On

2. Generate App Password:
   - Security → App passwords
   - Select app: Mail
   - Select device: Other (custom name)
   - Generate password

3. Use in application:
   - Email: your_email@gmail.com
   - Password: the generated app password (not your regular password)"""
    elif domain == 'yahoo.com':
        help_text = """Steps to connect Yahoo Mail:
1. Enable App Passwords:
   - Go to Yahoo Account Security settings
   - Click on "Generate app password"
   - Select app: Other (custom name)
   - Generate password

2. Use in application:
   - Email: your_email@yahoo.com
   - Password: the generated app password (not your regular password)"""    
    elif domain == 'outlook.com' or domain == 'hotmail.com' or domain == 'live.com':
        help_text = """Steps to connect Outlook:
1. Enable 2-Factor Authentication:
   - Go to Microsoft Account security settings
   - Security → Two-step verification → Turn On

2. Generate App Password:
   - Security → App passwords
   - Select app: Other (custom name)
   - Generate password

3. Use in application:
   - Email: your_email@outlook.com
   - Password: the generated app password (not your regular password)"""
    elif domain == 'icloud.com' or domain == 'me.com' or domain == 'mac.com':
        help_text = """Steps to connect iCloud Mail:
1. Enable App-Specific Passwords:
   - Go to Apple ID account settings
   - Security → App-Specific Passwords → Generate Password

2. Use in application:
   - Email: your_email@icloud.com
   - Password: the generated app-specific password (not your regular password)"""
    else:
        help_text = "No specific help available for this email provider."
    
    return help_text

def get_database_help_text():
    help_text = """Steps to connect to a SQL Database:
1. Install MySQL Connector:
   - Use pip: `pip install mysql-connector-python`

2. Use the following code to connect:
```python
import mysql.connector

conn = mysql.connector.connect(
   host="your_host",
   user="your_user",
   password="your_password",
   database="your_database"
)
```
3. Make sure to handle exceptions and close the connection properly."""
    return help_text