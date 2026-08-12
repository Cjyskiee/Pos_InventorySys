from flask import Flask, render_template, redirect, request, url_for
from flask import wrappers
from flask import sessions
import sqlite3
import datetime


app = Flask(__name__)

CATEGORIES = ["Canned Goods", "Beverages", "Biscuits", "Meat", "Fruits"]

def inventory_innit():



    conn = sqlite3.connect("InventorySys.db")
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
    conn.commit()


@app.route("/")
def home():
    return redirect("/homepage")

@app.route("/homepage", methods=["GET", "POST"])
def homepage():

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

    datestamp = datetime.datetime.now().strftime("%m/%d/%y")
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

        return redirect("/homepage")
        
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
        
if __name__ == "__main__":
    inventory_innit()
    app.run(debug=True)
