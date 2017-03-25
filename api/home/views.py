import json

from sqlalchemy import func

import models
from .. import base
from . import forms

__all__ = [
    "BannerHandler",
    "BannersHandler",
    "HomePhotographerHandler",
    "HomePhotographersHandler",
    "HomeCollectionHandler",
    "HomeCollectionsHandler",
]


class BannerHandler(base.APIBaseHandler):
    """
    URL: /home/banner/(?P<uuid>[0-9a-fA-F]{32})
    Allowed methods: GET, PATCH, DELETE
    """
    def get(self, uuid):
        return self.finish_object(models.Banner,
                                  uuid)

    @base.authenticated(admin=True)
    def patch(self, uuid):
        banner = self.get_or_404(models.Banner.query,
                                 uuid)

        form = forms.BannerForm(self.json_args,
                                locale_code=self.locale.code)
        if form.validate():
            banner = self.edit_banner(form, banner)
            self.finish(json.dumps(
                banner.format_detail()
            ))

    @base.authenticated(admin=True)
    def delete(self, uuid):
        banner = self.get_or_404(models.Banner.query,
                                 uuid)
        self.delete_banner(banner)
        self.set_status(204)
        self.finish()

    @base.db_success_or_500
    def edit_banner(self, form, banner):
        attr_list = ['cover', 'url']
        self.apply_edit(banner, form, attr_list)

        return banner

    @base.db_success_or_500
    def delete_banner(self, banner):
        self.session.delete(banner)


class BannersHandler(base.APIBaseHandler):
    """
    URL: /home/banner
    Allowed methods: GET, POST, PATCH
    """
    def get(self):
        return self.finish_objects(forms.BannersForm,
                                   query=models.Banner.query.order_by("number asc"))

    @base.authenticated(admin=True)
    def post(self):
        form = forms.BannerForm(self.json_args,
                                locale_code=self.locale.code)
        if form.validate():
            banner = self.create_banner(form)
            self.finish(json.dumps(
                banner.format_detail()
            ))
        else:
            self.validation_error(form)

    @base.authenticated(admin=True)
    def patch(self):
        form = forms.BannerSortForm(self.json_args,
                                    locale_code=self.locale.code)
        if form.validate():
            self.resort_banner(form)
            self.finish_objects(forms.BannersForm,
                                models.Banner)
        else:
            self.validation_error(form)

    @base.db_success_or_500
    def create_banner(self, form):
        maxnum = self.session.query(func.max(models.Banner.number)).first()[0]
        number = maxnum + 1 if maxnum else models.Banner.query.count()
        banner = models.Banner(
            cover=form.cover.data,
            number=number,
            url=form.url.data
        )
        self.session.add(banner)

        return banner

    @base.db_success_or_500
    def resort_banner(self, form):
        for i in range(0, len(form.banners.data)):
            banner = form.banners.data[i]
            banner.number = i

        self.session.flush()


class HomePhotographerHandler(base.APIBaseHandler):
    """
    URL: /home/photographer/(?P<uuid>[0-9a-fA-F]{32})
    Allowed methods: GET, DELETE
    """
    def get(self, uuid):
        return self.finish_object(models.HomePhotographer,
                                  uuid)

    @base.authenticated(admin=True)
    def delete(self, uuid):
        hp = self.get_or_404(models.HomePhotographer.query,
                             uuid)
        self.delete_home_photographer(hp)
        self.set_status(204)
        self.finish()

    @base.db_success_or_500
    def delete_home_photographer(self, hp):
        self.session.delete(hp)


class HomePhotographersHandler(base.APIBaseHandler):
    """
    URL: /home/photographer
    Allowed methods: GET, POST, PATCH
    """
    def get(self):
        return self.finish_objects(forms.HomePhotographersForm,
                                   query=models.HomePhotographer.query.order_by("number asc"))

    @base.authenticated(admin=True)
    def post(self):
        form = forms.HomePhotographerForm(self.json_args,
                                          locale_code=self.locale.code)
        if form.validate():
            hp = self.create_home_photographer(form)
            self.finish(json.dumps(
                hp.format_detail()
            ))
        else:
            self.validation_error(form)

    @base.authenticated(admin=True)
    def patch(self):
        form = forms.HomePhotographerSortForm(self.json_args,
                                              locale_code=self.locale.code)
        if form.validate():
            self.resort_home_photographer(form)
            self.finish_objects(forms.HomePhotographersForm,
                                models.HomePhotographer)
        else:
            self.validation_error(form)

    @base.db_success_or_pass
    def create_home_photographer(self, form):
        maxnum = self.session.query(func.max(models.HomePhotographer.number)).first()[0]
        number = maxnum + 1 if maxnum else models.HomePhotographer.query.count()

        hp = models.HomePhotographer(
            photographer=form.photographer.data,
            number=number
        )
        self.session.add(hp)

        return hp

    @base.db_success_or_500
    def resort_home_photographer(self, form):
        for i in range(0, len(form.photographers.data)):
            hp = form.photographers.data[i]
            hp.number = i

        self.session.flush()


class HomeCollectionHandler(base.APIBaseHandler):
    """
    URL: /home/collection/(?P<uuid>[0-9a-fA-F]{32})
    Allowed methods: GET, DELETE
    """
    def get(self, uuid):
        return self.finish_object(models.HomeCollection,
                                  uuid)

    @base.authenticated(admin=True)
    def delete(self, uuid):
        hc = self.get_or_404(models.HomeCollection.query,
                             uuid)
        self.delete_home_collection(hc)
        self.set_status(204)
        self.finish()

    @base.db_success_or_500
    def delete_home_collection(self, hc):
        self.session.delete(hc)


class HomeCollectionsHandler(base.APIBaseHandler):
    """
    URL: /home/collection
        Allowed methods: GET, POST, PATCH
    """
    def get(self):
        return self.finish_objects(forms.HomeCollectionsForm,
                                   models.HomeCollection)

    @base.authenticated(admin=True)
    def post(self):
        form = forms.HomeCollectionForm(self.json_args,
                                        locale_code=self.locale.code)
        if form.validate():
            hc = self.create_home_collection(form)
            self.finish(json.dumps(
                hc.format_detail()
            ))
        else:
            self.validation_error(form)

    @base.authenticated(admin=True)
    def patch(self):
        form = forms.HomeCollectionSortForm(self.json_args,
                                            locale_code=self.locale.code)
        if form.validate():
            self.resort_home_collection(form)
            self.finish_objects(forms.HomeCollectionsForm,
                                models.HomeCollection)
        else:
            self.validation_error(form)

    @base.db_success_or_500
    def create_home_collection(self, form):
        maxnum = self.session.query(func.max(models.HomeCollection.number)).first()[0]
        number = maxnum + 1 if maxnum else models.HomeCollection.query.count()

        hc = models.HomeCollection(
            collection=form.collection.data,
            number=number
        )
        self.session.add(hc)

        return hc

    @base.db_success_or_500
    def resort_home_collection(self, form):
        for i in range(0, len(form.collections.data)):
            hc = form.collections.data[i]
            hc.number = i

        self.session.flush()
