from datetime import datetime
import os
from datetime import datetime, timedelta
import ssl
from email.message import EmailMessage
import bcrypt
import secrets
import smtplib
import re
import requests
from pyotp import TOTP
# from apps import App
from flask import json
# from utilities import Utilities
from flask import (
    render_template,
    session,
    url_for,
    flash,
    redirect,
    request,
    Flask,
)

from flask_mail import Mail
from flask_pymongo import PyMongo
from tabulate import tabulate
from forms import (
    HistoryForm,
    RegistrationForm,
    LoginForm,
    CalorieForm,
    UserProfileForm,
    EnrollForm,
    WorkoutForm,
    TwoFactorForm,
    getDate,
    QuestionForm,
)
from service import history as history_service
import openai
from flask import jsonify
import random
from flask_apscheduler import APScheduler
from urllib.parse import quote
from model.meal_recommendation import recommend_meal_plan
from time import time

app = Flask(__name__)

app.secret_key = 'secret'
if os.environ.get('DOCKERIZED'):
    # Use Docker-specific MongoDB URI
    app.config['MONGO_URI'] = 'mongodb://mongo:27017/test'
else:
    # Use localhost MongoDB URI
    app.config['MONGO_URI'] = 'mongodb://localhost:27017/test'
app.config['MONGO_CONNECT'] = False
mongo = PyMongo(app)
app.config['RECAPTCHA_PUBLIC_KEY'] = "6LfVuRUpAAAAAI3pyvwWdLcyqUvKOy6hJ_zFDTE_"
app.config[
    'RECAPTCHA_PRIVATE_KEY'] = "6LfVuRUpAAAAANC8xNC1zgCAf7V66_wBV0gaaLFv"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = "bogusdummy123@gmail.com"
app.config['MAIL_PASSWORD'] = "helloworld123!"
mail = Mail(app)

scheduler = APScheduler()


@app.context_processor
def inject_cache_buster():
    return {'cache_buster': time()}


@app.route("/")
@app.route("/home")
def home():
    """
    home() function displays the homepage of our website.
    route "/home" will redirect to home() function.
    input: The function takes session as the input
    Output: Out function will redirect to the login page
    """
    print("Start")
    if session.get('email'):
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


@app.route("/login", methods=['GET', 'POST'])
def login():
    """"
    login() function displays the Login form (login.html) template
    route "/login" will redirect to login() function.
    LoginForm() called and if the form is submitted
    then various values are fetched and verified
    from the database entries
    Input: Email, Password, Login Type
    Output: Account Authentication and redirecting to Dashboard
    """

    if not session.get('email'):
        form = LoginForm()
        if form.validate_on_submit():
            temp = mongo.db.user.find_one(
                {'email': form.email.data},
                {'email', 'username', 'password', 'last_login', 'streak'})
            if temp is not None and temp['email'] == form.email.data and (
                    bcrypt.checkpw(form.password.data.encode("utf-8"),
                                   temp['password'])
                    or temp['password'] == form.password.data):
                flash('You have been logged in!', 'success')
                session['email'] = temp['email']
                session['username'] = temp['username']
                print(temp)
                last_login = temp.get('last_login')
                if datetime.now().date() - last_login.date() == timedelta(
                        days=1):
                    mongo.db.user.update_one(
                        {'email': form.email.data},
                        {
                            "$inc": {"streak": 1},
                            "$set": {"last_login": datetime.now()},
                        }
                    )
                else:
                    mongo.db.user.update_one(
                        {'email': form.email.data},
                        {
                            "$set": {
                                "streak": 0,
                                "last_login": datetime.now(),
                            }
                        }
                    )
                temp1 = mongo.db.user.find_one({'email': form.email.data},
                                               {'streak'})
                print(f"temp1={temp1}\nsession={session}")
                session['streak'] = temp1['streak']
                return redirect(url_for('dashboard'))
            else:
                flash(
                    'Login Unsuccessful. Please check username and password',
                    'danger'
                )

    else:
        return redirect(url_for('home'))
    return render_template('login.html', title='Login', form=form)


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    """
    logout() function just clears out the session and returns success
    route "/logout" will redirect to logout() function.
    Output: session clear
    """
    session.clear()
    return "success"


@app.route("/register", methods=['GET', 'POST'])
def register():
    """
    register() function displays the
    Registration portal (register.html) template
    route "/register" will redirect to
    register() function.
    RegistrationForm() called and if the form is
    submitted then various values are
    fetched and updated into the database
    Input: Username, Email, Password,
    Confirm Password, current height,
    current weight, target weight, target date
    Output: Value update in the
    database and redirected to the dashboard
    """
    print("here0")
    if not session.get('email'):
        form = RegistrationForm()
        if form.validate_on_submit():
            print("here1")
            email = request.form.get('email')
            password = request.form.get('password')

            # Generate and save 2FA secret to the session
            secret_key = secrets.token_urlsafe(20).replace('=', '')
            print("here2")
            totp = TOTP(secret_key)
            print("here3")
            two_factor_secret = totp.secret
            session['two_factor_secret'] = two_factor_secret
            session['registration_data'] = {
                'username':
                request.form.get('username'),
                'email':
                email,
                'password':
                bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()),
                'weight':
                request.form.get('weight'),
                'height':
                request.form.get('height'),
                'target_weight':
                request.form.get('target_weight'),
                'start_date':
                datetime.now().strftime('%Y-%m-%d'),
                'target_date':
                request.form.get('target_date'),
                'completed_challenges':
                {}  # Initialize with an empty dictionary
            }
            print("here4")
            send_2fa_email(email, two_factor_secret)
            print("here5")
            # Redirect to 2FA verification page
            return redirect(url_for('verify_2fa'))
        else:
            print("here6")
            return render_template('register.html',
                                   title='Register',
                                   form=form)
    else:
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


