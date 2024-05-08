from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)

# MongoDB setup
mongo_uri = "mongodb+srv://admin:admin@cluster0.6px5a.mongodb.net/"
client = MongoClient(mongo_uri)
db = client.postman01
products = db.products

@app.route('/products', methods=['GET'])
def get_products():
    all_products = list(products.find())
    for product in all_products:
        product['_id'] = str(product['_id'])
    return jsonify(all_products)

@app.route('/products/<id>', methods=['GET'])
def get_product(id):
    product = products.find_one({'_id': ObjectId(id)})
    if product:
        product['_id'] = str(product['_id'])
        return jsonify(product)
    else:
        return jsonify({"error": "Product not found"}), 404

@app.route('/products', methods=['POST'])
def add_product():
    product = request.json
    result = products.insert_one(product)
    product['_id'] = str(result.inserted_id)
    return jsonify(product), 201

@app.route('/products/<id>', methods=['PUT'])
def update_product(id):
    update_data = request.json
    result = products.update_one({'_id': ObjectId(id)}, {'$set': update_data})
    if result.modified_count:
        return jsonify({"_id": id})
    else:
        return jsonify({"error": "Product not updated"}), 404

@app.route('/products/<id>', methods=['DELETE'])
def delete_product(id):
    result = products.delete_one({'_id': ObjectId(id)})
    if result.deleted_count:
        return jsonify({"_id": id})
    else:
        return jsonify({"error": "Product not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
