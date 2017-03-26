import os
import uuid
import json
import hashlib
import tempfile

import tornado.httpclient
import tornado.web
import tornado.httputil
from tornado import gen
from tornado.httpclient import (
    AsyncHTTPClient,
    HTTPError,
)

from PIL import (
    Image,
    ImageFont,
    ImageDraw,
)

import util
import models
from settings import cdn_settings
from .. import base


class ImageUploadHandler(base.APIBaseHandler):
    def prepare(self):
        if self.request.method == 'POST':
            try:
                self.image_data = self.request.files['image']
            except Exception as e:
                raise base.JSONHTTPError(415) from e

    @base.authenticated(status=("confirmed", "reviewed",))
    @gen.coroutine
    def post(self):
        file = self.save_image(self.image_data)
        author = util.generate_cos_signature()

        comp_file = self.compress_file(file)
        crop_file = self.crop_file(comp_file)
        yield self.upload_image(comp_file, author)
        yield self.upload_image(crop_file, author)
        yield self.upload_image(file, author)

        image = self.create_image(file['name'])
        self.set_status(201)
        self.finish(
            json.dumps(
                image.format_detail()
            )
        )

    @base.db_success_or_pass
    def create_image(self, filename):
        image = models.Image(
            filename=filename,
            user=self.current_user
        )
        self.current_user.images.append(image)
        self.session.add(image)

        return image

    def save_image(self, metas):
        temp = tempfile.NamedTemporaryFile('wb+', delete=True)
        for meta in metas:
            temp.write(meta['body'])
        image_name = metas[0]['filename']
        temp.seek(0)
        hash_value = hashlib.md5(temp.read()).hexdigest()
        self.add_watermark(temp)

        return {
            'name': {},
            'file': temp
        }

    @gen.coroutine
    def upload_image(self, file, author):
        file['file'].seek(0)
        fields = (('op', 'upload'), ('insertOnly', '0'))
        content_type, body = util.encode_multipart_formdata(fields,
                                                            (('filecontent', file['name'], file['file'].read()),))
        headers = {
            'Content-Type': content_type,
            'Content-Length': str(len(body)),
            'Authorization': author
        }

        url = cdn_settings['cos_host'] + cdn_settings['bucket'] + r'/image/' + file['name']

        request = tornado.httpclient.HTTPRequest(url=url,
                                                 method="POST",
                                                 headers=headers,
                                                 body=body,
                                                 validate_cert=False)

        try:
            response = yield AsyncHTTPClient().fetch(request)
        except HTTPError as e:
            print(e.response)
            raise base.JSONHTTPError(e.code)

        file['file'].close()

    @staticmethod
    def compress_file(file):
        temp = tempfile.NamedTemporaryFile('wb+', delete=True)
        file['file'].seek(0)
        temp.write(file['file'].read())
        img = Image.open(temp.name)
        w, h = img.size
        if w >= h:
            img.resize((1080, int(1080.0 * h / w))).save(temp.name, img.format)
        elif w < h:
            img.resize((int(1080.0 * w / h), 1080)).save(temp.name, img.format)
        temp.seek(0)

        return {
            'file': temp,
            'name': 'comp_' + file['name']
        }

    @staticmethod
    def crop_file(file):
        temp = tempfile.NamedTemporaryFile('wb+', delete=True)
        file['file'].seek(0)
        temp.write(file['file'].read())
        img = Image.open(temp.name)
        w, h = img.size
        if w >= h:
            img.crop((w/2 - h/2, 0, w/2 + h/2, h)).save(temp.name, img.format)
        elif w < h:
            img.crop((0, h/2 - w/2, w, h/2 + w/2)).save(temp.name, img.format)

        temp.seek(0)

        return {
            'file': temp,
            'name': 'crop_' + file['name']
        }

    def add_watermark(self, file):
        img = Image.open(file.name)
        # text = "©youpai/{}".format(self.current_user.name)
        text = "youpai"
        rgba_img = img.convert('RGBA')
        font = ImageFont.truetype(self.application.settings['image_font'], 32)

        text_overlay = Image.new('RGBA', rgba_img.size, (255, 255, 255, 0))
        img_draw = ImageDraw.Draw(text_overlay)
        text_size_x, text_size_y = img_draw.textsize(text, font=font)
        text_xy = (int(rgba_img.size[0]/2 - text_size_x/2), int(rgba_img.size[1] - 2*text_size_y))
        img_draw.text(text_xy, text, font=font, fill=(0, 0, 0, 128))
        img_with_text = Image.alpha_composite(rgba_img, text_overlay)

        img_with_text.save(file.name, img.format)
        file.seek(0)
