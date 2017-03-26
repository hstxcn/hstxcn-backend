import json

import models
from .. import base
from . import forms

__all__ = [
    "CollectionHandler",
    "CollectionsHandler",
    "CollectionLikeHandler",
    "CollectionsCountHandler",
    "UserCollectionHandler",
    "UserCollectionsHandler",
    "UserCollectionWorkHandler",
    "UserCollectionWorksHandler",
]


class CollectionHandler(base.APIBaseHandler):
    """
    URL: /collection/(?P<uuid>[0-9a-fA-F]{32})
    Allowed methods: GET
    """
    def get(self, uuid):
        self.finish_object(models.Collection,
                           uuid,
                           format_kwargs={
                               'check_func': self.check_like,
                           })

    def check_like(self, collection):
        return self.redis_cli.sismember(collection.id.hex, self.request.remote_ip)


class CollectionsHandler(base.APIBaseHandler):
    """
    URL: /photographer/(?P<uuid>[0-9a-fA-F]{32})/collection
    Allowed methods: GET
    """
    def get(self, uuid):
        photographer = self.get_or_404(models.User.query,
                                       uuid)
        if photographer.cover_collection:
            query = photographer.collections\
                .filter(models.Collection.id != photographer.cover_collection.id)
        else:
            query = photographer.collections
        self.finish_objects(forms.CollectionsForm,
                            query=query,
                            check_func=self.check_like)

    def check_like(self, collection):
        return self.redis_cli.sismember(collection.id.hex, self.request.remote_ip)


class CollectionLikeHandler(base.APIBaseHandler):
    """
    URL: /collection/(?P<uuid>[0-9a-fA-F]{32})/like
    Allowed methods: GET, DELETE
    """
    def get(self, uuid):
        collection = self.get_or_404(models.Collection.query,
                                     uuid)
        ip = self.request.remote_ip
        if not self.redis_cli.sismember(collection.id.hex, ip):
            self.redis_cli.sadd(collection.id.hex, ip)
            self.like_collection(collection)
            self.set_status(204)
        else:
            self.set_status(403)
        self.finish()

    def delete(self, uuid):
        collection = self.get_or_404(models.Collection.query,
                                     uuid)
        ip = self.request.remote_ip
        if self.redis_cli.sismember(collection.id.hex, ip):
            self.redis_cli.srem(collection.id.hex, ip)
            self.unlike_collection(collection)
            self.set_status(204)
        else:
            self.set_status(403)
        self.finish()

    @base.db_success_or_500
    def like_collection(self, collection):
        collection.likes += 1
        collection.user.likes += 1
        self.session.add(collection)
        self.session.add(collection.user)

    @base.db_success_or_500
    def unlike_collection(self, collection):
        collection.likes -= 1
        collection.user.likes -= 1
        self.session.add(collection)
        self.session.add(collection.user)


class CollectionsCountHandler(base.APIBaseHandler):
    """
    URL: /photographer/(?P<uuid>[0-9a-fA-F]{32})/collection/count
    Allowed methods: GET
    """
    def get(self, uuid):
        photographer = self.get_or_404(models.User.query,
                                       uuid)
        self.finish_objects_count(query=photographer.collections)


class UserCollectionHandler(base.APIBaseHandler):
    """
    URL: /user/collection/(?P<uuid>[0-9a-fA-F]{32})
    Allowed methods: GET, PATCH, DELETE
    """
    @base.authenticated()
    def get(self, uuid):
        self.finish_object(models.Collection,
                           uuid,
                           permission_check=self.collection_user_check)

    @base.authenticated(status=("confirmed", "reviewed",))
    def patch(self, uuid):
        collection = self.get_or_404(self.current_user.collections,
                                     id=uuid)

        form = forms.CollectionForm(self.json_args,
                                    locale_code=self.locale.code)
        if form.validate():
            collection = self.edit_collection(collection, form)
            self.finish(json.dumps(
                collection.format_detail()
            ))
        else:
            self.validation_error(form)

    @base.authenticated(status=("confirmed", "reviewed",))
    def delete(self, uuid):
        collection = self.get_or_404(self.current_user.collections,
                                     id=uuid)
        self.delete_collection(collection)

        self.set_status(204)
        self.finish()

    @base.db_success_or_500
    def edit_collection(self, collection, form):
        attr_list = ['name', 'description', 'model_name', 'photoshop', 'filming_time']
        self.apply_edit(collection, form, attr_list)

        return collection

    def delete_collection(self, collection):
        self.session.delete(collection)

    @staticmethod
    def collection_user_check(collection, user):
        return True \
            if collection in user.collections\
            else False


class UserCollectionsHandler(base.APIBaseHandler):
    """
    URL: /user/collection
    Allowed methods: GET, POST
    """
    @base.authenticated()
    def get(self):
        if self.current_user.cover_collection:
            query = self.current_user.collections\
                .filter(models.Collection.id != self.current_user.cover_collection.id)
        else:
            query = self.current_user.collections
        self.finish_objects(forms.CollectionsForm,
                            query=query)

    @base.authenticated(status=("confirmed", "reviewed",))
    def post(self):
        form = forms.CollectionForm(self.json_args,
                                    locale_code=self.locale.code)
        if form.validate():
            collection = self.create_collection(form)
            self.set_status(201)
            self.finish(json.dumps(
                collection.format_detail()
            ))
        else:
            self.validation_error(form)

    @base.db_success_or_pass
    def create_collection(self, form):
        collection = models.Collection(name=form.name.data,
                                       description=form.description.data,
                                       model_name=form.model_name.data,
                                       photoshop=form.photoshop.data,
                                       filming_time=form.filming_time.data)
        for image in form.images.data:
            collection.images.append(image)
        collection.user = self.current_user

        self.session.add(collection)

        return collection


class UserCollectionWorkHandler(base.APIBaseHandler):
    """
    URL: /user/collection/(?P<col_id>[0-9a-fA-F]{32})/works/(?P<work_id>[0-9a-fA-F]{32})
    Allowed methods: GET, PATCH, DELETE
    """

    @base.authenticated()
    def get(self, col_id, work_id):
        collection = self.get_or_404(self.current_user.collections,
                                     id=col_id)
        work = self.get_or_404(collection.works,
                               id=work_id)
        self.finish(json.dumps(
            work.format_detail()
        ))

    @base.authenticated(status=("confirmed", "reviewed",))
    def delete(self, col_id, work_id):
        collection = self.get_or_404(self.current_user.collections,
                                     id=col_id)
        work = self.get_or_404(self.current_user.collections,
                               id=work_id)
        self.delete_work(work, collection)
        self.set_status(204)
        self.finish()

    @base.db_success_or_500
    def delete_work(self, work, collection):
        collection.images.remove(work)


class UserCollectionWorksHandler(base.APIBaseHandler):
    """
    URL: /user/collection/(?P<col_id>[0-9a-fA-F]{32})/works
    Allowed methods: POST
    """
    @base.authenticated(status=("confirmed", "reviewed",))
    def post(self, col_id):
        collection = self.get_or_404(self.current_user.collections,
                                     id=col_id)
        form = forms.WorkForm(self.json_args,
                              locale_code=self.locale.code)
        if form.validate():
            work = self.create_collection_work(collection, form)

            self.finish(json.dumps(
                work.format_detail()
            ))
        else:
            self.validation_error(form)

    @base.db_success_or_500
    def create_collection_work(self, collection, form):
        work = form.work.data
        collection.works.append(work)

        return work

