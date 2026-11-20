import os
import io
from pathlib import Path
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_file
)

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

from securebank_web.db import (
    init_db, query_one, query_all, execute,
    generate_account_number, execute_transfer
)
from securebank_web.auth import (
    hash_password, verify_password, money,
    login_required, validate_registration,
    validate_password_change, validate_amount
)

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)

# Secret key configuration for sessions
app.secret_key = os.environ.get("SECRET_KEY", "securebank-default-secret-key-39824982")

# Register template filters
app.jinja_env.filters["money"] = money

# Initialize database schema on startup
try:
    init_db()
except Exception as e:
    app.logger.warning(f"Database initialization deferred or already exists: {e}")


@app.context_processor
def inject_user():
    """Injects current user state into all templates."""
    if "user_id" in session:
        user = query_one(
            "SELECT id, full_name, username, account_number, balance FROM users WHERE id=?",
            (session["user_id"],)
        )
        return {"current_user": user}
    return {"current_user": None}


# -------------------------------------------------------------
# AUTHENTICATION ROUTES
# -------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html", username=username)

        user = query_one(
            "SELECT id, full_name, username, salt, password_hash, account_number FROM users WHERE username=?",
            (username,)
        )

        if not user or not verify_password(password, user["salt"], user["password_hash"]):
            flash("Invalid username or password.", "danger")
            return render_template("login.html", username=username)

        # Set session variables
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["full_name"] = user["full_name"]
        session["account_number"] = user["account_number"]

        flash(f"Welcome back, {user['full_name']}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        valid, error_msg = validate_registration(full_name, username, password, confirm)
        if not valid:
            flash(error_msg, "danger")
            return render_template("register.html", full_name=full_name, username=username)

        # Check existing username
        existing = query_one("SELECT id FROM users WHERE username=?", (username,))
        if existing:
            flash("This username is already registered. Choose another.", "danger")
            return render_template("register.html", full_name=full_name)

        salt, digest = hash_password(password)
        account_no = generate_account_number()

        try:
            execute("""
                INSERT INTO users (full_name, username, salt, password_hash, balance, account_number)
                VALUES (?, ?, ?, ?, 0.0, ?)
            """, (full_name, username, salt, digest, account_no))

            flash("Your demo account is ready! Please sign in with your credentials.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error creating account: {e}", "danger")
            return render_template("register.html", full_name=full_name, username=username)

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out securely.", "info")
    return redirect(url_for("login"))


# -------------------------------------------------------------
# CORE BANKING ROUTES
# -------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    user = query_one(
        "SELECT id, full_name, username, account_number, balance FROM users WHERE id=?",
        (session["user_id"],)
    )
    if not user:
        session.clear()
        return redirect(url_for("login"))

    recent_txns = query_all("""
        SELECT created_at, txn_type, amount, note
        FROM transactions
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
    """, (user["id"],))

    return render_template("dashboard.html", user=user, transactions=recent_txns)


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    user = query_one("SELECT id, balance FROM users WHERE id=?", (session["user_id"],))

    if request.method == "POST":
        amount_val, err = validate_amount(request.form.get("amount", ""))
        note = request.form.get("note", "").strip()

        if err:
            flash(err, "danger")
            return render_template("deposit.html", user=user)

        new_balance = round(float(user["balance"]) + amount_val, 2)
        now = datetime.now().strftime("%d-%m-%Y %I:%M %p")

        execute("UPDATE users SET balance=? WHERE id=?", (new_balance, user["id"]))
        execute("""
            INSERT INTO transactions (user_id, txn_type, amount, note, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user["id"], "Deposit", amount_val, note, now))

        flash(f"{money(amount_val)} deposited successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("deposit.html", user=user)


@app.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    user = query_one("SELECT id, balance FROM users WHERE id=?", (session["user_id"],))

    if request.method == "POST":
        amount_val, err = validate_amount(request.form.get("amount", ""))
        note = request.form.get("note", "").strip()

        if err:
            flash(err, "danger")
            return render_template("withdraw.html", user=user)

        if amount_val > float(user["balance"]):
            flash("Your balance is too low for this withdrawal.", "danger")
            return render_template("withdraw.html", user=user)

        new_balance = round(float(user["balance"]) - amount_val, 2)
        now = datetime.now().strftime("%d-%m-%Y %I:%M %p")

        execute("UPDATE users SET balance=? WHERE id=?", (new_balance, user["id"]))
        execute("""
            INSERT INTO transactions (user_id, txn_type, amount, note, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user["id"], "Withdraw", amount_val, note, now))

        flash(f"{money(amount_val)} withdrawn successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("withdraw.html", user=user)


@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    user = query_one("SELECT id, balance, account_number FROM users WHERE id=?", (session["user_id"],))

    if request.method == "POST":
        receiver_account = request.form.get("receiver_account", "").strip()
        amount_str = request.form.get("amount", "").strip()
        note = request.form.get("note", "").strip()

        if not receiver_account:
            flash("Please enter the receiver account number.", "danger")
            return render_template("transfer.html", user=user, receiver_account=receiver_account)

        amount_val, err = validate_amount(amount_str)
        if err:
            flash(err, "danger")
            return render_template("transfer.html", user=user, receiver_account=receiver_account)

        now = datetime.now().strftime("%d-%m-%Y %I:%M %p")
        success, message = execute_transfer(
            sender_id=user["id"],
            receiver_account_no=receiver_account,
            amount=amount_val,
            note=note,
            timestamp=now
        )

        if success:
            flash(message, "success")
            return redirect(url_for("dashboard"))
        else:
            flash(message, "danger")
            return render_template("transfer.html", user=user, receiver_account=receiver_account)

    return render_template("transfer.html", user=user)


@app.route("/mini-statement")
@login_required
def mini_statement():
    user = query_one("SELECT id, full_name, account_number, balance FROM users WHERE id=?", (session["user_id"],))
    txns = query_all("""
        SELECT created_at, txn_type, amount, note
        FROM transactions
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
    """, (user["id"],))

    return render_template("mini_statement.html", user=user, transactions=txns)


@app.route("/transactions")
@login_required
def transactions():
    user = query_one("SELECT id, full_name, account_number, balance FROM users WHERE id=?", (session["user_id"],))
    filter_type = request.args.get("type", "All")

    if filter_type != "All":
        txns = query_all("""
            SELECT created_at, txn_type, amount, note
            FROM transactions
            WHERE user_id=? AND txn_type=?
            ORDER BY id DESC
            LIMIT 50
        """, (user["id"], filter_type))
    else:
        txns = query_all("""
            SELECT created_at, txn_type, amount, note
            FROM transactions
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT 50
        """, (user["id"],))

    return render_template("transactions.html", user=user, transactions=txns, filter_type=filter_type)


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_pass = request.form.get("current_password", "")
        new_pass = request.form.get("new_password", "")
        confirm_pass = request.form.get("confirm_password", "")

        valid, err = validate_password_change(current_pass, new_pass, confirm_pass)
        if not valid:
            flash(err, "danger")
            return render_template("change_password.html")

        user = query_one("SELECT salt, password_hash FROM users WHERE id=?", (session["user_id"],))
        if not user or not verify_password(current_pass, user["salt"], user["password_hash"]):
            flash("Current password is incorrect.", "danger")
            return render_template("change_password.html")

        new_salt, new_hash = hash_password(new_pass)
        execute(
            "UPDATE users SET salt=?, password_hash=? WHERE id=?",
            (new_salt, new_hash, session["user_id"])
        )

        flash("Your password has been changed successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("change_password.html")


@app.route("/download-statement-pdf")
@login_required
def download_statement_pdf():
    user = query_one(
        "SELECT id, full_name, account_number, balance FROM users WHERE id=?",
        (session["user_id"],)
    )
    rows = query_all("""
        SELECT created_at, txn_type, amount, note
        FROM transactions
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
    """, (user["id"],))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()
    elements = []

    # Statement Header
    elements.append(Paragraph("SECUREBANK - BANK STATEMENT", styles["Title"]))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"<b>Account Holder:</b> {user['full_name']}", styles["Normal"]))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Account Number:</b> {user['account_number']}", styles["Normal"]))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Available Balance:</b> Rs. {float(user['balance']):,.2f}", styles["Normal"]))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"<b>Generated On:</b> {datetime.now().strftime('%d-%m-%Y %I:%M %p')}", styles["Normal"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Recent 10 Transactions", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    data = [["DATE & TIME", "TYPE", "AMOUNT", "DESCRIPTION"]]
    for r in rows:
        data.append([
            str(r["created_at"]),
            str(r["txn_type"]),
            f"Rs. {float(r['amount']):,.2f}",
            str(r["note"] or "-")
        ])

    if len(data) == 1:
        data.append(["-", "No transactions", "Rs. 0.00", "No recent activity"])

    table = Table(data, colWidths=[42 * mm, 25 * mm, 30 * mm, 65 * mm])
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
    buffer.seek(0)

    filename = f"SecureBank_Statement_{user['account_number']}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )


# -------------------------------------------------------------
# ERROR HANDLERS
# -------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
