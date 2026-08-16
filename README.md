# Pos_InventorySys

# InventorySys (POS + Inventory Management)

A Flask and SQLite web app that combines inventory tracking with a point-of-sale checkout system. Tracks stock by category, flags low inventory, and processes sales with automatic stock deduction.

## Features

### Inventory Management
- Dashboard overview
- Add / Edit items
- View all items grouped by category
- Low stock report
- Transaction log

### Point of Sale
- Checkout / cart system
- Automatic stock deduction on sale
- Sales history / receipt log

## Tech Stack
Flask SQLite Jinja2 HTML/CSS

## Usage
1. Visit `localhost:5000`
2. Add items via the Add Item form
3. Go to the POS/Checkout page to select items and complete a sale
4. Stock updates automatically after checkout
5. Check the Low Stock Report or Transactions log for history

## Setup
\`\`\`bash
git clone https://github.com/Cjyskiee/InventorySys.git
cd InventorySys
pip install -r requirements.txt
python app.py
\`\`\`
