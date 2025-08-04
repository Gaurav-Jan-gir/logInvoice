# Invo### Core Functionality
- **📧 Email Integration**: Automatic invoice download from email accounts (Gmail, Outlook, Yahoo, etc.)
- **📄 PDF Processing**: Intelligent text extraction and data parsing from PDF invoices using pdfplumber
- **🗃️ Database Storage**: MySQL-based storage with relational data structure
- **🖥️ GUI Interface**: User-friendly Tkinter-based graphical interface
- **📊 Excel Export**: Professional Excel reports with item-level detail using openpyxl
- **💱 Multi-Currency Support**: Automatic detection and handling of multiple currencies (USD, EUR, GBP, INR)
- **🔄 Automated Processing**: Configurable periodic processing with retry mechanismsxtractor

A comprehensive Python application for automated invoice processing, featuring email integration, intelligent data extraction, and professional Excel reporting capabilities.

## 🚀 Features

### Core Functionality
- **📧 Email Integration**: Automatic invoice download from email accounts (Gmail, Outlook, Yahoo, etc.)
- **📄 PDF Processing**: Intelligent text extraction and data parsing from PDF invoices using pdfplumber
- **🗃️ Database Storage**: MySQL-based storage with relational data structure
- **🖥️ GUI Interface**: User-friendly Tkinter-based graphical interface (main implementation)
- **� CLI Interface**: Command-line interface available in alternative implementation
- **🌐 Web Interface**: Experimental web-based interface for headless environments  
- **�📊 Excel Export**: Professional Excel reports with item-level detail using openpyxl
- **💱 Multi-Currency Support**: Automatic detection and handling of multiple currencies (USD, EUR, GBP, INR)
- **🔄 Automated Processing**: Configurable periodic processing with retry mechanisms

### Advanced Features
- **🛡️ Robust Parsing**: Intelligent fallback values for missing data
- **📅 Flexible Date Handling**: Support for multiple date formats
- **🔍 Smart Data Extraction**: Pattern-based extraction for invoice numbers, amounts, and items
- **🔐 Secure Credentials**: Encrypted storage of email and database credentials
- **📈 Data Visualization**: Built-in database viewer with filtering and search
- **⚡ Background Processing**: Non-blocking operations for better user experience

## 📋 System Requirements

### Software Requirements
- **Python**: 3.8 or higher
- **MySQL**: 5.7 or higher
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)

### Hardware Requirements
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 1GB free space
- **Network**: Internet connection for email integration

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/Gaurav-Jan-gir/logInvoice.git
cd logInvoice
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database
```sql
CREATE DATABASE invoice_logger;
CREATE USER 'invoice_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON invoice_logger.* TO 'invoice_user'@'localhost';
FLUSH PRIVILEGES;
```

## 🚀 Quick Start

### Launch Application
```bash
cd src
source ../.venv/bin/activate
python gui1.py
```

### Basic Workflow
1. **Connect Database**: Configure MySQL connection
2. **Connect Email**: Set up email account (optional)
3. **Fetch Invoices**: Process invoices automatically or manually
4. **View Data**: Use database viewer to review processed invoices
5. **Export Reports**: Generate Excel reports with detailed item breakdown

## 📁 Project Structure

```
logInvoice/
├── src/                           # Main application source
│   ├── gui1.py                   # Main GUI application
│   ├── gui_functions1.py         # GUI helper functions  
│   ├── database_functions1.py    # Database operations
│   ├── help.py                   # Help and documentation functions
│   ├── invoice_data.py           # Data parsing and extraction
│   ├── invoice_download.py       # Email integration
│   ├── pdf_reader.py            # PDF processing
│   └── gui.py                   # (Empty placeholder)
├── attachments/                  # Downloaded invoice PDFs (auto-created)
├── extracted_text/              # Extracted text files (auto-created)
├── parsed_data/                 # Processed invoice data (auto-created)
├── docs/                        # Project documentation
├── tex/                         # LaTeX documentation guides
└── UserGuide.md                # Comprehensive user guide
```

### Database Schema

The application uses MySQL with the following schema:

### Invoices Table
```sql
CREATE TABLE invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_number VARCHAR(255) UNIQUE,
    invoice_date DATE,
    sender_info TEXT,
    billed_to VARCHAR(255),
    address TEXT,
    total_amount DECIMAL(10,2),
    currency VARCHAR(10) DEFAULT 'USD',
    original_filename VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Invoice Items Table
```sql
CREATE TABLE invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT,
    item_description VARCHAR(255),
    quantity INT,
    unit_price DECIMAL(10,2),
    total DECIMAL(10,2),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