def send_2fa_email(email, two_factor_secret):

    sender = 'burnoutapp123@gmail.com'
    password = 'xszyjpklynmwqsgh'
    receiver = email

    subject = 'Two-Factor Authentication Code'
    body = f'Your Two-Factor Authentication Code: {two_factor_secret}'

    try:

        em = EmailMessage()
        em['From'] = sender
        em['To'] = receiver
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, receiver, em.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
        flash(
            'Failed to send Two-Factor Authentication code. Please try again.',
            'danger')


@app.route("/user_profile", methods=['GET', 'POST'])
def user_profile():
    """
    user_profile() function displays the
    UserProfileForm (user_profile.html) template
    route "/user_profile" will redirect
    to user_profile() function.
    user_profile() called and if the form is
    submitted then various values are fetched
    and updated into the database entries
    Input: Email, height, weight, goal, Target weight
    Output: Value update in database and redirected to home login page
    """
    if session.get('email'):
        form = UserProfileForm()
        email = session.get('email')

        # Fetch existing user profile data
        existing_profile = mongo.db.profile.find_one({'email': email}, {
            'height': 1,
            'weight': 1,
            'target_weight': 1,
            'goal': 1
        })
        existing_user = mongo.db.user.find_one({'email': email}, {
            'height': 1,
            'weight': 1,
            'target_weight': 1
        })
        print(existing_profile)
        # Populate the form with existing values
        form.populate_obj(request.form)
        if existing_profile:
            form.weight.data = request.form.get('weight')
            form.height.data = request.form.get('height')
            form.goal.data = request.form.get('goal')
            form.target_weight.data = request.form.get('target_weight')
        if form.validate_on_submit():
            # Get form values
            weight = form.weight.data
            height = form.height.data
            goal = form.goal.data
            target_weight = form.target_weight.data
            if existing_profile is not None:
                # Update existing profile
                mongo.db.profile.update_one({'email': email}, {
                    '$set': {
                        'weight': form.weight.data,
                        'height': form.height.data,
                        'goal': form.goal.data,
                        'target_weight': form.target_weight.data
                    }
                })
            else:
                # Insert new profile
                mongo.db.profile.insert_one({
                    'email': email,
                    'height': height,
                    'weight': weight,
                    'goal': goal,
                    'target_weight': target_weight
                })
            flash('User Profile Updated', 'success')

            # Redirect to a page where you display the updated profile
            return redirect(url_for('user_profile'))

    else:
        return redirect(url_for('login'))

    return render_template('user_profile.html',
                           status=True,
                           form=form,
                           existing_profile=existing_profile,
                           existing_user=existing_user)


@app.route("/calories", methods=['GET', 'POST'])
def calories():
    """
    calorie() function displays the Calorieform (calories.html) template
    route "/calories" will redirect to calories() function.
    CalorieForm() called and if the form is submitted
    then various values are fetched and updated
    into the database entries
    Input: Email, date, food, burnout
    Output: Value update in database and redirected to home page
    """
    # now = datetime.now()
    # now = now.strftime('%Y-%m-%d')

    get_session = session.get('email')
    if get_session is not None:
        form = CalorieForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                email = session.get('email')
                food = request.form.get('food')
                selected_date = request.form.get('target_date')
                # cals = food.split(" ")
                # print('cals is ',cals)
                match = re.search(r'\((\d+)\)', food)
                if match:
                    cals = int(match.group(1))
                else:
                    cals = 0
                # cals = int(cals[1][1:len(cals[1]) - 1])
                mongo.db.calories.insert_one({
                    'date': selected_date,
                    'email': email,
                    'calories': cals
                })
                flash('Successfully sent email and updated the data!',
                      'success')
                add_food_entry_email_notification(email, food, selected_date)
                return redirect(url_for('calories'))

    else:
        return redirect(url_for('home'))
    return render_template('calories.html', form=form)


def add_food_entry_email_notification(email, food, date):
    sender = 'burnoutapp123@gmail.com'
    password = 'xszyjpklynmwqsgh'
    receiver = email

    subject = 'New food entry recorded'
    body = f'You recorded a new entry for {food} on the date {date}'

    try:

        em = EmailMessage()
        em['From'] = sender
        em['To'] = receiver
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, receiver, em.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
        flash('Failed to send email but the entry is recorded', 'danger')


def add_burn_entry_email_notification(email, burn, date):
    sender = 'burnoutapp123@gmail.com'
    password = 'xszyjpklynmwqsgh'
    receiver = email

    subject = 'New burn entry recorded'
    body = f'You recorded a new entry of {burn} on  {date}'

    try:

        em = EmailMessage()
        em['From'] = sender
        em['To'] = receiver
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, receiver, em.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
        flash('Failed to send email but the entry is recorded', 'danger')


