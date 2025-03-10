import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from data_models import db, Author, Book

app = Flask(__name__)

# Get the absolute path of the directory containing app.py
base_dir = os.path.abspath(os.path.dirname(__file__))
# Create path for database in 'data' subdirectory
db_path = os.path.join(base_dir, 'data', 'library.sqlite')
db_dir = os.path.dirname(db_path)

# Ensure the directory exists
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
db.init_app(app)