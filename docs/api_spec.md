# 📖 AI Money Mentor API Specification

This document details the backend REST API endpoints exposed by the Flask application, including their expected JSON payloads, response shapes, and validation rules.

---

## 🤖 Chat Endpoint
- **URL**: `/chat`
- **Method**: `POST`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "message": "What is tax exemption under Section 80C?",
    "history": []
  }
  ```
- **Response Shape**:
  ```json
  {
    "reply": "Section 80C allows deductions up to ₹1.5L for specific investments like ELSS, PPF, and EPF..."
  }
  ```

---

## 📈 SIP Calculator Endpoint
- **URL**: `/sip`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "monthly": 10000.0,
    "rate": 12.0,
    "years": 10,
    "inflation": 6.0
  }
  ```
- **Response Shape**:
  ```json
  {
    "future_value": 2323390.8,
    "nominal_value": 2323390.8,
    "inflation_adjusted_value": 1297380.5,
    "inflation_applied": 6.0
  }
  ```

---

## 💸 Tax Planner Endpoint
- **URL**: `/tax`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "income": 1200000.0,
    "deduction_80c": 150000.0,
    "deduction_80d": 25000.0,
    "deduction_hra": 50000.0
  }
  ```
- **Response Shape**:
  ```json
  {
    "tax": {
      "gross_income": 1200000.0,
      "deductions_applied": {
        "80c": 150000.0,
        "80d": 25000.0,
        "hra": 50000.0,
        "total": 275000.0
      },
      "new_regime": {
        "standard_deduction": 75000,
        "taxable_income": 1125000.0,
        "base_tax": 78750.0,
        "cess": 3150.0,
        "total_tax": 81900.0
      },
      "old_regime": {
        "standard_deduction": 50000,
        "taxable_income": 925000.0,
        "base_tax": 97500.0,
        "cess": 3900.0,
        "total_tax": 101400.0
      },
      "recommended": "New Regime",
      "savings": 19500.0
    }
  }
  ```

---

## 📄 PDF Parser Upload Endpoint
- **URL**: `/upload`
- **Method**: `POST`
- **Request Headers**: `Content-Type: multipart/form-data`
- **Form Data**:
  - `file`: (Binary File - PDF format)
- **Response Shape**:
  ```json
  {
    "data": {
      "document_type": "Form 16",
      "employer_organization": "Example Corp Ltd",
      "gross_income": 1500000.0,
      "tax_deducted_tds": 65000.0,
      "confidence_score": 0.98
    }
  }
  ```

---

## 🧠 Multi-Agent Analysis Endpoint
- **URL**: `/agent`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "query": "Should I invest in NPS or PPF for retirement?"
  }
  ```
- **Response Shape**:
  ```json
  {
    "response": "Based on specialized routing, the Retirement Planner advisor recommends..."
  }
  ```

---

## 💰 Money Score Evaluation Endpoint
- **URL**: `/money-score`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "income": 100000.0,
    "expenses": 40000.0,
    "savings": 30000.0,
    "investments": 20000.0,
    "debt": 10000.0,
    "emergency": 240000.0
  }
  ```
- **Response Shape**:
  ```json
  {
    "score": 85,
    "status": "Excellent 💚"
  }
  ```

---

## 📊 Live Stock Price Endpoint
- **URL**: `/portfolio`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "stock": "TCS"
  }
  ```
- **Response Shape**:
  ```json
  {
    "symbol": "TCS",
    "price": 3850.5,
    "currency": "INR"
  }
  ```

---

## 💸 Expense Tracker Endpoints

### 1. Add Local Expense
- **URL**: `/add_expense`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "category": "Food",
    "amount": 250.0,
    "date": "2026-06-05"
  }
  ```
- **Response Shape**:
  ```json
  {
    "status": "success"
  }
  ```

### 2. Fetch Aggregated Expenses
- **URL**: `/calculate`
- **Method**: `GET`
- **Response Shape**:
  ```json
  {
    "total_spend": 250.0,
    "average_expense": 250.0,
    "expenses": [
      {
        "id": 1,
        "category": "Food",
        "amount": 250.0,
        "date": "2026-06-05"
      }
    ]
  }
  ```

### 3. Generate Expense Insights
- **URL**: `/insights`
- **Method**: `GET`
- **Response Shape**:
  ```json
  {
    "insights": "<div class=\"insight-card\"><h3>AI Insights</h3><p>Your major spend is Food. Consider reducing dine-outs...</p></div>"
  }
  ```

---

## 💎 Net Worth Tracker Endpoints

### 1. Fetch Net Worth Summary
- **URL**: `/net-worth`
- **Method**: `GET`
- **Response Shape**:
  ```json
  {
    "assets": [
      {
        "id": 0,
        "name": "Savings Account",
        "amount": 50000.0
      }
    ],
    "liabilities": [
      {
        "id": 0,
        "name": "Credit Card",
        "amount": 5000.0
      }
    ],
    "total_assets": 50000.0,
    "total_liabilities": 5000.0,
    "net_worth": 45000.0
  }
  ```

### 2. Add Asset
- **URL**: `/add-asset`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "name": "Gold Mutual Fund",
    "amount": 20000.0
  }
  ```
- **Response Shape**:
  ```json
  {
    "status": "success"
  }
  ```

### 3. Add Liability
- **URL**: `/add-liability`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "name": "Car Loan",
    "amount": 350000.0
  }
  ```
- **Response Shape**:
  ```json
  {
    "status": "success"
  }
  ```

### 4. Delete Net Worth Item
- **URL**: `/delete-item`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "type": "asset",
    "id": 0
  }
  ```
- **Response Shape**:
  ```json
  {
    "status": "success"
  }
  ```