@app.route("/workout", methods=['GET', 'POST'])
def workout():
    # now = datetime.now()
    # now = now.strftime('%Y-%m-%d')
    get_session = session.get('email')
    if get_session is not None:
        form = WorkoutForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                email = session.get('email')
                burn = request.form.get('burnout')
                selected_date = request.form.get('target_date')

                mongo.db.calories.insert_one({
                    'date': selected_date,
                    'email': email,
                    'calories': -float(burn)
                })
                if float(burn) < 100:
                    existing_user_entry = mongo.db.bronze_list.find_one({
                        'date':
                        selected_date,
                        'users':
                        email
                    })
                    if existing_user_entry:
                        mongo.db.bronze_list.delete_one({
                            'date': selected_date,
                            'users': email
                        })
                if float(burn) > 100:
                    flash(
                        f'YaY!You are in bronze list: {selected_date}',
                        'success'
                    )
                    existing_user_entry = mongo.db.bronze_list.find_one({
                        'date':
                        selected_date,
                        'users':
                        email
                    })
                    if existing_user_entry:
                        mongo.db.bronze_list.update_one(
                            {'date': selected_date},
                            {'$addToSet': {
                                'users': email
                            }})
                    else:
                        mongo.db.bronze_list.insert_one({
                            'date': selected_date,
                            'users': [email]
                        })

                flash('Successfully sent email and updated the data!',
                      'success')
                add_burn_entry_email_notification(email, burn, selected_date)
                return redirect(url_for('workout'))
    else:
        return redirect(url_for('home'))
    return render_template('workout.html', form=form)


# New route to display the bronze list for the current day
@app.route("/bronze_list", methods=['GET', 'POST'])
def bronze_list_page():
    form = getDate()

    if request.method == 'POST' and form.validate_on_submit():
        today = form.target_date.data.strftime('%Y-%m-%d')

        bronze_list_cursor = mongo.db.bronze_list.find({'date': today})

        if bronze_list_cursor:
            bronze_users = []
            for bronze_doc in bronze_list_cursor:
                users = bronze_doc.get('users', [])
                # Add the users from the database
                bronze_users.extend(users)
                mongo.db.bronze_list.update_one({'_id': bronze_doc['_id']},
                                                {'$set': {
                                                    'users': users
                                                }})
        else:
            # If no document exists for today, create a new one
            mongo.db.bronze_list.insert_one({'date': today, 'users': users})
            bronze_users = users

        return render_template('bronze_list.html',
                               title='Bronze List',
                               form=form,
                               bronze_users=bronze_users)

    return render_template('bronze_list.html',
                           title='Bronze List',
                           form=form,
                           bronze_users=[])


@app.route("/quiz", methods=['GET', 'POST'])
def quiz():
    # ############################
    # quiz() function displays the quiz start page.
    # The route "/quiz" triggers this function,
    # which initializes a form and renders the main layout template.
    # - Input: None (form is initialized but not directly used here).
    # - Output: Renders 'layout.html' as the quiz introduction or start page.
    # ############################
    # form = getDate()
    return render_template('layout.html')

@app.route("/water", methods=['GET', 'POST'])
def water():
    return render_template('water.html')


@app.route('/question/<int:id>', methods=['GET', 'POST'])
def question(id):
    # ############################
    # question() function displays and processes each
    # quiz question based on the provided question ID.
    # The route "/question/<int:id>" triggers this function,
    # which retrieves the question and handles user answers.
    # - Input: Question ID (URL parameter),
    # form submission with selected answer.
    # - Output: If answer is correct, 10 points
    # are added to the user's score;
    # otherwise, no points are added.
    #           Redirects to the next question or
    # the score page upon completion.
    # ############################

    form = QuestionForm()
    q = mongo.db.questions.find_one({"q_id": id})

    if 'marks' not in session:
        session['marks'] = 0

    if not q:
        return redirect(url_for('score'))

    answer_mapping = {
        q['options']['a']: 'a',
        q['options']['b']: 'b',
        q['options']['c']: 'c',
        q['options']['d']: 'd'
    }

    if request.method == 'POST':
        option = request.form['options']
        option = answer_mapping.get(option)

        print(option)
        print(q['ans'])
        if option == q['ans']:
            session['marks'] += 10
            print(f"Current Marks: {session['marks']}")
        return redirect(url_for('question', id=(id + 1)))

    form.options.choices = [(q['options']['a'], q['options']['a']),
                            (q['options']['b'], q['options']['b']),
                            (q['options']['c'], q['options']['c']),
                            (q['options']['d'], q['options']['d'])]

    return render_template('question.html',
                           form=form,
                           q=q,
                           title='Question {}'.format(id),
                           score=session.get('marks'))


@app.route('/score')
def score():
    # ############################
    # score() function displays the user's
    # final score at the end of the quiz.
    # The route "/score" triggers this function,
    # rendering a final score summary page.
    # - Input: None.
    # - Output: Renders 'score.html' with the
    # total score accumulated in the session.
    # ############################

    return render_template('score.html',
                           title='Final Score',
                           score=session.get('marks', 0))


