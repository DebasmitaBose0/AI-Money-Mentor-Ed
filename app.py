from flask import Flask, request, jsonify, render_template
import yfinance as yf
import os
import sys
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

# ── Startup validation ───────────────────────────────────────
# Fail fast and clearly if the required API key is missing.
# Copy .env.example → .env and set your GROQ_API_KEY.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY or GROQ_API_KEY.strip() in ("", "your_groq_api_key_here"):
    print(
        "\n[ERROR] GROQ_API_KEY is not configured.\n"
        "  1. Copy .env.example to .env\n"
        "  2. Set your GROQ_API_KEY in .env\n"
        "  Obtain a free key at: https://console.groq.com/\n",
        file=sys.stderr,
    )
    sys.exit(1)
# ---------------- IMPORT UTILS ----------------
from utils.sip import calculate_sip
from utils.tax import calculate_tax
from utils.pdf_parser import extract_income
from utils.money_score import calculate_money_score
from utils.multi_agent import run_multi_agent
from utils.stock import get_stock_price
from utils.expense_track import calculate_expense, insights
from utils import persistence

app = Flask(__name__)

# ---------------- INIT DATABASE ----------------
from models import db, Expense, Asset, Liability

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///money_mentor.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()

# ---------------- INIT GROQ ----------------
client = Groq(api_key=GROQ_API_KEY)

# ── Dev-mode startup message ─────────────────────────────────
if os.getenv("FLASK_ENV", "development") != "production":
    print("[OK] Groq client initialised successfully.")
# ---------------- VALIDATION HELPERS ----------------
def validate_float(data, key, min_val=0.0):
    if not data or key not in data:
        raise ValueError(f"'{key}' is required.")
    try:
        val = float(data[key])
    except (TypeError, ValueError):
        raise ValueError(f"'{key}' must be a valid number.")
    if val < min_val:
        raise ValueError(f"'{key}' must be at least {min_val}.")
    return val

def validate_int(data, key, min_val=0):
    if not data or key not in data:
        raise ValueError(f"'{key}' is required.")
    try:
        val = int(data[key])
    except (TypeError, ValueError):
        raise ValueError(f"'{key}' must be a valid integer.")
    if val < min_val:
        raise ValueError(f"'{key}' must be at least {min_val}.")
    return val

def validate_string(data, key, max_len=200):
    if not data or key not in data:
        raise ValueError(f"'{key}' is required.")
    val = str(data[key]).strip()
    if not val:
        raise ValueError(f"'{key}' cannot be empty.")
    if len(val) > max_len:
        raise ValueError(f"'{key}' exceeds maximum length of {max_len} characters.")
    return val

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- HEALTH CHECK ----------------
@app.route("/health", methods=["GET"])
def health_check():
    """Lightweight liveness probe for deployment environments (Docker, Railway, etc.)."""
    return jsonify({"status": "ok", "service": "AI Money Mentor"}), 200


# ---------------- ERROR HANDLERS ----------------
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "error": "Bad Request",
        "message": str(error),
        "status_code": 400
    }), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "message": "The requested endpoint does not exist.",
        "status_code": 404
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method Not Allowed",
        "message": str(error),
        "status_code": 405
    }), 405


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred. Please try again later.",
        "status_code": 500
    }), 500


