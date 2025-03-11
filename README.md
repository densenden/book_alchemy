# Studio Sen Library

Studio Sen Library is a web application for managing a library of books and authors. It allows users to add, view, and delete books and authors.

## Setup

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Create a virtual environment and activate it:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up the database:
    ```sh
    flask db init
    flask db migrate
    flask db upgrade
    ```

5. Run the application:
    ```sh
    flask run
    ```

## Usage

- Navigate to `http://127.0.0.1:5000/` to access the application.
- Use the menu to add authors and books.
- Search for books by title, author, or year.
- View detailed information about books and authors.
- Delete books and authors as needed.

## License

This project is licensed under the MIT License.