@app.route("/history", methods=['GET'])
def history():
    # ############################
    # history() function displays the Historyform (history.html) template
    # route "/history" will redirect to history() function.
    # HistoryForm() called and if the form is submitted
    # then various values are fetched and update into the database entries
    # Input: Email, date
    # Output: Value fetched and displayed
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        form = HistoryForm()

    # Find out the last 7 day's calories burnt by the user
    labels = []
    values = []
    pipeline = history_service.get_calories_per_day_pipeline(7)
    filtered_calories = mongo.db.calories.aggregate(pipeline)
    for calorie_each_day in filtered_calories:
        if calorie_each_day['_id'] == 'Other':
            continue
        net_calories = int(calorie_each_day['total_calories']) - 2000
        labels.append(calorie_each_day['date'])
        values.append(str(net_calories))

    # The first day when the user registered or started using the app
    user_start_date = mongo.db.user.find({'email': email})[0]['start_date']
    user_target_date = mongo.db.user.find({'email': email})[0]['target_date']
    target_weight = mongo.db.user.find({'email': email})[0]['target_weight']
    current_weight = mongo.db.user.find({'email': email})[0]['weight']

    # Find out the actual calories which user needed
    # to burn/gain to achieve goal from the start day
    target_calories_to_burn = history_service.total_calories_to_burn(
        target_weight=int(target_weight), current_weight=int(current_weight))
    print(f'########## {target_calories_to_burn}')

    # Find out how many calories user has gained or burnt uptill now
    calories_till_today = mongo.db.calories.aggregate(
        history_service.get_calories_burnt_till_now_pipeline(
            email, user_start_date))
    current_calories = 0
    for calorie in calories_till_today:
        current_calories += calorie['SUM']
    # current_calories = [x for x in calories_till_today][0]['SUM']
    # if len(list(calories_till_today)) != 0 else 0

    # Find out no of calories user has to burn/gain in future per day
    calories_to_burn = history_service.calories_to_burn(
        target_calories_to_burn,
        current_calories,
        target_date=datetime.strptime(user_target_date, '%Y-%m-%d'),
        start_date=datetime.strptime(user_start_date, '%Y-%m-%d'))

    return render_template('history.html',
                           form=form,
                           labels=labels,
                           values=values,
                           burn_rate=calories_to_burn,
                           target_date=user_target_date)


@app.route("/ajaxhistory", methods=['POST'])
def ajaxhistory():
    # ############################
    # ajaxhistory() is a POST function that displays
    # and fetches various information from the database.
    # Route "/ajaxhistory" will redirect
    # to ajaxhistory() function.
    # Details corresponding to the given
    # email address are fetched
    # from the database entries.
    # Input: Email, date
    # Output: date, email, calories, burnout
    # ##########################
    email = get_session = session.get('email')
    print(email)
    if get_session is not None:
        if request.method == "POST":
            date = request.form.get('date')
            res = mongo.db.calories.find_one({
                'email': email,
                'date': date
            }, {'date', 'email', 'calories', 'burnout'})
            if res:
                return json.dumps({
                    'date': res['date'],
                    'email': res['email'],
                    'burnout': res['burnout'],
                    'calories': res['calories']
                }), 200, {
                    'ContentType': 'application/json'
                }
            else:
                return json.dumps({
                    'date': "",
                    'email': "",
                    'burnout': "",
                    'calories': ""
                }), 200, {
                    'ContentType': 'application/json'
                }


@app.route("/friends", methods=['GET'])
def friends():
    email = session.get('email')
    myFriends = list(
        mongo.db.friends.find({
            'sender': email,
            'accept': True
        }, {'sender', 'receiver', 'accept'}))
    myFriendsList = list()

    for f in myFriends:
        myFriendsList.append(f['receiver'])

    print(myFriends)
    allUsers = list(mongo.db.user.find({}, {'name', 'email'}))

    pendingRequests = list(
        mongo.db.friends.find({
            'sender': email,
            'accept': False
        }, {'sender', 'receiver', 'accept'}))
    # Count the number of pending friend requests

    pendingReceivers = list()
    for p in pendingRequests:
        pendingReceivers.append(p['receiver'])

    pendingApproves = list()
    pendingApprovals = list(
        mongo.db.friends.find({
            'receiver': email,
            'accept': False
        }, {'sender', 'receiver', 'accept'}))
    pending_requests_count = len(pendingApprovals)
    if len(pendingApprovals):
        # Flash the count to be displayed in the template
        flash(f"You have {pending_requests_count} pending friend requests.",
              'info')
    for p in pendingApprovals:
        pendingApproves.append(p['sender'])

    # print(pendingApproves)

    # Retrieve burn_rate and target_date from the user's data
    user_data = mongo.db.user.find_one({"email": email})
    burn_rate = user_data.get("burn_rate",
                              0)  # Adjust if burn_rate calculation differs
    target_date = user_data.get("target_date", "your goal date")

    # Create the shareable message
    # Ensure this is properly aligned with the preceding block
    if burn_rate > 0:
        shareable_message = (
            f"I’m working hard to gain {abs(burn_rate)} calories daily "
            f"to reach my goal by {target_date}! #CalorieApp"
        )
    else:
        shareable_message = (
            f"Burning {abs(burn_rate)} calories daily to stay on track for my "
            f"goal by {target_date}! #CalorieApp"
        )

    # print(pendingRequests)
    return render_template('friends.html',
                           allUsers=allUsers,
                           pendingRequests=pendingRequests,
                           active=email,
                           pendingReceivers=pendingReceivers,
                           pendingApproves=pendingApproves,
                           myFriends=myFriends,
                           myFriendsList=myFriendsList,
                           burn_rate=burn_rate,
                           target_date=target_date,
                           shareable_message=shareable_message)


