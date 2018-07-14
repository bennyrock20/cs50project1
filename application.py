import os
from flask import Flask, session, render_template, request, redirect,url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy import create_engine
import csv


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



@app.route("/")
def index():
    create_tables();
    if session.get('logged_in') != True:
        return redirect(url_for('login'))
    else:
     search = request.args.get("search","")
     books = []
     if search != "":
         print("searching book")
         books = db.execute("SELECT * FROM books WHERE isbn like :query or title like :query or author like :query  limit 50", {"query":  '%'+ search + '%'}).fetchall()
     else:
         print("no search")
         books = db.execute("SELECT * FROM books limit 50").fetchall()

     return render_template('index.html', books= books, search= search)

@app.route("/book/<int:book_id>")
def book(book_id):
    """List details about a single Book."""
    if session.get('logged_in') != True:
        return redirect(url_for('login'))
    # Make sure Book exists.
    book = db.execute("SELECT * FROM books WHERE id = :book_id  limit 1", {"book_id": book_id}).fetchone()
    if book is None:
        return redirect(url_for('index'))

    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id  limit 100", {"book_id": book_id}).fetchall()

    user_id = session.get('user')

    has_reviewed = db.execute("SELECT * FROM reviews WHERE book_id = :book_id  and user_id =:user_id limit 1", {"book_id": book_id, "user_id" : user_id}).fetchone()

    return render_template("book.html", book=book, reviews = reviews, has_reviewed = has_reviewed)



@app.route("/login", methods=['post','get'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        if  password and email:
            result = db.execute("SELECT * FROM users WHERE email = :email and password = :password", {"email": email, "password": password}).fetchone()
            if result:
                print()
                session['logged_in'] = True
                session['user'] = result[0]
                return redirect(url_for('index'))
    return render_template('login.html')

@app.route("/make-review", methods=['post'])
def make_review():
    if session.get('logged_in') != True:
        return redirect(url_for('login'))
    if request.method == 'POST':
        comment = request.form.get("comment")
        rating = request.form.get("rating")
        book_id = request.form.get("book_id")
        user_id = session.get('user')

        if  rating and book_id and user_id:
            db.execute("INSERT INTO reviews (comment,rating,user_id,book_id) VALUES (:comment,:rating,:user_id,:book_id)",
                    {"comment":comment,"rating": rating, "user_id": user_id,"book_id": book_id})
            db.commit()
            return redirect(url_for('book', book_id = book_id))
    return redirect(url_for('index'))

@app.route("/register", methods=['post','get'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        if username and password and email:
            db.execute("INSERT INTO users (username,email,password) VALUES (:username,:email,:password)",
                    {"username":username,"email": email, "password": password})
            db.commit()
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/logout")
def logout():
    session['logged_in'] = False
    session['user'] = 0
    return redirect(url_for('login'))

def create_tables():
    metadata = MetaData()
    user = Table('users', metadata,
    Column('user_id', Integer, primary_key=True),
    Column('username', String(50), nullable=False),
    Column('email', String(60)),
    Column('password', String(20), nullable=False),
    )
    user = Table('books', metadata,
    Column('id', Integer, primary_key=True),
    Column('isbn', String(50), nullable=False),
    Column('title', String(50), nullable=False),
    Column('author', String(50), nullable=False),
    Column('year', String(50), nullable=False),
    )

    user = Table('reviews', metadata,
    Column('id', Integer, primary_key=True),
    Column('comment', String(50), nullable=False),
    Column('rating', Integer, nullable=False),
    Column('user_id', Integer, ForeignKey("users.user_id"),nullable=False),
    Column('book_id', Integer, ForeignKey("books.id"),nullable=False)
    )
    metadata.create_all(engine)

def import_data():
    f = open("books.csv")
    reader = csv.reader(f)
    cont= 0;
    for isbn,title,author,year in reader:
        result = db.execute("INSERT INTO books (isbn, title, author,year) VALUES (:isbn, :title, :author,:year)",
                   {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Added book {isbn} - {title} - {cont}")
        cont= cont+1
    #db.commit()