```

## 📊 Excel Export Format

The application generates professional Excel reports with the following columns:
- **Invoice_No**: Invoice identifier
- **Date**: Invoice date
- **Receiver**: Customer information
- **Receiver_Address**: Customer address
- **Sender**: Vendor/sender details
- **Sender_Address**: Vendor address
- **Item_Name**: Product/service description
- **Item_Quantity**: Quantity of items
- **Unit_Price**: Price per unit
- **Total_Price**: Total for each line item
- **Currency**: Currency code (USD, EUR, INR, etc.)

## 🔧 Configuration

### Email Setup
Supports major email providers with secure authentication:

#### Gmail Configuration
1. Enable 2-Factor Authentication
2. Generate App Password (Google Account → Security → App passwords)
3. Use app password in application (not your regular password)

#### Other Providers
- **Outlook/Hotmail**: Standard IMAP with app password
- **Yahoo**: App-specific password required
- **Custom IMAP**: Manual server configuration

### Database Configuration
Configure MySQL connection through the GUI or configuration files:
- **Host**: localhost or remote MySQL server
- **Database**: invoice_logger (or custom name)
- **User**: MySQL username with appropriate privileges
- **Password**: Secure MySQL password

## 🎯 Usage Examples

### Processing Email Invoices
```python
# Automatic processing every 30 minutes
# Set interval in GUI and click "Start Fetching"
```

### Manual PDF Processing
```python
# Place PDFs in attachments/ folder
# Click "Fetch Invoices Now" in GUI
```

### Database Queries
```sql
-- View recent invoices
SELECT * FROM invoices WHERE invoice_date >= DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Total revenue by currency
SELECT currency, SUM(total_amount) as total_revenue 
FROM invoices 
GROUP BY currency;

-- Item analysis
SELECT item_description, SUM(quantity) as total_quantity, AVG(unit_price) as avg_price
FROM invoice_items 
GROUP BY item_description;
```

## 🛠️ Advanced Features

### Data Parsing Intelligence
- **Multi-format Date Support**: DD/MM/YYYY, MM/DD/YYYY, "July 14, 2025"
- **Currency Detection**: Symbol recognition (₹, $, €, £) and text patterns
- **Fallback Values**: Comprehensive default values for missing data
- **Sender Extraction**: Smart pattern matching with length validation

### Error Handling
- **Robust Processing**: Continues processing even with malformed data
- **Retry Mechanisms**: Automatic retry for failed operations
- **Debug Logging**: Detailed console output for troubleshooting
- **Graceful Degradation**: Fallback values prevent system crashes

### Performance Optimization
- **Background Processing**: Non-blocking operations
- **Memory Management**: Efficient handling of large datasets
- **Database Indexing**: Optimized query performance
- **Batch Processing**: Handle multiple invoices simultaneously

## 🔍 Troubleshooting

### Common Issues

#### Database Connection
```bash
# Check MySQL service
sudo systemctl status mysql

# Test connection
mysql -u invoice_user -p invoice_logger
```

#### Email Connection
- Verify IMAP is enabled in email settings
- Use app-specific passwords for Gmail
- Check firewall/antivirus settings

#### PDF Processing
- Ensure PDFs are not password-protected
- Verify sufficient disk space
- Check PDF contains extractable text (not scanned images)

### Debug Mode
Enable verbose logging by setting debug mode in the GUI interface or by modifying the configuration files.

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Install dependencies: `pip install -r requirements.txt`
4. Make changes and test thoroughly
5. Submit pull request with detailed description

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Include docstrings for functions and classes
- Write unit tests for new features

## 📚 Documentation

- **[UserGuide.md](UserGuide.md)**: Comprehensive user documentation

## 🔄 Version History

### Current Version: 2.1.0
- Enhanced Excel export with single-sheet format
- Improved currency detection and storage
- Robust parsing with comprehensive fallback values
- Advanced date handling for multiple formats
- Professional GUI with better error handling

### Previous Versions
- **2.0.0**: Added MySQL database support and GUI interface
- **1.5.0**: Implemented email integration and automated processing
- **1.0.0**: Basic PDF processing and data extraction

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
1. **User Guide**: Check [UserGuide.md](UserGuide.md) for detailed instructions
2. **Debug Output**: Enable debug mode for detailed error information
3. **Issues**: Create GitHub issue with reproduction steps
4. **Documentation**: Review technical documentation in `/docs`

### Feature Requests
Submit feature requests through GitHub issues with:
- Clear description of desired functionality
- Use case examples
- Potential implementation approach

### Bug Reports
Include the following information:
- Operating system and Python version
- Complete error messages
- Steps to reproduce the issue
- Sample data (anonymized) if applicable

---

## 🎉 Success Stories

This application has successfully processed thousands of invoices across various formats and currencies, providing reliable automated invoice management for businesses and individuals.

**Ready to streamline your invoice processing? Get started with the [UserGuide.md](UserGuide.md)!**
