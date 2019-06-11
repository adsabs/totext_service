from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired

class QueryForm(FlaskForm):
    q = StringField('q', validators=[DataRequired()])
    #sort = StringField('sort', default="date desc, bibcode desc")
    sort = SelectField('sort', default="date desc, bibcode desc",
                       choices=[
                           ('date desc, bibcode desc', 'Date (desc)'),
                           ('citation_count desc, bibcode desc', 'Citations (desc)'),
                           ('score desc, bibcode desc', 'Score (desc)'),
                           ('date asc, bibcode asc', 'Date (asc)'),
                           ('citation_count asc, bibcode asc', 'Citations (asc)'),
                           ('score asc, bibcode asc', 'Score (asc)'),
                       ])
    rows = IntegerField('rows', default=5)
    start = IntegerField('start', default=0)
    submit = SubmitField('Search')
