# This creates a basic eCommerce website using Flask and SQLite
# Zachary Rubin, zrubin@rtc.edu
# CNA 340 Spring 2019

from flask import *
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'cna340'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_login_details():
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        if 'email' not in session:
            logged_in = False
            first_name = ''
            no_of_items = 0
        else:
            logged_in = True
            cur.execute("SELECT userId, firstName FROM users WHERE email = '" + session['email'] + "'")
            user_id, first_name = cur.fetchone()
            cur.execute("SELECT count(productId) FROM kart WHERE userId = " + str(user_id))
            no_of_items = cur.fetchone()[0]
    conn.close()
    return (logged_in, first_name, no_of_items)

@app.route("/")
def root():
    logged_in, first_name, no_of_items = get_login_details()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        # Show last product added
        cur.execute('SELECT productId, name, price, description, image, stock FROM products ORDER BY productId DESC LIMIT 1 ')
        # Show all items
        #cur.execute('SELECT productId, name, price, description, image, stock FROM products LIMIT 1')
        item_data = cur.fetchall()
        # Show an error instead of the categories
        category_data = [(-1,"Error")]
        # Show all categories
        cur.execute('SELECT categoryId, name FROM categories')
        category_data = cur.fetchall()
    item_data = parse(item_data)
    return render_template('home.html', itemData=item_data, loggedIn=logged_in, firstName=first_name, noOfItems=no_of_items, categoryData=category_data)

@app.route("/add")
def admin():
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT categoryId, name FROM categories")
        categories = cur.fetchall()
    conn.close()
    return render_template('add.html', categories=categories)

@app.route("/addItem", methods=["GET", "POST"])
def addItem():
    if request.method == "POST":
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        categoryId = int(request.form['category'])

        #Upload image
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        imagename = filename
        with sqlite3.connect('database.db') as conn:
            try:
                cur = conn.cursor()
                cur.execute('''INSERT INTO products (name, price, description, image, stock, categoryId) VALUES (?, ?, ?, ?, ?, ?)''', (name, price, description, imagename, stock, categoryId))
                conn.commit()
                msg="Added successfully"
            except:
                msg="Error occured"
                conn.rollback()
        conn.close()
        print(msg)
        return redirect(url_for('root'))

@app.route("/displayCategory")
def displayCategory():
    logged_in, first_name, no_of_items = get_login_details()
    category_id = request.args.get("categoryId")
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT products.productId, products.name, products.price, products.image, categories.name FROM products, categories WHERE products.categoryId = categories.categoryId AND categories.categoryId = " + category_id)
        data = cur.fetchall()
    conn.close()
    category_name = data[0][4]
    data = parse(data)
    return render_template('displayCategory.html', data=data, loggedIn=logged_in, firstName=first_name,
                           noOfItems=no_of_items, categoryName=category_name)


@app.route("/account/profile")
def profile_home():
    if 'email' not in session:
        return redirect(url_for('root'))
    logged_in, first_name, no_of_items = get_login_details()
    return render_template("profileHome.html", loggedIn=logged_in, firstName=first_name, noOfItems=no_of_items)

@app.route("/account/profile/edit")
def edit_profile():
    if 'email' not in session:
        return redirect(url_for('root'))
    logged_in, first_name, no_of_items = get_login_details()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId, email, first_name, lastName, address1, address2, zipcode, city, state, country, phone FROM users WHERE email = '" + session['email'] + "'")
        profile_data = cur.fetchone()
    conn.close()
    return render_template("editProfile.html", profileData=profile_data, loggedIn=logged_in, firstName=first_name, noOfItems=no_of_items)

@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def change_password():
    if 'email' not in session:
        return redirect(url_for('login_form'))
    if request.method == "POST":
        old_password = request.form['oldpassword']
        old_password = hashlib.md5(old_password.encode()).hexdigest()
        new_password = request.form['newpassword']
        new_password = hashlib.md5(new_password.encode()).hexdigest()
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId, password FROM users WHERE email = '" + session['email'] + "'")
            user_id, password = cur.fetchone()
            if (password == old_password):
                try:
                    cur.execute("UPDATE users SET password = ? WHERE userId = ?", (new_password, user_id))
                    conn.commit()
                    msg="Changed successfully"
                except:
                    conn.rollback()
                    msg = "Failed"
                return render_template("changePassword.html", msg=msg)
            else:
                msg = "Wrong password"
        conn.close()
        return render_template("changePassword.html", msg=msg)
    else:
        return render_template("changePassword.html")

