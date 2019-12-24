# Importeer alle nodige libraries/packages
from flask import Flask, session, render_template, request, url_for, redirect, jsonify, abort
from flask_session import Session
from sqlalchemy import create_engine, text, exc
from sqlalchemy.orm import scoped_session, sessionmaker
import hashlib
import os
import requests

# Maak een Flask-object aan en sla dit op in de app-variabele
app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Encrypt-functie om wachtwoord te versleutelen
def encrypt(password):

    # Salt om de hash te versterken
    salt = "SuPeRgEhEiM007"

    # Encrypt het wachtwoord zodat het niet in plain-tekst in de database terecht komt
    hash_object = hashlib.sha256(password.encode() + salt.encode())
    hex_dig = hash_object.hexdigest()

    # Return de hash
    return hex_dig


# Functie om api_requests uit te voeren
def api_request(isbn):

    # Api-request
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "pXNhbslj5YpEEAGZM2Nag", "isbns": isbn}).json()

    select_query = text("SELECT title, author, year FROM books WHERE isbn = :i")
    data = db.execute(select_query, {"i": isbn}).fetchall()

    # Dictionary die we aan de template gaan meegeven
    dict = {}

    dict["title"] = data[0].title
    dict["author"] = data[0].author
    dict["publication year"] = data[0].year

    # Manier om door een dict die als value een list met dict heeft te loopen:
    for items in res["books"]:
        for key in items:
            dict[key] = items[key]

    return dict

# Functie om reviews op te vragen
def get_reviews(isbn):

    # Query om alle reviews te pakken voor een gegeven boek
    review_query = text(
        "SELECT review, username FROM reviews FULL OUTER JOIN users ON reviews.user_id = users.user_id WHERE reviews.isbn = :i")

    # Voer query uit en sla het op in een variabele
    reviews = db.execute(review_query, {"i": isbn})
    review_data = reviews.fetchall()

    return review_data


# Root-route
@app.route('/')
def index():

    # Render de html-template op basis van de session-key
    return render_template('index.html', username=session.get('username'))

# Login-route
@app.route('/login')
def login():

    # Als de user bestaat, redirect naar books-url, anders naar login-page
    if session.get('username') != None:
        return redirect(url_for("books"))

    return render_template("login.html")

# Authenticate-Route
@app.route('/auth', methods=["POST"])
def auth():

    # Query de login-gegevens van de form en sla het op in de variabelen
    username = request.form.get("username")
    password = request.form.get("password")

    # Gebruik de encrypt-functie om het wachtwoord te hashen
    hash = encrypt(password)

    # Query de user met zijn wachtwoord in de database
    full_query = text("SELECT username, password FROM users WHERE username = :u")
    auth = db.execute(full_query, {'u':username}).fetchall()

    # Try/catch voor wanneer de username niet in de database voorkomt, en je dus de indexen niet kan gebruiken
    try:
        # Als de user gelijk is aan de user in de db en de hash gelijk is aan de hash in de db
        if username == auth[0].username and hash == auth[0].password:

            # Zet de username sessie
            session['username'] = username

            return redirect(url_for('login'))

    # Wanneer er geen index is omdat de user niet bestaat, vang dit op en laat het programma niet crashen
    except IndexError:
        pass

    # User bestaat niet of de user heeft een ongeldige wachtwoord gegeven
    error = "Invalid username or password!"

    # Verwijs de user naar de login-pagina met een foutmelding
    return render_template("login.html", error=error)

# Logout-route
@app.route('/logout', methods=["GET"])
def logout():

    # Als er een sessie aanwezig is, pop de sessie en informeer de user dat het uitloggen gelukt is
    if session.get('username') != None:

        session.pop('username')
        logout = "You have succesfully logged out!"

        return render_template("login.html", logout=logout)

    # Zo niet, dan stuur de user door naar de login-page zonder message
    return redirect(url_for('login'))

# Registreer route
@app.route('/register')
def register():
    return render_template("register.html")

# Registratie-validatie route
@app.route('/validate', methods=["POST"])
def validate():

    # Query de login-gegevens van de form en sla het op in de variabelen
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    address = request.form.get("address")
    city = request.form.get("city")
    zip = request.form.get("zip")

    # Back-end validatie, is maar gedeeltelijk maar het kan!
    if len(username) <= 1:
        error = "Username must contain atleast two characters!"
        return render_template("register.html", error=error)

    if len(password) < 8:
        error = "Password must be equal or greater than 8!"
        return render_template("register.html", error=error)

    # Roep encryptie functie aan om wachtwoord te hashen
    hash = encrypt(password)

    # Try/except om de user aan te maken
    try:
        # Sla de user op in de database met Anti-SQL injection :D, door parameter injectie/binding te gebruiken
        insert_query = text("INSERT INTO users (username, password, email, address, city, zip) VALUES (:u, :p, :e, :a, :c, :z)")
        db.execute(insert_query, {"u":username, "p":hash, "e":email, "a":address, "c":city, "z":zip})
        db.commit()

        success = "You have successfully created an account!"

        return render_template("login.html", success=success)

    # Except om bij een duplicate-error een foutmelding weer te geven
    except exc.IntegrityError:
        error = "Username already taken!"
        return render_template("register.html", error=error)

# Books-route
@app.route('/books')
def books():

    if session.get('username') != None:
        return render_template("books.html")

    return redirect(url_for('login'))

