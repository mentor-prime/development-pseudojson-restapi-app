from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import jwt
import datetime

app = Flask(__name__)
app.secret_key = 'echo1234567890'
jwt_secret = 'your_jwt_secret_key'  # Use a secure key in a real application

# MongoDB setup
mongo_uri = "mongodb+srv://admin:admin@cluster0.6px5a.mongodb.net/"
client = MongoClient(mongo_uri)
db = client.postman01
products = db.products02

# In-memory token blacklist
blacklisted_tokens = set()

def token_is_blacklisted(token):
    return token in blacklisted_tokens

@app.route('/')
def home():
    return render_template('index9.html')


@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # Redirect to login if not logged in
    token = session.get('token')
    return render_template('dashboard.html', token=token)  # Pass token to the template


@app.route('/products', methods=['GET'])
def get_products():
    skip = int(request.args.get('skip', 0))  # Default to 0 if not provided
    limit = int(request.args.get('limit', 100))  # Default to 30 if not provided

    all_products = list(products.find().sort("id", 1).skip(skip).limit(limit))  # Sort by 'id' in ascending order
    for product in all_products:
        product['_id'] = str(product['_id'])
    total_count = products.count_documents({})
    return jsonify({"products": all_products, "total": total_count})


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
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization header missing or invalid"}), 401

    token = auth_header.split(' ')[1]
    if token_is_blacklisted(token):
        return jsonify({"error": "Token is blacklisted"}), 401

    try:
        jwt.decode(token, jwt_secret, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

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
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization header missing or invalid"}), 401

    token = auth_header.split(' ')[1]
    if token_is_blacklisted(token):
        return jsonify({"error": "Token is blacklisted"}), 401

    try:
        jwt.decode(token, jwt_secret, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    result = products.delete_one({'id': id})
    if result.deleted_count:
        return jsonify({"id": id})
    else:
        return jsonify({"error": "Product not found"}), 404


@app.route('/products/category/<category_name>', methods=['GET'])
def get_products_by_category(category_name):
    skip = int(request.args.get('skip', 0))
    limit = int(request.args.get('limit', 100))

    category_products = products.find({'category': {'$regex': category_name, '$options': 'i'}}).skip(skip).limit(limit)
    result = []
    for product in category_products:
        product['_id'] = str(product['_id'])
        result.append(product)

    total_count = products.count_documents({'category': {'$regex': category_name, '$options': 'i'}})
    return jsonify({'products': result, 'total': total_count, 'category': category_name})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            token = jwt.encode({
                'user': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }, jwt_secret, algorithm='HS256')
            session['logged_in'] = True
            session['token'] = token  # Store the token in the session
            return jsonify({"token": token})  # Return the token in the response
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    return render_template('login.html')  # Display the login page for GET requests

@app.route('/logout')
def logout():
    token = session.pop('token', None)
    session.pop('logged_in', None)
    if token:
        blacklisted_tokens.add(token)
    return redirect(url_for('home'))

@app.route('/api/check_token', methods=['GET'])
def check_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Authorization header missing or invalid"}), 401

    token = auth_header.split(' ')[1]
    if token_is_blacklisted(token):
        return jsonify({"error": "Token is blacklisted"}), 401

    try:
        jwt.decode(token, jwt_secret, algorithms=['HS256'])
        return jsonify({"message": "Token is valid"})
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

# @app.route('/add_product')
@app.route('/manage_products')
def add_product_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # Redirect to login if not logged in
    token = session.get('token')
    return render_template('manage_products.html', token=token)  # Pass token to the template

@app.route('/delete_product')
def delete_product_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # Redirect to login if not logged in
    token = session.get('token')
    return render_template('delete_product.html', token=token)  # Pass token to the template

if __name__ == '__main__':
    app.run(debug=True)
