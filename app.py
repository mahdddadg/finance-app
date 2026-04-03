from flask import Flask, request, redirect, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

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

# ---------- CREATE DATABASE ----------
with app.app_context():
    db.create_all()

# ---------- AI ----------
def ai_advice(data):
    income = sum(t.amount for t in data if t.type == "deposit")
    expense = sum(t.amount for t in data if t.type == "spend")

    if expense > income:
        return "⚠️ You are spending more than you earn!"
    elif income - expense < 100:
        return "💡 Try saving more money."
    else:
        return "🚀 Mahdi & Mela — you are getting fucking rich! billioners ! " \
        "When your overthinking , overthink the MOST POSITIVE OUTCOME ! " 

# ---------- HOME ----------
@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        t = Transaction(
            user_id=current_user.id,
            amount=float(request.form["amount"]),
            category=request.form["category"],
            type=request.form["type"]
        )
        db.session.add(t)
        db.session.commit()

    data = Transaction.query.filter_by(user_id=current_user.id).all()

    income = sum(t.amount for t in data if t.type == "deposit")
    expense = sum(t.amount for t in data if t.type == "spend")
    balance = income - expense

    advice = ai_advice(data)

    return render_template_string("""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
    body {
        font-family: Arial;
        background: linear-gradient(135deg, #d4fc79, #96e6a1, #c2e9fb, #a18cd1);
        background-size: 400% 400%;
        animation: bg 10s ease infinite;
        padding: 20px;
        margin: 0;
        overflow-x: hidden;
    }

    @keyframes bg {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }

    h1 {
        text-align: center;
        color: #1c1c1e;
    }

    .money {
        position: fixed;
        font-size: 30px;
        animation: float 6s linear infinite;
        opacity: 0.6;
    }

    @keyframes float {
        0% { transform: translateY(100vh); }
        100% { transform: translateY(-100vh); }
    }

    .card {
        background: rgba(255,255,255,0.9);
        padding: 20px;
        border-radius: 20px;
        margin-top: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }

    .balance {
        font-size: 40px;
        font-weight: bold;
        color: #34c759;
        text-align: center;
    }

    input, select {
        width: 100%;
        padding: 12px;
        margin-top: 8px;
        border-radius: 10px;
        border: none;
        background: #f2f2f7;
    }

    button {
        width: 100%;
        padding: 12px;
        margin-top: 10px;
        border-radius: 10px;
        border: none;
        background: linear-gradient(135deg, #5856d6, #34c759);
        color: white;
        font-weight: bold;
    }

    .transaction {
        padding: 10px 0;
        border-bottom: 1px solid #eee;
    }

    .positive { color: green; font-weight: bold; }
    .negative { color: red; font-weight: bold; }

    .message {
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        margin-top: 10px;
        color: #5856d6;
    }
    </style>
    </head>

    <body>

    <!-- Floating money -->
    <div class="money" style="left:10%;">💸</div>
    <div class="money" style="left:30%; animation-delay:2s;">💰</div>
    <div class="money" style="left:60%; animation-delay:4s;">💵</div>
    <div class="money" style="left:80%; animation-delay:1s;">💸</div>

    <h1>💰 Finance App</h1>

    <div class="message">
    Mahdi, Mela you are getting rich! Millions! 🚀💸
    </div>

    <div class="card">
        <div class="balance">${{balance}}</div>
    </div>

    <!-- 📊 CHART -->
    <div class="card">
        <canvas id="chart"></canvas>
    </div>

    <!-- 🤖 AI -->
    <div class="card">
        <h3>🤖 AI Advice</h3>
        <p>{{advice}}</p>
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
            <span class="{{'positive' if t.type=='deposit' else 'negative'}}">
                {{'+' if t.type=='deposit' else '-'}}${{t.amount}}
            </span>
            - {{t.category}}
        </div>
        {% endfor %}
    </div>

    <div class="card">
        <a href="/logout">Logout</a>
    </div>

    <script>
    new Chart(document.getElementById('chart'), {
        type: 'doughnut',
        data: {
            labels: ['Income', 'Expense'],
            datasets: [{
                data: [{{income}}, {{expense}}]
            }]
        }
    });
    </script>

    </body>
    </html>
    """, data=data, balance=balance, income=income, expense=expense, advice=advice)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=generate_password_hash(request.form["password"])
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return """
    <h2>Register</h2>
    <form method="post">
        <input name="username">
        <input name="password">
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
        <input name="username">
        <input name="password">
        <button>Login</button>
    </form>
    <a href="/register">Register</a>
    """

# ---------- LOGOUT ----------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)