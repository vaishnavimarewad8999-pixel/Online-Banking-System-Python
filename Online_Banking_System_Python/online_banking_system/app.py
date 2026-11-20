import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
# PDF GENERATION IMPORTS
from tkinter import filedialog

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

DB_PATH = Path(__file__).with_name("banking.db")
CURRENCY = "₹"

def connect_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    with connect_db() as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0,
                account_number TEXT UNIQUE
                  )
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
            )
        """)
        # Check existing database columns
        cur.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cur.fetchall()]

        # Add account number column if missing
        if "account_number" not in columns:
            cur.execute(
                "ALTER TABLE users ADD COLUMN account_number TEXT"
            )

        # Create unique index
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_users_account_number
            ON users(account_number)
        """)

        # Generate account numbers for existing users
        cur.execute("""
            SELECT id FROM users
            WHERE account_number IS NULL
        """)

        existing_users = cur.fetchall()

        for user in existing_users:
            account_no = generate_account_number(cur)
            cur.execute(
                "UPDATE users SET account_number=? WHERE id=?",
                (account_no, user[0])
            )
        con.commit()

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000
    ).hex()
    return salt, digest


def money(amount):
    return f"{CURRENCY}{amount:,.2f}"


def generate_account_number(cur):
    while True:
        account_no = str(
            secrets.randbelow(9000000000) + 1000000000
        )

        cur.execute(
            "SELECT id FROM users WHERE account_number=?",
            (account_no,)
        )

        if cur.fetchone() is None:
            return account_no

