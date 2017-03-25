from wtforms.fields import (
    Field,
    StringField,
    SelectField,
    TextAreaField,
    IntegerField,
)
from wtforms.validators import (
    ValidationError,
    InputRequired,
    Email,
    Length,
)

import models
from form import Form

from .. import baseForms
from .. import baseValidators


class BannerForm(Form):
    """
    Used in:
        user.BannersHandler
            method=['POST']
            Create a new banner.
    """
    cover = StringField('cover', [
        baseValidators.image_get
    ])
    url = StringField('url')


class BannersForm(Form, baseForms.SliceMixin):
    sortby = SelectField('sortby', default="number", choices=[
        ("create_time", "create_time"),
        ("number", "number"),
    ])
    order = SelectField('order', default="asc", choices=[
        ("asc", "asc"),
        ("desc", "desc"),
    ])


class BannerSortForm(Form):
    """
        Used in:
        user.BannersHandler
            method=['PATCH']
            exchange two banners' number.
    """
    banners = Field('banners', default=[], validators=[
        baseValidators.banners_get
    ])


class HomePhotographerForm(Form):
    photographer = StringField('photographer', [
        baseValidators.photographer_get
    ])


class HomePhotographersForm(Form, baseForms.SliceMixin):
    sortby = SelectField('sortby', default="number", choices=[
        ("number", "number"),
    ])
    order = SelectField('order', default="asc", choices=[
        ("asc", "asc"),
        ("desc", "desc"),
    ])


class HomePhotographerSortForm(Form):
    photographers = Field('photographers', default=[], validators=[
        baseValidators.photographers_get,
    ])


class HomeCollectionForm(Form):
    collection = StringField('collection', [
        baseValidators.collection_get
    ])


class HomeCollectionsForm(Form, baseForms.SliceMixin):
    sortby = SelectField('sortby', default="number", choices=[
        ("number", "number"),
    ])
    order = SelectField('order', default="asc", choices=[
        ("asc", "asc"),
        ("desc", "desc"),
    ])


class HomeCollectionSortForm(Form):
    collections = Field('collections', default=[], validators=[
        baseValidators.collections_get,
    ])
