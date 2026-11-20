import os
import sqlite3
import secrets
from pathlib import Path
from contextlib import contextmanager

# Determine database engine
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")

# Normalize URL for psycopg2 if postgres:// prefix is used
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = bool(DATABASE_URL)

# Fallback path for SQLite (local dev or /tmp in serverless)
if os.environ.get("VERCEL") and not IS_POSTGRES:
    LOCAL_DB_PATH = Path("/tmp/banking.db")
else:
    LOCAL_DB_PATH = Path(__file__).resolve().parent / "banking.db"


def get_raw_connection():
    """Returns a raw database connection based on environment."""
    if IS_POSTGRES:
        import psycopg2
        from psycopg2.extras import DictCursor
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
        return conn
    else:
        conn = sqlite3.connect(str(LOCAL_DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn


def adapt_sql(sql: str) -> str:
    """Adapts '?' placeholders to '%s' if using PostgreSQL."""
    if IS_POSTGRES:
        return sql.replace("?", "%s")
    return sql


@contextmanager
def get_db():
    """Context manager for obtaining a database connection with auto commit/rollback."""
    conn = get_raw_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_one(sql: str, params=()):
    """Execute a query and return a single row as a dict, or None."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(adapt_sql(sql), params)
        row = cur.fetchone()
        if row is None:
            return None
        return dict(row)


def query_all(sql: str, params=()):
    """Execute a query and return all rows as a list of dicts."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(adapt_sql(sql), params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def execute(sql: str, params=()):
    """Execute an INSERT, UPDATE, or DELETE query and commit."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(adapt_sql(sql), params)
        return cur.rowcount


def init_db():
    """Initialize database tables for SQLite or PostgreSQL."""
    with get_db() as conn:
        cur = conn.cursor()
        if IS_POSTGRES:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    salt VARCHAR(100) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    balance DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                    account_number VARCHAR(50) UNIQUE
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    txn_type VARCHAR(50) NOT NULL,
                    amount DOUBLE PRECISION NOT NULL,
                    note TEXT,
                    created_at VARCHAR(100) NOT NULL
                );
            """)
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_account_number
                ON users(account_number);
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    salt TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    balance REAL NOT NULL DEFAULT 0,
                    account_number TEXT UNIQUE
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    txn_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
            """)
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_users_account_number
                ON users(account_number);
            """)


def generate_account_number() -> str:
    """Generate a unique 10-digit account number."""
    while True:
        account_no = str(secrets.randbelow(9000000000) + 1000000000)
        existing = query_one("SELECT id FROM users WHERE account_number=?", (account_no,))
        if not existing:
            return account_no


def execute_transfer(sender_id: int, receiver_account_no: str, amount: float, note: str, timestamp: str):
    """
    Executes an atomic transfer between two accounts.
    Returns (success: bool, message: str).
    """
    with get_db() as conn:
        cur = conn.cursor()

        # Fetch sender
        cur.execute(adapt_sql("SELECT id, full_name, account_number, balance FROM users WHERE id=?"), (sender_id,))
        sender_row = cur.fetchone()
        if not sender_row:
            return False, "Sender account not found."
        sender = dict(sender_row)

        # Fetch receiver
        cur.execute(adapt_sql("SELECT id, full_name, account_number, balance FROM users WHERE account_number=?"), (receiver_account_no,))
        receiver_row = cur.fetchone()
        if not receiver_row:
            return False, "Receiver account does not exist."
        receiver = dict(receiver_row)

        if receiver["id"] == sender_id:
            return False, "You cannot transfer money to your own account."

        if float(sender["balance"]) < amount:
            return False, "Insufficient balance for this transfer."

        new_sender_balance = round(float(sender["balance"]) - amount, 2)
        new_receiver_balance = round(float(receiver["balance"]) + amount, 2)

        # Update balances
        cur.execute(adapt_sql("UPDATE users SET balance=? WHERE id=?"), (new_sender_balance, sender_id))
        cur.execute(adapt_sql("UPDATE users SET balance=? WHERE id=?"), (new_receiver_balance, receiver["id"]))

        # Insert sender transaction
        sender_note = f"To: {receiver['full_name']} ({receiver['account_number']}). {note}".strip()
        cur.execute(adapt_sql("""
            INSERT INTO transactions (user_id, txn_type, amount, note, created_at)
            VALUES (?, ?, ?, ?, ?)
        """), (sender_id, "Transfer", amount, sender_note, timestamp))

        # Insert receiver transaction
        receiver_note = f"From: {sender['full_name']} ({sender['account_number']}). {note}".strip()
        cur.execute(adapt_sql("""
            INSERT INTO transactions (user_id, txn_type, amount, note, created_at)
            VALUES (?, ?, ?, ?, ?)
        """), (receiver["id"], "Received", amount, receiver_note, timestamp))

        return True, f"₹{amount:,.2f} transferred successfully to {receiver['full_name']}."
