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
    "ResendConfirmationHandler"
]


class MailMixin():
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


class RegisterHandler(base.APIBaseHandler, MailMixin):
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
        self.session.add(user)

        return user

    @base.db_success_or_500
    def create_collection(self):
        collection = models.Collection(
            name='cover'
        )
        self.session.add(collection)

        return collection


class ConfirmationHandler(base.APIBaseHandler):
    """
    URL: /user/(?P<uuid>[0-9a-fA-F]{32})/confirmation/(?P<token>.*)
    Allowed methods: POST
    """
    def post(self, uuid, token):
        user = self.get_or_404(models.User.query,
                               uuid)
        if not self.confirm(user, token):
            self.set_status(403)
        self.finish(json.dumps(
            user.format_detail()
        ))

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


class ResendConfirmationHandler(base.APIBaseHandler, MailMixin):
    """
    URL: /user/(?P<uuid>[0-9a-fA-F]{32})/confirmation
    Allowed methods: POST
    """
    @base.authenticated(status=("unconfirmed",))
    @gen.coroutine
    def post(self, uuid):
        user = self.get_or_404(models.User.query,
                               uuid)
        yield self.send_confirm_mail(user)
        self.finish()


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
    Allowed methods: GET, PATCH, PUT, DELETE
    """
    @base.authenticated(status=("unconfirmed", "confirmed", "reviewing", "reviewed", ))
    def get(self):
        """
        Check your profile.
        """
        self.finish(json.dumps(
            self.current_user.format_detail(get_email=True, get_collections=True)
        ))

    @base.authenticated(status=("confirmed", "reviewed",))
    def patch(self):
        """
        Edit your profile.
        """
        form = forms.ProfileForm(self.json_args,
                                 locale_code=self.locale.code,
                                 current_user=self.current_user)
        if form.validate():
            self.edit_profile(form)

            self.finish(json.dumps(
                self.current_user.format_detail(get_email=True, get_collections=True)
            ))
        else:
            self.validation_error(form)

    @base.authenticated(status=("confirmed",))
    def put(self):
        self.submit_profile()
        self.set_status(201)
        self.finish()

    @base.authenticated(status=("reviewing",))
    def delete(self):
        self.cancel_submit_profile()
        self.set_status(201)
        self.finish()

    @base.db_success_or_pass
    def edit_profile(self, form):
        attr_list = ['name', 'sex', 'description',
                     'major', 'imagelink']
        self.apply_edit(self.current_user, form, attr_list)

        if form.password.data:
            self.current_user.set_password(form.password.data)
        if form.avatar.data:
            self.current_user.avatar = form.avatar.data
        if form.school.data:
            self.current_user.school = form.school.data
        if form.tags.data:
            for o in self.current_user.tags:
                self.current_user.tags.remove(o)
                self.session.delete(o)
            for d in form.tags.data:
                self.current_user.tags.append(d)
        if form.styles.data:
            for o in self.current_user.styles:
                self.current_user.styles.remove(o)
            for s in form.styles.data:
                self.current_user.styles.append(s)
        if form.categories.data:
            for o in self.current_user.categories:
                self.current_user.categories.remove(o)
            for c in form.categories.data:
                self.current_user.categories.append(c)
        self.session.add(self.current_user)

    @base.db_success_or_500
    def submit_profile(self):
        self.current_user.status = "reviewing"
        self.session.add(self.current_user)

    @base.db_success_or_500
    def cancel_submit_profile(self):
        self.current_user.status = "confirmed"
        self.session.add(self.current_user)


class UserQueryHandler(base.APIBaseHandler):
    """
    URL: /users
    Allowed methods: GET
    """
    @base.authenticated(admin=True)
    def get(self):
        args = dict()
        print(self.request.arguments)
        for key, value in self.request.arguments.items():
            args[key] = [value]
        form = forms.UserQueryForm(args,
                                   locale_code=self.locale.code)
        if form.validate():
            users = models.User.query\
                .filter(or_(models.User.status == s for s in form.status.data))\
                .all()
            self.finish(json.dumps(
                [user.format_detail(get_email=True, get_collections=True) for user in users]
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
                user.format_detail(get_email=True, get_collections=True)
            ))
        else:
            self.validation_error(form)

    @gen.coroutine
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
        self.session.flush()
        return user

    @base.db_success_or_500
    @gen.coroutine
    def unactivate_user(self, user):
        yield self.send_activate_mail(user, False)
        user.status = "confirmed"
        self.session.add(user)
        self.session.flush()
        return user

    @gen.coroutine
    def send_activate_mail(self, user, is_activate=True):
        subjects = ("【友拍平台】摄影师审核失败", "【友拍平台】摄影师审核通过")
        s = SMTPAsync()
        yield s.connect(mail_settings['host'], mail_settings['port'])
        yield s.starttls()
        yield s.login(mail_settings['email'], mail_settings['password'])

        me = mail_settings['email']
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subjects[is_activate]
        msg['From'] = me
        msg['To'] = user.email
        texts = (
            """
            <html>
              <body>
                尊敬的摄影师您好，很遗憾您没有获得友拍的入驻资格，原因不是在您，而是由于友拍平台的发展限制，我们还在萌芽阶段，
                我们希望能够创造一个足够精致的约拍环境，满足所有人追求美的心愿，衷心的希望平台能和您一同成长，在未来的某一天，
                能一同为华科里想拍照的人带来方便。要约拍，来友拍。谢谢！
              </body>
            </html>
            """,
            """
            <html>
              <body>
                尊敬的摄影师您好，恭喜您已经获得了友拍平台（华科约拍平台）的入驻资格，友拍非常欣
                喜能迎来您这样以为优秀的摄影师，祝愿您能够充分的利用好友拍平台，拍摄更多佳作，得到更多收获
                。为了让您更方便使用友拍，请注意以下几点：<br/>
                首先请您添加我们的微信客服友小拍拉您进入友拍入驻摄影师群，所有的友拍摄影师都在那里等您。友小拍微信号：18162591091<br/>
                第二：您可以使用我们的管理页面管理您的照片，欢迎您常常更新~。<br/>
                我们希望有更多的摄影师加入我们，提高平台的质量，来吸引大量的用户，如果您身边有我们还未发掘的优秀摄影师，那请
                一定介绍给我们，友拍还在萌芽阶段，衷心感谢各位摄影师的支持与帮助。要约拍，来友拍，美照恒久远，一张永流传。谢谢！
              </body>
            </html>
            """)
        content = MIMEText(texts[is_activate], "html")
        msg.attach(content)

        yield s.sendmail(me, user.email, msg.as_string())
        yield s.quit()
