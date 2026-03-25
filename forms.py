from flask_wtf import FlaskForm 
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange, ValidationError, InputRequired


class AddTeamForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired('Team Name can not be empty ')])
    score = IntegerField('Score', validators=[InputRequired('Team Score can not be empty '),NumberRange(-100000,+100000,'Score is not in the range')],default=0)

class EditTeamForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired('Team Name can not be empty ')])
    score = IntegerField('Score', validators=[InputRequired('Team Score can not be empty '),NumberRange(-100000,+100000,'Score is not in the range')])

class AddPlayerForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired('First Name can not be empty ')])
    lastname = StringField('Last Name', validators=[DataRequired('Last Name can not be empty ')])
    score = IntegerField('Score', validators=[InputRequired('Player Score can not be empty '),NumberRange(-100000,+100000,'Score is not in the range')],default=0)

class EditPlayerForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired('Player Name can not be empty ')])
    lastname = StringField('Last Name', validators=[DataRequired('Player Name can not be empty ')])
    score = IntegerField('Score', validators=[InputRequired('Player Score can not be empty '),NumberRange(-100000,+100000,'Score is not in the range')])