@app.route("/send_email", methods=['GET', 'POST'])
def send_email():
    # ############################
    # send_email() function shares Calorie History with friend's email
    # route "/send_email" will redirect to send_email()
    # function which redirects to friends.html page.
    # Input: Email
    # Output: Calorie History Received on specified email
    # ##########################
    email = session.get('email')
    data = list(
        mongo.db.calories.find({'email': email},
                               {'date', 'email', 'calories', 'burnout'}))
    table = [['Date', 'Email ID', 'Calories', 'Burnout']]
    for a in data:
        tmp = [a['date'], a['email'], a['calories'], a['burnout']]
        table.append(tmp)

    friend_email = str(request.form.get('share')).strip()
    friend_email = str(friend_email).split(',')
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    # Storing sender's email address and password
    sender_email = "calorie.app.server@gmail.com"
    sender_password = "Temp@1234"

    # Logging in with sender details
    server.login(sender_email, sender_password)
    message = (
        'Subject: Calorie History\n\n'
        'Your Friend wants to share their calorie history with you!\n'
        '{}'.format(tabulate(table))
    )
    for e in friend_email:
        print(e)
        server.sendmail(sender_email, e, message)

    server.quit()

    myFriends = list(
        mongo.db.friends.find({
            'sender': email,
            'accept': True
        }, {'sender', 'receiver', 'accept'}))
    myFriendsList = list()

    for f in myFriends:
        myFriendsList.append(f['receiver'])

    allUsers = list(mongo.db.user.find({}, {'name', 'email'}))

    pendingRequests = list(
        mongo.db.friends.find({
            'sender': email,
            'accept': False
        }, {'sender', 'receiver', 'accept'}))
    pendingReceivers = list()
    for p in pendingRequests:
        pendingReceivers.append(p['receiver'])

    pendingApproves = list()
    pendingApprovals = list(
        mongo.db.friends.find({
            'receiver': email,
            'accept': False
        }, {'sender', 'receiver', 'accept'}))
    for p in pendingApprovals:
        pendingApproves.append(p['sender'])

    return render_template('friends.html',
                           allUsers=allUsers,
                           pendingRequests=pendingRequests,
                           active=email,
                           pendingReceivers=pendingReceivers,
                           pendingApproves=pendingApproves,
                           myFriends=myFriends,
                           myFriendsList=myFriendsList)


@app.route("/ajaxsendrequest", methods=['POST'])
def ajaxsendrequest():
    # ############################
    # ajaxsendrequest() is a function that updates friend
    # request information into database
    # route "/ajaxsendrequest" will redirect to
    # ajaxsendrequest() function.
    # Details corresponding to given email address are fetched
    # from the database entries and send request details updated
    # Input: Email, receiver
    # Output: DB entry of receiver info into database and
    # return TRUE if success and FALSE otherwise
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        receiver = request.form.get('receiver')
        res = mongo.db.friends.insert_one({
            'sender': email,
            'receiver': receiver,
            'accept': False
        })
        if res:
            return json.dumps({'status': True}), 200, {
                'ContentType': 'application/json'
            }
    return json.dumps({'status': False}), 500, {
        'ContentType:': 'application/json'
    }


@app.route("/ajaxcancelrequest", methods=['POST'])
def ajaxcancelrequest():
    # ############################
    # ajaxcancelrequest() is a function that updates
    # friend request information into database
    # route "/ajaxcancelrequest" will redirect
    # to ajaxcancelrequest() function.
    # Details corresponding to given email address are fetched
    # from the database entries and cancel request details updated
    # Input: Email, receiver
    # Output: DB deletion of receiver info into database
    # and return TRUE if success and FALSE otherwise
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        receiver = request.form.get('receiver')
        res = mongo.db.friends.delete_one({
            'sender': email,
            'receiver': receiver
        })
        if res:
            return json.dumps({'status': True}), 200, {
                'ContentType': 'application/json'
            }
    return json.dumps({'status': False}), 500, {
        'ContentType:': 'application/json'
    }


@app.route("/ajaxapproverequest", methods=['POST'])
def ajaxapproverequest():
    # ############################
    # ajaxapproverequest() is a function that
    # updates friend request information into database
    # route "/ajaxapproverequest" will redirect
    # to ajaxapproverequest() function.
    # Details corresponding to given email address are fetched
    # from the database entries and approve request details updated
    # Input: Email, receiver
    # Output: DB updation of accept as TRUE info into database
    # and return TRUE if success and FALSE otherwise
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        receiver = request.form.get('receiver')
        print(email, receiver)
        res = mongo.db.friends.update_one(
            {
                'sender': receiver,
                'receiver': email
            },
            {"$set": {
                'sender': receiver,
                'receiver': email,
                'accept': True
            }})
        mongo.db.friends.insert_one({
            'sender': email,
            'receiver': receiver,
            'accept': True
        })
        if res:
            return json.dumps({'status': True}), 200, {
                'ContentType': 'application/json'
            }
    return json.dumps({'status': False}), 500, {
        'ContentType:': 'application/json'
    }


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    # ############################
    # dashboard() function displays the dashboard.html template
    # route "/dashboard" will redirect to dashboard() function.
    # dashboard() called and displays the list of activities
    # Output: redirected to dashboard.html
    # ##########################
    return render_template('dashboard.html', title='Dashboard')


@app.route("/yoga", methods=['GET', 'POST'])
def yoga():
    # ############################
    # yoga() function displays the yoga.html template
    # route "/yoga" will redirect to yoga() function.
    # A page showing details about yoga is shown and
    # if clicked on enroll then DB updation
    # done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "yoga"
                mongo.db.user.insert_one({'Email': email, 'Status': enroll})
            flash(f' You have succesfully enrolled in our {enroll} plan!',
                  'success')
            return render_template('new_dashboard.html', form=form)
            # return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('dashboard'))
    return render_template('yoga.html', title='Yoga', form=form)


