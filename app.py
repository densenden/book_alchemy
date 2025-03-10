import os
from flask import Flask, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from data_models import db, Author, Book
from datetime import datetime

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


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        try:
            # Parse form data
            name = request.form['name']
            birth_date = datetime.strptime(request.form['birthdate'], '%Y-%m-%d').date()
            date_of_death = None
            if request.form['date_of_death']:
                date_of_death = datetime.strptime(request.form['date_of_death'], '%Y-%m-%d').date()

            # Create new author
            new_author = Author(
                name=name,
                birth_date=birth_date,
                date_of_death=date_of_death
            )

            # Add to database
            db.session.add(new_author)
            db.session.commit()

            flash('Author added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding author: {str(e)}', 'error')

    return render_template('add_author.html')

app.secret_key = os.urandom(24)

if __name__ == '__main__':
    app.run(debug=True, port=5000)