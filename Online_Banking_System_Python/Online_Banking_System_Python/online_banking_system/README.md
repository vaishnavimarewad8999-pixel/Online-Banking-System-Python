# SecureBank — Online Banking System (GUI)

A beginner-friendly Python + Tkinter + SQLite mini-project.

## Features
- User registration and login
- Password hashing using PBKDF2-HMAC-SHA256 (passwords are not stored as plain text)
- Account balance dashboard
- Deposit and withdraw operations
- Insufficient-funds and invalid-input checks
- Transaction history with date, type, amount, and note
- Logout and login again

## Requirements
- Python 3.10 or later
- Tkinter (included with most standard Windows Python installations)
- SQLite (included with Python)

No `pip install` is required.

## Run in VS Code (Windows)
1. Extract the ZIP file.
2. Open the `online_banking_system` folder in VS Code.
3. Open Terminal → New Terminal.
4. Run:

   ```powershell
   python app.py
   ```

   If `python` does not work, try `py app.py`.

5. Select **Create account**, register with a name, username, and password (minimum 6 characters), then sign in.
6. Use Deposit / Withdraw and review Recent transactions.

## Database
The app automatically creates `banking.db` in the same folder the first time it runs. It stores demo users, account balances, and transactions.

## Important
This is an educational simulation only. It is not connected to a real bank and must not be used for real deposits, withdrawals, credentials, or financial transactions. For a production banking system, additional security, auditing, encryption, authorization, testing, and regulatory controls are required.
