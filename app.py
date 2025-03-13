import os
from flask import Flask, render_template, request, flash, redirect, jsonify
from datetime import datetime
import requests
from data_models import db, Book, Author


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), "data", "library.sqlite")}'
app.secret_key = os.urandom(24)
db.init_app(app)  # Initialize the db instance with the app


def get_wikipedia_author_image(author_name):
    try:
        search_url = f"https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": author_name
        }
        search_response = requests.get(search_url, params=search_params).json()
        if not search_response["query"]["search"]:
            return '/static/default_author_photo.png'  # Fallback image

        page_title = search_response["query"]["search"][0]["title"]

        page_info_url = f"https://en.wikipedia.org/w/api.php"
        page_info_params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "pageprops",
            "ppprop": "wikibase_item"
        }
        page_info_response = requests.get(page_info_url, params=page_info_params).json()
        pages = page_info_response["query"]["pages"]
        wikidata_id = next(iter(pages.values())).get("pageprops", {}).get("wikibase_item", None)

        if not wikidata_id:
            return '/static/default_author_photo.png'  # Fallback image

        wikidata_url = f"https://www.wikidata.org/w/api.php"
        wikidata_params = {
            "action": "wbgetclaims",
            "format": "json",
            "entity": wikidata_id,
            "property": "P18"
        }
        wikidata_response = requests.get(wikidata_url, params=wikidata_params).json()
        claims = wikidata_response.get("claims", {}).get("P18", [])

        if not claims:
            return '/static/default_author_photo.png'  # Fallback image

        image_filename = claims[0]["mainsnak"]["datavalue"]["value"]
        image_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{image_filename}"
        return image_url

    except Exception as e:
        return '/static/default_author_photo.png'  # Fallback image


@app.route('/')
def home():
    search_query = request.args.get('search', '')
    criteria = request.args.get('criteria', 'title')
    direction = request.args.get('direction', 'asc')

    query = db.session.query(Book, Author).join(Author, Book.author_id == Author.id)

    if search_query:
        query = query.filter(Book.title.ilike(f'%{search_query}%'))

    if criteria == 'title':
        query = query.order_by(Book.title.asc() if direction == 'asc' else Book.title.desc())
    elif criteria == 'author':
        query = query.order_by(Author.name.asc() if direction == 'asc' else Author.name.desc())
    elif criteria == 'year':
        query = query.order_by(Book.publication_year.asc() if direction == 'asc' else Book.publication_year.desc())
    elif criteria == 'id':
        query = query.order_by(Book.id.asc() if direction == 'asc' else Book.id.desc())

    books = query.all()
    book_data = [
        {
            'id': book.id, 'title': book.title, 'isbn': book.isbn, 'year': book.publication_year,
            'author': author.name, 'birth_date': author.birth_date, 'date_of_death': author.date_of_death,
            'cover_url': f"https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg"
        }
        for book, author in books
    ]
    return render_template('home.html', books=book_data, criteria=criteria, direction=direction)


@app.route('/book/<int:book_id>/detail', methods=['GET'])
def book_detail(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Book not found.', 'error')
        return redirect('/')
    author = Author.query.get(book.author_id)

    # Get the next book ID
    next_book = Book.query.filter(Book.id > book_id).order_by(Book.id.asc()).first()
    next_book_id = next_book.id if next_book else None

    # Get the previous book ID
    prev_book = Book.query.filter(Book.id < book_id).order_by(Book.id.desc()).first()
    prev_book_id = prev_book.id if prev_book else None


    book_data = {
        'id': book.id,
        'title': book.title,
        'isbn': book.isbn,
        'year': book.publication_year,
        'author': author.name if author else 'N/A',
        'author_id': author.id if author else None,
        'birth_date': author.birth_date if author else 'N/A',
        'date_of_death': author.date_of_death if author else 'N/A',
        'cover_url': f"https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg",
        'next_book_id': next_book_id,
        'prev_book_id': prev_book_id
    }

    return render_template('detail_book.html', book=book_data)


@app.route('/author/<int:author_id>/detail')
def author_detail(author_id):
    author = Author.query.get(author_id)
    if not author:
        flash('Author not found.', 'error')
        return redirect('/')

    books = Book.query.filter_by(author_id=author_id).all()
    for book in books:
        book.cover_url = f"https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg"
    author_image = get_wikipedia_author_image(author.name)

    # Get the next author ID
    next_author = Author.query.filter(Author.id > author_id).order_by(Author.id.asc()).first()
    next_author_id = next_author.id if next_author else None

    # Get the previous author ID
    prev_author = Author.query.filter(Author.id < author_id).order_by(Author.id.desc()).first()
    prev_author_id = prev_author.id if prev_author else None

    author_data = {
        'name': author.name,
        'summary': get_author_summary(author.name),
        'birthdate': author.birth_date,
        'date_of_death': author.date_of_death,
        'books': books,
        'id': author.id,
        'year': book.publication_year,
        'author_image': author_image,
        'next_author_id': next_author_id,
        'prev_author_id'  : prev_author_id
    }

    return render_template('detail_author.html', author=author_data)

    return render_template(
        'detail_author.html', author=author_data)


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
            new_author = Author(name=name, birth_date=birth_date, date_of_death=date_of_death)
            db.session.add(new_author)
            db.session.commit()
            flash('Author added successfully!', 'success')
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
            return redirect('/?criteria=id&direction=desc')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding book: {str(e)}', 'error')
    authors = Author.query.all()
    return render_template('add_book.html', authors=authors)


@app.route('/book/<int:book_id>/delete', methods=['POST', 'DELETE'])
def delete_book(book_id):
    if book_id <= 600:
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