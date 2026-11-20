import unittest
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Use an isolated test database
os.environ["DATABASE_URL"] = ""  # Force SQLite
TEST_DB_PATH = ROOT_DIR / "tests" / "test_banking.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

# Point LOCAL_DB_PATH to test db
import securebank_web.db as db_mod
db_mod.LOCAL_DB_PATH = TEST_DB_PATH

from securebank_web.app import app
from securebank_web.db import init_db, query_one, query_all
from securebank_web.auth import hash_password, verify_password


class BankingWebTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        init_db()

    def tearDown(self):
        if TEST_DB_PATH.exists():
            try:
                TEST_DB_PATH.unlink()
            except Exception:
                pass

    def test_01_password_hashing_and_verification(self):
        password = "SecretPassword123!"
        salt, p_hash = hash_password(password)
        self.assertEqual(len(salt), 32)
        self.assertEqual(len(p_hash), 64)
        self.assertTrue(verify_password(password, salt, p_hash))
        self.assertFalse(verify_password("WrongPassword", salt, p_hash))

    def test_02_registration_and_account_number(self):
        # Missing fields
        res = self.client.post("/register", data={
            "full_name": "", "username": "user1", "password": "password123", "confirm": "password123"
        }, follow_redirects=True)
        self.assertIn(b"Please fill in all fields", res.data)

        # Password mismatch
        res = self.client.post("/register", data={
            "full_name": "Alice Bob", "username": "alice", "password": "password123", "confirm": "different"
        }, follow_redirects=True)
        self.assertIn(b"Password and confirm password do not match", res.data)

        # Password too short (<6)
        res = self.client.post("/register", data={
            "full_name": "Alice Bob", "username": "alice", "password": "123", "confirm": "123"
        }, follow_redirects=True)
        self.assertIn(b"at least 6 characters", res.data)

        # Successful registration
        res = self.client.post("/register", data={
            "full_name": "Alice Test", "username": "alicetest", "password": "password123", "confirm": "password123"
        }, follow_redirects=True)
        self.assertIn(b"Your demo account is ready", res.data)

        # Verify DB
        user = query_one("SELECT * FROM users WHERE username=?", ("alicetest",))
        self.assertIsNotNone(user)
        self.assertEqual(user["full_name"], "Alice Test")
        self.assertEqual(len(user["account_number"]), 10)
        self.assertEqual(float(user["balance"]), 0.0)

        # Duplicate username prevention
        res = self.client.post("/register", data={
            "full_name": "Another Alice", "username": "alicetest", "password": "password123", "confirm": "password123"
        }, follow_redirects=True)
        self.assertIn(b"already registered", res.data)

    def test_03_login_and_session(self):
        # Register user
        self.client.post("/register", data={
            "full_name": "Bob Test", "username": "bobtest", "password": "password123", "confirm": "password123"
        })

        # Invalid login
        res = self.client.post("/login", data={
            "username": "bobtest", "password": "wrongpassword"
        }, follow_redirects=True)
        self.assertIn(b"Invalid username or password", res.data)

        # Valid login
        res = self.client.post("/login", data={
            "username": "bobtest", "password": "password123"
        }, follow_redirects=True)
        self.assertIn(b"Welcome back, Bob Test!", res.data)
        self.assertIn(b"Your dashboard", res.data)

        # Check dashboard access
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Available Balance", res.data)

    def test_04_deposit_and_withdrawal(self):
        # Register & Login
        self.client.post("/register", data={
            "full_name": "Charlie Test", "username": "charliest", "password": "password123", "confirm": "password123"
        })
        self.client.post("/login", data={"username": "charliest", "password": "password123"})

        # Invalid deposit (negative / zero)
        res = self.client.post("/deposit", data={"amount": "-50", "note": "invalid"}, follow_redirects=True)
        self.assertIn(b"Amount must be greater than zero", res.data)

        # Successful deposit
        res = self.client.post("/deposit", data={"amount": "1500.50", "note": "Initial test deposit"}, follow_redirects=True)
        self.assertIn(b"deposited successfully", res.data)

        # Check balance
        user = query_one("SELECT balance FROM users WHERE username=?", ("charliest",))
        self.assertEqual(float(user["balance"]), 1500.50)

        # Withdrawal exceeding balance
        res = self.client.post("/withdraw", data={"amount": "2000.00", "note": "Too much"}, follow_redirects=True)
        self.assertIn(b"Your balance is too low", res.data)

        # Valid withdrawal
        res = self.client.post("/withdraw", data={"amount": "500.50", "note": "ATM withdrawal"}, follow_redirects=True)
        self.assertIn(b"withdrawn successfully", res.data)

        # Check balance again
        user = query_one("SELECT balance FROM users WHERE username=?", ("charliest",))
        self.assertEqual(float(user["balance"]), 1000.00)

        # Verify transactions recorded
        txns = query_all("SELECT * FROM transactions WHERE user_id=?", (user["id"] if "id" in user else 1,))
        self.assertEqual(len(txns), 2)
        self.assertEqual(txns[0]["txn_type"], "Deposit")
        self.assertEqual(txns[1]["txn_type"], "Withdraw")

    def test_05_money_transfer_between_accounts(self):
        # Register User A (Sender)
        self.client.post("/register", data={
            "full_name": "Sender User", "username": "sender1", "password": "password123", "confirm": "password123"
        })
        sender = query_one("SELECT * FROM users WHERE username=?", ("sender1",))

        # Register User B (Receiver)
        self.client.post("/register", data={
            "full_name": "Receiver User", "username": "receiver1", "password": "password123", "confirm": "password123"
        })
        receiver = query_one("SELECT * FROM users WHERE username=?", ("receiver1",))

        # Login as Sender and deposit funds
        self.client.post("/login", data={"username": "sender1", "password": "password123"})
        self.client.post("/deposit", data={"amount": "3000.00", "note": "Salary"})

        # Transfer to non-existent account
        res = self.client.post("/transfer", data={
            "receiver_account": "9999999999", "amount": "500", "note": "Test"
        }, follow_redirects=True)
        self.assertIn(b"Receiver account does not exist", res.data)

        # Transfer to self
        res = self.client.post("/transfer", data={
            "receiver_account": sender["account_number"], "amount": "500", "note": "Self"
        }, follow_redirects=True)
        self.assertIn(b"cannot transfer money to your own account", res.data)

        # Transfer exceeding balance
        res = self.client.post("/transfer", data={
            "receiver_account": receiver["account_number"], "amount": "5000", "note": "Too much"
        }, follow_redirects=True)
        self.assertIn(b"Insufficient balance", res.data)

        # Valid transfer of 1200
        res = self.client.post("/transfer", data={
            "receiver_account": receiver["account_number"], "amount": "1200", "note": "Project payment"
        }, follow_redirects=True)
        self.assertIn(b"transferred successfully", res.data)

        # Verify balances
        sender_updated = query_one("SELECT balance FROM users WHERE id=?", (sender["id"],))
        receiver_updated = query_one("SELECT balance FROM users WHERE id=?", (receiver["id"],))
        self.assertEqual(float(sender_updated["balance"]), 1800.00)
        self.assertEqual(float(receiver_updated["balance"]), 1200.00)

        # Verify transaction records for both parties
        sender_txns = query_all("SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC", (sender["id"],))
        receiver_txns = query_all("SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC", (receiver["id"],))
        
        self.assertEqual(sender_txns[0]["txn_type"], "Transfer")
        self.assertIn("Receiver User", sender_txns[0]["note"])
        
        self.assertEqual(receiver_txns[0]["txn_type"], "Received")
        self.assertIn("Sender User", receiver_txns[0]["note"])

    def test_06_mini_statement_and_full_history(self):
        # Register and log in
        self.client.post("/register", data={
            "full_name": "Statement Test", "username": "statement_user", "password": "password123", "confirm": "password123"
        })
        self.client.post("/login", data={"username": "statement_user", "password": "password123"})

        # Make 12 deposits
        for i in range(1, 13):
            self.client.post("/deposit", data={"amount": str(i * 10), "note": f"Deposit #{i}"})

        # Mini statement should display 10 rows
        res = self.client.get("/mini-statement")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Mini Statement", res.data)
        self.assertIn(b"Deposit #12", res.data)

        # All history should include older records too
        res = self.client.get("/transactions")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Deposit #1", res.data)

    def test_07_change_password(self):
        # Register user
        self.client.post("/register", data={
            "full_name": "Pass User", "username": "passuser", "password": "oldpassword123", "confirm": "oldpassword123"
        })
        self.client.post("/login", data={"username": "passuser", "password": "oldpassword123"})

        # Wrong current password
        res = self.client.post("/change-password", data={
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }, follow_redirects=True)
        self.assertIn(b"Current password is incorrect", res.data)

        # Short new password (<8)
        res = self.client.post("/change-password", data={
            "current_password": "oldpassword123",
            "new_password": "short",
            "confirm_password": "short"
        }, follow_redirects=True)
        self.assertIn(b"at least 8 characters", res.data)

        # Mismatch new password
        res = self.client.post("/change-password", data={
            "current_password": "oldpassword123",
            "new_password": "newpassword123",
            "confirm_password": "differentpassword"
        }, follow_redirects=True)
        self.assertIn(b"do not match", res.data)

        # Valid password change
        res = self.client.post("/change-password", data={
            "current_password": "oldpassword123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }, follow_redirects=True)
        self.assertIn(b"changed successfully", res.data)

        # Logout and test new password
        self.client.get("/logout")
        res_old = self.client.post("/login", data={"username": "passuser", "password": "oldpassword123"}, follow_redirects=True)
        self.assertIn(b"Invalid username or password", res_old.data)

        res_new = self.client.post("/login", data={"username": "passuser", "password": "newpassword123"}, follow_redirects=True)
        self.assertIn(b"Welcome back", res_new.data)

    def test_08_pdf_statement_generation(self):
        self.client.post("/register", data={
            "full_name": "PDF User", "username": "pdfuser", "password": "password123", "confirm": "password123"
        })
        self.client.post("/login", data={"username": "pdfuser", "password": "password123"})
        self.client.post("/deposit", data={"amount": "2500", "note": "Test deposit for PDF"})

        res = self.client.get("/download-statement-pdf")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/pdf")
        self.assertTrue(res.data.startswith(b"%PDF"))
        self.assertIn("SecureBank_Statement_", res.headers.get("Content-Disposition", ""))

    def test_09_sql_adapter_and_postgres_compatibility(self):
        from securebank_web.db import adapt_sql
        # Test SQLite mode (default)
        db_mod.IS_POSTGRES = False
        sql_sqlite = "SELECT * FROM users WHERE username=? AND id=?"
        self.assertEqual(adapt_sql(sql_sqlite), sql_sqlite)

        # Test PostgreSQL mode
        db_mod.IS_POSTGRES = True
        self.assertEqual(
            adapt_sql(sql_sqlite),
            "SELECT * FROM users WHERE username=%s AND id=%s"
        )
        db_mod.IS_POSTGRES = False


if __name__ == "__main__":
    unittest.main()
