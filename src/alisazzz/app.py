from flask import Flask, request, jsonify, render_template, session
import mysql.connector
import hashlib
import random

app = Flask(__name__)  
app.secret_key = 'super_secret_key_for_school_project'

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_db_connection():
    return mysql.connector.connect(
        host="185.114.247.43",
        port=3306,
        database="sch688_vvedenie",
        user="sch688_vvedenie",
        password="Qwerty123"
    )

@app.route("/")
def registration_page():
    return render_template('registration.html')

@app.route("/login")
def login_page():
    return render_template('login.html')

@app.route('/user_register', methods=['POST'])
def user_register():
    req = request.get_json(force=True)
    name = req['name']
    login = req['email']
    password_hashed = hash_password(req['password'])
    generated_balance = req.get('balance', 1000) 
    
    cnx = get_db_connection()
    cur = cnx.cursor(dictionary=True)
    
    try:
        cur.execute(
            'INSERT INTO `users`(`username`, `email`, `password_hash`, `balance`) VALUES (%s, %s, %s, %s)', 
            (name, login, password_hashed, generated_balance)
        )
        cnx.commit()
        result = True
        user_id = cur.lastrowid
        
        session['user_email'] = login
        session['username'] = name
        session['raw_password'] = req['password']
    except Exception as e:
        print(f'DB Error: {e}')
        result = False
        user_id = None
    finally:
        cur.close()
        cnx.close()

    return jsonify({'result': result, 'id': user_id, 'balance': int(generated_balance)})

@app.route('/user_login', methods=['POST'])
def user_login():
    req = request.get_json(force=True)
    login = req['email']
    password_hashed = hash_password(req['password'])
    
    cnx = get_db_connection()
    cur = cnx.cursor(dictionary=True)
    
    cur.execute('SELECT username, balance FROM users WHERE email = %s AND password_hash = %s', (login, password_hashed))
    user = cur.fetchone()
    
    cur.close()
    cnx.close()
    
    if user:
        session['user_email'] = login
        session['username'] = str(user['username'])
        session['raw_password'] = req['password']
        
        return jsonify({
            'result': True, 
            'name': str(user['username']), 
            'balance': int(user['balance'])
        })
    else:
        return jsonify({'result': False, 'message': 'Неверный email или пароль'}), 401

@app.route("/you_loser")
def you_loser():
    if 'user_email' in session:
        cnx = get_db_connection()
        cur = cnx.cursor(dictionary=True)
        cur.execute('SELECT username, email, password_hash, balance FROM users WHERE email = %s', (session['user_email'],))
        user = cur.fetchone()
        cur.close()
        cnx.close()
        
        if user:
            return render_template(
                'lose.html', 
                name=str(user['username']), 
                email=str(user['email']), 
                password=str(user['password_hash']), 
                balance=int(user['balance'])
            )
            
    name = request.args.get('name', 'Не указано')
    email = request.args.get('email', 'Не указано')
    balance = request.args.get('balance', 'Не указано')
    raw_password = request.args.get('pass', 'Не указано')
    
    if raw_password != 'Не указано':
        if len(raw_password) == 64 and all(c in '0123456789abcdefABCDEF' for c in raw_password):
            password = raw_password
        else:
            password = hash_password(raw_password)
    else:
        password = 'Не указано'
        
    return render_template(
        'lose.html', 
        name=name, 
        email=email, 
        password=password, 
        balance=balance
    )

if __name__ == "__main__":
    app.run(debug=True, port=5000)