@app.route("/updateProfile", methods=["GET", "POST"])
def update_profile():
    if request.method == 'POST':
        email = request.form['email']
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        with sqlite3.connect('database.db') as con:
                try:
                    cur = con.cursor()
                    cur.execute('UPDATE users SET firstName = ?, lastName = ?, address1 = ?, address2 = ?, zipcode = ?, city = ?, state = ?, country = ?, phone = ? WHERE email = ?', (first_name, last_name, address1, address2, zipcode, city, state, country, phone, email))

                    con.commit()
                    msg = "Saved Successfully"
                except:
                    con.rollback()
                    msg = "Error occured"
        con.close()
        return redirect(url_for('edit_profile'))

@app.route("/loginForm")
def login_form():
    # Uncomment to enable logging in and registration
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', error='')

@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid UserId / Password'
            return render_template('login.html', error=error)

@app.route("/productDescription")
def product_description():
    logged_in, first_name, no_of_items = get_login_details()
    product_id = request.args.get('productId')
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT productId, name, price, description, image, stock FROM products WHERE productId = ' + product_id)
        productData = cur.fetchone()
    conn.close()
    return render_template("productDescription.html", data=productData, loggedIn=logged_in, firstName=first_name,
                           noOfItems=no_of_items)

@app.route("/addToCart")
def add_to_cart():
    if 'email' not in session:
        return redirect(url_for('login_form'))
    else:
        product_id = int(request.args.get('productId'))
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = '" + session['email'] + "'")
            user_id = cur.fetchone()[0]
            try:
                cur.execute("INSERT INTO kart (userId, productId) VALUES (?, ?)", (user_id, product_id))
                conn.commit()
                msg = "Added successfully"
            except:
                conn.rollback()
                msg = "Error occured"
        conn.close()
        return redirect(url_for('root'))

@app.route("/cart")
def cart():
    if 'email' not in session:
        return redirect(url_for('login_form'))
    logged_in, first_name, no_of_items = get_login_details()
    email = session['email']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        user_id = cur.fetchone()[0]
        cur.execute("SELECT products.productId, products.name, products.price, products.image FROM products, kart WHERE products.productId = kart.productId AND kart.userId = " + str(user_id))
        products = cur.fetchall()
    total_price = 0
    for row in products:
        total_price += row[2]
    return render_template("cart.html", products = products, totalPrice=total_price, loggedIn=logged_in, firstName=first_name, noOfItems=no_of_items)

@app.route("/removeFromCart")
def remove_from_cart():
    if 'email' not in session:
        return redirect(url_for('login_form'))
    email = session['email']
    product_id = int(request.args.get('productId'))
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE email = '" + email + "'")
        user_id = cur.fetchone()[0]
        try:
            cur.execute("DELETE FROM kart WHERE user_id = " + str(user_id) + " AND productId = " + str(product_id))
            conn.commit()
            msg = "removed successfully"
        except:
            conn.rollback()
            msg = "error occured"
    conn.close()
    return redirect(url_for('root'))

@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))

def is_valid(email, password):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('SELECT email, password FROM users')
    data = cur.fetchall()
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False


@app.route("/checkout", methods=['GET','POST'])
def payment():
    if 'email' not in session:
        return redirect(url_for('login_form'))
    logged_in, first_name, no_of_items = get_login_details()
    email = session['email']

    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        user_id = cur.fetchone()[0]
        cur.execute("SELECT products.productId, products.name, products.price, products.image FROM products, kart WHERE products.productId = kart.productId AND kart.userId = " + str(user_id))
        products = cur.fetchall()
    total_price = 0
    for row in products:
        total_price += row[2]
        print(row)
        cur.execute("INSERT INTO Orders (userId, productId) VALUES (?, ?)", (user_id, row[0]))
    cur.execute("DELETE FROM kart WHERE userId = " + str(user_id))
    conn.commit()

        

    return render_template("checkout.html", products = products, totalPrice=total_price, loggedIn=logged_in, firstName=first_name, noOfItems=no_of_items)

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        #Parse form data    
        password = request.form['password']
        email = request.form['email']
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']

        with sqlite3.connect('database.db') as con:
            try:
                cur = con.cursor()
                cur.execute('INSERT INTO users (password, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (hashlib.md5(password.encode()).hexdigest(), email, first_name, last_name, address1, address2, zipcode, city, state, country, phone))

                con.commit()

                msg = "Registered Successfully"
            except:
                con.rollback()
                msg = "Error occured"
        con.close()
        return render_template("login.html", error=msg)

@app.route("/registrationForm")
def registration_form():
    return render_template("register.html")

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans

if __name__ == '__main__':
    app.run(debug=True)
