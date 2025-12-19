from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_strong_secret_12345'  # यहाँ अपना मजबूत पासवर्ड डालें
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///activations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Activation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    android_id = db.Column(db.String(50), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=False)
    expiry_date = db.Column(db.Date, nullable=True)

with app.app_context():
    db.create_all()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'your_password_123':  # यहाँ अपना पासवर्ड डालें
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
    return '''
    <h1>Login - RP KRISHNATREYA</h1>
    <form method="post">
        Username: <input type="text" name="username"><br><br>
        Password: <input type="password" name="password"><br><br>
        <input type="submit" value="Login">
    </form>
    '''

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        android_id = request.form['android_id'].strip()
        active = 'active' in request.form
        expiry_str = request.form.get('expiry_date')
        expiry = datetime.strptime(expiry_str, '%Y-%m-%d').date() if expiry_str else None
        activation = Activation.query.filter_by(android_id=android_id).first()
        if activation:
            activation.active = active
            activation.expiry_date = expiry
        else:
            activation = Activation(android_id=android_id, active=active, expiry_date=expiry)
            db.session.add(activation)
        db.session.commit()
    activations = Activation.query.all()
    return render_template_string('''
    <h1>Activation Panel - RP KRISHNATREYA</h1>
    <a href="/logout">Logout</a><br><br>
    <form method="post">
        Android ID: <input type="text" name="android_id" required><br><br>
        Active: <input type="checkbox" name="active"><br><br>
        Expiry Date: <input type="date" name="expiry_date"><br><br>
        <input type="submit" value="Add/Update ID">
    </form>
    <h2>Existing IDs</h2>
    <table border="1">
        <tr><th>Android ID</th><th>Active</th><th>Expiry Date</th><th>Action</th></tr>
        {% for act in activations %}
        <tr>
            <td>{{ act.android_id }}</td>
            <td>{{ 'Yes' if act.active else 'No' }}</td>
            <td>{{ act.expiry_date or 'None' }}</td>
            <td><a href="/delete/{{ act.id }}">Delete</a></td>
        </tr>
        {% endfor %}
    </table>
    ''', activations=activations)

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    activation = Activation.query.get(id)
    if activation:
        db.session.delete(activation)
        db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/check')
def check():
    android_id = request.args.get('id')
    if not android_id:
        return jsonify({'active': False})
    activation = Activation.query.filter_by(android_id=android_id).first()
    if activation and activation.active:
        today = datetime.today().date()
        if not activation.expiry_date or activation.expiry_date >= today:
            return jsonify({'active': True})
    return jsonify({'active': False})

if __name__ == '__main__':
    app.run(debug=True)
