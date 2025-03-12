import os
from flask import Flask, render_template, request, flash, redirect
from datetime import datetime
import requests
from data_models import db, Book, Author  # Import the db instance and models

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), "data", "library.sqlite")}'
app.secret_key = os.urandom(24)
db.init_app(app)  # Initialize the db instance with the app

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
    book_data = [
        {
            'id': book.id, 'title': book.title, 'isbn': book.isbn, 'year': book.publication_year,
            'author': author.name, 'birth_date': author.birth_date, 'date_of_death': author.date_of_death,
            'cover_url': f"https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg"
        }
        for book, author in books
    ]
    return render_template('home.html', books=book_data)

@app.route('/book/<int:book_id>/detail', methods=['GET'])
def book_detail(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect('/')
    author = Author.query.get(book.author_id)
    return render_template(
        'detail_book.html',
        book=book,
        author=author,
        cover_url=f"https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg",
        year=book.publication_year,
        isbn=book.isbn,
        birth_date=author.birth_date if author else 'N/A',
        date_of_death=author.date_of_death if author else 'N/A'
    )

@app.route('/author/<int:author_id>/detail', methods=['GET'])
def author_detail(author_id):
    author = Author.query.get(author_id)
    if not author:
        flash('Author not found.', 'error')
        return redirect('/')
    books = Book.query.filter_by(author_id=author_id).all()
    for book in books:
        book.cover_url = f"https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg"
    return render_template(
        'detail_author.html',
        name=author.name,
        summary=get_author_summary(author.name),
        birthdate=author.birth_date,
        date_of_death=author.date_of_death,
        books=books,
        id=author.id,
        book=books[0] if books else None
    )

def get_author_summary(name):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('extract', 'No summary available.')
    return 'No summary available.'

@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        try:
            name = request.form['name']
            birth_date = datetime.strptime(request.form['birthdate'], '%Y-%m-%d').date()
            date_of_death = datetime.strptime(request.form['date_of_death'], '%Y-%m-%d').date() if request.form['date_of_death'] else None
            db.session.add(new_author)
            db.session.commit()
            flash('Author added successfully!', 'success')
        except ValueError as ve:
            flash(f'Invalid date format: {str(ve)}', 'error')
        except Exception as e:
            db.session.rollback()
    return render_template('add_author.html')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        try:
            isbn = request.form['isbn']
            title = request.form['title']
            publication_year = int(request.form['publication_year'])
            author_id = int(request.form['author_id'])
            new_book = Book(isbn=isbn, title=title, publication_year=publication_year, author_id=author_id)
            db.session.add(new_book)
            db.session.commit()
            flash('Book added successfully!', 'success')
            return redirect('/')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding book: {str(e)}', 'error')
    authors = Author.query.all()
    return render_template('add_book.html', authors=authors)

@app.route('/book/<int:book_id>/delete', methods=['POST', 'DELETE'])
def delete_book(book_id):
    if book_id <= 50:
        flash('Deleting this book is not allowed.', 'error')
        return redirect('/')
    if request.form.get('_method') == 'DELETE':
        try:
            book = Book.query.get(book_id)
            if not book:
                flash('Book not found.', 'error')
                return redirect('/')
            author_id = book.author_id
            db.session.delete(book)
            db.session.commit()
            if Book.query.filter_by(author_id=author_id).count() == 0:
                db.session.delete(Author.query.get(author_id))
                db.session.commit()
            flash('Book deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting book: {str(e)}', 'error')
    return redirect('/')

@app.route('/author/<int:author_id>/delete', methods=['POST', 'DELETE'])
def delete_author(author_id):
    if author_id <= 130:
        flash('Deleting this Author is not allowed.', 'error')
        return redirect('/')
    if request.form.get('_method') == 'DELETE':
        try:
            author = Author.query.get(author_id)
            if not author:
                flash('Author not found.', 'error')
                return redirect('/')
            if Book.query.filter_by(author_id=author_id).count() > 0:
                flash('Author has books and cannot be deleted.', 'error')
                return redirect('/')
            db.session.delete(author)
            db.session.commit()
            flash('Author deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting author: {str(e)}', 'error')
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=5000)