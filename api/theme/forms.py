from wtforms.fields import (
    StringField,
    TextAreaField,
    SelectField,
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


class ThemeCollectionsForm(Form, baseForms.SliceMixin):
    sortby = SelectField('sortby', default="likes", choices=[
        ("create_time", "create_time"),
        ("likes", "likes"),
    ])
    order = SelectField('order', default="asc", choices=[
        ("asc", "asc"),
        ("desc", "desc"),
    ])


class ThemesForm(Form, baseForms.SliceMixin):
    sortby = SelectField('sortby', default="create_time", choices=[
        ("create_time", "create_time"),
        ("name", "name"),
    ])
    order = SelectField('order', default="asc", choices=[
        ("asc", "asc"),
        ("desc", "desc"),
    ])


class ThemeForm(Form):
    name = StringField('name')
    cover = StringField('cover', [
        baseValidators.image_get
    ])
    collections = StringField('collections', [
        baseValidators.collections_get
    ])


class ThemeCollectionForm(Form):
    collection = StringField('collection', [
        baseValidators.collection_get
    ])
