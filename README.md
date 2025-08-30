# Iden Automation Challenge – Integration Engineer Application

Automating the Iden Challenge for data handling, UI interaction, and problem-solving skills assessment.

---

## 🧠 Overview
This project automates the scraping of product data from the Iden platform as part of the **Integration Engineer application challenge**.  

It is designed to handle dynamically loaded tables, collect relevant product information, and save it in a structured JSON format.

**Key objectives:**
- Demonstrate ability to interact with web UI programmatically
- Handle dynamic content and large datasets efficiently
- Implement robust session and authentication management

---

## 🚀 Features
- **Dynamic Table Scrolling:** Handles large product tables efficiently, including lazy-loaded and paginated content.  
- **Smart Waiting:** Implements intelligent wait strategies for elements to appear before interaction, improving reliability.  
- **Full Data Capture:** Harvests all product details including:
  - ID  
  - Last Updated  
  - Category  
  - Material  
  - Price  
  - Weight (kg)  
  - Item Name  
  - Rating  
  - Manufacturer  
- **Session Management:** Checks for existing sessions and reuses them to avoid repeated logins.  
- **Authentication Handling:** Logs in securely with credentials if no session exists, and gracefully handles invalid login attempts.  
- **Navigation Automation:** Traverses the hidden path to the product table automatically: `Menu → Data Management → Inventory → View All Products`.  
- **Error-Resistant:** Robust exception handling to prevent crashes and gracefully handle browser closure or network issues.  
- **Data Export:** Exports scraped data to a structured JSON file for further analysis.  
- **Secure:** Sensitive credentials stored in `.env` file (ignored in GitHub).  
- **Clean & Documented Code:** Well-structured Python script for maintainability and clarity.  

---

## 🛠️ Technical Approach

| Component | Details |
|-----------|---------|
| Automation | Playwright (Python) |
| Data Storage | JSON |
| Session Handling | Stores session for faster login and avoids repeated authentication |
| Error Handling | Detects invalid login, browser closure, or network issues |

---

## 🌐 Usage

### 1. Clone the Repository
```bash
git clone https://github.com/YourUsername/Iden_Challenge.git
cd Iden_Challenge

**### 2. Install Dependencies
```pip install -r requirements.txt
playwright install

**### 3. Add Credentials**
Create a .env file in the root folder:
```IDEN_EMAIL=your_email
IDEN_PASSWORD=your_password

**### 4. Run the automation script:**
```python automate.py

**### 5. 📂 Project Structure**
```Iden_Challenge/
├── automate.py        # Main automation script
├── .env               # Environment variables (ignored)
├── venv/              # Python virtual environment (ignored)
├── README.md          # Project documentation
└── .gitignore         # Ignore .env and venv







