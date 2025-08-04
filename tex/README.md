# LaTeX Documentation

This folder contains comprehensive LaTeX documentation for text processing and data conversion.

## Files

### Text-to-DataFrame Guide
- **`text_to_dataframe_guide.tex`** - Complete guide for converting text to DataFrames
- **`text_to_dataframe_guide.pdf`** - Compiled PDF version (169KB)
- **`Makefile`** - Build automation for LaTeX compilation

### Regular Expressions Guide
- **`regex_complete_guide.tex`** - Comprehensive regular expressions guide
- **`regex_complete_guide.pdf`** - Compiled PDF version (209KB)
- **`Makefile_regex`** - Build automation for regex guide
- **`regex_examples.py`** - Practical Python regex examples

## Compilation

### Text-to-DataFrame Guide
```bash
# Using make (recommended)
make pdf

# Or manually
pdflatex text_to_dataframe_guide.tex
```

### Regular Expressions Guide
```bash
# Using make (recommended)
make -f Makefile_regex regex-pdf

# Or manually
pdflatex regex_complete_guide.tex
```

## Document Contents

The LaTeX guide covers:

### 1. Introduction and Foundations
- Why convert text to DataFrames
- Understanding text structure
- Data types and schemas

### 2. Core Methodologies
- Regular expression parsing
- Line-by-line processing
- Pattern matching techniques

### 3. Implementation Strategies
- Multi-DataFrame approach
- Comprehensive single DataFrame
- Pros and cons of each approach

### 4. Advanced Techniques
- Contextual state machines
- Multi-pass processing
- Complex document handling

### 5. Data Validation
- Schema validation
- Business logic validation
- Data consistency checks

### 6. Performance Optimization
- Efficient string operations
- Memory management
- Large dataset processing

### 7. Integration
- Database integration
- API integration
- Export capabilities

### 8. Case Studies
- Simple invoice processing
- Batch processing examples
- Real-world scenarios

### 9. Error Handling
- Common parsing errors
- Robust error handling
- Troubleshooting guide

### 10. Best Practices
- Design principles
- Code organization
- Configuration management

## Building the PDF

### Prerequisites
You need a LaTeX distribution installed:

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-full
```

**macOS:**
```bash
brew install --cask mactex
```

**Windows:**
Download and install MiKTeX or TeX Live

### Compilation
```bash
# Using Makefile (recommended)
make pdf

# Or manually
pdflatex text_to_dataframe_guide.tex
pdflatex text_to_dataframe_guide.tex  # Second pass for TOC
```

### Cleaning
```bash
# Clean auxiliary files
make clean

# Clean everything including PDF
make distclean
```

### Viewing
```bash
# Open PDF (Linux)
make view

# Or manually open the generated PDF file
```

## Document Features

- **Comprehensive Coverage**: 40+ pages of detailed explanations
- **Code Examples**: Fully functional Python code snippets
- **Visual Elements**: Tables, lists, and structured formatting
- **Cross-References**: Linked table of contents and sections
- **Professional Layout**: Academic paper formatting
- **Practical Focus**: Real-world examples and case studies

## Usage

This document serves as:
- **Learning Resource**: Comprehensive tutorial for beginners
- **Reference Manual**: Quick lookup for experienced developers
- **Implementation Guide**: Step-by-step instructions
- **Best Practices**: Industry-standard approaches

## Output

The compiled PDF provides:
- Detailed theoretical background
- Practical implementation examples
- Performance optimization techniques
- Error handling strategies
- Integration patterns
- Future enhancement suggestions

Perfect for understanding the complete process of converting unstructured invoice text into structured pandas DataFrames!
