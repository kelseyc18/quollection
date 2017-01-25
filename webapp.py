from flask import Flask, url_for, flash, render_template, redirect, request, g, send_from_directory
from flask import session as login_session
from model import *
import random

app = Flask(__name__)
app.secret_key = "239238423sdf83sfjk3"

engine = create_engine('sqlite:///quollection.db')
Base.metadata.bind = engine
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine, autoflush=False)
session = DBSession()

@app.route('/')
def homepage():
    if 'id' not in login_session:
        return redirect(url_for('login'))
    all_quotes = session.query(Quote).filter_by(user_id=login_session['id']).all()
    if len(all_quotes) > 0:
        random_quote = random.choice(all_quotes)
        return render_template('home.html', random_quote=random_quote)
    else:
        return render_template('home.html')

@app.route('/all')
def view_all_quotes():
    if 'id' not in login_session:
        flash("You must be logged in to perform this action", 'alert-danger')
        return redirect(url_for('login'))
    quotes = session.query(Quote).filter_by(user_id=login_session['id']).all()
    return render_template('all_quotes.html', quotes=quotes)

@app.route('/mood/<int:mood_id>')
def view_quotes_by_mood(mood_id):
    if 'id' not in login_session:
        flash("You must be logged in to perform this action", 'alert-danger')
        return redirect(url_for('login'))
    mood = session.query(Mood).filter_by(id=mood_id).one()
    moodAssociations = session.query(MoodAssociation).filter_by(mood_id=mood_id).all()
    quotes = []
    for moodAssociation in moodAssociations:
        quotes.append(moodAssociation.quote)
    return render_template('all_quotes.html', quotes=quotes, mood=mood)

def verify_password(email, password):
    user = session.query(User).filter_by(email=email).first()
    if not user or not user.verify_password(password):
        return False
    return True

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        if 'id' in login_session:
            flash("You are already logged in.", 'alert-info')
            return redirect(url_for('homepage'))
        email = request.form['email']
        password = request.form['password']
        if email is None or password is None:
            flash('Missing Arguments', 'alert-danger')
            return redirect(url_for('login'))
        if verify_password(email, password):
            user = session.query(User).filter_by(email=email).one()
            flash('Login Successful. Welcome, %s!' % user.name, 'alert-success')
            login_session['name'] = user.name
            login_session['email'] = user.email
            login_session['id'] = user.id
            return redirect(url_for('homepage'))
        else:
            # incorrect username/password
            flash('Incorrect username/password combination', 'alert-danger')
            return redirect(url_for('login'))

@app.route('/logout')
def logout():
    if 'id' not in login_session:
        flash("You must be logged in order to log out", 'alert-warning')
        return redirect(url_for('login'))
    del login_session['name']
    del login_session['email']
    del login_session['id']
    flash("Logged Out Successfully", 'alert-success')
    return redirect(url_for('login'))

@app.route('/new_user', methods = ['GET', 'POST'])
def new_user():
    if request.method == 'GET':
        return render_template('new_user.html')
    elif request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if name is None or email is None or password is None:
            flash("Your form is missing arguments", 'alert-danger')
            return redirect(url_for('new_user'))
        if session.query(User).filter_by(email = email).first() is not None:
            flash("A user with this email address already exists", 'alert-danger')
            return redirect(url_for('new_user'))
        user = User(name=name, email=email)
        user.hash_password(password)
        session.add(user)
        session.commit()
        return redirect(url_for('login'))

@app.route('/add_quote', methods = ['GET', 'POST'])
def add_quote():
    if 'id' not in login_session:
        flash("You must be logged in to perform this action", 'alert-info')
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('add_quote.html')
    elif request.method == 'POST':
        text = request.form['text']
        source = request.form['source']
        quote_source = request.form['quote_source']
        user = session.query(User).filter_by(id=login_session['id']).one()
        quote = Quote(text=text, source=source, quote_source=quote_source, user_id=login_session['id'])

        # Handle moods
        mood_names = request.form['moods']
        update_mood_associations(mood_names, user, quote)
        return redirect(url_for('view_all_quotes'))

@app.route('/edit/<int:quote_id>', methods = ['GET', 'POST'])
def edit_quote(quote_id):
    if 'id' not in login_session:
        flash("You must be logged in to perform this action", 'alert-info')
        return redirect(url_for('login'))
    if request.method == 'GET':
        quote = session.query(Quote).filter_by(id=quote_id).one()
        if quote.user_id != login_session['id']:
            flash("You do not have the access privilege to view this quote", 'alert-danger')
            return redirect(url_for('view_all_quotes'))
        moodAssociations = session.query(MoodAssociation).filter_by(quote_id=quote_id).all()
        moods_list = [moodAssociation.mood.description for moodAssociation in moodAssociations]
        print moods_list
        moods_string = ", ".join(moods_list)
        print moods_string
        return render_template('edit_quote.html', quote=quote, moods=moods_string)
    elif request.method == 'POST':
        print 'post to edit_quote'
        text = request.form['text']
        source = request.form['source']
        quote_source = request.form['quote_source']
        quote = session.query(Quote).filter_by(id=quote_id).one()
        user = session.query(User).filter_by(id=login_session['id']).one()
        session.query(MoodAssociation).filter_by(quote_id=quote_id).delete()
        session.commit()

        # Handle moods
        mood_names = request.form['moods']
        update_mood_associations(mood_names, user, quote)
        flash("Your quote has been successfully edited.", 'alert-success')
        return redirect(url_for('view_all_quotes'))

def update_mood_associations(mood_names, user, quote):
    mood_names = mood_names.split(',')
    for mood_name in mood_names:
        mood_name = mood_name.lower().lstrip().rstrip()
        mood = session.query(Mood).filter_by(description=mood_name).first()
        if mood is None:
            mood = Mood(description=mood_name, user=user, user_id=login_session['id'])
            session.add(mood)
            session.commit()
        assoc = MoodAssociation(mood=mood, quote=quote)
        session.add_all([mood, quote, assoc])
        session.commit()

if __name__ == '__main__':
    app.run(debug=True)
