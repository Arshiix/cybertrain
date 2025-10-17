
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
import sqlite3
from datetime import datetime
import bleach
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
import os
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_secure_random_secret_key_here')  

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2000 per day", "100 per hour"]
)

# Database setup
DB_NAME = '/data/reviews.db'


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS reviews
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           username
                           TEXT
                           NOT
                           NULL,
                           review_text
                           TEXT
                           NOT
                           NULL,
                           timestamp
                           DATETIME
                           NOT
                           NULL
                       )
                       ''')
        conn.commit()


# Initialize database
init_db()


def load_tools():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'tools.json'), 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error: tools.json not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in tools.json - {e}")
        return []

# Security headers decorator
def add_security_headers(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        if hasattr(response, 'headers'):
            response.headers[
                'Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; img-src 'self' data:"
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    return decorated_function


# Form class with CSRF protection
class ReviewForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=50)])
    review = TextAreaField('Review', validators=[DataRequired(), Length(min=1, max=2000)])
    submit = SubmitField('Submit Review')


@app.route('/robots.txt')
def robots_txt():
    return send_from_directory('static', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    return send_from_directory('static', 'sitemap.xml')


@app.route('/', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
@add_security_headers
def index():
    form = ReviewForm()
    tools = load_tools()

    if form.validate_on_submit():
        username = bleach.clean(form.username.data, tags=[], strip=True)
        review_text = bleach.clean(form.review.data, tags=[], strip=True)
        timestamp = datetime.now()

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO reviews (username, review_text, timestamp) VALUES (?, ?, ?)',
                (username, review_text, timestamp)
            )
            conn.commit()

        return redirect(url_for('index'))

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username, review_text, timestamp FROM reviews ORDER BY timestamp DESC LIMIT 50')
        reviews = cursor.fetchall()

    return render_template('index.html', tools=tools, form=form, reviews=reviews)


@app.route('/api/tools', methods=['GET'])
@limiter.limit("10 per minute")
@add_security_headers
def api_tools():
    tools = load_tools()
    return jsonify(tools)


if __name__ == '__main__':
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
