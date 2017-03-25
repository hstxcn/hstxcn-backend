import json
import string
import random

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import tornado.httpclient
from tornado import gen

from sqlalchemy import (
    func,
    or_,
)

from tornado_smtpclient.client import SMTPAsync
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

import util
import models
from settings import mail_settings
from .. import base
from . import forms

__all__ = [
    "LoginHandler",
    "RegisterHandler",
    "ProfileHandler",
    "ActivateHandler",
    "UserQueryHandler",
    "ConfirmationHandler",
]


class RegisterHandler(base.APIBaseHandler):
    """
    URL: /register
    Allowed methods: POST
    """
    @gen.coroutine
    def post(self):
        """
        Create a new user.
        """
        form = forms.RegisterForm(self.json_args,
                                  locale_code=self.locale.code)
        if form.validate():
            user = self.create_user(form)
            yield self.send_confirm_mail(user)

            self.set_status(201)
            self.finish(json.dumps({
                'auth': self.get_auth(user.id.hex).decode('utf8'),
            }))
        else:
            self.validation_error(form)

    @base.db_success_or_500
    def create_user(self, form):
        avatar_num = random.randint(1, 3)
        avatar_name = "avatar{}.png".format(avatar_num)
        admin = models.User.query.filter_by(number=0).first()
        avatar = admin.images.filter_by(filename=avatar_name).first()

        number = self.session.query(func.max(models.User.number)).first()[0] + 1

        user = models.User(email=form.email.data,
                           name=form.name.data,
                           avatar=avatar,
                           number=number)
        user.set_password(form.password.data)

        self.session.add(user)
        self.session.flush()

        cover = self.create_collection()
        user.cover_collection = cover

        return user

    @base.db_success_or_500
    def create_collection(self):
        collection = models.Collection(
            name='cover'
        )
        self.session.add(collection)

        return collection

    @gen.coroutine
    def send_confirm_mail(self, user):
        s = SMTPAsync()
        yield s.connect(mail_settings['host'], mail_settings['port'])
        yield s.starttls()
        yield s.login(mail_settings['email'], mail_settings['password'])

        me = mail_settings['email']
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "【友拍平台】摄影师注册确认"
        msg['From'] = me
        msg['To'] = user.email
        confirm_url = "http://{host}/user/{uid}/confirmation/{token}"\
                      .format(host=self.request.host,
                              uid=user.id.hex,
                              token=self.generate_confirmation_token(user).decode())
        text = """
                <html>
                  <body>
                    尊敬的摄影师您好，恭喜您注册友拍成功，请<a href="{}">点击链接</a>
                    验证您的邮箱，并完善您的信息，您可以上传至少两套照片以便于我们审核。审核的结果会以邮件形式通知您。<br/>
                    感激您对友拍的信任。要约拍，来友拍。
                  </body>
                </html>
               """\
               .format(confirm_url)
        content = MIMEText(text, "html")
        msg.attach(content)

        yield s.sendmail(me, user.email, msg.as_string())
        yield s.quit()

    def generate_confirmation_token(self, user, expiration=86400):
        s = Serializer(self.application.settings['cookie_secret'], expiration)

        return s.dumps({'confirm': user.id.hex})


class ConfirmationHandler(base.APIBaseHandler):
    """
    URL: /user/(?P<uuid>[0-9a-fA-F]{32})/confirmation/(?P<token>)
    Allowed methods: POST
    """
    @base.authenticated(status=("unconfirmed",))
    def post(self, uuid, token):
        user = self.get_or_404(models.User,
                               uuid)
        if not self.confirm(user, token):
            self.set_status(403)
        self.finish()

    @base.db_success_or_500
    def confirm(self, user, token):
        s = Serializer(self.application.settings['cookie_secret'])
        try:
            data = s.loads(token)
        except Exception:
            return False
        if data.get('confirm', None) != user.id.hex:
            return False
        user.status = "confirmed"

        return True


class LoginHandler(base.APIBaseHandler):
    """
    URL: /login
    Allowed methods: POST
    """
    def post(self):
        """
        Get auth token.
        """
        form = forms.LoginForm(self.json_args,
                               locale_code=self.locale.code)
        if form.validate():
            user = form.kwargs['user']

            self.finish(json.dumps({
                'auth': self.get_auth(user.id.hex).decode('utf8'),
            }))
        else:
            self.validation_error(form)


