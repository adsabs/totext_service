from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, BooleanField
from wtforms.validators import DataRequired

class QueryForm(FlaskForm):
    q = StringField('q', validators=[DataRequired()])
    sort = SelectField('sort', default="date desc",
                       choices=[
                           ('date desc', 'Date (desc)'),
                           ('citation_count desc', 'Citations (desc)'),
                           ('score desc', 'Score (desc)'),
                           ('date asc', 'Date (asc)'),
                           ('citation_count asc', 'Citations (asc)'),
                           ('score asc', 'Score (asc)'),
                       ])
    rows = IntegerField('rows', default=5)
    start = IntegerField('start', default=0)
    submit = SubmitField('Search')