class BankingApp(tk.Tk):
    BG = "#eef3f7"
    NAVY = "#10243a"
    TEAL = "#087e8b"
    WHITE = "#ffffff"
    TEXT = "#203247"
    MUTED = "#718096"
    GREEN = "#16845b"
    RED = "#c0392b"

    def __init__(self):
        super().__init__()
        self.title("SecureBank | Online Banking Demo")
        self.geometry("1000x680")
        self.minsize(850, 600)
        self.configure(bg=self.BG)
        self.current_user = None
        self.current_user_id = None
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.configure_styles()
        self.show_login()

    def configure_styles(self):
        self.style.configure("TFrame", background=self.BG)
        self.style.configure("Card.TFrame", background=self.WHITE)
        self.style.configure("TLabel", background=self.BG, foreground=self.TEXT, font=("Segoe UI", 10))
        self.style.configure("Title.TLabel", background=self.BG, foreground=self.NAVY, font=("Segoe UI", 23, "bold"))
        self.style.configure("Sub.TLabel", background=self.BG, foreground=self.MUTED, font=("Segoe UI", 10))
        self.style.configure("CardTitle.TLabel", background=self.WHITE, foreground=self.MUTED, font=("Segoe UI", 10))
        self.style.configure("CardValue.TLabel", background=self.WHITE, foreground=self.NAVY, font=("Segoe UI", 22, "bold"))
        self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(16, 10),
                             background=self.TEAL, foreground=self.WHITE)
        self.style.map("Primary.TButton", background=[("active", "#06636d")])
        self.style.configure("Secondary.TButton", font=("Segoe UI", 10), padding=(12, 8))
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=30, background=self.WHITE, fieldbackground=self.WHITE)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#dce7ef")

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def field(self, parent, label, show=None):
        wrap = ttk.Frame(parent, style="Card.TFrame")
        wrap.pack(fill="x", pady=7)
        ttk.Label(wrap, text=label, background=self.WHITE, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
        entry = tk.Entry(wrap, font=("Segoe UI", 11), relief="solid", bd=1,
                         highlightthickness=1, highlightbackground="#d7e0e8",
                         highlightcolor=self.TEAL, show=show)
        entry.pack(fill="x", ipady=9)
        return entry

    def auth_shell(self, heading, subtitle):
        self.clear()
        outer = tk.Frame(self, bg=self.BG)
        outer.pack(expand=True, fill="both", padx=20, pady=25)
        panel = tk.Frame(outer, bg=self.WHITE, highlightbackground="#dce5ec", highlightthickness=1)
        panel.place(relx=0.5, rely=0.5, anchor="center", width=440)
        tk.Label(panel, text="●  SECUREBANK", bg=self.WHITE, fg=self.TEAL,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=38, pady=(32, 18))
        tk.Label(panel, text=heading, bg=self.WHITE, fg=self.NAVY,
                 font=("Segoe UI", 23, "bold")).pack(anchor="w", padx=38)
        tk.Label(panel, text=subtitle, bg=self.WHITE, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=38, pady=(5, 18))
        content = tk.Frame(panel, bg=self.WHITE)
        content.pack(fill="x", padx=38)
        return panel, content

    def show_login(self):
        panel, content = self.auth_shell("Welcome back", "Sign in to access your demo banking dashboard.")
        username = self.field(content, "USERNAME")
        password = self.field(content, "PASSWORD", show="•")
        show_var = tk.BooleanVar(value=False)
        tk.Checkbutton(content, text="Show password", variable=show_var,
                       command=lambda: password.config(show="" if show_var.get() else "•"),
                       bg=self.WHITE, fg=self.MUTED, activebackground=self.WHITE).pack(anchor="w", pady=(0, 12))
        ttk.Button(content, text="Sign In", style="Primary.TButton",
                   command=lambda: self.login(username.get().strip(), password.get())).pack(fill="x", pady=(4, 12))
        row = tk.Frame(panel, bg=self.WHITE)
        row.pack(pady=(0, 30))
        tk.Label(row, text="New to SecureBank? ", bg=self.WHITE, fg=self.MUTED).pack(side="left")
        tk.Button(row, text="Create account", bd=0, bg=self.WHITE, fg=self.TEAL,
                  font=("Segoe UI", 9, "bold"), cursor="hand2",
                  command=self.show_register).pack(side="left")
        tk.Label(self, text="Educational demo only • No real money or bank connection",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 8)).pack(side="bottom", pady=12)

    def show_register(self):
        panel, content = self.auth_shell("Create account", "Register a demo account to get started.")
        name = self.field(content, "FULL NAME")
        username = self.field(content, "USERNAME")
        password = self.field(content, "PASSWORD", show="•")
        confirm = self.field(content, "CONFIRM PASSWORD", show="•")
        ttk.Button(content, text="Create Account", style="Primary.TButton",
                   command=lambda: self.register(name.get().strip(), username.get().strip(),
                                                  password.get(), confirm.get())).pack(fill="x", pady=(14, 12))
        row = tk.Frame(panel, bg=self.WHITE)
        row.pack(pady=(0, 25))
        tk.Label(row, text="Already registered? ", bg=self.WHITE, fg=self.MUTED).pack(side="left")
        tk.Button(row, text="Sign in", bd=0, bg=self.WHITE, fg=self.TEAL,
                  font=("Segoe UI", 9, "bold"), cursor="hand2",
                  command=self.show_login).pack(side="left")

    def register(self, name, username, password, confirm):
        if not name or not username or not password or not confirm:
            messagebox.showwarning("Missing details", "Please fill in all fields.")
            return
        if len(password) < 6:
            messagebox.showwarning("Weak password", "Password must contain at least 6 characters.")
            return
        if password != confirm:
            messagebox.showerror("Password mismatch", "Password and confirm password do not match.")
            return
        salt, digest = hash_password(password)
        try:
            with connect_db() as con:
                cur = con.cursor()
                account_no = generate_account_number(cur)
                cur.execute("""
        INSERT INTO users(
            full_name, username, salt,
            password_hash, account_number
        )
        VALUES(?,?,?,?,?)
    """, (name, username, salt, digest, account_no))

            messagebox.showinfo("Account created", "Your demo account is ready. Please sign in.")
            self.show_login()
        except sqlite3.IntegrityError:
            messagebox.showerror("Username exists", "This username is already registered. Choose another.")

    def login(self, username, password):
        if not username or not password:
            messagebox.showwarning("Missing details", "Enter username and password.")
            return
        with connect_db() as con:
            row = con.execute("""
    SELECT id, full_name, salt, password_hash, account_number
    FROM users
    WHERE username=?
""", (username,)).fetchone()
            
        if not row:
            messagebox.showerror("Login failed", "Invalid username or password.")
            return
        salt, expected = row[2], row[3]
        _, actual = hash_password(password, salt)
        if not secrets.compare_digest(actual, expected):
            messagebox.showerror("Login failed", "Invalid username or password.")
            return
        self.current_user_id = row[0]
        self.current_user = row[1]
        self.current_account_number = row[4]
        self.show_dashboard()

    def header(self, parent):
        top = tk.Frame(parent, bg=self.NAVY, height=76)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="SECUREBANK", bg=self.NAVY, fg=self.WHITE,
                 font=("Segoe UI", 17, "bold")).pack(side="left", padx=28)
        tk.Label(top, text=f"Welcome, {self.current_user}", bg=self.NAVY, fg="#d7e7f1",
                 font=("Segoe UI", 10)).pack(side="right", padx=22)
        return top

    def show_dashboard(self):
        self.clear()
        self.header(self)
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=28, pady=24)
        ttk.Label(body, text="Your dashboard", style="Title.TLabel").pack(anchor="w")
        ttk.Label(body, text="Manage your demo account and review recent activity.",
                  style="Sub.TLabel").pack(anchor="w", pady=(3, 18))

        cards = tk.Frame(body, bg=self.BG)
        cards.pack(fill="x", pady=(0, 18))
        balance = self.get_balance()
        self.stat_card(cards, "AVAILABLE BALANCE", money(balance), self.TEAL).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.stat_card(
    cards,
    "ACCOUNT NUMBER",
    self.current_account_number,
    self.TEAL
).pack(side="left", fill="x", expand=True, padx=8)
        self.stat_card(cards, "ACCOUNT STATUS", "ACTIVE", self.GREEN).pack(side="left", fill="x", expand=True, padx=(8, 0))

        ttk.Button(
            body,
            text="Mini Statement",
            command=self.show_mini_statement
        ).pack(anchor="e", pady=(0, 10))

        ttk.Button(
            body,
            text="Download Statement PDF",
            command=self.download_statement_pdf
        ).pack(anchor="e", pady=(0, 10))


        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=(0, 18))
        ttk.Button(actions, text="＋  Deposit", style="Primary.TButton",
                   command=lambda: self.transaction_dialog("Deposit")).pack(side="left", padx=(0, 10))
        ttk.Button(actions, text="－  Withdraw", style="Secondary.TButton",
                   command=lambda: self.transaction_dialog("Withdraw")).pack(side="left", padx=5)
        ttk.Button(
            actions,
            text="Change Password",
            style="Secondary.TButton",
            command=self.change_password
        ).pack(side="left", padx=5)
        
        

        ttk.Button(
    actions,
    text="Transfer Money",
    style="Primary.TButton",
    command=self.transfer_dialog
).pack(side="left", padx=5)
        ttk.Button(actions, text="↻  Refresh", style="Secondary.TButton",
                   command=self.show_dashboard).pack(side="left", padx=5)
        ttk.Button(actions, text="Log out", style="Secondary.TButton",
                   command=self.logout).pack(side="right")
        
        ttk.Label(body, text="Recent transactions", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(5, 8))
        columns = ("date", "type", "amount", "note")
        tree = ttk.Treeview(body, columns=columns, show="headings", height=9)
        for col, label, width in [
            ("date", "DATE & TIME", 190), ("type", "TYPE", 130),
            ("amount", "AMOUNT", 140), ("note", "DESCRIPTION", 360)
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="both", expand=True)
        for txn in self.get_transactions():
            tree.insert("", "end", values=(txn[0], txn[1], money(txn[2]), txn[3] or "—"))
        tk.Label(body, text="This application is a learning project. It is not connected to any real bank.",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 8)).pack(anchor="w", pady=(12, 0))

    def stat_card(self, parent, label, value, accent):
        card = tk.Frame(parent, bg=self.WHITE, padx=18, pady=16,
                        highlightbackground="#dce5ec", highlightthickness=1)
        tk.Label(card, text=label, bg=self.WHITE, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(card, text=value, bg=self.WHITE, fg=accent,
                 font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(8, 0))
        return card

    def get_balance(self):
        with connect_db() as con:
            row = con.execute("SELECT balance FROM users WHERE id=?", (self.current_user_id,)).fetchone()
        return float(row[0]) if row else 0.0

    def get_transactions(self):
        with connect_db() as con:
            return con.execute(
                "SELECT created_at, txn_type, amount, note FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 50",
                (self.current_user_id,)
            ).fetchall()

    def transaction_dialogl(self, txn_type):
        dialog = tk.Toplevel(self)
        dialog.title(txn_type)
        dialog.configure(bg=self.WHITE)
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        frame = tk.Frame(dialog, bg=self.WHITE, padx=28, pady=24)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text=txn_type + " funds", bg=self.WHITE, fg=self.NAVY,
                 font=("Segoe UI", 17, "bold")).pack(anchor="w")
        tk.Label(frame, text=f"Current balance: {money(self.get_balance())}",
                 bg=self.WHITE, fg=self.MUTED).pack(anchor="w", pady=(5, 18))
        tk.Label(frame, text="Amount (₹)", bg=self.WHITE, fg=self.TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        amount_entry = tk.Entry(frame, font=("Segoe UI", 12), relief="solid", bd=1)
        amount_entry.pack(fill="x", ipady=8, pady=(5, 14))
        tk.Label(frame, text="Note (optional)", bg=self.WHITE, fg=self.TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        note_entry = tk.Entry(frame, font=("Segoe UI", 10), relief="solid", bd=1)
        note_entry.pack(fill="x", ipady=8, pady=(5, 18))

        def submit():
            try:
                amount = float(amount_entry.get().strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid amount", "Enter a valid amount greater than zero.", parent=dialog)
                return
            current = self.get_balance()
            if txn_type == "Withdraw" and amount > current:
                messagebox.showerror("Insufficient funds", "Your balance is too low for this withdrawal.", parent=dialog)
                return
            new_balance = current + amount if txn_type == "Deposit" else current - amount
            now = datetime.now().strftime("%d-%m-%Y %I:%M %p")
            with connect_db() as con:
                con.execute("UPDATE users SET balance=? WHERE id=?", (new_balance, self.current_user_id))
                con.execute(
                    "INSERT INTO transactions(user_id, txn_type, amount, note, created_at) VALUES(?,?,?,?,?)",
                    (self.current_user_id, txn_type, amount, note_entry.get().strip(), now)
                )
            dialog.destroy()
            self.show_dashboard()
            messagebox.showinfo("Success", f"{txn_type} completed successfully.")

        ttk.Button(frame, text=f"Confirm {txn_type}", style="Primary.TButton",
                   command=submit).pack(fill="x")
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dialog.winfo_height()) // 2
        
        dialog.geometry(f"+{x}+{y}")

    # TRANSFER MONEY FEATURE
    def transfer_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("SecureBank - Transfer Money")
        dialog.geometry("450x480")
        dialog.configure(bg=self.WHITE)
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        frame = tk.Frame(
            dialog,
            bg=self.WHITE,
            padx=28,
            pady=24
        )
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="TRANSFER MONEY",
            bg=self.WHITE,
            fg=self.NAVY,
            font=("Segoe UI", 17, "bold")
        ).pack(anchor="w", pady=(0, 15))

        tk.Label(
            frame,
            text=f"Available Balance: {money(self.get_balance())}",
            bg=self.WHITE,
            fg=self.MUTED
        ).pack(anchor="w", pady=(0, 15))

        tk.Label(
            frame,
            text="Receiver Account Number",
            bg=self.WHITE,
            fg=self.TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        account_entry = tk.Entry(
            frame,
            font=("Segoe UI", 12),
            relief="solid",
            bd=1
        )
        account_entry.pack(fill="x", ipady=8, pady=(5, 15))

        tk.Label(
            frame,
            text="Transfer Amount (₹)",
            bg=self.WHITE,
            fg=self.TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        amount_entry = tk.Entry(
            frame,
            font=("Segoe UI", 12),
            relief="solid",
            bd=1
        )
        amount_entry.pack(fill="x", ipady=8, pady=(5, 15))

        tk.Label(
            frame,
            text="Note (Optional)",
            bg=self.WHITE,
            fg=self.TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        note_entry = tk.Entry(
            frame,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1
        )
        note_entry.pack(fill="x", ipady=8, pady=(5, 20))

        def submit_transfer():
            receiver_account = account_entry.get().strip()

            if not receiver_account:
                messagebox.showerror(
                    "Missing Details",
                    "Enter receiver account number.",
                    parent=dialog
                )
                return

            try:
                amount = round(float(amount_entry.get().strip()), 2)

                if amount <= 0:
                    raise ValueError

            except ValueError:
                messagebox.showerror(
                    "Invalid Amount",
                    "Enter a valid amount greater than zero.",
                    parent=dialog
                )
                return

            try:
                with connect_db() as con:
                    con.execute("BEGIN IMMEDIATE")

                    sender = con.execute("""
                        SELECT full_name, account_number, balance
                        FROM users WHERE id=?
                    """, (self.current_user_id,)).fetchone()

                    receiver = con.execute("""
                        SELECT id, full_name, account_number, balance
                        FROM users WHERE account_number=?
                    """, (receiver_account,)).fetchone()

                    if not sender:
                        messagebox.showerror(
                            "Error", "Sender account not found.",
                            parent=dialog
                        )
                        return

                    if not receiver:
                        messagebox.showerror(
                            "Invalid Account",
                            "Receiver account does not exist.",
                            parent=dialog
                        )
                        return

                    if receiver[0] == self.current_user_id:
                        messagebox.showerror(
                            "Invalid Transfer",
                            "You cannot transfer money to your own account.",
                            parent=dialog
                        )
                        return

                    if amount > sender[2]:
                        messagebox.showerror(
                            "Insufficient Balance",
                            "You do not have enough balance.",
                            parent=dialog
                        )
                        return

                    confirm = messagebox.askyesno(
                        "Confirm Transfer",
                        f"Receiver: {receiver[1]}\n"
                        f"Account: {receiver[2]}\n"
                        f"Amount: {money(amount)}\n\n"
                        "Do you want to continue?",
                        parent=dialog
                    )

                    if not confirm:
                        return

                    sender_balance = sender[2] - amount
                    receiver_balance = receiver[3] + amount

                    con.execute(
                        "UPDATE users SET balance=? WHERE id=?",
                        (sender_balance, self.current_user_id)
                    )

                    con.execute(
                        "UPDATE users SET balance=? WHERE id=?",
                        (receiver_balance, receiver[0])
                    )

                    now = datetime.now().strftime(
                        "%d-%m-%Y %I:%M %p"
                    )

                    note = note_entry.get().strip()

                    con.execute("""
                        INSERT INTO transactions
                        (user_id, txn_type, amount, note, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        self.current_user_id,
                        "Transfer",
                        amount,
                        f"To: {receiver[1]} ({receiver[2]}). {note}",
                        now
                    ))

                    con.execute("""
                        INSERT INTO transactions
                        (user_id, txn_type, amount, note, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        receiver[0],
                        "Received",
                        amount,
                        f"From: {sender[0]} ({sender[1]}). {note}",
                        now
                    ))

                dialog.destroy()
                self.show_dashboard()

                messagebox.showinfo(
                    "Transfer Successful",
                    f"{money(amount)} transferred successfully!"
                )

            except Exception as error:
                messagebox.showerror(
                    "Transfer Failed",
                    f"Transaction could not be completed.\n{error}",
                    parent=dialog
                )

        ttk.Button(
            frame,
            text="Confirm Transfer",
            style="Primary.TButton",
            command=submit_transfer
        ).pack(fill="x")



    # MINI STATEMENT FEATURE
    def show_mini_statement(self):
        window = tk.Toplevel(self)
        window.title("SecureBank - Mini Statement")
        window.geometry("750x450")
        window.configure(bg="white")

        ttk.Label(
            window,
            text="MINI STATEMENT - LAST 10 TRANSACTIONS",
            font=("Segoe UI", 15, "bold")
        ).pack(pady=15)

        columns = ("date", "type", "amount", "note")

        tree = ttk.Treeview(
            window,
            columns=columns,
            show="headings",
            height=10
        )

        tree.heading("date", text="DATE & TIME")
        tree.heading("type", text="TYPE")
        tree.heading("amount", text="AMOUNT")
        tree.heading("note", text="DESCRIPTION")

        tree.column("date", width=180)
        tree.column("type", width=120)
        tree.column("amount", width=120)
        tree.column("note", width=250)

        tree.pack(fill="both", expand=True, padx=15, pady=10)

        with connect_db() as con:
            rows = con.execute("""
                SELECT created_at, txn_type, amount, note
                FROM transactions
                WHERE user_id=?
                ORDER BY id DESC
                LIMIT 10
            """, (self.current_user_id,)).fetchall()

        for row in rows:
            tree.insert("", "end", values=(
                row[0], row[1], money(row[2]), row[3] or "-"
            ))
           
    # DOWNLOAD BANK STATEMENT AS PDF
    def download_statement_pdf(self):

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile="SecureBank_Statement.pdf"
        )

        if not file_path:
            return

        try:
            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm
            )

            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph(
                "SECUREBANK - BANK STATEMENT",
                styles["Title"]
            ))

            elements.append(Spacer(1, 15))

            elements.append(Paragraph(
                f"Account Holder: {self.current_user}",
                styles["Normal"]
            ))

            elements.append(Spacer(1, 8))

            elements.append(Paragraph(
                f"Account Number: {self.current_account_number}",
                styles["Normal"]
            ))

            elements.append(Spacer(1, 8))

            balance = self.get_balance()

            elements.append(Paragraph(
                f"Available Balance: Rs. {balance:,.2f}",
                styles["Normal"]
            ))

            elements.append(Spacer(1, 20))

            elements.append(Paragraph(
                "Recent 10 Transactions",
                styles["Heading2"]
            ))

            with connect_db() as con:
                rows = con.execute("""
                    SELECT created_at, txn_type, amount, note
                    FROM transactions
                    WHERE user_id=?
                    ORDER BY id DESC
                    LIMIT 10
                """, (self.current_user_id,)).fetchall()

            data = [
                ["DATE & TIME", "TYPE", "AMOUNT", "DESCRIPTION"]
            ]

            for row in rows:
                data.append([
                    str(row[0]),
                    str(row[1]),
                    f"Rs. {row[2]:,.2f}",
                    str(row[3] or "-")
                ])

            table = Table(
                data,
                colWidths=[42*mm, 25*mm, 30*mm, 55*mm]
            )

            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10243A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 7),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
            ]))

            elements.append(table)

            doc.build(elements)

            messagebox.showinfo(
                "PDF Downloaded",
                "Bank statement PDF saved successfully!"
            )

        except Exception as e:
            messagebox.showerror(
                "PDF Error",
                f"Unable to generate PDF:\n{e}"
            )

    # CHANGE PASSWORD FEATURE
    def change_password(self):

        dialog = tk.Toplevel(self)
        dialog.title("SecureBank - Change Password")
        dialog.geometry("420x390")
        dialog.configure(bg=self.WHITE)
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        frame = tk.Frame(
            dialog,
            bg=self.WHITE,
            padx=28,
            pady=24
        )
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="CHANGE PASSWORD",
            bg=self.WHITE,
            fg=self.NAVY,
            font=("Segoe UI", 17, "bold")
        ).pack(anchor="w", pady=(0, 20))

        tk.Label(
            frame,
            text="Current Password",
            bg=self.WHITE
        ).pack(anchor="w")

        current_entry = tk.Entry(
            frame, show="*", font=("Segoe UI", 11)
        )
        current_entry.pack(fill="x", ipady=7, pady=(5, 14))

        tk.Label(
            frame,
            text="New Password",
            bg=self.WHITE
        ).pack(anchor="w")

        new_entry = tk.Entry(
            frame, show="*", font=("Segoe UI", 11)
        )
        new_entry.pack(fill="x", ipady=7, pady=(5, 14))

        tk.Label(
            frame,
            text="Confirm New Password",
            bg=self.WHITE
        ).pack(anchor="w")

        confirm_entry = tk.Entry(
            frame, show="*", font=("Segoe UI", 11)
        )
        confirm_entry.pack(fill="x", ipady=7, pady=(5, 20))

        def submit_password():

            old_password = current_entry.get()
            new_password = new_entry.get()
            confirm_password = confirm_entry.get()

            if not old_password or not new_password or not confirm_password:
                messagebox.showwarning(
                    "Missing Details",
                    "Please fill all password fields.",
                    parent=dialog
                )
                return

            if len(new_password) < 8:
                messagebox.showwarning(
                    "Weak Password",
                    "New password must contain at least 8 characters.",
                    parent=dialog
                )
                return

            if new_password != confirm_password:
                messagebox.showerror(
                    "Password Mismatch",
                    "New password and confirm password do not match.",
                    parent=dialog
                )
                return

            with connect_db() as con:

                row = con.execute(
                    "SELECT salt, password_hash FROM users WHERE id=?",
                    (self.current_user_id,)
                ).fetchone()

                if not row:
                    messagebox.showerror(
                        "Error",
                        "User account not found.",
                        parent=dialog
                    )
                    return

                salt, expected = row

                _, actual = hash_password(old_password, salt)

                if not secrets.compare_digest(actual, expected):
                    messagebox.showerror(
                        "Incorrect Password",
                        "Current password is incorrect.",
                        parent=dialog
                    )
                    return

                new_salt, new_hash = hash_password(new_password)

                con.execute(
                    """
                    UPDATE users
                    SET salt=?, password_hash=?
                    WHERE id=?
                    """,
                    (new_salt, new_hash, self.current_user_id)
                )

            dialog.destroy()

            messagebox.showinfo(
                "Success",
                "Your password has been changed successfully!",
                parent=self
            )

        ttk.Button(
            frame,
            text="Update Password",
            style="Primary.TButton",
            command=submit_password
        ).pack(fill="x")

 

    def logout(self):
        self.current_user = None
        self.current_user_id = None
        self.show_login()

if __name__ == "__main__":
    init_db()
    app = BankingApp()
    app.mainloop()
