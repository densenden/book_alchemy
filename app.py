import os
from flask import Flask, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from data_models import db, Author, Book
from datetime import datetime
import requests
import logging

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


# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    # Query books with their authors using SQLAlchemy's join
    books = db.session.query(Book, Author) \
        .join(Author, Book.author_id == Author.id) \
        .all()

    # Process books and fetch cover images
    book_data = []
    for book, author in books:
        # Get cover image from OpenLibrary API
        cover_url = f"https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg"
        author_photo_url = f"https://covers.openlibrary.org/a/olid/{author.olid}-L.jpg"

        # Log the dates for debugging
        logging.debug(f"Processing author: {author.name}, birth_date: {author.birth_date}, date_of_death: {author.date_of_death}")

        # Check for valid dates


        birth_date = author.birth_date.isoformat() if author.birth_date is not None else 'N/A'
        date_of_death = author.date_of_death.isoformat() if author.date_of_death is not None else 'N/A'


        book_data.append({
            'title': book.title,
            'isbn': book.isbn,
            'year': book.publication_year,
            'author': author.name,
            'birth_date': birth_date,
            'date_of_death': date_of_death,
            'cover_url': cover_url,
            'author_photo_url': author_photo_url
        })

    return render_template('home.html', books=book_data)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        try:
            # Parse form data
            name = request.form['name']
            birth_date_str = request.form['birthdate']
            date_of_death_str = request.form['date_of_death']

            # Validate and parse dates
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            date_of_death = None
            if date_of_death_str:
                date_of_death = datetime.strptime(date_of_death_str, '%Y-%m-%d').date()

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
        except ValueError as ve:
            flash(f'Invalid date format: {str(ve)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding author: {str(e)}', 'error')

    return render_template('add_author.html')


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        try:
            # Parse form data
            isbn = request.form['isbn']
            title = request.form['title']
            publication_year = int(request.form['publication_year'])
            author_id = int(request.form['author_id'])

            # Create new book
            new_book = Book(
                isbn=isbn,
                title=title,
                publication_year=publication_year,
                author_id=author_id
            )

            # Add to database
            db.session.add(new_book)
            db.session.commit()

            flash('Book added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding book: {str(e)}', 'error')

    # Fetch all authors for the dropdown menu
    authors = Author.query.all()
    return render_template('add_book.html', authors=authors)


app.secret_key = os.urandom(24)

if __name__ == '__main__':
    app.run(debug=True, port=5000)