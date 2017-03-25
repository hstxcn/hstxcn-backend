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


class CollectionForm(Form):
    name = StringField('name')
    description = TextAreaField('description')
    model_name = StringField('model_name')
    photoshop = StringField('photoshop')
    filming_time = StringField('filming_time')
    images = Field('images', default=[], validators=[
        baseValidators.images_get
    ])


class CollectionsForm(Form, baseForms.SliceMixin):
    sortby = SelectField('sortby', default="create_time", choices=[
        ("create_time", "create_time"),
        ("likes", "likes"),
    ])
    order = SelectField('order', default="asc", choices=[
        ("asc", "asc"),
        ("desc", "desc"),
    ])


class CoverCollectionForm(Form):
    collection = StringField('collection', [
        baseValidators.user_collection_get
    ])


class WorksForm(Form, baseForms.SliceMixin):
    sortby = SelectField('sortby', default="create_time", choices=[
        ("create_time", "create_time"),
        ("filming_time", "filming_time"),
    ])
    order = SelectField('order', default="asc", choices=[
        ("asc", "asc"),
        ("desc", "desc"),
    ])


class WorkForm(Form):
    work = StringField('work', [
        baseValidators.image_get
    ])

