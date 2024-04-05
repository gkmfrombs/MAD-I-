from application.database import db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime


class User(db.Model):
    __tablename__='user'
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(32),unique=True,nullable=False)
    passhash=db.Column(db.String(512),nullable=False)
    name=db.Column(db.String(64),nullable=True)
    is_librarian = db.Column(db.Boolean,nullable=False,default = False)

    # -----relationship
    books_access = db.relationship('Book', secondary='bookuser', back_populates='users_access')




    @property
    def password(self,password):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self,password):
        self.passhash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.passhash,password) 
    

class Section(db.Model):
    __tablename__='section'
    section_id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(64),unique=True,nullable=False)
    created_date=db.Column(db.DateTime,default=datetime.datetime.utcnow)
    description=db.Column(db.Text)
    
    # -----relationdhip
    books = db.relationship('Book',backref='section',lazy=True,cascade='all, delete-orphan')

class  Book(db.Model):
    __tablename__ = 'book'
    book_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    thumbnail_path = db.Column(db.String(512))
    content_path = db.Column(db.String(512))
    author = db.Column(db.String(64))
    date_issued = db.Column(db.Date)
    section_id=db.Column(db.Integer,db.ForeignKey('section.section_id' , ondelete='CASCADE'),nullable=True)
    

    # -----relationship
    users_access = db.relationship('User', secondary='bookuser', back_populates='books_access')






class BookUser(db.Model):
    __tablename__='bookuser'
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),primary_key=True)
    book_id=db.Column(db.Integer,db.ForeignKey('book.book_id'),primary_key=True)




  
   

class Request(db.Model):
    __tablename__='request'
    request_id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    book_id=db.Column(db.Integer,db.ForeignKey('book.book_id'))
    request_date=db.Column(db.Date)
    return_date = db.Column(db.Date)
    expiry_date = db.Column(db.DateTime, nullable=True)

    # Establish relationship with User
    user = db.relationship('User', backref=db.backref('requests', lazy=True))

    # Establish relationship with Book
    book = db.relationship('Book', backref=db.backref('requests', lazy=True))



class Feedback(db.Model):
    __tablename__='feedback'
    feedback_id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    book_id=db.Column(db.Integer,db.ForeignKey('book.book_id'))
    feedback_date=db.Column(db.Date)
    comment = db.Column(db.Text)
    rating = db.Column(db.Integer)