@app.route("/swim", methods=['GET', 'POST'])
def swim():
    # ############################
    # swim() function displays the swim.html template
    # route "/swim" will redirect to swim() function.
    # A page showing details about swimming is shown and
    # if clicked on enroll then DB updation
    # done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "swimming"
                mongo.db.user.insert_one({'Email': email, 'Status': enroll})
            flash(f' You have succesfully enrolled in our {enroll} plan!',
                  'success')
            return render_template('new_dashboard.html', form=form)
            # return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('dashboard'))
    return render_template('swim.html', title='Swim', form=form)


@app.route("/abbs", methods=['GET', 'POST'])
def abbs():
    # ############################
    # abbs() function displays the abbs.html template
    # route "/abbs" will redirect to abbs() function.
    # A page showing details about abbs
    # workout is shown and
    # if clicked on enroll then DB updation
    # done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and
    # redirected to new dashboard
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "abbs"
                mongo.db.user.insert_one({'Email': email, 'Status': enroll})
            flash(f' You have succesfully enrolled in our {enroll} plan!',
                  'success')
            return render_template('new_dashboard.html', form=form)
    else:
        return redirect(url_for('dashboard'))
    return render_template('abbs.html', title='Abbs Smash!', form=form)


@app.route("/belly", methods=['GET', 'POST'])
def belly():
    # ############################
    # belly() function displays the belly.html template
    # route "/belly" will redirect to belly() function.
    # A page showing details about belly workout is shown and
    # if clicked on enroll then DB updation
    # done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and
    # redirected to new dashboard
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "belly"
                mongo.db.user.insertOne({'Email': email, 'Status': enroll})
            flash(f' You have succesfully enrolled in our {enroll} plan!',
                  'success')
            return render_template('new_dashboard.html', form=form)
            # return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('dashboard'))
    return render_template('belly.html', title='Belly Burner', form=form)


@app.route("/core", methods=['GET', 'POST'])
def core():
    # ############################
    # core() function displays the belly.html template
    # route "/core" will redirect to
    # core() function.
    # A page showing details about core workout is shown and
    # if clicked on enroll then DB updation
    # done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "core"
                mongo.db.user.insert_one({'Email': email, 'Status': enroll})
            flash(f' You have succesfully enrolled in our {enroll} plan!',
                  'success')
            return render_template('new_dashboard.html', form=form)
    else:
        return redirect(url_for('dashboard'))
    return render_template('core.html', title='Core Conditioning', form=form)


@app.route("/gym", methods=['GET', 'POST'])
def gym():
    # ############################
    # gym() function displays the gym.html template
    # route "/gym" will redirect to gym() function.
    # A page showing details about gym plan is shown and
    # if clicked on enroll then DB updation done
    # and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and
    # redirected to new dashboard
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "gym"
                mongo.db.user.insert_one({'Email': email, 'Status': enroll})
            flash(f' You have succesfully enrolled in our {enroll} plan!',
                  'success')
            return render_template('new_dashboard.html', form=form)
            # return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('dashboard'))
    return render_template('gym.html', title='Gym', form=form)


@app.route("/walk", methods=['GET', 'POST'])
def walk():
    # ############################
    # walk() function displays the walk.html template
    # route "/walk" will redirect to walk() function.
    # A page showing details about walk plan is shown and
    # if clicked on enroll then DB updation
    # done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment
    # and redirected to new dashboard
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "walk"
                mongo.db.user.insert_one({'Email': email, 'Status': enroll})
            flash(f' You have succesfully enrolled in our {enroll} plan!',
                  'success')
            return render_template('new_dashboard.html', form=form)
            # return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('dashboard'))
    return render_template('walk.html', title='Walk', form=form)


@app.route("/dance", methods=['GET', 'POST'])
def dance():
    # ############################
    # dance() function displays the dance.html template
    # route "/dance" will redirect to dance() function.
    # A page showing details about dance plan is shown and
    # if clicked on enroll then DB updation done
    # and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "dance"
                mongo.db.user.insert_one({'Email': email, 'Status': enroll})
            flash(f' You have succesfully enrolled in our {enroll} plan!',
                  'success')
            return render_template('new_dashboard.html', form=form)
            # return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('dashboard'))
    return render_template('dance.html', title='Dance', form=form)


@app.route("/hrx", methods=['GET', 'POST'])
def hrx():
    # ############################
    # hrx() function displays the hrx.html template
    # route "/hrx" will redirect to hrx() function.
    # A page showing details about hrx plan is shown and
    # if clicked on enroll then DB updation
    # done and redirected to new_dashboard
    # Input: Email
    # Output: DB entry about enrollment and redirected to new dashboard
    # ##########################
    email = get_session = session.get('email')
    if get_session is not None:
        form = EnrollForm()
        if form.validate_on_submit():
            if request.method == 'POST':
                enroll = "hrx"
                mongo.db.user.insert_one({'Email': email, 'Status': enroll})
            flash(f' You have succesfully enrolled in our {enroll} plan!',
                  'success')
            return render_template('new_dashboard.html', form=form)
            # return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('dashboard'))
    return render_template('hrx.html', title='HRX', form=form)


