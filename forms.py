# from datetime import date
# from re import sub
# from flask import app
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import (
    FloatField,
    RadioField,
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
)
from wtforms import DateField
from wtforms import SelectField

# from wtforms.fields.core import (
#     # DateField,
#     # SelectField,
# )
from wtforms.validators import (
    DataRequired,
    Length,
    Email,
    EqualTo,
    ValidationError,
    Regexp
)
from apps import App
# from wtforms.validators import Regexp


class RegistrationForm(FlaskForm):
    recaptcha = RecaptchaField()
    username = StringField('Username',
                           validators=[DataRequired(),
                                       Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters"),
            Regexp('.*[A-Z].*',
                   message="Password must contain at least one capital letter")
        ])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(),
                    EqualTo('password')]
    )
    weight = StringField(
        'Weight',
        validators=[
            DataRequired(),
            Length(min=2, max=20),
            Regexp(r'^\d*\.?\d*$', message="Height must be a valid number")
        ]
    )
    height = StringField(
        'Height',
        validators=[
            DataRequired(),
            Length(min=2, max=20),
            Regexp(r'^\d*\.?\d*$', message="height must be a valid number")
        ]
    )
    target_weight = StringField(
        'Target Weight',
        validators=[
            DataRequired(),
            Length(min=2, max=20),
            Regexp(r'^\d*\.?\d*$', message="height must be a valid number")
        ]
    )
    target_date = DateField(DataRequired())

    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        app_object = App()
        mongo = app_object.mongo

        temp = mongo.db.user.find_one({'email': email.data},
                                      {'email', 'password'})
        if temp:
            raise ValidationError('Email already exists!')


class getDate(FlaskForm):
    target_date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Show Bronze List')


class TwoFactorForm(FlaskForm):
    two_factor_code = StringField('Two-Factor Code',
                                  validators=[DataRequired()])
    submit = SubmitField('Verify')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class QuestionForm(FlaskForm):
    options = RadioField('Options: ', validators=[DataRequired()], default=1)
    submit = SubmitField('Next')


class WorkoutForm(FlaskForm):
    app = App()
    mongo = app.mongo

    # cursor = mongo.db.food.find()
    # get_docs = []
    # for record in cursor:
    #     get_docs.append(record)

    # result = []
    # temp = ""
    # for i in get_docs:
    #     temp = i['food'] + ' (' + i['calories'] + ')'
    #     result.append((temp, temp))

    # food = SelectField(
    #     'Select Food', choices=result)

    date = DateField(DataRequired())
    burnout = FloatField('Burn Out',
                         validators=[DataRequired()])
    # def validate_burnout(self, field):
    #     # Custom validation to check if input contains only number
    #     if not field.data.isdigit():
    #         raise ValidationError('Burn Out
    # field should only contain number.')
    submit = SubmitField('Save')


class CalorieForm(FlaskForm):
    app = App()
    mongo = app.mongo

    cursor = mongo.db.food.find()
    get_docs = []
    for record in cursor:
        get_docs.append(record)

    result = []
    temp = ""
    for i in get_docs:
        temp = i['food'] + ' (' + i['calories'] + ')'
        result.append((temp, temp))

    date = DateField(DataRequired())
    food = SelectField('Select Food', choices=result)

    submit = SubmitField('Save')


class UserProfileForm(FlaskForm):
    weight = StringField('Weight',
                         validators=[DataRequired(),
                                     Length(min=2, max=20)])
    height = StringField('Height',
                         validators=[DataRequired(),
                                     Length(min=2, max=20)])
    goal = StringField('Goal',
                       validators=[DataRequired(),
                                   Length(min=2, max=20)])
    target_weight = StringField(
        'Target Weight', validators=[DataRequired(),
                                     Length(min=2, max=20)])
    submit = SubmitField('Save Profile')


class HistoryForm(FlaskForm):
    app = App()
    mongo = app.mongo
    date = DateField()
    submit = SubmitField('Fetch')


class EnrollForm(FlaskForm):
    app = App()
    mongo = app.mongo
    submit = SubmitField('Enroll')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(),
                    EqualTo('password')]
    )
    submit = SubmitField('Reset')