# ---------------- 🤖 AI CHAT ----------------
@app.route("/chat", methods=["POST"])
def chat():
    try:
        msg = validate_string(request.json, "message", max_len=1000)

        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a financial advisor for India."},
                {"role": "user", "content": msg}
            ]
        )

        return jsonify({
            "reply": res.choices[0].message.content
        })

    except ValueError as e:
        return jsonify({"error": "Validation Error", "message": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Groq API Error: {str(e)}")

        return jsonify({
            "reply": "Unable to generate a response at the moment. Please try again later."
        }), 500


# ---------------- 💸 SIP ----------------
@app.route("/sip", methods=["POST"])
def sip():
    try:
        data = request.json
        monthly = validate_float(data, "monthly", min_val=0.0)
        rate = validate_float(data, "rate", min_val=0.0)
        years = validate_int(data, "years", min_val=0)
        result = calculate_sip(monthly, rate, years)
        return jsonify({"future_value": result})

    except ValueError as e:
        return jsonify({"error": "Validation Error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- 📊 STOCK ----------------
@app.route("/portfolio", methods=["POST"])
def portfolio():
    try:
        stock = validate_string(request.json, "stock", max_len=10).upper()
        result = get_stock_price(stock)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": "Validation Error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ---------------- 💸 TAX ----------------
@app.route("/tax", methods=["POST"])
def tax():
    try:
        income = validate_float(request.json, "income", min_val=0.0)
        return jsonify({"tax": calculate_tax(income)})

    except ValueError as e:
        return jsonify({"error": "Validation Error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- 📄 PDF ----------------
@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files["file"]
        result = extract_income(file)
        return jsonify({"data": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- 🧠 MULTI AGENT ----------------
@app.route("/agent", methods=["POST"])
def run_agent_route():
    try:
        query = validate_string(request.json, "query", max_len=1000)
        response = run_multi_agent(client, query)
        return jsonify({"response": response})

    except ValueError as e:
        return jsonify({"error": "Validation Error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- 💰 MONEY SCORE ----------------
@app.route("/money-score", methods=["POST"])
def money_score():
    try:
        data = request.json
        income = validate_float(data, "income", min_val=0.0)
        expenses = validate_float(data, "expenses", min_val=0.0)
        savings = validate_float(data, "savings", min_val=0.0)
        investments = validate_float(data, "investments", min_val=0.0)
        debt = validate_float(data, "debt", min_val=0.0)
        emergency = validate_float(data, "emergency", min_val=0.0)

        score = calculate_money_score(income, expenses, savings, investments, debt, emergency)

        if score >= 80:
            status = "Excellent 💚"
        elif score >= 60:
            status = "Good 👍"
        elif score >= 40:
            status = "Average ⚠️"
        else:
            status = "Needs Improvement ❌"

        return jsonify({
            "score": score,
            "status": status
        })

    except ValueError as e:
        return jsonify({"error": "Validation Error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- EXPENSE TRACKER ----------------

@app.route("/add_expense", methods=["POST"])
def add_expense():
    try:
        data = request.json
        category = validate_string(data, "category", max_len=120)
        amount = validate_float(data, "amount", min_val=0.0)
        date = validate_string(data, "date", max_len=40)

        expense = Expense(
            category=category,
            amount=amount,
            date=date
        )
        db.session.add(expense)
        db.session.commit()
        return jsonify({"status": "success"})
    except ValueError as e:
        return jsonify({"error": "Validation Error", "message": str(e)}), 400
    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/calculate", methods=["GET"])
def calculate():
    expense_data = [e.to_dict() for e in Expense.query.order_by(Expense.id).all()]
    result = calculate_expense(expense_data)
    result["expenses"] = expense_data
    return jsonify(result)


@app.route("/insights", methods=["GET"])
def expense_insights():
    expense_data = [e.to_dict() for e in Expense.query.order_by(Expense.id).all()]
    result = insights(client, expense_data)
    return jsonify(result)


# ---------------- NET WORTH TRACKER ----------------
@app.route("/net-worth", methods=["GET", "POST"])
def get_net_worth():
    assets = Asset.query.order_by(Asset.id).all()
    liabilities = Liability.query.order_by(Liability.id).all()
    assets_data = [a.to_dict(i) for i, a in enumerate(assets)]
    liabilities_data = [l.to_dict(i) for i, l in enumerate(liabilities)]
    total_assets = sum(item['amount'] for item in assets_data)
    total_liabilities = sum(item['amount'] for item in liabilities_data)
    return jsonify({
        "assets": assets_data,
        "liabilities": liabilities_data,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "net_worth": total_assets - total_liabilities,
    })


@app.route("/add-asset", methods=["POST"])
def add_asset():
    try:
        data = request.json
        name = validate_string(data, "name", max_len=120)
        amount = validate_float(data, "amount", min_val=0.0)
        asset = Asset(name=name, amount=amount)
        db.session.add(asset)
        db.session.commit()
        return jsonify({"status": "success"})
    except ValueError as e:
        return jsonify({"error": "Validation Error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/add-liability", methods=["POST"])
def add_liability():
    try:
        data = request.json
        name = validate_string(data, "name", max_len=120)
        amount = validate_float(data, "amount", min_val=0.0)
        liability = Liability(name=name, amount=amount)
        db.session.add(liability)
        db.session.commit()
        return jsonify({"status": "success"})
    except ValueError as e:
        return jsonify({"error": "Validation Error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/delete-item", methods=["POST"])
def delete_item():
    """Delete an asset or liability by its stable id (NOT list index).

    Previously this used list.pop(index) which silently corrupted
    all subsequent indices after the first deletion.
    """
    try:
        data = request.json
        item_type = validate_string(data, "type", max_len=20)
        if item_type not in ("asset", "liability"):
            raise ValueError("type must be either 'asset' or 'liability'")
        item_id = validate_int(data, "id", min_val=0)

        if item_type == 'asset':
            rows = Asset.query.order_by(Asset.id).all()
            db.session.delete(rows[item_id])
        else:
            rows = Liability.query.order_by(Liability.id).all()
            db.session.delete(rows[item_id])

        db.session.commit()
        return jsonify({"status": "success"})
    except ValueError as e:
        return jsonify({"error": "Validation Error", "message": str(e)}), 400
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- RUN ----------------
if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
    app.run(debug=debug_mode)
