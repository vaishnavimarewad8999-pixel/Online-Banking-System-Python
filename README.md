# 🏦 SecureBank – Online Banking System

A secure banking application built with Python. SecureBank provides a simple, elegant interface to perform banking operations, manage accounts, and view transaction records. Available as both a **Desktop Application (Tkinter)** and a **Web Application (Flask + Bootstrap + Vercel)**.

---

## 🚀 Features

- **User Authentication:** Secure user registration and login with PBKDF2-HMAC-SHA256 password hashing.
- **Account Number Generation:** Automatically generates a unique 10-digit account number for each user.
- **Dashboard:** Displays account holder details, account number, available balance, and account status.
- **Deposit Money:** Add money with instant balance update and transaction logging.
- **Withdraw Money:** Withdraw money with real-time balance validation.
- **Money Transfer:** Atomic funds transfer between registered accounts with sender and receiver transaction entries.
- **Mini Statement:** View the last 10 transactions.
- **Transaction History:** Comprehensive activity log with filtering options.
- **PDF Statement Download:** Export bank statement as an official PDF report.
- **Change Password:** Securely update login credentials with validation.
- **Input Validation:** Strict validation for positive amounts, non-self transfers, and password criteria.
- **Session Security:** Cryptographically signed session management and protected routes.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python 3 | Core programming language |
| Flask | Web framework & routing |
| Tkinter & ttk | Original desktop GUI |
| HTML5, CSS3, Bootstrap 5 | Modern, responsive web user interface |
| Bootstrap Icons | Visual UI icons |
| SQLite | Local development database |
| PostgreSQL / psycopg2 | Production persistent database (Vercel) |
| ReportLab | PDF statement generation |
| hashlib & secrets | PBKDF2 password hashing & cryptographic randoms |
| Vercel Serverless | Cloud hosting & deployment |

---

## 📂 Project Structure

```text
Online-Banking-System-Python/
│
├── app.py                      # Flask web application root entry point
├── online_banking_system/      # Desktop Tkinter application module
│   ├── app.py                  # Tkinter GUI entry point
│   └── banking.db
│
├── securebank_web/             # Web Application (Flask)
│   ├── __init__.py
│   ├── app.py                  # Flask routes & server logic
│   ├── db.py                   # Unified DB layer (SQLite & PostgreSQL)
│   ├── auth.py                 # PBKDF2 hashing, validations & decorators
│   ├── requirements.txt        # Web app dependencies
│   ├── static/
│   │   ├── css/style.css       # Custom banking styling
│   │   └── js/main.js          # Interactive UI scripts & clipboard copy
│   └── templates/              # Responsive Jinja2 templates
│       ├── base.html
│       ├── login.html
│       ├── register.html
│       ├── dashboard.html
│       ├── deposit.html
│       ├── withdraw.html
│       ├── transfer.html
│       ├── mini_statement.html
│       ├── transactions.html
│       ├── change_password.html
│       ├── 404.html
│       └── 500.html
│
├── api/
│   └── index.py                # Vercel serverless WSGI entry point
│
├── tests/
│   └── test_banking_web.py     # Automated unit test suite (10 test cases)
│
├── vercel.json                 # Vercel deployment routing configuration
├── .env.example                # Example environment variables
├── requirements.txt            # Root dependencies for Vercel
├── .gitignore
└── README.md
```

---

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/vaishnavimarewad8999-pixel/Online-Banking-System-Python.git
cd Online-Banking-System-Python
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🖥️ Running the Applications

### Option A: Run Web Application (Flask)

```bash
python app.py
# or:
python -m securebank_web.app
```
Then open your browser and navigate to:
**`http://127.0.0.1:5000`**

### Option B: Run Desktop Application (Tkinter)

```bash
python online_banking_system/app.py
```

---

## 🧪 Running Automated Tests

Run the comprehensive unit test suite covering registration, PBKDF2 hashing, authentication, deposit, withdrawal, atomic transfer, mini statement, password changes, and PDF generation:

```bash
python -m unittest tests/test_banking_web.py
```

---

## ☁️ Deploying to Vercel

### Step 1: Push Code to GitHub

```bash
git add .
git commit -m "Add SecureBank Flask web application with Vercel deployment config"
git push origin main
```

### Step 2: Import Project in Vercel

1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New** &rarr; **Project**.
3. Import your `Online-Banking-System-Python` GitHub repository.
4. Ensure **Root Directory** is left as default `./` (project root).
5. Leave build settings as default (Vercel automatically detects `vercel.json` and `@vercel/python`).

### Step 3: Configure Environment Variables

Under **Project Settings** &rarr; **Environment Variables**, add:

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Cryptographic secret for signing sessions | `any_long_random_secret_string` |
| `DATABASE_URL` | Persistent PostgreSQL connection URL | `postgresql://user:pass@ep-host.region.neon.tech/dbname?sslmode=require` |

> **Note:** You can obtain a free PostgreSQL database from [Neon.tech](https://neon.tech), [Supabase](https://supabase.com), or [Vercel Postgres](https://vercel.com/storage/postgres). If `DATABASE_URL` is omitted, the app will fall back to local SQLite.

### Step 4: Deploy

Click **Deploy**. Once built, Vercel provides a live URL (e.g., `https://your-project.vercel.app`) where your web banking system is fully live and accessible worldwide!

---

## 🔐 Security Features

- **PBKDF2-HMAC-SHA256:** Password hashing with 200,000 iterations and 16-byte random salts.
- **Constant-Time Verification:** Uses `secrets.compare_digest` to prevent timing attacks.
- **Atomic Money Transfers:** Uses database transactions ensuring sender deduction and receiver addition happen together or roll back on error.
- **Input Sanitation & Strict Validation:** Enforces positive transfer amounts, receiver account verification, and prevents self-transfers.
- **Protected Endpoints:** Secure session checking with `@login_required` decorator across all banking actions.

---

## ⚠️ Disclaimer

This project is developed for educational and learning purposes only. It is a banking simulation and is not connected to any real bank or financial institution. Do not use real banking credentials or real money.

---

## 👩‍💻 Author

**Vaishnavi Marewad**  
GitHub: [@vaishnavimarewad8999-pixel](https://github.com/vaishnavimarewad8999-pixel)
