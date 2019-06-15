from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, BooleanField, TextAreaField
from wtforms.validators import DataRequired

class ModernForm(FlaskForm):
    q = StringField('q', validators=[DataRequired()])
    sort = StringField('sort', default="date desc")
    rows = IntegerField('rows', default=25)
    start = IntegerField('start', default=0)
    submit = SubmitField('Search')

class PaperForm(FlaskForm):
    bibcodes = TextAreaField('bibcodes')
    bibstem = StringField('bibstem')
    year = IntegerField('year')
    volume = IntegerField('volume')
    page = IntegerField('page')

class ClassicForm(FlaskForm):
    astronomy = BooleanField('astronomy', default=True)
    physics = BooleanField('physics', default=False)
    refereed = BooleanField('refereed', default=False)
    article = BooleanField('article', default=False)
    author_logic = StringField('author_logic', default="AND")
    author_names = StringField('author_names')
    object_logic = StringField('object_logic', default="AND")
    object_names = StringField('object_names')
    month_from = IntegerField('month_from')
    year_from = IntegerField('year_from')
    month_to = IntegerField('month_to')
    year_to = IntegerField('year_to')
    title_logic = StringField('title_logic', default="AND")
    title = StringField('title')
    abstract_logic = StringField('abstract_logic', default="AND")
    abstract = StringField('abstract')
    bibstem = StringField('bibstem')
