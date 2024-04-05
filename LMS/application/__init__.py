from flask import Flask
from application.database import db
from application.models import *




app = Flask(__name__,template_folder='../templates',static_folder='../static')
app.config['SECRET_KEY'] = 'gkm7412@lim'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)




with app.app_context():
    db.create_all()

    librarian = User.query.filter_by(username='librarian').first()
    if not librarian:
        librarian = User(username='librarian', password='librarian', name='Librarian', is_librarian=True)
        db.session.add(librarian)
        db.session.commit()




