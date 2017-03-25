import json

import models
from .. import base
from . import forms

__all__ = [
    "ThemeHandler",
    "ThemesHandler",
    "ThemesCountHandler",
    "ThemeCollectionHandler",
    "ThemeCollectionsHandler",
    "ThemeCollectionsCountHandler",
]


class ThemeHandler(base.APIBaseHandler):
    """
    URL: /theme/(?P<uuid>[0-9a-fA-F]{32})
    Allowed methods: GET, PATCH, DELETE
    """
    def get(self, uuid):
        """
        Get a theme's info.
        """
        self.finish_object(models.Theme,
                           uuid)

    @base.authenticated(admin=True)
    def patch(self, uuid):
        form = forms.ThemeForm(self.json_args,
                               locale_code=self.locale.code)
        theme = self.get_or_404(models.Theme.query,
                                uuid)
        if form.validate():
            self.edit_theme(theme, form)
            self.finish(json.dumps(
                theme.format_detail()
            ))
        else:
            self.validation_error(form)

    @base.authenticated(admin=True)
    def delete(self, uuid):
        theme = self.get_or_404(models.Theme.query,
                                uuid)
        self.delete_theme(theme)
        self.set_status(204)
        self.finish()

    @base.db_success_or_500
    def edit_theme(self, theme, form):
        attr_list = ['name']
        if form.cover.data:
            theme.cover = form.cover.data
        self.apply_edit(theme, form, attr_list)

        return theme

    @base.db_success_or_500
    def delete_theme(self, theme):
        self.session.delete(theme)


class ThemesHandler(base.APIBaseHandler):
    """
    URL: /theme
    Allowed methods: GET, POST
    """
    def get(self):
        """
        Get some themes' info.
        """
        self.finish_objects(forms.ThemesForm,
                            models.Theme)

    @base.authenticated(admin=True)
    def post(self):
        """
        Create new theme.
        """
        form = forms.ThemeForm(self.json_args,
                               locale_code=self.locale.code)
        if form.validate():
            theme = self.create_theme(form)
            self.set_status(201)
            self.finish(json.dumps(
                theme.format_detail()
            ))
        else:
            self.validation_error(form)

    @base.db_success_or_500
    def create_theme(self, form):
        theme = models.Theme(
            cover=form.cover.data,
            name=form.name.data
        )
        if form.collections.data:
            for collection in form.collections.data:
                theme.collections.append(collection)
        self.session.add(theme)

        return theme


class ThemesCountHandler(base.APIBaseHandler):
    """
    URL: /theme/count
    """
    def get(self):
        self.finish_objects_count(models.Theme)


class ThemeCollectionHandler(base. APIBaseHandler):
    """
    URL: /theme/(?P<theme_id>[0-9a-fA-F]{32})/collection/(?P<col_id>[0-9a-fA-F]{32})
    Allowed methods: GET, DELETE
    """
    def get(self, theme_id, col_id):
        theme = self.get_or_404(models.Theme.query, theme_id)
        collection = self.get_or_404(theme.collections, col_id)

        self.finish(json.dumps(
            collection.format_detail()
        ))

    @base.authenticated(admin=True)
    def delete(self, theme_id, col_id):
        theme = self.get_or_404(models.Theme.query,
                                theme_id)
        collection = self.get_or_404(models.Collection.query,
                                     col_id)
        self.delete_theme_collection(theme, collection)
        self.set_status(204)
        self.finish()

    @base.db_success_or_500
    def delete_theme_collection(self, theme, collection):
        theme.collections.remove(collection)
        self.session.flush()
        if not theme.collections.filter_by(user=collection.user).first():
            collection.user.themes.remove(theme)


class ThemeCollectionsHandler(base.APIBaseHandler):
    """
    URL: /theme/(?P<uuid>[0-9a-fA-F]{32})/collection
    Allowed methods: GET
    """
    def get(self, uuid):
        theme = self.get_or_404(models.Theme.query, uuid)

        self.finish_objects(forms.ThemeCollectionsForm,
                            query=theme.collections)

    @base.authenticated(admin=True)
    def post(self, uuid):
        theme = self.get_or_404(models.Theme.query, uuid)
        form = forms.ThemeCollectionForm(self.json_args,
                                         locale_code=self.locale.code)
        if form.validate():
            self.add_theme_collection(theme, form.collection.data)
            self.finish(json.dumps(
                form.collection.data.format_detail()
            ))
        else:
            self.validation_error(form)

    @base.db_success_or_500
    def add_theme_collection(self, theme, collection):
        theme.collections.append(collection)
        collection.user.themes.append(theme)


class ThemeCollectionsCountHandler(base.APIBaseHandler):
    """
    URL: /theme/(?P<uuid>[0-9a-fA-F]{32})/collection/count
    Allowed methods: GET
    """
    def get(self, uuid):
        theme = self.get_or_404(models.Theme.query,
                                uuid)

        self.finish_objects_count(query=theme.collections)

