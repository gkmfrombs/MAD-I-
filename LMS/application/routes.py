from application import app
from flask import render_template,redirect,url_for,flash,session,request
from application.models import *
from functools import wraps
from datetime import datetime, timedelta 
import os
from werkzeug.utils import secure_filename 
from sqlalchemy import or_ # for search function
#=======stats====
import matplotlib.pyplot as plt
from io import BytesIO
import base64


UPLOAD_FOLDER = 'static/thumbnails'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf','txt','docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# =============== AUTHENTICATIONS ===============

def auth_required(func):
    @wraps(func)
    def inner(*args,**kwargs):
        if 'user_id' not in session:
            flash("You need to login first")
            return redirect(url_for('login'))
        return func(*args,**kwargs)
    return inner

def librarian_required(func):
    @wraps(func)
    def inner(*args,**kwargs):
        if 'user_id' not in session:
            flash("You need to login first")
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_librarian:
            flash("You are not authorized to view this page.")
            return redirect(url_for('index'))
        return func(*args,**kwargs)
    return inner
#======================================================================================================

#=============== PROFILE =============== 
#=======================================
@app.route('/profile')
@auth_required
def profile():
    return render_template('profile.html', user=User.query.get(session['user_id']))

@app.route('/profile', methods=['POST'])
@auth_required
def profile_post():
    user = User.query.get(session['user_id'])
    username = request.form.get('username')
    name = request.form.get('name')
    password = request.form.get('password')
    cpassword = request.form.get('cpassword')
    if username == '' or password == '' or cpassword == '' or name == '':
        flash("All fields are required")
        return redirect(url_for('profile'))
    if not user.check_password(cpassword):
        flash("Current password is incorrect")
        return redirect(url_for('profile'))
    if User.query.filter_by(username=username).first():
        flash("Username already exists")
        return redirect(url_for('profile'))
    user.username = username
    user.name = name
    user.password = password
    db.session.commit()
    flash("Profile updated successfully")
    return redirect(url_for('profile'))