@app.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    form = TwoFactorForm()  # Create a new form for 2FA verification

    if form.validate_on_submit():
        # Verify the entered 2FA code against the stored one in the session
        entered_code = form.two_factor_code.data
        stored_code = session.get('two_factor_secret')

        if stored_code and entered_code == stored_code:
            # 2FA code is correct, proceed with registration
            user_data = session.get('registration_data')
            print(f"user_data={user_data}")
            session['email'] = user_data['email']
            user_data['last_login'] = datetime.now()
            user_data['streak'] = 1
            mongo.db.user.insert_one(user_data)
            session.pop('two_factor_secret')
            session.pop('registration_data')
            flash('Two-Factor Authentication successful! User registered.',
                  'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Two-Factor Authentication code. ', 'danger')
            flash('User registration failed. Please try again.', 'danger')
            if 'registration_data' in session:
                del session['registration_data']
            return redirect(url_for('register'))

    return render_template('verify_2fa.html', title='Verify 2FA', form=form)


# @app.route("/ajaxdashboard", methods=['POST'])
# def ajaxdashboard():
#     # ############################
#     # login() function displays the Login form (login.html) template
#     # route "/login" will redirect to login() function.
#     # LoginForm() called and if the form is submitted
    # then various values are fetched and verified from the database entries
#     # Input: Email, Password, Login Type
#     # Output: Account Authentication and redirecting to Dashboard
#     # ##########################
#     email = get_session = session.get('email')
#     print(email)
#     if get_session is not None:
#         if request.method == "POST":
#             result = mongo.db.user.find_one(
#                 {'email': email}, {'email', 'Status'})
#             if result:
#                 return json.dumps({'email': result['email'],
#    'Status': result['result']}), 200, {
#                     'ContentType': 'application/json'}
#             else:
#                 return json.dumps({'email': "", 'Status': ""}), 200, {
#                     'ContentType': 'application/json'}


def get_completion(prompt):
    print(prompt)
    query = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )

    response = query.choices[0].text
    return response


@app.route("/chat", methods=['POST', 'GET'])
def query_view():
    if request.method == 'POST':
        print('step1')
        prompt = request.form['prompt']
        response = get_completion(prompt)
        print(response)

        return jsonify({'response': response})
    return render_template('chat.html')


@app.route("/api/share", methods=['POST'])
def log_share():
    """
    Logs each social share action to the backend.
    """
    user_id = session.get('email')  # Assuming the user ID is the email
    platform = request.json.get('platform')

    if not user_id or not platform:
        return jsonify({
            "status": "error",
            "message": "User or platform not specified"
        }), 400

    # Log share action (can be stored in DB if needed)
    print(f"User {user_id} shared on {platform}.")
    return jsonify({"status": "success"})


DAILY_CHALLENGES = [
    "Drink 8 glasses of water", "Walk 5,000 steps", "Avoid sugary drinks",
    "Eat at least 3 servings of vegetables", "Complete a 15-minute meditation",
    "Do a 30-minute workout", "Sleep for at least 7 hours"
]


@app.route('/daily_challenge', methods=['GET', 'POST'])
def daily_challenge():
    user_email = session.get('email')
    if not user_email:
        # Redirect unauthorized users to the login page
        return redirect(url_for('login'))

    today = datetime.today().strftime('%Y-%m-%d')
    random.seed(today)
    daily_challenges = random.sample(DAILY_CHALLENGES, 3)

    user_data = mongo.db.users.find_one({"email": user_email},
                                        {"completed_challenges": 1}) or {}
    completed_challenges = user_data.get("completed_challenges", {})

    challenges_status = {}
    all_completed = True
    for challenge in daily_challenges:
        is_completed = completed_challenges.get(f"{today}_{challenge}", False)
        challenges_status[challenge] = is_completed
        if not is_completed:
            all_completed = False

    if request.method == 'POST':
        completed_challenge = request.form.get('completed_challenge')
        if completed_challenge and not challenges_status[completed_challenge]:
            mongo.db.users.update_one({"email": user_email}, {
                "$set": {
                    f"completed_challenges.{today}_{completed_challenge}": True
                }
            },
                upsert=True
            )
            flash(f"Challenge '{completed_challenge}' completed! Great job!",
                  "success")
            return redirect(url_for('daily_challenge'))

    # Define the shareable message if all challenges are completed
    shareable_message = ""
    if all_completed:
        shareable_message = (
            "I completed all my daily challenges today! "
            "Feeling great and staying on track with #CalorieApp."
        )
    return render_template('daily_challenge.html',
                           daily_challenges=daily_challenges,
                           challenges_status=challenges_status,
                           all_completed=all_completed,
                           shareable_message=shareable_message)


