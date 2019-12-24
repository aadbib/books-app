from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
import csv
import os

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

"""
ERD-Model:
   
   Een user GEEFT een review (over een boek, maar de primary key van book zit al in reviews als forn_key, zie hieronder),
   1 op 1 relatie met reviews-tabel. PRIM KEY van users als FORN KEY bij Reviews.
   Een boek HEEFT meerdere reviews, 1 op veel relatie met books. PRIM KEY van books als FORN key bij Reviews.

   Nu heeft Reviews de primary key van users en books als foreign key, dus is het mogelijk om te controleren of een user al een review heeft gegeven.
   Tevens kan zo een boek meerdere reviews bevatten.
   Ook is er een unique constraint in reviews gezet, zodat een user maar een enkele review voor een boek kan posten.

"""

# Creer automatisch een books-tabel als het er nog niet is
table_books_create_query = text("CREATE TABLE IF NOT EXISTS books(isbn VARCHAR PRIMARY KEY NOT NULL,\
title VARCHAR NOT NULL,\
author VARCHAR NOT NULL,\
year int NOT NULL)")

# Creer een index voor het snel opzoeken van isbn, title en autheur
cover_index_create_query = text("CREATE INDEX IF NOT EXISTS cover_index ON books (isbn, title, author)")

# Creer automatisch een users-tabel als het er nog niet is
table_users_create_query = text("CREATE TABLE IF NOT EXISTS users(user_id SERIAL PRIMARY KEY NOT NULL,\
username VARCHAR UNIQUE NOT NULL,\
password VARCHAR NOT NULL,\
email VARCHAR NOT NULL,\
address VARCHAR NOT NULL,\
city VARCHAR NOT NULL,\
zip VARCHAR NOT NULL)")

# Creer een index voor het authentiseren van gebruikers
auth_index_create_query = text("CREATE INDEX IF NOT EXISTS auth_index ON users (username, password)")

# Creer automatisch een reviews-tabel als het er nog niet is, waarbij de primary-key van book als foreign_key in reviews terecht komt (1 op veel relatie)
table_reviews_create_query = text("CREATE TABLE IF NOT EXISTS reviews(rev_id SERIAL PRIMARY KEY NOT NULL,\
review TEXT NOT NULL,\
rating INT NOT NULL,\
isbn VARCHAR REFERENCES books (isbn) NOT NULL,\
user_id INT REFERENCES users (user_id) NOT NULL,\
UNIQUE (isbn, user_id) )")

# Creer een index voor het versnellen van queries over gebruikers en hun reviews
user_rev_index_create_query = text("CREATE INDEX IF NOT EXISTS user_rev_index ON reviews (user_id, isbn)")

# Voer de querys daadwerkelijk uit
db.execute(table_books_create_query)
db.execute(cover_index_create_query)
db.execute(table_users_create_query)
db.execute(auth_index_create_query)
db.execute(table_reviews_create_query)
db.execute(user_rev_index_create_query)
db.commit()

def main():
    f = open("books.csv")

    # Query de database voor één match
    select_query = text("SELECT * FROM books")
    select_result = db.execute(select_query).fetchone()

    # Als de tabel books leeg is, vul dan de tabel met data vanuit het csv-bestand
    if select_result is None:

        reader = csv.reader(f)
        next(reader, None)

        for isbn, title, author, year in reader:

            # Sla het boek op in de database met Anti-SQL injection :D, door parameter injectie/binding te gebruiken
            insert_query = text(
                "INSERT INTO books (isbn, title, author, year) VALUES (:i, :t, :a, :y)")
            db.execute(insert_query, {"i": isbn, "t": title, "a": author, "y": year})

        db.commit()

if __name__ == "__main__":
    main()

