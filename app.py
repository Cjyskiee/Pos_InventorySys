from flask import Flask, render_template, redirect, request, url_for
from flask import wrappers
from flask import session
import sqlite3
import datetime

datestamp = datetime.datetime.now().strftime("%Y-%m-%d")
app = Flask(__name__)
app.secret_key = "something-secret" 
CATEGORIES = ["Canned Goods", "Beverages", "Biscuits", "Meat", "Fruits"]

def inventory_innit():



    conn = sqlite3.connect("InventorySys.db")
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS inventory(
                    id INTEGER PRIMARY KEY,
                    Item TEXT,
                    Category TEXT,
                    Quantity INTEGER,
                    Price REAL,
                    reorder_reporter INTEGER,
                    timestamp INTEGER
                )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS sales(
                    id INTEGER PRIMARY KEY,
                    total REAL,
                    timestamp INTEGER
                )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS sales_items(
                    id INTEGER PRIMARY KEY,
                    sale_id INTEGER,
                    item_id INTEGER,
                    Quantity_Sold INTEGER,
                    Price_at_Sale REAL,
                    FOREIGN KEY (sale_id) REFERENCES sales(id)
                    FOREIGN KEY (item_id) REFERENCES inventory(id)
                )""")

    conn.commit()


@app.route("/")
def home():
    return redirect("/Inventory_homepage")


@app.route("/pos_homepage", methods=["GET", "POST"])
def POS_Homepage():

    conn = sqlite3.connect("InventorySys.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()


    cur.execute("SELECT * FROM inventory ORDER BY Category, Item")
    viewCat = cur.fetchall()

    cart = session.get("cart", [])

    cart_details = []
    cart_total = 0

    for cart_item in cart:
        cur.execute("SELECT * FROM inventory WHERE id = ?", (cart_item["item_id"],))
        item = cur.fetchone()

        if item:
            subtotal = item["Price"] * cart_item["quantity"]
            cart_total += subtotal
            cart_details.append({
                "name": item["Item"],
                "quantity": cart_item["quantity"],
                "subtotal": subtotal
            })

    if request.method == "POST":

        req_Category = request.form.get("Category")
        if not req_Category or not req_Category.strip():
            return render_template("pos_homepage.html", error="Category must be fill up")

        cur.execute("SELECT * FROM inventory WHERE Category = ?", (req_Category,))
        view_by_Cat = cur.fetchall()

        if not view_by_Cat:
            conn.close()
            return render_template("pos_homepage.html", error="No items available")
        return render_template("pos_homepage.html", viewCategory=view_by_Cat,)

    conn.close()
    return render_template("pos_homepage.html", viewCategory=viewCat, cart=cart_details, cart_total=cart_total)

@app.route("/pos_add", methods=["POST", "GET"])
def POS_AddCart():
    if request.method == "POST":
        req_item_id = int(request.form.get("item_id"))
        req_quantity = int(request.form.get("quantity"))

        if "cart" not in session:
            session["cart"] = []

        found = False
        for cart_item in session["cart"]:
            if cart_item["item_id"] == req_item_id:
                cart_item["quantity"] += req_quantity
                found = True
                break

        if not found:
            session["cart"].append({
                        "item_id" : req_item_id, 
                        "quantity" : req_quantity
            })

        session.modified = True
    return redirect("/pos_homepage")

@app.route("/pos_checkout", methods=["POST", "GET"])
def Pos_Checkout():
    conn = sqlite3.connect("InventorySys.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cart_total = 0

    cart = session.get("cart", [])

    if not cart:
        conn.close()
        return render_template("pos_homepage.html", error="No Items in Cart")
    else:

        for cart_checkoutItem in cart:
            cur.execute("SELECT * FROM inventory WHERE id = ?", (cart_checkoutItem["item_id"],))
            item = cur.fetchone()
            cart_total += item["Price"] * cart_checkoutItem["quantity"]

        cur.execute("INSERT INTO sales (total, timestamp) VALUES (?, ?)", (cart_total, datestamp,))
        new_saleID = cur.lastrowid

        for cart_saveToSales_Item in cart:
            cur.execute("SELECT Price FROM inventory WHERE id = ?", (cart_saveToSales_Item["item_id"],))
            price = cur.fetchone()["Price"]
            cur.execute("INSERT INTO sales_items (sale_id, item_id, Quantity_Sold, Price_at_Sale) VALUES (?, ?, ?, ?)", (new_saleID, cart_saveToSales_Item["item_id"], cart_saveToSales_Item["quantity"], price,))
            cur.execute("UPDATE inventory SET Quantity = Quantity - ? WHERE id = ?", (cart_saveToSales_Item["quantity"], cart_saveToSales_Item["item_id"],))

        session["cart"] = []

        conn.commit()
        conn.close()

        return redirect("/pos_homepage")

@app.route("/Inventory_homepage", methods=["GET", "POST"])
def Inventory_Homepage():

    conn = sqlite3.connect("InventorySys.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM inventory")
    all_Item = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT Category) FROM inventory")
    all_categories = cur.fetchone()[0]

    cur.execute("SELECT SUM(Quantity <= reorder_reporter) FROM inventory")
    sum_lowStock = cur.fetchone()[0]


    cur.execute("SELECT SUM(Quantity * Price) FROM inventory")
    sum_totalValue = cur.fetchone()[0]



    return render_template("dashboard.html", ALL_ITEMS=all_Item, ALL_CATEGORIES=all_categories, SUM_LOWSTOCK=sum_lowStock, SUM_TOTALVALUE=sum_totalValue, )


@app.route("/add_items", methods=["POST", "GET"])
def AddItems():

    if request.method == "POST":

        req_Item = request.form.get("Item")
        if not req_Item or not req_Item.strip():
            return render_template("add_items.html", error="Item must be fill up")
        req_Category = request.form.get("Category")
        if not req_Category or not req_Category.strip():
            return render_template("add_items.html", error="Category must be fill up")
        try:
            req_Quantity = int(request.form.get("Quantity"))
            req_Price = float(request.form.get("Price"))
            req_reorder_reporter = int(request.form.get("reorder_reporter"))
        except ValueError:
            conn.close()
            return render_template("add_items.html", error="Invalid Input!")
    
        conn = sqlite3.connect("InventorySys.db")
        cur = conn.cursor()



        cur.execute("SELECT * FROM inventory WHERE Category = ? AND Item = ?", (req_Category, req_Item))
        Category_Item_Exist = cur.fetchone()

        if Category_Item_Exist:
            conn.close()
            return render_template("add_items.html", error="Catergory or Item already exist!!")

        cur.execute("INSERT INTO inventory (Item, Category, Quantity, Price, reorder_reporter, timestamp) VALUES (?,?,?,?,?,?)", (req_Item, req_Category, req_Quantity, req_Price, req_reorder_reporter, datestamp,))
        conn.commit()
        conn.close()

        return redirect("/Inventory_homepage")
        
    return render_template("add_items.html", categories=CATEGORIES)


@app.route("/View_All", methods=["GET", "POST"])
def ViewAll():
    conn = sqlite3.connect("InventorySys.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if request.method == "POST":

        req_Category = request.form.get("Category")
        if not req_Category or not req_Category.strip():
            conn.close()
            return render_template("add_items.html", error="Category must be fill up")


        cur.execute("SELECT * FROM inventory WHERE Category = ?", (req_Category,))
        view_BY_Category = cur.fetchall()

        if not view_BY_Category:
            conn.close()
            return render_template("View_All.html", error="No Items available.")
        return render_template("View_All.html",  viewItem_Category=view_BY_Category)

    cur.execute("SELECT * FROM inventory ORDER BY Category, Item")
    all_items = cur.fetchall()
    
    conn.close()
    return render_template("View_All.html", viewItem_Category=all_items)

@app.route("/edit/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):

    conn = sqlite3.connect("InventorySys.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM inventory WHERE id = ?", (item_id,))
    Item_select_edit = cur.fetchone()

    if request.method == "POST":

        edit_Item = request.form.get("Item")
        if not edit_Item or not edit_Item.strip():
            conn.close()
            return render_template("edit_item.html", select_edit_item=Item_select_edit, error = "Item must be fill up")
        try:
            edit_Quantity = int(request.form.get("Quantity"))
            edit_Price = float(request.form.get("Price"))
            edit_reorder_reporter = int(request.form.get("reorder_reporter"))
        except ValueError:
            conn.close()
            return render_template("edit_item.html", select_edit_item=Item_select_edit,  error="Invalid Input!")

        cur.execute("UPDATE inventory SET item = ?, Quantity = ?, Price = ?, reorder_reporter = ? WHERE id = ?", (edit_Item, edit_Quantity, edit_Price, edit_reorder_reporter, item_id,))
        conn.commit()
        conn.close()
        return redirect("/View_All")

    conn.close() 
    return render_template("edit_item.html", select_edit_item=Item_select_edit)
    

@app.route("/Items_Reorder", methods=["GET", "POST"])
def items_reorder():
    conn = sqlite3.connect("InventorySys.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM inventory WHERE (Quantity <= reorder_reporter)")
    view_reorders = cur.fetchall()

    if not view_reorders:
        conn.close()
        return render_template("/dashboard.html", error="No low Stock available.")

    if request.method == "POST":
    
            req_Category = request.form.get("Category")
            if not req_Category or not req_Category.strip():
                conn.close()
                return render_template("dashboard.html", error="Category must be fill up")
    
    
            cur.execute("SELECT * FROM inventory WHERE Category = ? AND (Quantity <= reorder_reporter)", (req_Category,))
            view_BY_Category = cur.fetchall()


            if not view_BY_Category:
                conn.close()
                return render_template("Items_Reorder.html", error="No Items available.")
            return render_template("Items_Reorder.html",  VIEW_ALL_REORDERS=view_BY_Category,)
    
    conn.close()
    return render_template("Items_Reorder.html", VIEW_ALL_REORDERS=view_reorders,)

@app.route("/Transaction$", methods=["POST", "GET"])
def transaction():

    conn = sqlite3.connect("InventorySys.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    week_offset = request.args.get("week", 0, type=int)


    if request.method == "POST":
        req_Category = request.form.get("Category")
        if not req_Category or not req_Category.strip():
            conn.close()
            return render_template("Transaction$.html", error="Category must be fill up")

        cur.execute("SELECT sales_items.*, inventory.Item, inventory.Category, sales.timestamp FROM sales_items JOIN inventory ON sales_items.item_id = inventory.id JOIN sales_items.sale_id = sales.id WHERE inventory.Category = ? AND strftime('%Y-%W', sales.timestamp) = strftime('%Y-%W', 'now', ? || ' days')", (req_Category, week_offset * 7,))
        transactions_BY_Category = cur.fetchall()

        if not transactions_BY_Category:
            conn.close()
            return render_template("Transaction$.html", error="No Items available.")
        conn.close()
        return render_template("Transaction$.html",  Transaction_Category=transactions_BY_Category, week_offset=week_offset)

    cur.execute("SELECT sales_items.*, inventory.Item, inventory.Category, sales.timestamp FROM sales_items JOIN inventory ON sales_items.item_id = inventory.id  JOIN sales ON sales_items.sale_id = sales.id WHERE strftime('%Y-%W', sales.timestamp) = strftime('%Y-%W', 'now', ? || ' days') ORDER BY inventory.Category", (week_offset * 7,))
    all_Transactions = cur.fetchall()
    conn.close()

    return render_template("Transaction$.html", Transaction_Item_Category=all_Transactions, week_offset=week_offset)
        
if __name__ == "__main__":
    inventory_innit()
    app.run(debug=True)
