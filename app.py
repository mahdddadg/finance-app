from flask import Flask, request, redirect, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ---------- MODELS ----------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    category = db.Column(db.String(50))
    type = db.Column(db.String(10))  # deposit or spend

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- AUTO FIX DATABASE ----------
with app.app_context():
    if not os.path.exists("db.sqlite3"):
        db.create_all()
    else:
        try:
            db.session.execute("SELECT type FROM transaction LIMIT 1")
        except:
            os.remove("db.sqlite3")
            db.create_all()

# ---------- HOME ----------
@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        amount = float(request.form["amount"])
        category = request.form["category"]
        t_type = request.form["type"]

        t = Transaction(
            user_id=current_user.id,
            amount=amount,
            category=category,
            type=t_type
        )

        db.session.add(t)
        db.session.commit()

    data = Transaction.query.filter_by(user_id=current_user.id).all()

    balance = sum(t.amount if t.type == "deposit" else -t.amount for t in data)

    return render_template_string("""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body {
        font-family: -apple-system;
        background: linear-gradient(to bottom, #f2f2f7, #e5e5ea);
        padding: 20px;
        margin: 0;
    }

    h1 { font-size: 28px; font-weight: bold; }

    .card {
        background: rgba(255,255,255,0.9);
        backdrop-filter: blur(10px);
        padding: 18px;
        border-radius: 20px;
        margin-top: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }

    .balance {
        font-size: 40px;
        font-weight: bold;
    }

    .positive { color: #34c759; }
    .negative { color: #ff3b30; }

    input, select {
        width: 100%;
        padding: 14px;
        margin-top: 8px;
        border-radius: 12px;
        border: none;
        background: #f2f2f7;
    }

    button {
        width: 100%;
        padding: 14px;
        margin-top: 10px;
        border-radius: 12px;
        border: none;
        background: linear-gradient(135deg, #007AFF, #5856D6);
        color: white;
        font-weight: bold;
    }

    .transaction {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #eee;
    }

    .category {
        color: gray;
        font-size: 14px;
    }
    </style>
    </head>

    <body>

    <h1>💰 Finance</h1>

    <div class="card">
        <div class="balance">${{balance}}</div>
        <div class="category">Current Balance</div>
    </div>

    <div class="card">
        <form method="post">
            <input name="amount" placeholder="Amount" required>
            <input name="category" placeholder="Category">

            <select name="type">
                <option value="deposit">Deposit 💰</option>
                <option value="spend">Spend 💸</option>
            </select>

            <button>Add Transaction</button>
        </form>
    </div>

    <div class="card">
        <h3>History</h3>

        {% for t in data[::-1] %}
        <div class="transaction">
            <div>
                <div class="{{'positive' if t.type=='deposit' else 'negative'}}">
                    {{'+' if t.type=='deposit' else '-'}}${{t.amount}}
                </div>
                <div class="category">{{t.category}}</div>
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="card">
        <a href="/logout">Logout</a>
    </div>

    </body>
    </html>
    """, data=data, balance=balance)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return """
    <h2>Create Account</h2>
    <form method="post">
        <input name="username" placeholder="Username" required>
        <input name="password" placeholder="Password" required>
        <button>Register</button>
    </form>
    """

# ---------- LOGIN ----------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect("/")

    return """
    <h2>Login</h2>
    <form method="post">
        <input name="username" placeholder="Username" required>
        <input name="password" placeholder="Password" required>
        <button>Login</button>
    </form>
    <br>
    <a href="/register">Create account</a>
    """

# ---------- LOGOUT ----------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ---------- RUN LOCAL ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
