import os
from flask import Flask, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Delete

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

# For multiple methods to access the book details
def get_book_details(book_id):
    book = Book.query.get(book_id)
    author = Author.query.get(book.author_id)
    cover_url = f"https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg"
    isbn = Book.query.get(isbn)
    birthdate = author.birth_date.isoformat() if author.birth_date is not None else 'N/A'
    date_of_death = author.date_of_death.isoformat() if author.date_of_death is not None else 'N/A'


    return book, author, cover_url, book_id, isbn, birthdate, date_of_death

@app.route('/')
def home():
    search_query = request.args.get('search', '')
    criteria = request.args.get('criteria', 'title')

    query = db.session.query(Book, Author).join(Author, Book.author_id == Author.id)

    if search_query:
        query = query.filter(Book.title.ilike(f'%{search_query}%'))

    if criteria == 'title':
        query = query.order_by(Book.title)
    elif criteria == 'author':
        query = query.order_by(Author.name)
    elif criteria == 'year':
        query = query.order_by(Book.publication_year)

    books = query.all()

    book_data = []
    for book, author in books:
        _, _, cover_url = get_book_details(book.id)
        birth_date = author.birth_date.isoformat() if author.birth_date is not None else 'N/A'
        date_of_death = author.date_of_death.isoformat() if author.date_of_death is not None else 'N/A'

        book_data.append({
            'id': book.id,
            'title': book.title,
            'isbn': book.isbn,
            'year': book.publication_year,
            'author': author.name,
            'birth_date': birth_date,
            'date_of_death': date_of_death,
            'cover_url': cover_url
        })

    return render_template('home.html', books=book_data)


@app.route('/book/<int:book_id>/detail', methods=['GET', 'DELETE'])
def book_detail(book_id):
    book, author, cover_url, year, isbn = get_book_details(book_id)
    return render_template('detail_book.html', book=book, author=author, cover_url=cover_url, year=year, isbn=isbn)


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
            return redirect('/')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding book: {str(e)}', 'error')

    # Fetch all authors for the dropdown menu
    authors = Author.query.all()
    return render_template('add_book.html', authors=authors)


@app.route('/book/<int:book_id>/delete', methods=['POST', 'DELETE'])
def delete_book(book_id):
    if book_id <= 130:
        flash('Deleting this book is not allowed. Try a user-generated book. Thank you for not hacking our Library.', 'error')
        return redirect('/')

    if request.form.get('_method') == 'DELETE':
        try:
            # Find the book by ID
            book = Book.query.get(book_id)
            if not book:
                flash('Book not found.', 'error')
                return redirect('/')

            # Check if the author has other books
            author_id = book.author_id
            db.session.delete(book)
            db.session.commit()

            # Check if the author has any other books
            other_books = Book.query.filter_by(author_id=author_id).count()
            if other_books == 0:
                author = Author.query.get(author_id)
                db.session.delete(author)
                db.session.commit()

            flash('Book deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting book: {str(e)}', 'error')

    return redirect('/')


app.secret_key = os.urandom(24)

if __name__ == '__main__':
    app.run(debug=True, port=5000)