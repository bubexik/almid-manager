from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from io import BytesIO
import csv

app = Flask(__name__)
CORS(app)
DATABASE = 'almid.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles
                (id INTEGER PRIMARY KEY, plate TEXT, model TEXT, brand TEXT, year INTEGER, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS drivers
                (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, license TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                (id INTEGER PRIMARY KEY, client TEXT, from_location TEXT, to_location TEXT, 
                 date TEXT, driver_id INTEGER, vehicle_id INTEGER, status TEXT, cost REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                (id INTEGER PRIMARY KEY, type TEXT, number TEXT, date TEXT, 
                 amount REAL, description TEXT, file_path TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM vehicles')
    vehicles_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM drivers')
    drivers_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM orders WHERE status="completed"')
    completed_orders = c.fetchone()[0]
    c.execute('SELECT SUM(cost) FROM orders WHERE status="completed"')
    revenue = c.fetchone()[0] or 0
    conn.close()
    return jsonify({
        'vehicles': vehicles_count,
        'drivers': drivers_count,
        'completed_orders': completed_orders,
        'revenue': revenue
    })

@app.route('/api/vehicles', methods=['GET', 'POST'])
def vehicles():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if request.method == 'POST':
        data = request.get_json()
        c.execute('INSERT INTO vehicles (plate, model, brand, year, status) VALUES (?, ?, ?, ?, ?)',
                 (data['plate'], data['model'], data['brand'], data['year'], 'active'))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        c.execute('SELECT * FROM vehicles')
        vehicles = [{'id': row[0], 'plate': row[1], 'model': row[2], 'brand': row[3], 'year': row[4], 'status': row[5]} for row in c.fetchall()]
        conn.close()
        return jsonify(vehicles)

@app.route('/api/drivers', methods=['GET', 'POST'])
def drivers():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if request.method == 'POST':
        data = request.get_json()
        c.execute('INSERT INTO drivers (name, phone, license, status) VALUES (?, ?, ?, ?)',
                 (data['name'], data['phone'], data['license'], 'active'))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        c.execute('SELECT * FROM drivers')
        drivers = [{'id': row[0], 'name': row[1], 'phone': row[2], 'license': row[3], 'status': row[4]} for row in c.fetchall()]
        conn.close()
        return jsonify(drivers)

@app.route('/api/orders', methods=['GET', 'POST'])
def orders():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if request.method == 'POST':
        data = request.get_json()
        c.execute('INSERT INTO orders (client, from_location, to_location, date, driver_id, vehicle_id, status, cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                 (data['client'], data['from'], data['to'], data['date'], data['driver_id'], data['vehicle_id'], 'pending', data['cost']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        c.execute('SELECT * FROM orders')
        orders = [{'id': row[0], 'client': row[1], 'from': row[2], 'to': row[3], 'date': row[4], 'driver_id': row[5], 'vehicle_id': row[6], 'status': row[7], 'cost': row[8]} for row in c.fetchall()]
        conn.close()
        return jsonify(orders)

@app.route('/api/documents', methods=['GET', 'POST'])
def documents():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if request.method == 'POST':
        data = request.get_json()
        c.execute('INSERT INTO documents (type, number, date, amount, description, file_path) VALUES (?, ?, ?, ?, ?, ?)',
                 (data['type'], data['number'], data['date'], data['amount'], data['description'], data['file_path']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        c.execute('SELECT * FROM documents')
        documents = [{'id': row[0], 'type': row[1], 'number': row[2], 'date': row[3], 'amount': row[4], 'description': row[5]} for row in c.fetchall()]
        conn.close()
        return jsonify(documents)

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM orders')
    orders = c.fetchall()
    conn.close()
    
    si = BytesIO()
    with open('/tmp/orders.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Klient', 'Z', 'Do', 'Data', 'Kierowca', 'Pojazd', 'Status', 'Koszt'])
        for order in orders:
            writer.writerow(order)
    
    return send_file('/tmp/orders.csv', as_attachment=True, download_name='zlecenia.csv')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
