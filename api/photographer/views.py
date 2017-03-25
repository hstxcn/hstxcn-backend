import json
from sqlalchemy import or_

import models
from .. import base
from . import forms


__all__ = [
    "PhotographerHandler",
    "PhotographersHandler",
    "PhotographersCountHandler",
    "PhotographersSearchHandler",
    "PhotographerOptionHandler",
]


class PhotographerHandler(base.APIBaseHandler):
    """
    URL: /photographer/(?P<uuid>[0-9a-fA-F]{32})
    Allowed methods: GET
    """
    def get(self, uuid):
        """
        Get a photographer's info.
        """
        self.finish_object(models.User,
                           uuid)


class PhotographersHandler(base.APIBaseHandler):
    """
    URL: /photographer
    Allowed methods: GET
    """
    def get(self):
        form = forms.PhotographersForm(self.request.arguments,
                                       locale_code=self.locale.code)
        if form.validate():
            query = models.User.query\
                .filter_by(is_admin=False, status='reviewed')\
                .filter(or_(s in models.User.styles for s in form.styles.data))\
                .filter(or_(models.User.school == s for s in form.schools.data))\
                .filter(or_(c in models.User.categories for c in form.categories.data))\
                .filter(or_(t in models.User.themes for t in form.themes.data))

            objects_query = self.apply_order(query, form)
            objects = objects_query.all()

            response = list()
            for obj in objects:
                response.append(
                    obj.format_detail()
                )
            self.finish(json.dumps(response))
        else:
            self.validation_error(form)


class PhotographersCountHandler(base.APIBaseHandler):
    """
    URL: /photographer/count
    Allowed methods: GET
    """
    def get(self):
        self.finish_objects_count(
            query=models.User.filter_by(is_admin=False, status='reviewed'))


class PhotographersSearchHandler(base.APIBaseHandler):
    """
    URL: /photographer/search
    Allowed methods: GET
    """
    def get(self):
        form = forms.PhotographersSearchForm(self.request.arguments,
                                             locale_code=self.locale.code)
        if form.validate():
            if form.keyword.data:
                query = models.User.query\
                    .filter_by(is_admin=False, status='reviewed')\
                    .filter(or_(models.User.name.like('%'+k+'%') for k in form.keyword.data))
            else:
                query = models.User.query.filter_by(is_admin=False, status='reviewed')
            objects_query = self.apply_order(query, form)
            objects = objects_query.all()

            response = list()
            for obj in objects:
                response.append(
                    obj.format_detail()
                )
            self.finish(json.dumps(response))
        else:
            self.validation_error(form)


class PhotographerOptionHandler(base.APIBaseHandler):
    """
    URL: /photographer/option
    Allowed methods: GET
    """
    def get(self):
        styles = models.Style.query.order_by("id desc").all()
        schools = models.School.query.order_by("id desc").all()
        categories = models.Category.query.order_by("id desc").all()
        themes = models.Theme.query.order_by("create_time asc").all()

        response = {
            "styles": [style.format_detail() for style in styles],
            "schools": [school.format_detail() for school in schools],
            "categories": [category.format_detail() for category in categories],
            "themes": [theme.format_detail() for theme in themes]
        }

        self.finish(json.dumps(response))

    @base.authenticated(admin=True)
    def post(self):
        form = forms.PhotographerOptionForm(self.json_args,
                                            locale_code=self.locale.code)
        if form.validate():
            option = self.create_option(form)
            self.finish(
                option.format_detail()
            )
        else:
            self.validation_error(form)

    @base.db_success_or_500
    def create_option(self, form):
        option = form.Type.data(
            name=form.name.data
        )
        self.session.add(option)

        return option
