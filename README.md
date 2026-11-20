# 🏦 SecureBank – Online Banking System

A Python-based desktop banking application built using **Tkinter and SQLite**. SecureBank provides a simple and user-friendly graphical interface to perform basic banking operations, manage accounts, and view transaction records.

## 🚀 Features

- **User Authentication:** Secure user registration and login.
- **Account Number Generation:** Automatically generates a unique account number for each user.
- **Dashboard:** Displays account holder details, account number, available balance, and account status.
- **Deposit Money:** Add money to the account.
- **Withdraw Money:** Withdraw money with balance validation.
- **Money Transfer:** Transfer funds between registered bank accounts.
- **Mini Statement:** View the last 10 transactions.
- **Transaction History:** View recent deposits, withdrawals, and transfers.
- **Change Password:** Update account login credentials.
- **Input Validation:** Handles invalid amounts, insufficient funds, and invalid receiver account numbers.
- **Logout:** Securely exit the current user session.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Tkinter | Graphical User Interface |
| SQLite | Database management |
| hashlib | Password hashing |
| secrets | Secure random value generation |
| ttk | Modern GUI components |

## 📂 Project Structure

```text
Online-Banking-System-Python/
│
├── app.py
│
├── online_banking_system/
│   ├── app.py
│   └── banking.db
│
├── .gitignore
│
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/vaishnavimarewad8999-pixel/Online-Banking-System-Python.git
```

### 2. Open the Project Folder

```bash
cd Online-Banking-System-Python
```

### 3. Run the Application

Make sure Python is installed on your system.

```bash
python app.py
```

The SecureBank desktop application will launch.

## 🖥️ Application Modules

1. Login and Registration
2. Account Management
3. Banking Dashboard
4. Deposit and Withdrawal
5. Money Transfer
6. Mini Statement
7. Transaction History
8. Password Management

## 🔐 Security Features

- Password hashing using PBKDF2-HMAC with SHA-256.
- Random salt generation for password protection.
- Login credential verification.
- Input validation for banking transactions.
- SQLite database for storing account and transaction records.

## 🎯 Project Objective

The main objective of SecureBank is to demonstrate the basic working principles of an online banking system through a desktop application. It helps users understand account management, transaction processing, database connectivity, authentication, and GUI development using Python.

## ⚠️ Disclaimer

This project is developed for educational and learning purposes only. It is a banking simulation and is not connected to any real bank or financial institution. Do not use real banking credentials or financial information.

## 👩‍💻 Author

**Vaishnavi Marewad**

GitHub: [@vaishnavimarewad8999-pixel](https://github.com/vaishnavimarewad8999-pixel)

## ⭐ Support

If you find this project useful, consider giving the repository a star!

