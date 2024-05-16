from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = 'echo1234567890'

# MongoDB setup
mongo_uri = "mongodb+srv://admin:admin@cluster0.6px5a.mongodb.net/"
client = MongoClient(mongo_uri)
db = client.postman01
products = db.products02

@app.route('/')
def home():
    return render_template('index8.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('dashboard.html')  # Render the dashboard page

@app.route('/products', methods=['GET'])
def get_products():
    all_products = list(products.find())
    for product in all_products:
        product['_id'] = str(product['_id'])
    return jsonify(all_products)

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = products.find_one({'id': id})
    if product:
        product['_id'] = str(product['_id'])
        return jsonify(product)
    else:
        return jsonify({"error": "Product not found"}), 404

@app.route('/products', methods=['POST'])
def add_product():
    product = request.json
    if not product.get('id'):
        return jsonify({"error": "ID is required"}), 400
    if products.find_one({'id': product['id']}):
        return jsonify({"error": "Product with this ID already exists"}), 409
    result = products.insert_one(product)
    product['_id'] = str(result.inserted_id)
    return jsonify(product), 201

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    update_data = request.json
    result = products.update_one({'id': id}, {'$set': update_data})
    if result.modified_count:
        return jsonify({"id": id})
    else:
        return jsonify({"error": "Product not updated"}), 404

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    result = products.delete_one({'id': id})
    if result.deleted_count:
        return jsonify({"id": id})
    else:
        return jsonify({"error": "Product not found"}), 404

@app.route('/products/category/<category_name>', methods=['GET'])
def get_products_by_category(category_name):
    category_products = products.find({'category': category_name})
    result = [product for product in category_products if product['category'].lower() == category_name.lower()]
    for product in result:
        product['_id'] = str(product['_id'])
    return jsonify({'products': result, 'total': len(result), 'category': category_name})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin@postman123!':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))  # Redirect to the dashboard page after login
        else:
            return 'Invalid credentials', 401
    return render_template('login.html')  # Display the login page for GET requests

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
