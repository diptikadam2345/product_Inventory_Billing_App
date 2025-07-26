from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# -------------------- Database Connection --------------------
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Dipti@123",
        database="product_db"
    )
    conn.autocommit = True
    return conn

# -------------------- Home --------------------
@app.route('/')
def homepage():
    return render_template('index.html')

# -------------------- Product CRUD --------------------
@app.route('/product')
def product():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('product.html', products=products)

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    quantity = request.form['quantity']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, description, price, quantity) VALUES (%s, %s, %s, %s)",
        (name, description, price, quantity)
    )
    cursor.close()
    conn.close()
    return redirect('/product')

@app.route('/edit_product/<int:id>', methods=['POST'])
def edit_product(id):
    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    quantity = request.form['quantity']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET name=%s, description=%s, price=%s, quantity=%s WHERE id=%s",
        (name, description, price, quantity, id)
    )
    cursor.close()
    conn.close()
    return redirect('/product')

@app.route('/delete_product/<int:id>')
def delete_product(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=%s", (id,))
    cursor.close()
    conn.close()
    return redirect('/product')

# -------------------- Inventory Management --------------------
@app.route('/inventory')
def inventory():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM inventory")
    inventory = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('inventory.html', inventory=inventory)

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    product_id = request.form['product_id']
    batch = request.form['batch']
    quantity = request.form['quantity']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        if not product:
            cursor.close()
            conn.close()
            return "Product ID does not exist. Please add the product first.", 400

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO inventory (product_id, batch, quantity) VALUES (%s, %s, %s)",
            (product_id, batch, quantity)
        )
        conn.commit()

    except mysql.connector.Error as err:
        print("Error updating inventory:", err)
        conn.rollback()
        return "Database error: " + str(err), 500
    finally:
        cursor.close()
        conn.close()

    return redirect('/inventory')

# -------------------- Billing System --------------------
@app.route('/billing')
def billing():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('billing.html', products=products)

@app.route('/generate_bill', methods=['POST'])
def generate_bill():
    product_ids = request.form.getlist('product_ids')
    quantities = request.form.getlist('quantities')
    discount = float(request.form.get('discount', 0))
    tax = float(request.form.get('tax', 0))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    total = 0
    bill_items = []

    try:
        for index, pid in enumerate(product_ids):
            if index >= len(quantities):
                continue

            qty_raw = quantities[index].strip()
            if not qty_raw:
                continue

            qty = int(qty_raw)
            if qty <= 0:
                continue

            cursor.execute("SELECT * FROM products WHERE id = %s", (pid,))
            product = cursor.fetchone()
            if not product:
                continue

            price = float(product['price'])  # ensure float
            subtotal = price * qty
            total += subtotal
            bill_items.append({
                 'name': product['name'],
                 'qty': qty,
                 'price': price,
                 'subtotal': subtotal
            })


        if not bill_items:
            return "No valid items selected for billing.", 400

        total_after_discount = total - (total * discount / 100)
        final_amount = total_after_discount + (total_after_discount * tax / 100)

        cursor.execute(
            "INSERT INTO bills (total, discount, tax, final_amount) VALUES (%s, %s, %s, %s)",
            (total, discount, tax, final_amount)
        )
        bill_id = cursor.lastrowid

        for item in bill_items:
            cursor.execute(
                "INSERT INTO bill_items (bill_id, product_name, quantity, price, subtotal) VALUES (%s, %s, %s, %s, %s)",
                (bill_id, item['name'], item['qty'], item['price'], item['subtotal'])
            )

        conn.commit()
        return render_template('bill_summary.html', items=bill_items, total=round(final_amount, 2))

    except Exception as e:
        import traceback
        traceback.print_exc()
        conn.rollback()
        return f"Internal error: {str(e)}", 500

    finally:
        cursor.close()
        conn.close()

# -------------------- ML Dashboard --------------------
@app.route('/ml-dashboard')
def ml_dashboard():
    return render_template('analytics.html')

# -------------------- Run App --------------------
if __name__ == '__main__':
    app.run(debug=True)
