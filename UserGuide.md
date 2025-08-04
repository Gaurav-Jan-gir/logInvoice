# Invoice Data Extractor - User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Main Interface](#main-interface)
6. [Email Configuration](#email-configuration)
7. [Database Setup](#database-setup)
8. [Processing Invoices](#processing-invoices)
9. [Database Viewer](#database-viewer)
10. [Excel Export](#excel-export)
11. [Troubleshooting](#troubleshooting)
12. [Advanced Features](#advanced-features)

## Introduction

The Invoice Data Extractor is a comprehensive Python application designed to automate the process of extracting invoice data from PDF documents, storing it in a structured database, and providing various interfaces for viewing and exporting the data.

### Key Features
- **Email Integration**: Automatically download invoices from email accounts
- **PDF Processing**: Extract text and structured data from PDF invoices
- **Database Storage**: Store invoice data in MySQL with proper relationships
- **Excel Export**: Generate detailed Excel reports with multiple sheets
- **GUI Interface**: User-friendly graphical interface for all operations
- **Currency Support**: Automatic detection and storage of multiple currencies
- **Robust Parsing**: Handles various invoice formats with fallback values

## System Requirements

### Software Requirements
- **Python**: Version 3.8 or higher
- **MySQL**: Version 5.7 or higher (for database storage)
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)

### Python Dependencies
The application automatically installs required packages, including:
- `mysql-connector-python` - Database connectivity
- `pandas` - Data manipulation
- `openpyxl` - Excel file generation
- `pdfplumber` - PDF text extraction
- `tkinter` - GUI framework (usually included with Python)
- `cryptography` - Secure credential storage

### Hardware Requirements
- **RAM**: Minimum 4GB, recommended 8GB
- **Storage**: At least 1GB free space for application and data
- **Network**: Internet connection for email integration

## Installation

### 1. Download the Application
```bash
git clone https://github.com/Gaurav-Jan-gir/logInvoice.git
cd logInvoice
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
# Navigate to source directory
cd src

# Run the main GUI application
python gui1.py
```

## Getting Started

### First Launch
When you first run the application, you'll see the main interface with several options. Before processing invoices, you need to configure:

1. **Email Connection** (optional but recommended)
2. **Database Connection** (required for data storage)

### Quick Start Workflow
1. Launch the application: `python gui1.py`
2. Connect to your database
3. Connect to your email (if using email integration)
4. Process invoices using "Fetch & Log Invoices"
5. View results in "Database Viewer"
6. Export data using "Export to Excel"

## Main Interface

The main interface provides access to all major functions:

### Main Menu Options

#### 1. Connect Email / Disconnect Email
- **Purpose**: Establish connection to your email account for automatic invoice download
- **When to use**: If you want to automatically download invoices from email
- **Status**: Shows "Connect Email" when disconnected, "Disconnect Email" when connected

#### 2. Connect Database / Disconnect Database
- **Purpose**: Establish connection to MySQL database for storing invoice data
- **When to use**: Required for all data storage operations
- **Status**: Shows "Connect Database" when disconnected, "Disconnect Database" when connected

#### 3. Fetch & Log Invoices
- **Purpose**: Main processing function to download, parse, and store invoice data
- **Requirements**: Both email and database connections must be active
- **Features**: Manual fetch, automatic periodic fetching, retry failed invoices

#### 4. Database Viewer
- **Purpose**: View, search, and export stored invoice data
- **Features**: Invoice listing, date filtering, SQL queries, Excel export
- **Requirements**: Database connection must be active

#### 5. Exit
- **Purpose**: Safely close the application and all connections

## Email Configuration

### Supported Email Providers
- **Gmail**: Requires app-specific password
- **Outlook/Hotmail**: Uses standard IMAP
- **Yahoo Mail**: Requires app password
- **Other IMAP providers**: Custom server configuration

### Setting Up Email Connection

#### 1. Access Email Login
Click "Connect Email" from the main menu to open the email configuration screen.

#### 2. Enter Credentials
- **Email Address**: Your full email address
- **Password**: 
  - For Gmail: Use app-specific password (not your regular password)
  - For other providers: May use regular password or app password

#### 3. Configuration Options
- **Remember Email**: Check to save credentials securely for future use
- **Help**: Click for provider-specific setup instructions

### Gmail Setup (Detailed)
1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and your device
   - Copy the generated 16-character password
3. **Use in Application**:
   - Email: your.email@gmail.com
   - Password: the 16-character app password (no spaces)

### Troubleshooting Email Connection
- **"Invalid credentials"**: Double-check email and password
- **"Connection timeout"**: Check internet connection and firewall settings
- **"Authentication failed"**: Ensure app passwords are enabled for your provider

## Database Setup

### MySQL Configuration

#### 1. Database Installation
Ensure MySQL is installed and running on your system:
- **Windows**: Download from MySQL official website
- **macOS**: Use Homebrew: `brew install mysql`
- **Linux**: Use package manager: `sudo apt install mysql-server`

#### 2. Create Database
```sql
CREATE DATABASE invoice_logger;
CREATE USER 'invoice_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON invoice_logger.* TO 'invoice_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 3. Application Configuration
Click "Connect Database" and enter:
- **Host**: localhost (or your MySQL server IP)
- **User**: invoice_user (or your MySQL username)
- **Password**: your MySQL password
- **Database**: invoice_logger (or your preferred database name)

### Database Schema
The application automatically creates required tables:

#### Invoices Table
- `id`: Primary key
- `invoice_number`: Unique invoice identifier
- `invoice_date`: Date of the invoice
- `sender_info`: Sender details
- `billed_to`: Customer information
- `address`: Customer address
- `total_amount`: Invoice total
- `currency`: Currency code (USD, EUR, INR, etc.)
- `original_filename`: Source file name
- `created_at`: Processing timestamp

#### Invoice Items Table
- `id`: Primary key
- `invoice_id`: Foreign key to invoices table
- `item_description`: Item name/description
- `quantity`: Item quantity
- `unit_price`: Price per unit
- `total`: Total price for the item

## Processing Invoices

### Fetch & Log Invoices Interface

#### Manual Processing
1. **Fetch Invoices Now**: Process all new invoices immediately
2. **Retry Old Invoices**: Reprocess previously failed invoices with improved parsing

#### Automatic Processing
1. **Set Fetch Interval**: Choose interval in minutes (default: 30)
2. **Start Fetching**: Begin automatic periodic processing
3. **Stop Fetching**: End automatic processing

### Processing Workflow
1. **Email Download**: Connect to email and download PDF attachments
2. **Text Extraction**: Extract text content from PDF files
3. **Data Parsing**: Parse invoice data using intelligent patterns:
   - Invoice numbers
   - Dates (multiple formats supported)
   - Sender information
   - Customer details
   - Line items with quantities and prices
   - Currency detection
4. **Database Storage**: Store parsed data with proper relationships
5. **Error Handling**: Log and retry failed processes

### Data Parsing Features

#### Robust Date Handling
- Supports formats: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD
- Handles month names: "July 14, 2025", "14 Jul 2025"
- Fallback to current date if parsing fails

#### Currency Detection
- Automatic symbol recognition: $, €, £, ₹
- Text pattern matching: USD, EUR, GBP, INR
- Default fallback to USD

#### Sender Information
- Multiple pattern matching for sender extraction
- Email address detection and formatting
- Length validation to prevent over-capturing
- Fallback to "Unknown Sender"

#### Fallback Values
- **Invoice Number**: Auto-generated if missing
- **Date**: Current date if not found
- **Customer**: "Customer" if billed_to missing
- **Address**: "N/A" if not found
- **Total Amount**: 0.00 if parsing fails

## Database Viewer

### Main Features

#### 1. View Invoices
- **Full List**: Display all invoices with details
- **Date Filtering**: Filter by date range
- **Item Details**: Show individual line items
- **Search**: Find specific invoices

#### 2. SQL Queries (Advanced)
- **Direct SQL Access**: Execute custom queries
- **Data Analysis**: Perform complex data analysis
- **Reporting**: Generate custom reports

#### 3. View Summary
- **Statistics**: Total invoices, amounts, averages
- **Recent Activity**: Latest processed invoices
- **Overview**: Quick system status

#### 4. Export to Excel
- **Detailed Export**: Complete invoice and item data
- **Multiple Formats**: Various export options
- **Professional Formatting**: Ready-to-use Excel files

### Date Filtering
Use the date filtering feature to narrow down invoice views:
- **Date Format**: DD-MM-YYYY (e.g., 03-08-2025)
- **Time Format**: HH:MM:SS (optional)
- **Range Selection**: Use both "Date In" and "Date Out" for ranges
- **Leave Empty**: Show all invoices

## Excel Export

### Export Features
The Excel export creates a comprehensive spreadsheet with detailed invoice data:

#### Column Structure
- **Invoice_No**: Invoice number/identifier
- **Date**: Invoice date
- **Receiver**: Customer/billed to information
- **Receiver_Address**: Customer address
- **Sender**: Sender information
- **Sender_Address**: Sender address (future use)
- **Item_Name**: Individual item description
- **Item_Quantity**: Quantity of each item
- **Unit_Price**: Price per unit
- **Total_Price**: Total for each item
- **Currency**: Currency code

#### Export Process
1. Click "Export to Excel" from Database Viewer
2. Choose save location and filename
3. Wait for processing completion
4. Open Excel file to view results

#### Excel File Features
- **Professional Formatting**: Bold headers, auto-sized columns
- **Item-Level Detail**: Each row represents one invoice item
- **Multiple Invoices**: All invoices in single sheet
- **Currency Information**: Clearly marked currency for each transaction

## Troubleshooting

### Common Issues and Solutions

#### Database Connection Issues
**Problem**: "Error connecting to database"
**Solutions**:
- Verify MySQL is running
- Check credentials (host, user, password, database name)
- Ensure database exists and user has permissions
- Check firewall settings

#### Email Connection Issues
**Problem**: "Error connecting to email"
**Solutions**:
- Verify email credentials
- Use app-specific passwords for Gmail
- Check internet connection
- Enable IMAP in email settings

#### PDF Processing Issues
**Problem**: "Failed to extract text from PDF"
**Solutions**:
- Ensure PDF is not password-protected
- Check PDF is not corrupted
- Verify sufficient disk space
- Try processing single file manually

#### Parsing Issues
**Problem**: "Invoice data not extracted correctly"
**Solutions**:
- Check PDF text quality (OCR may be needed for scanned images)
- Review invoice format - application supports standard business invoices
- Use "Retry Old Invoices" after system updates
- Check debug output for parsing details

#### Export Issues
**Problem**: "Excel export fails or incomplete"
**Solutions**:
- Ensure sufficient disk space
- Check file permissions in target directory
- Verify database contains invoice data
- Close Excel if file is already open

### Debug Information
The application provides detailed debug output in the console:
- **Parsing Progress**: Shows what data is being extracted
- **Currency Detection**: Displays detected currency
- **Sender Information**: Shows extracted sender details
- **Database Operations**: Logs all database transactions
- **Error Details**: Specific error messages for troubleshooting

### Getting Help
1. **Console Output**: Check terminal/command prompt for detailed error messages
2. **Log Files**: Application creates logs for debugging
3. **Test Mode**: Use individual test scripts for component testing
4. **Documentation**: Refer to technical documentation in `/docs`

## Advanced Features

### Bulk Processing
- **Folder Monitoring**: Process all PDFs in a directory
- **Batch Operations**: Handle multiple invoices simultaneously
- **Progress Tracking**: Monitor processing status

### Data Validation
- **Duplicate Detection**: Prevent duplicate invoice entries
- **Data Integrity**: Validate parsed data before storage
- **Error Recovery**: Automatic retry mechanisms

### Security Features
- **Encrypted Storage**: Credentials stored securely
- **SSL Connections**: Secure email and database connections
- **Access Control**: Database user permissions

### Performance Optimization
- **Background Processing**: Non-blocking operations
- **Memory Management**: Efficient handling of large datasets
- **Database Indexing**: Optimized query performance

### Customization Options
- **Currency Support**: Add new currency types
- **Date Formats**: Configure additional date patterns
- **Parsing Rules**: Customize extraction patterns
- **Export Formats**: Modify Excel output structure

## Support and Maintenance

### Regular Maintenance
- **Database Backup**: Regular backup of invoice data
- **Log Cleanup**: Remove old log files
- **Update Dependencies**: Keep Python packages current
- **Performance Monitoring**: Monitor system resource usage

### Updates and Upgrades
- **Version Control**: Track application versions
- **Feature Updates**: New functionality additions
- **Bug Fixes**: Regular maintenance releases
- **Security Updates**: Security patch management

---

## Conclusion

The Invoice Data Extractor provides a comprehensive solution for automated invoice processing. By following this user guide, you should be able to:

1. Set up and configure the application
2. Connect to email and database systems
3. Process invoices automatically or manually
4. View and analyze invoice data
5. Export professional Excel reports
6. Troubleshoot common issues

For technical support or feature requests, refer to the project documentation or contact the development team.