class ProfileHandler(base.APIBaseHandler):
    """
    URL: /profile
    Allowed methods: GET, PATCH, PUT
    """
    @base.authenticated(status=("confirmed", "reviewing", "reviewed",))
    def get(self):
        """
        Check your profile.
        """
        self.finish(json.dumps(
            self.current_user.format_detail(get_email=True)
        ))

    @base.authenticated(status=("confirmed", "reviewed",))
    def patch(self):
        """
        Edit your profile.
        """
        form = forms.ProfileForm(self.json_args,
                                 locale_code=self.locale.code,
                                 current_user=self.current_user,
                                 email_ignore=self.current_user.email)
        if form.validate():
            self.edit_profile(form)

            self.finish(json.dumps(
                self.current_user.format_detail()
            ))
        else:
            self.validation_error(form)

    @base.authenticated(status=("confirmed", "reviewed",))
    def put(self):
        self.submit_profile()
        self.set_status(200)
        self.finish()

    @base.db_success_or_500
    def edit_profile(self, form):
        attr_list = ['name', 'email', 'sex', 'description',
                     'major', 'imagelink']
        self.apply_edit(self.current_user, form, attr_list)

        if form.password.data:
            self.current_user.set_password(form.password.data)
        if form.avatar.data:
            self.current_user.avatar = form.avatar.data
        if form.school.data:
            self.current_user.school = form.school.data
        if form.tags.data:
            for d in form.tags.data:
                self.current_user.tags.append(d)
        if form.styles.data:
            for s in form.styles.data:
                self.current_user.styles.append(s)
        if form.categories.data:
            for c in form.categories.data:
                self.current_user.categories.append(c)

    @base.db_success_or_500
    def submit_profile(self):
        self.current_user.status = "reviewing"


class UserQueryHandler(base.APIBaseHandler):
    """
    URL: /users
    Allowed methods: GET
    """
    @base.authenticated(admin=True)
    def get(self):
        form = forms.UserQueryForm(self.json_args,
                                   locale_code=self.locale.code)
        if form.validate():
            users = models.User.query\
                .filter(models.User.status in form.status.data)\
                .all()
            self.finish(json.dumps(
                [user.format_detail(get_email=True) for user in users]
            ))
        else:
            self.validation_error(form)


class ActivateHandler(base.APIBaseHandler):
    """
    URL: /user/activate
    """
    @base.authenticated(admin=True)
    @gen.coroutine
    def post(self):
        form = forms.ActivateForm(self.json_args,
                                  locale_code=self.locale.code)
        if form.validate():
            user = form.kwargs['user']
            user = yield self.activate_user(user)

            self.finish(json.dumps(
                user.format_detail()
            ))
        else:
            self.validation_error(form)

    def delete(self):
        form = forms.ActivateForm(self.json_args,
                                  locale_code=self.locale.code)
        if form.validate():
            user = form.kwargs['user']
            user = yield self.unactivate_user(user)

            self.finish(json.dumps(
                user.format_detail()
            ))
        else:
            self.validation_error(form)

    @base.db_success_or_500
    @gen.coroutine
    def activate_user(self, user):
        yield self.send_activate_mail(user)
        user.status = "reviewed"
        self.session.add(user)
        return user

    @base.db_success_or_500
    @gen.coroutine
    def unactivate_user(self, user):
        yield self.send_activate_mail(user, False)
        user.status = "confirmed"
        self.session.add(user)
        return user

    @gen.coroutine
    def send_activate_mail(self, user, is_activate=True):
        subjects = ("【友拍平台】摄影师审核失败", "【友拍平台】摄影师审核通过")
        s = SMTPAsync()
        yield s.connect(mail_settings['host'], mail_settings['port'])
        yield s.starttls()
        yield s.login(mail_settings['email'], mail_settings['password'])

        me = mail_settings['host']
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subjects[is_activate]
        msg['From'] = me
        msg['To'] = user.email
        text = "您好，我是你爸爸"
        content = MIMEText(text, "html")
        msg.attach(content)

        yield s.sendmail(me, user.email, msg.as_string())
        yield s.quit()