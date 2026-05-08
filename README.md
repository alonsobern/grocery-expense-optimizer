# Grocery & Expense Optimizer

A professional, full-stack Flask application designed to track grocery expenses, manage inventory, and provide actionable financial insights through a modern analytics dashboard.

![Dashboard Preview](https://via.placeholder.com/800x450.png?text=Grocery+Analytics+Dashboard+Preview)

## 🚀 Features

### 📊 Advanced Analytics Dashboard

- **KPI Tracking**: Real-time monitoring of total spending, average purchase price, and item counts.
- **Dynamic Visualization**: Interactive charts powered by Chart.js showing spending trends over time and category distributions.
- **Filtered Reports**: Comprehensive filtering by date range, store, and category to drill down into spending habits.

### 🛡️ Robust Data Integrity

- **Composite Validation**: Supports products with identical names across different categories (e.g., "Apple" in "Fruits" vs. "Frozen") while preventing duplicates within the same category.
- **Strict Constraints**: Enforces `NOT NULL`, `UNIQUE`, and `CHECK` constraints at the SQLite level to ensure high-quality data.
- **Actionable Feedback**: Premium inline error messaging system provides immediate feedback without intrusive browser alerts.

### ☁️ Deployment Ready (Render Optimized)

- **Zero-Config Startup**: Automatically initializes the SQLite database and directory structure on first run.
- **Smart Seeding**: Automatically populates the application with 150+ realistic purchase records on fresh deployments to demonstrate analytics capabilities instantly.
- **Production Grade**: Pre-configured for `Gunicorn` and Linux-based cloud environments.

## 🛠️ Tech Stack

- **Backend**: Python 3.x, Flask
- **Database**: SQLite3 with Foreign Key enforcement
- **Frontend**: HTML5, Vanilla CSS3 (Modern Glassmorphism UI), JavaScript (ES6)
- **Visualization**: Chart.js
- **Deployment**: Render / Gunicorn

## 🏁 Getting Started

### Prerequisites

- Python 3.8+
- Pip (Python package manager)

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/alonsobern/grocery-optimizer.git
   cd grocery-optimizer
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python run.py
   ```
   The app will be available at `http://127.0.0.1:5000`.

## 📁 Project Structure

```text
├── app/
│   ├── static/          # CSS, JS, and Images
│   ├── templates/       # Jinja2 HTML Templates
│   ├── analytics.py     # Data processing and reporting logic
│   ├── db.py            # Database CRUD and Initialization
│   ├── routes.py        # Flask view controllers
│   └── __init__.py      # App factory
├── database/
│   ├── schema.sql       # Database table definitions
│   └── grocery.db       # SQLite Database (auto-generated)
├── requirements.txt     # Production dependencies
├── run.py               # Application entry point
└── seed_data.py         # Standalone manual seeding script
```

## 📈 Demo Data

Upon first startup in a new environment, the application will automatically seed itself with a synthetic dataset containing:

- **Stores**: Whole Foods, Trader Joe's, Costco, etc.
- **History**: 150+ purchases spread over the last 6 months.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