# ==================LOGIN & REGISTER ===============

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == '' or password == '':
        flash("Username or password can not be empty.")
        return  redirect(url_for('login'))
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("User does not exist")
        return redirect(url_for('login'))
    if not user.check_password(password):
        flash("incorrect password")
        return redirect(url_for('login'))
    # login successful
    session['user_id'] = user.id
    return  redirect(url_for('index'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')
    if username == '' or password == '':
        flash("Username or password can not be empty.")
        return redirect(url_for('register'))

    if User.query.filter_by(username=username).first():
        flash("already exist")
        return redirect(url_for('register'))
    
    user = User(username=username, password=password, name=name)
    db.session.add(user)
    db.session.commit()
    flash("User successfully registered")
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('user_id',None)
    return redirect(url_for('login'))

#=======================================================================================================


# ================= LIBRARIAN DASHBOARD ===============
#======================================================   

@app.route('/librarian')
@librarian_required
def librarian():
    user = User.query.get(session['user_id'])
    if not user.is_librarian:
        flash("You are not authorized to view this page.")
        return redirect(url_for('index'))
    return render_template('librarian.html', user=user, sections=Section.query.all())

# ================= SECTION ROUTES ===============

@app.route('/section/add')
@librarian_required
def section_add():
    return render_template('section/add.html', user=User.query.get(session['user_id'])) 



@app.route('/section/add', methods=['POST'])
@librarian_required
def section_add_post():
    name = request.form.get('name')
    created_date = request.form.get('created_date')  # Add this line to get created_date
    description = request.form.get('description')  # Add this line to get description

    if name == '' or created_date == '' or description == '':
        flash("All fields are required")
        return redirect(url_for('section_add'))
    
        # Convert created_date string to a datetime object
    created_date = datetime.strptime(created_date, '%Y-%m-%d').date()

    section = Section(name=name, created_date=created_date, description=description)  # Assuming Section model has created_date and description columns
    db.session.add(section)
    db.session.commit()
    flash("Section added successfully")
    return redirect(url_for('librarian'))


@app.route('/section/edit/<int:id>')
@librarian_required
def section_edit(id):
    return render_template('section/edit.html',
                            user=User.query.get(session['user_id']),
                              section=Section.query.get(id))

@app.route('/section/edit/<int:id>', methods=['POST'])
@librarian_required
def section_edit_post(id):
    section = Section.query.get(id)
    name = request.form.get('name')
    created_date = request.form.get('created_date')
    description = request.form.get('description')
    if name == '' or created_date == '' or description == '':
        flash("All fields are required")
        return redirect(url_for('section_edit', id=id))
    created_date = datetime.strptime(created_date, '%Y-%m-%d').date()
    section.name=name
    section.created_date=created_date
    section.description=description
    db.session.commit()
    flash("Section updated successfully")
    return redirect(url_for('librarian'))

@app.route('/section/view/<int:id>')
@librarian_required
def section_view(id):
    return render_template('section/view.html',
                            user=User.query.get(session['user_id']),
                              section=Section.query.get(id))

@app.route('/section/delete/<int:id>')
@librarian_required
def section_delete(id):
    section = Section.query.get(id)
    if not section:
        flash("Section does not exist")
        return redirect(url_for('librarian'))
    return render_template('section/delete.html', user=User.query.get(session['user_id']), section=section)

@app.route('/section/delete/<int:id>', methods=['POST'])
@librarian_required
def section_delete_post(id):
    section = Section.query.get(id)
    if not section:
        flash("Section does not exist")
        return redirect(url_for('librarian'))
    db.session.delete(section)
    db.session.commit()
    flash("Section deleted successfully")
    return redirect(url_for('librarian'))


# ================= BOOK ROUTES ===============

@app.route('/book/add')
@librarian_required
def book_add():
    section_id=-1
    args = request.args
    print(args)
    if 'section_id' in args:
        if Section.query.get(int(args.get('section_id'))):
            section_id = int(args.get('section_id'))                             
    return render_template('book/add.html',
                            user=User.query.get(session['user_id']),
                            sections=Section.query.all(),
                            section_id=section_id,
                            maxstring=datetime.today().strftime('%Y-%m-%d')
                            )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/book/add', methods=['POST'])
@librarian_required
def book_add_post():
    name = request.form.get('name')
    author = request.form.get('author')
    date_issued = request.form.get('date_issued')
    section = request.form.get('section')
    content = request.form.get('content')
    
    if name == '' or author == '' or date_issued == '' or section == '' or content == '':
        flash("All fields are required")
        return redirect(url_for('book_add'))
    if len(name) > 64:
        flash("Name should be less than 64 characters")
        return redirect(url_for('book_add'))
    if len(author) > 64:
        flash("Author name should be less than 64 characters")
        return redirect(url_for('book_add'))
    section = Section.query.get(section)
    if not section:
        flash("Invalid section")
        return redirect(url_for('book_add'))
        
    try:
        date_issued = datetime.strptime(date_issued, '%Y-%m-%d')
    except ValueError:
        flash("Invalid date format")
        return redirect(url_for('book_add'))
    
    
    if 'thumbnail' in request.files:
        thumbnail = request.files['thumbnail']
        if thumbnail and allowed_file(thumbnail.filename):
            filename = secure_filename(thumbnail.filename)
            thumbnail_path =os.path.join(app.config['UPLOAD_FOLDER'], filename)
            thumbnail.save(thumbnail_path)
        else:
            flash("Invalid image format")
            return redirect(url_for('book_add'))
    else:
        thumbnail_path = None
        
    if 'content' in request.files:
        content = request.files['content']
        if content and allowed_file(content.filename):
            filename = secure_filename(content.filename)
            content_path =os.path.join(app.config['UPLOAD_FOLDER'], filename)
            content.save(content_path)
        else:
            flash("Invalid content format")
            return redirect(url_for('book_add'))
    else:
        content_path = None
    


    

    thumbnail_path = thumbnail_path[6:]
    content_path = content_path[6:]
    

    
    new_book = Book(name=name, thumbnail_path=thumbnail_path.replace('\\', '/'),
                     content_path=content_path.replace('\\', '/'), 
                     author=author, date_issued=date_issued, 
                     section_id=section.section_id)    
    db.session.add(new_book)
    db.session.commit()
    flash("Book added successfully")
    return redirect(url_for('section_view', id=section.section_id))

@app.route('/book/edit/<int:id>')
@librarian_required
def book_edit(id):
    book = Book.query.get(id)
    return render_template('book/edit.html', user=User.query.get(session['user_id']), 
                           book=book,
                           sections=Section.query.all(),
                           maxstring=datetime.today().strftime('%Y-%m-%d'),
                           date_issued=book.date_issued.strftime('%Y-%m-%d')
                           )

@app.route('/book/edit/<int:id>', methods=['POST'])
@librarian_required
def book_edit_post(id):
    name = request.form.get('name')
    author = request.form.get('author')
    date_issued = request.form.get('date_issued')
    section = request.form.get('section')
    content = request.form.get('content')
    
    if name == '' or author == '' or date_issued == '' or section == '' or content == '':
        flash("All fields are required")
        return redirect(url_for('book_add'))
    if len(name) > 64:
        flash("Name should be less than 64 characters")
        return redirect(url_for('book_add'))
    if len(author) > 64:
        flash("Author name should be less than 64 characters")
        return redirect(url_for('book_add'))
    section = Section.query.get(section)
    if not section:
        flash("Invalid section")
        return redirect(url_for('book_add'))
        
    try:
        date_issued = datetime.strptime(date_issued, '%Y-%m-%d')
    except ValueError:
        flash("Invalid date format")
        return redirect(url_for('book_add'))
    
    
    if 'thumbnail' in request.files:
        thumbnail = request.files['thumbnail']
        if thumbnail and allowed_file(thumbnail.filename):
            filename = secure_filename(thumbnail.filename)
            thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            thumbnail.save(thumbnail_path)
        else:
            flash("Invalid image format")
            return redirect(url_for('book_add'))
    else:
        thumbnail_path=None
        



    if 'content' in request.files:
        content = request.files['content']
        if content and allowed_file(content.filename):
            filename = secure_filename(content.filename)
            content_path =os.path.join(app.config['UPLOAD_FOLDER'], filename)
            content.save(content_path)
        else:
            flash("Invalid content format")
            return redirect(url_for('book_add'))
    else:
        content_path = None
        

    


    

    thumbnail_path = thumbnail_path[6:]
    content_path = content_path[6:]
    

    

    book = Book.query.get(id)
    book.name = name
    book.thumbnail_path = thumbnail_path.replace('\\', '/')
    book.content_path = content_path.replace('\\', '/')
    
    book.author = author
    book.date_issued = date_issued
    book.section_id = section.section_id
    db.session.commit()
    flash("Book updated successfully")
    return redirect(url_for('section_view', id=section.section_id))



@app.route('/book/delete/<int:id>',)
@librarian_required
def book_delete(id):
    book = Book.query.get(id)
    if not book:
        flash("Book does not exist")
        return redirect(url_for('librarian'))
    return render_template('book/delete.html', user=User.query.get(session['user_id']), book=book)

@app.route('/book/delete/<int:id>', methods=['POST'])
@librarian_required
def book_delete_post(id):
    book = Book.query.get(id)
    if not book:
        flash("Book does not exist")
        return redirect(url_for('librarian'))
    db.session.delete(book)
    db.session.commit()
    flash("Book deleted successfully")
    return redirect(url_for('section_view', id=book.section_id))

# ================== USER ACTIVITY ===============


@app.route('/activity/<int:id>')
@librarian_required
def activity(id):
    return render_template('section/activity.html', user=User.query.get(session['user_id']), section=Section.query.get(id))



@app.route('/book/revoke/<int:user_id>/<int:book_id>')
@librarian_required
def book_revoke(user_id, book_id):
    user = User.query.get(user_id)
    book = Book.query.get(book_id)

    if not user or not book:
        flash("User or book does not exist")
        return redirect(url_for('librarian'))

    all_users = User.query.all()

    return render_template('book/revoke.html', user=user, book=book, all_users=all_users)


@app.route('/book/revoke/<int:user_id>/<int:book_id>', methods=['POST'])
@librarian_required
def book_revoke_post(user_id, book_id):
    user = User.query.get(user_id)
    book = Book.query.get(book_id)

    if not user or not book:
        flash("User or book does not exist")
        return redirect(url_for('librarian'))

    # Check CSRF token for security
    if request.form.get('confirmation') != 'CONFIRM':
        flash("Confirmation text is incorrect. Access not revoked.")
        return redirect(url_for('activity', id=book.section_id))

    # Add logic to revoke access for the user to the specified book
    if user not in book.users_access:
        flash(f"{user.username} does not have access to {book.name}")
        return redirect(url_for('activity', id=book.section_id))

    try:
        book.users_access.remove(user)
        db.session.commit()
        flash(f"{user.username} no longer has access to {book.name}")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to revoke access: {str(e)}")

    return redirect(url_for('activity', id=book.section_id))





@app.route('/book/activate/<int:user_id>/<int:book_id>')
@librarian_required
def book_activate(user_id, book_id):
    user = User.query.get(user_id)
    book = Book.query.get(book_id)

    if not user or not book:
        flash("User or book does not exist")
        return redirect(url_for('librarian'))
    
    all_users = User.query.all()

    return render_template('book/activate.html', user=user, book=book, all_users=all_users,)


@app.route('/book/activate/<int:user_id>/<int:book_id>', methods=['POST'])
@librarian_required
def book_activate_post(user_id, book_id):
    user = User.query.get(user_id)
    book = Book.query.get(book_id)

    if not user or not book:
        flash("User or book does not exist")
        return redirect(url_for('librarian'))

    confirmation = request.form.get('confirmation')

    if confirmation != 'CONFIRM':
        flash("Confirmation text is incorrect. Access not activated.")
        return redirect(url_for('activity', id=book.section_id))

    # Add logic to activate access for the user to the specified book
    # ...
    if user in book.users_access:
        flash(f"{user.username} already has access to {book.name}")
        return redirect(url_for('activity', id=book.section_id))

    try:
        book.users_access.append(user)
        db.session.commit()
        flash(f"{user.username} now has access to {book.name}")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to activate access: {str(e)}")

    return redirect(url_for('activity', id=book.section_id))


@app.route('/status/<int:id>')
@librarian_required
def status(id):
    requests = Request.query.filter_by(user_id=id).all()
    name = User.query.get(id).name
    id = session['user_id']
    return render_template('status.html', requests=requests , id=id, name=name)
#===============================================================================================================

# ==============USER DASHBOARD==============
#===========================================

@app.route('/')
@auth_required
def index():
    user = User.query.get(session['user_id'])

    top_books = db.session.query(Book).join(Feedback).group_by(Book.book_id).order_by(db.func.count(Feedback.book_id).desc()).limit(5).all()
    
    if user.is_librarian:
        return redirect(url_for('librarian'))
    else:
        return render_template('index.html', 
                               user=user,
                                sections=Section.query.all(),
                                feedbacks = Feedback.query.filter_by(book_id=Book.book_id).order_by(Feedback.feedback_date.desc()).all(), 
                                top_books=top_books)
    

@app.route('/book/details/<int:id>')
@auth_required
def book_details(id):
    book = Book.query.get(id)
    feedbacks = Feedback.query.filter_by(book_id=book.book_id).all()
    return render_template('book/details.html', book=book, feedbacks=feedbacks, user=User.query.get(session['user_id']))

@app.route('/search')
@auth_required
def search():
    query = request.args.get('query')
    books = Book.query.filter(or_(Book.name.contains(query), Book.author.contains(query))).all()
    sections = Section.query.filter(or_(Section.name.contains(query), Section.description.contains(query))).all()
    return render_template('search_results.html',
                            books=books,
                              sections=sections,
                              query=query,
                                user=User.query.get(session['user_id']))



# ================ BOOKS STATS ===============

@app.route('/stats')
@auth_required
def stats():
    user = User.query.get(session['user_id'])
    # Get statistics data
    total_users = User.query.count()
    total_books = Book.query.count()
    total_requests = Request.query.count()
    average_rating = Feedback.query.with_entities(db.func.avg(Feedback.rating)).scalar()

    # Create a bar chart using matplotlib
    labels = ['Total Users', 'Total Books', 'Total Requests', 'Average Rating']
    values = [total_users, total_books, total_requests, average_rating]

    plt.figure(figsize=(8, 5))
    plt.bar(labels, values, color=['blue', 'green', 'orange', 'purple'])
    plt.title('Library Statistics')
    plt.xlabel('Categories')
    plt.ylabel('Values')

    # Save the plot to a BytesIO object
    image_stream = BytesIO()
    plt.savefig(image_stream, format='png')
    image_stream.seek(0)
    encoded_image = base64.b64encode(image_stream.read()).decode('utf-8')

    plt.close()

    # Render the template with the graph and other statistics
    return render_template('stats.html', encoded_image=encoded_image,
                            total_users=total_users,
                              total_books=total_books,
                                total_requests=total_requests,
                                  average_rating=average_rating, 
                                  user=user)




# ================ REQUEST AND RETURN ===============
@app.route('/book/request/<int:id>')
@auth_required
def book_request(id):
    user_id = session['user_id']
    book = Book.query.get(id)
    if user_id not in [user.id for user in book.users_access]:
        flash("You do not have access to this book")
        return redirect(url_for('book_summary', id=id))

    if not book:
        flash("Book not found")
        return redirect(url_for('index'))

    request_date = datetime.now().date()
    # Check if the user has already requested the maximum allowed  books
    total_requests = Request.query.filter_by(user_id=user_id).count()
    if total_requests >= 5:
        flash("You have already requested the maximum number of books")
        return redirect(url_for('book_summary', id=id))
    #Caluclate expiration date
    expiry_period = 3
    expiry_date = request_date + timedelta(days=expiry_period)

    # Check if the user has already requested this book
    existing_request = Request.query.filter_by(user_id=user_id, book_id=id).first()
    if existing_request:
        flash("You have already requested this book")
        return redirect(url_for('book_summary', id=id))
    

    new_request = Request(user_id=user_id, book_id=id, request_date=request_date, expiry_date=expiry_date)
    db.session.add(new_request)
    db.session.commit()

    flash("Book requested successfully")
    return redirect(url_for('mybooks'))


@app.route('/mybooks')
@auth_required
def mybooks():
    user_id = session['user_id']
    requests = Request.query.filter_by(user_id=user_id).all()
    current_date = datetime.now().date()
    expired_request = Request.query.filter(Request.expiry_date <= current_date).all()
    
    return render_template('mybooks.html', 
                           requests=requests ,
                            expired_request=expired_request,
                              user_id=user_id,user=User.query.get(user_id))

@app.route('/booksummary/<int:id>')
@auth_required
def book_summary(id):
    user_id = User.query.get(session['user_id'])
    book = Book.query.get(id)
    return render_template('booksummary.html', book=book, user=user_id)

@app.route('/book/return/<int:id>')
@auth_required
def book_return(id):
    user_id = session['user_id']
    book = Book.query.get(id)

    if not book:
        flash("Book not found")
        return redirect(url_for('index'))

    # Check if the user has requested this book
    request = Request.query.filter_by(user_id=user_id, book_id=id).first()
    if not request:
        flash("You haven't requested this book")
        return redirect(url_for('index'))

    db.session.delete(request)
    db.session.commit()

    flash("Book returned successfully")
    return redirect(url_for('mybooks'))



# ================== FEEDBACK ===============


@app.route('/feedback/<int:book_id>')
@auth_required
def feedback(book_id):
    book = Book.query.get(book_id)
    return render_template('feedback.html', book=book)

@app.route('/feedback/<int:book_id>', methods=['POST'])
@auth_required
def feedback_post(book_id):
    comment = request.form.get('comment')
    rating = request.form.get('rating')
    feedback_date = datetime.now().date()
    feedback = Feedback(user_id=session['user_id'], book_id=book_id, comment=comment, rating=rating, feedback_date=feedback_date)
    db.session.add(feedback)
    db.session.commit()
    return redirect(url_for('book_details', id=book_id))


#============================================================================================================
#=====================================================================================================



















