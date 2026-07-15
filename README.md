# 🌿 Smart Farmer-to-Consumer Green Marketplace

An organic produce marketplace platform that connects regional farmers directly with consumers. By eliminating middlemen, farmers receive 100% of the sale value, and consumers purchase fresh, chemical-free vegetables at fair, transparent, and AI-predicted prices.

---

## 🚀 Key Features

### 1. Farmer Portal
* **Product Management**: List fresh vegetables, define prices, quantities, and units.
* **Dashboard Stats**: Real-time summary of active listings and order histories.
* **Authentication**: Password hashing using `cryptography` library for high security.

### 2. Consumer Experience
* **Fresh Catalog**: Dynamic listing of vegetables with advanced search, category filtration, and sorting (by newest, price, and alphabetical order).
* **Shopping Cart & Checkout**: Interactive shopping basket with quantity controls and a simulated UPI checkout flow.
* **Feedback System**: Customers can submit ratings and detailed reviews for products they purchase.

### 3. AI Price Prediction Engine
* Custom forecasting algorithm that calculates recommended prices using:
  * **Seasonality cosine waves** matching peak harvest periods.
  * **Demand & Supply multipliers** to simulate real market price fluctuations.
  * Deterministic market noise fluctuations for realism.
  * Visualized using interactive **Chart.js** 12-month trend graphs.

### 4. Aesthetics & Dark Mode
* Clean modern layout with glassmorphic cards and card hover micro-animations.
* **Dark/Light Mode Theme Toggle** built using CSS custom properties (variables) for smooth transitions.

---

## 🛠️ Tech Stack

* **Backend**: Python 3.12 (Flask Framework)
* **Database**: SQLite (SQLAlchemy ORM)
* **Frontend**: HTML5, Vanilla CSS3 (Custom styles system), Vanilla JavaScript (ES6)
* **Visualization**: Chart.js (Interactive UI graphs)
* **Security**: Cryptography (pbkdf2 password hashing)

---

## 📥 Setup & Run Instructions

Follow these steps to set up and run the application locally on Windows:

### 1. Open Terminal & Navigate to Project
```powershell
cd "c:\Users\lokes\OneDrive\Desktop\Lokesh.ff\Lokesh"
```

### 2. Activate Python Virtual Environment
* **PowerShell**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
* **Command Prompt (CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

### 3. Reset & Seed Database (Optional - Starts Blank)
If you want to clear the database and start fresh:
```bash
python seed.py
```
*(Seeding initializes pre-registered testing accounts and leaves the products list blank so you can test adding items).*

### 4. Run the Application
Start the local development server:
```bash
python app.py
`
---

## 📂 Project Structure

```
Lokesh/
│
├── app.py                                               # Main Flask server and routes controller
├── models.py                                           # SQLAlchemy database schemas (Farmer, Customer, Product, Order, etc.)
├── config.py                                            # App configuration keys & paths
├── prediction_engine.py                                 # AI price prediction algorithms
├── recommender.py                                  # Customer purchase recommendation logic
├── seed.py                                          # Database initialization and mock data seeder
├── test_app.py                                       # Automated unit tests suite
├── requirements.txt                                    # Python dependency manifest
│
├── static/
│   ├── css/style.css                                       # Core styles, glassmorphic themes, and animations
│   └── js/main.js                                           # Theme toggle handler and search queries
│
└── templates/                                               # HTML layout templates (base, index, products, dashboard, etc.)
```
## 🚀 Live Demo
https://smart-farmer-nwfy.onrender.com