# Search-route om boeken in onze database op te zoeken
@app.route('/search', methods=["GET"])
def search():

    book = request.args.get("book")

    if len(book) >= 1 and not book.isspace():
        book = "%" + book + "%"

    select_query = text("SELECT title, isbn FROM books WHERE title LIKE :t OR isbn LIKE :t OR author LIKE :t")
    books = db.execute(select_query, {"t":book}).fetchall()
    empty = len(books) < 1

    return render_template("books.html", books=books, empty=empty)

# Book-info route om de informatie weer te geven die vanuit de externe API komt
@app.route('/bookinfo', methods=['GET'])
def bookinfo():

    if session.get('username') != None:

        isbn = request.args.get("isbn")
        dict = api_request(isbn)
        review_data = get_reviews(isbn)

        return render_template("bookinfo.html", res=dict, reviews=review_data)

    return redirect(url_for('login'))

# Reviews-route om reviews voor een gegeven boek te plaatsen
@app.route('/reviews', methods=["POST"])
def reviews():

    if session.get('username') != None:

        # Pak alle argumenten die met de form worden gegeven
        rating = request.form.get("rating")
        text_area = request.form.get("textarea")
        book_isbn = request.form.get("isbn")
        user = session.get('username')

        # Doe opnieuw een api_request door de functie aan te roepen, zodat we dezelfde pagina opnieuw kunnen renderen (ja, dit kan veel beter dmv javascript)
        dict = api_request(book_isbn)

        # Geef ons weer alle reviews die we willen laten zien
        review_data = get_reviews(book_isbn)

        # Er moeten gegevens van de form gehaald zijn, anders gebeurd er niks
        if None not in [rating, text_area, book_isbn]:

            # Try/Catch om de error op te vangen als een gebruiker een boek wilt reviewen die hij al gereviewed heeft
            try:

                # Maak een nested query aan om de review naar de database te posten
                nested_query = text(
                    "INSERT INTO reviews (review, rating, isbn, user_id) VALUES (:r, :ra, :i, (SELECT (select user_id FROM users WHERE username = :u)))"
                )

                # Voer de query daadwerkelijk uit
                db.execute(nested_query, {"r": text_area, "ra": rating, "i": book_isbn, "u": user})
                db.commit()

                success = "You have successfully posted a review!"

                # Geef ons OPNIEUW weer alle reviews die we willen laten zien, na de insert dus
                review_data = get_reviews(book_isbn)

                return render_template("bookinfo.html", res=dict, reviews=review_data, success=success)

            # Vang duplicate error op om het aan de template door te sturen
            except exc.IntegrityError:

                error = "You already submitted a review for this book!"

                return render_template("bookinfo.html", res=dict, reviews=review_data, error=error)

        # Wanneer er een None is, dat betekent dat de user de form niet volledig heeft ingevuld. Stuur foutmelding
        else:
            error = "You have to give a review and rating before you post!"

            return render_template("bookinfo.html", res=dict, reviews=review_data, error=error)

# Contact-route om contactgegevens op te vragen
@app.route('/contact')
def contact():

    return render_template("contact.html", username=session.get('username'))

# API-route om een JSON-object van een gegeven boek op te vragen
@app.route('/api/<string:isbn>', methods=["GET"])
def api(isbn):

    # Mijn machtige query die alles in 1x ophaalt dmv FULL outer joins en subquerys :)
    mighty_query = text(
        "SELECT (SELECT COUNT(rev_id) FROM reviews FULL OUTER JOIN books ON books.isbn = reviews.isbn WHERE books.isbn = :i)\
        review_count, (SELECT AVG(rating) FROM reviews FULL OUTER JOIN books ON books.isbn = reviews.isbn WHERE books.isbn = :i)\
        avg_rating, title, author, year, books.isbn FROM books WHERE books.isbn = :i"
    )

    result = db.execute(mighty_query, {"i": isbn}).fetchall()

    # Als er niks gevonden is, return een 404 HTTP-status
    if len(result) == 0:
        abort(404)

    # Json_dict die nodig is om de sql_query in een dictionary op te slaan
    json_dict = {}

    # Loop door de tuple heen, en zet de juiste waarden in de json_dict, waabij een ternary-operator gebruikt wordt voor average_score (want je kan null niet afronden!)
    # float()-cast gebruikt omdat jsonify() niet met decimals om kan gaan!
    for tuple in result:
        json_dict["title"] = tuple.title
        json_dict["author"] = tuple.author
        json_dict["publication_date"] = tuple.year
        json_dict["isbn"] = tuple.isbn
        json_dict["review_count"] = tuple.review_count
        json_dict["average_score"] = round(float(tuple.avg_rating), 2) if tuple.avg_rating is not None else 0

    # Return een json-object met de gegevens in de json_dict
    return jsonify(json_dict)

# Autocomplete route om tijdens het zoeken naar een boek, suggesties te geven
@app.route('/autocomplete', methods=['GET'])
def autocomplete():

    # Haal het argument van jQuery's AJAX Call
    search = request.args.get('b_query')

    # Definieert de "like" om in de sql-query te inserten
    result = "%" + str(search) + "%"

    # Raw-SQL query om de data op te halen
    query = db.execute("SELECT title FROM books WHERE title LIKE :s OR isbn LIKE :s OR author LIKE :s", {"s": result}).fetchall()

    # Maak in 1x een lijst zonder een lege lijst te initialiseren, en zet meteen de data van de query erin
    results = [mv[0] for mv in query]

    # Return het resultaat als json-object, want dat verwacht jQuery
    return jsonify(matching_results=results)