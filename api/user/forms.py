from wtforms.fields import (
    StringField,
    TextAreaField,
    SelectField,
    BooleanField,
    Field,
)
from wtforms.validators import (
    StopValidation,
    ValidationError,
    InputRequired,
    EqualTo,
    Email,
    Regexp,
    Length,
    Optional,
)

import models

from form import Form

from .. import baseForms
from .. import baseValidators


class RegisterForm(Form):
    name = StringField('name', [
        InputRequired(),
        Length(max=128),
    ])
    email = StringField('email', [
        Email(),
        InputRequired(),
    ])
    password = StringField('password', [
        Length(min=6),
        InputRequired(),
    ])

    def validate_email(form, field):
        _ = field.gettext
        count = models.User.query \
            .filter(models.User.email == field.data) \
            .count()
        if count != 0:
            raise ValidationError(_('邮箱已被使用。'))


class ProfileForm(Form):
    self_password = StringField('self_password')
    password = StringField('password', [
        Length(min=6),
        Optional(),
    ])
    tags = Field('tags', default=[])
    school = StringField('school', [
        baseValidators.school_get,
        Optional(),
    ])
    categories = Field('categories', default=[], validators=[
        baseValidators.categories_get
    ])
    styles = Field('styles', default=[], validators=[
        baseValidators.styles_get
    ])
    name = StringField('name')
    avatar = StringField('avatar', [
        baseValidators.image_get,
        Optional(),
    ])
    email = StringField('email', [
        Email(),
        Optional(),
    ])
    sex = BooleanField('sex', false_values={False, 'false', 0})
    description = TextAreaField('description')
    major = StringField('major')
    imagelink = StringField('imagelink')

    def validate_self_password(form, field):
        current_user = form.kwargs.get("current_user", None)
        if current_user is None:
            return
        if not current_user.password:
            return
        if not form.password.data:
            return

        if not current_user.check_password(field.data):
            _ = field.gettext
            raise StopValidation(_("密码错误."))

    def validate_email(form, field):
        if not field.data:
            return
        if baseValidators.ignore_match('email_ignore', form, field):
            return

        _ = field.gettext
        count = models.User.query\
            .filter(models.User.email == field.data)\
            .count()
        if count != 0:
            raise ValidationError(_('邮箱已被使用.'))

    def validate_tags(form, field):
        current_user = form.kwargs.get("current_user", None)
        if current_user is None:
            return
        tags = list()
        for text in list(field.data):
            d = current_user.tags.filter_by(text=text).first()
            if d is None:
                nd = models.Tag(
                    user=current_user,
                    text=text
                )
                tags.append(nd)
        field.data = tags

    def validate_sex(form, field):
        current_user = form.kwargs.get("current_user", None)
        if current_user is None:
            return
        if field.data == '':
            field.data = current_user.sex


class LoginForm(Form):
    """
    Used in:
        user.LoginHandler
            method=['POST']
            Get auth token.
    """
    email = StringField('email', [
        InputRequired(),
    ])
    password = StringField('password', [
        InputRequired(),
    ])

    def validate_email(form, field):
        _ = field.gettext
        try:
            user = models.User.query\
                .filter_by(email=form.email.data)\
                .first()
            assert user.check_password(form.password.data) is True
            form.kwargs['user'] = user
        except Exception:
            raise ValidationError(_('邮箱或密码错误。'))

    validate_password = validate_email


class ActivateForm(Form):
    email = StringField('email', [
        InputRequired()
    ])

    def validate_email(form, field):
        _ = field.gettext
        try:
            user = models.User.query\
                .filter_by(is_admin=False, email=field.data)\
                .first()

            assert user is not None
            form.kwargs['user'] = user
        except Exception:
            raise ValidationError(_('Invalid email.'))


class UserQueryForm(Form):
    status = SelectField('status', default="reviewed", choices=[
        ("unconfirmed", "unconfirmed"),
        ("confirmed", "confirmed"),
        ("reviewing", "reviewing"),
        ("reviewed", "reviewed")
    ])