def get_weekly_summary(user_email):
    """
    Fetch weekly progress data for a user and
    prepare a summary with social sharing buttons.
    """
    today = datetime.now()
    one_week_ago = today - timedelta(days=7)

    # Fetch calories burned in the last week
    calories_burned = mongo.db.calories.find({
        "email": user_email,
        "date": {
            "$gte": one_week_ago
        }
    })
    total_calories = sum(cal["calories"] for cal in calories_burned)

    # Fetch challenges completed in the last week
    user_data = mongo.db.users.find_one({"email": user_email},
                                        {"completed_challenges": 1}) or {}
    completed_challenges = user_data.get("completed_challenges", {})
    weekly_challenges = [
        challenge_date.split('_', 1)[1]
        for challenge_date, is_completed in completed_challenges.items()
        if is_completed and datetime.strptime(
            challenge_date.split('_', 1)[0], '%Y-%m-%d') >= one_week_ago
    ]

    # Customize the message body based on user data
    message_body = f"""
    <html>
    <body>
    <p>Hello!</p>

    <p>Here’s your weekly progress summary:</p>
    <ul>
        <li>Total calories burned this week: {total_calories}</li>
        <li>Challenges completed: {len(weekly_challenges)}</li>
    </ul>

    <p>Keep up the great work and stay
    motivated for the next week!</p>
    """
    # Social sharing message
    share_message = (
        f"I’ve burned {total_calories} calories and completed "
        f"{len(weekly_challenges)} challenges this week! #CalorieApp"
    )
    encoded_share_message = quote(share_message)
    # Social sharing buttons with inline CSS for styling
    twitter_url = (
        f"https://twitter.com/intent/tweet?text={encoded_share_message}"
    )
    facebook_url = (
        "https://www.facebook.com/sharer/sharer.php?"
        f"u=https://calorieapp.com&quote={encoded_share_message}"
    )
    # Include the share message and social sharing buttons in the email body
    message_body += f"""
    <p>{share_message}</p>
    <p>
        <a href="{twitter_url}"
           style="display:inline-block; padding:10px 20px; font-size:16px;
                  color:#fff; background-color:#1DA1F2; text-decoration:none;
                  border-radius:5px; margin-right:10px;">
            Share on Twitter
        </a>
        <a href="{facebook_url}"
           style="display:inline-block; padding:10px 20px; font-size:16px;
                  color:#fff; background-color:#3b5998; text-decoration:none;
                  border-radius:5px; margin-right:10px;">
            Share on Facebook
        </a>
    </p>
    <p>Best,<br>The CalorieApp Team</p>
    </body>
    </html>
    """

    return message_body


def send_weekly_email(user_email):
    """
    Sends the weekly progress summary email
    to the user with social sharing buttons.
    """
    # Generate the email body
    email_body = get_weekly_summary(user_email)
    subject = "Your Weekly Progress Summary"

    # Setup email message
    msg = EmailMessage()
    msg.set_content(email_body,
                    subtype='html')  # Use HTML format for clickable buttons
    msg["Subject"] = subject
    msg["From"] = app.config['MAIL_USERNAME']
    msg["To"] = user_email

    # Send the email using SMTP
    try:
        with smtplib.SMTP_SSL(app.config['MAIL_SERVER'],
                              app.config['MAIL_PORT']) as smtp:
            smtp.login(app.config['MAIL_USERNAME'],
                       app.config['MAIL_PASSWORD'])
            smtp.send_message(msg)
        print(f"Weekly summary sent to {user_email}")
    except Exception as e:
        print(f"Error sending weekly summary to {user_email}: {e}")


def scheduled_weekly_email():
    """
    Scheduled job to send weekly progress emails to all users.
    """
    try:
        # Retrieve all users from the database
        users = mongo.db.user.find({}, {"email": 1})
        for user in users:
            user_email = user["email"]
            send_weekly_email(user_email)
    except Exception as e:
        print(f"Error in scheduled weekly email job: {e}")


# Scheduler job configuration
scheduler.add_job(
    id="Weekly Email Job",
    func=scheduled_weekly_email,  # Note: No user_email argument needed
    trigger="cron",
    day_of_week="mon",
    hour=8,
    minute=0)


@app.route("/meal_plan")
def meal_plan():
    """
    Renders the meal_plan.html template,
    where users can view their recommended meal plan.
    """
    return render_template("meal_plan.html", title="Meal Plan")


@app.route('/recommend_meal_plan', methods=['POST', 'GET'])
def recommend_meal_plan_endpoint():
    """
    Endpoint to recommend a meal plan based on user preferences.
    Receives JSON data with goal, calories, protein,
    carbs, and fat values, then generates a recommendation.
    """
    # Parse user data from the request
    user_data = request.json
    goal = user_data.get('goal')
    calories = user_data.get('calories')
    protein = user_data.get('protein')
    carbs = user_data.get('carbs')
    fat = user_data.get('fat')

    # Generate meal recommendations
    recommended_meals = recommend_meal_plan(goal, calories, protein, carbs,
                                            fat)
    return jsonify(recommended_meals)


@app.after_request
def add_header(response):
    # Disable caching
    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, public, max-age=0"
    )

    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/exercise", methods=["GET", "POST"])
def exercise():
    exercises = []  # To store exercises
    error_message = None

    if request.method == "POST":
        # Get user input
        muscle = request.form.get("muscle").lower()
        difficulty = request.form.get("difficulty").lower()

        # API call
        api_url = f"https://api.api-ninjas.com/v1/exercises?muscle={muscle}&difficulty={difficulty}"
        headers = {'X-Api-Key': 'ThMgHV6VS4iYBAsvrUnNRg==vDzibI5DsOwhxevU'}
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            exercises = response.json()[:5]  # Get only 5 exercises
            if not exercises:
                error_message = f"No exercises found for {muscle} at {difficulty} level."
        else:
            error_message = f"Error {response.status_code}: Unable to fetch exercises."

    return render_template("exercise.html", exercises=exercises, error_message=error_message)


if __name__ == "__main__":
    if os.environ.get('DOCKERIZED'):
        # Use Docker-specific MongoDB URI
        app.run(host='0.0.0.0', debug=True)
    else:
        app.run(debug=True)
