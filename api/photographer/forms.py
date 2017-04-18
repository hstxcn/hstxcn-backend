import re
from wtforms.fields import (
    StringField,
    TextAreaField,
    SelectField,
    Field,
)
from wtforms.validators import (
    ValidationError,
    InputRequired,
    EqualTo,
    Email,
    Regexp,
    Length,
)

import models

from form import Form

from .. import baseForms
from .. import baseValidators


class PhotographersForm(Form, baseForms.SliceMixin):
    sortby = SelectField('sortby', default="number", choices=[
        ("number", "number"),
        ("create_time", "create_time"),
        ("likes", "likes"),
    ])
    order = SelectField('order', default="asc", choices=[
        ("asc", "asc"),
        ("desc", "desc"),
    ])
    styles = Field('styles', default=[], validators=[
        baseValidators.styles_get
    ])
    themes = Field('themes', default=[], validators=[
        baseValidators.themes_get
    ])
    schools = Field('schools', default=[], validators=[
        baseValidators.schools_get
    ])
    categories = Field('categories', default=[], validators=[
        baseValidators.categories_get
    ])


class PhotographersSearchForm(Form, baseForms.SliceMixin):
    keyword = StringField("keyword")
    sortby = SelectField('sortby', default="number", choices=[
        ("number", "number"),
        ("create_time", "create_time"),
        ("likes", "likes"),
    ])
    order = SelectField('order', default="asc", choices=[
        ("asc", "asc"),
        ("desc", "desc"),
    ])

    def validate_keyword(form, field):
        _ = field.gettext
        re_str = r"[\s+!\"#$%&\'()*,-./:;<=>?@[\\]^_`{|}~]+|[×—～！，。？、~@#￥%…&*（）]+"
        field.data = re.sub(re_str, " ", field.data).split()


class PhotographerOptionForm(Form):
    Type = SelectField('type', default="style", choices=[
        ("school", models.School),
        ("style", models.Style),
        ("category", models.Category)
    ])
    name = StringField("name", [
        InputRequired()
    ])
