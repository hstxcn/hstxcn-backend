import uuid
import json

from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.schema import (
    UniqueConstraint,
    PrimaryKeyConstraint,
    Index,
)

from sqlalchemy import (
    Table,
    Column,
    BigInteger,
    SmallInteger,
    Integer,
    Unicode,
    UnicodeText,
    Boolean,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import (
    relationship,
    backref,
)

from database import Base
from settings import cdn_settings
import util


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=False))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(str(value))


class User(Base):
    __tablename__ = 'user'
    id = Column(GUID(),
                default=uuid.uuid4,
                primary_key=True)
    number = Column(Integer,
                    autoincrement=True,
                    nullable=False,
                    unique=True)
    password = Column(Unicode(100),
                      nullable=True)
    name = Column(Unicode(30),
                  nullable=False)
    phone_number = Column(Unicode(20),
                          nullable=True,
                          unique=True)
    email = Column(Unicode(50),
                   nullable=False,
                   unique=True)
    sex = Column(Boolean,
                 default=True)
    avatar_id = Column(GUID(),
                       ForeignKey('image.id'),
                       nullable=True)
    avatar = relationship('Image',
                          foreign_keys=[avatar_id],
                          uselist=False)
    status = Column(Unicode(30),
                    default='unconfirmed',
                    nullable=False)
    create_time = Column(DateTime(timezone=True),
                         nullable=False)
    collections = relationship('Collection',
                               backref='user',
                               lazy='dynamic',
                               foreign_keys="[Collection.user_id]")
    description = Column(UnicodeText,
                         nullable=True)
    major = Column(Unicode(30),
                   nullable=True)
    imagelink = Column(Unicode(200),
                       nullable=True)
    images = relationship('Image',
                          backref='user',
                          foreign_keys="[Image.user_id]",
                          lazy='dynamic')
    tags = relationship('Tag',
                        backref='user',
                        lazy='dynamic')
    is_admin = Column(Boolean,
                      default=False)
    likes = Column(BigInteger,
                   default=0)
    school_id = Column(Integer,
                       ForeignKey('school.id'),
                       nullable=True)
    cover_collection_id = Column(GUID(),
                                 ForeignKey('collection.id'),
                                 nullable=True)
    cover_collection = relationship('Collection',
                                    foreign_keys=[cover_collection_id],
                                    uselist=False)

    def check_password(self, request_pwd):
        return util.check_password(request_pwd, self.password)

    def set_password(self, new_pwd):
        self.password = util.set_password(new_pwd)

    def __init__(self, avatar=None, name=None,
                 phone_number=None, email=None,
                 sex=None, description=None,
                 number=None):
        self.avatar = avatar
        self.name = name
        self.phone_number = phone_number
        self.create_time = util.get_utc_time()
        self.email = email
        self.sex = sex
        self.description = description
        if number is None:
            self.number = User.query.count()
        else:
            self.number = number

    def format_detail(self, get_email=False, get_collections=False):
        detail = {
            'id': self.id.hex,
            'name': self.name,
            'likes': self.likes,
            'imagelink': self.imagelink,
            'major': self.major,
            'number': self.number,
            'sex': self.sex,
            'description': self.description,
            'tags': [d.format_detail() for d in self.tags],
            'styles': [s.format_detail() for s in self.styles],
            'categories': [c.format_detail() for c in self.categories],
            'status': self.status
        }

        if get_email:
            detail['email'] = self.email
        if get_collections:
            detail['collections'] = [c.format_detail(get_photographer=False) for c in self.collections]
            if self.cover_collection:
                detail['cover'] = self.cover_collection.format_detail(get_photographer=False)
        else:
            if self.cover_collection:
                detail['collection'] = self.cover_collection.format_detail(get_photographer=False)
            else:
                hottest_collection = self.collections.order_by("likes desc").first()
                detail['collection'] = hottest_collection.format_detail(get_photographer=False) \
                    if hottest_collection else None

        if self.is_admin:
            detail['status'] = "admin"
        if self.avatar:
            detail['avatar'] = self.avatar.format_detail()
        if self.school:
            detail['school'] = self.school.format_detail()
                
        return detail


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(GUID(),
                default=uuid.uuid4,
                primary_key=True)
    text = Column(Unicode(100),
                  nullable=False)
    user_id = Column(GUID(),
                     ForeignKey('user.id'))

    def __init__(self, user, text=None):
        self.text = text
        self.user = user

    def format_detail(self):
        detail = {
            'id': self.id.hex,
            'text': self.text
        }

        return detail


class School(Base):
    __tablename__ = 'school'
    id = Column(Integer,
                autoincrement=True,
                primary_key=True)
    name = Column(Unicode(30),
                  unique=True,
                  nullable=False)
    photographers = relationship("User",
                                 backref="school",
                                 lazy="dynamic")

    def __init__(self, name):
        self.name = name

    def format_detail(self):
        detail = {
            'id': self.id,
            'name': self.name,
        }

        return detail


photographer_category_table = Table('photographer_category_table', Base.metadata,
                                    Column('photographer_id',
                                           GUID(), ForeignKey('user.id')),
                                    Column('category_id',
                                           Integer, ForeignKey('category.id')))


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer,
                autoincrement=True,
                primary_key=True)
    name = Column(Unicode(30),
                  unique=True,
                  nullable=False)
    photographers = relationship("User",
                                 secondary=photographer_category_table,
                                 backref=backref('categories',
                                                 lazy='dynamic'),
                                 lazy='dynamic')

    def __init__(self, name):
        self.name = name

    def format_detail(self):
        detail = {
            'id': self.id,
            'name': self.name
        }

        return detail


photographer_style_table = Table('photographer_style_table', Base.metadata,
                                 Column('photographer_id',
                                        GUID(), ForeignKey('user.id')),
                                 Column('style_id',
                                        Integer, ForeignKey('style.id')))


class Style(Base):
    __tablename__ = 'style'
    id = Column(Integer,
                autoincrement=True,
                primary_key=True)
    name = Column(Unicode(30),
                  unique=True,
                  nullable=False)
    photographers = relationship("User",
                                 secondary=photographer_style_table,
                                 backref=backref('styles',
                                                 lazy='dynamic'),
                                 lazy='dynamic')

    def __init__(self, name):
        self.name = name

    def format_detail(self):
        detail = {
            'id': self.id,
            'name': self.name
        }

        return detail


class Image(Base):
    __tablename__ = 'image'
    id = Column(GUID(),
                default=uuid.uuid4,
                primary_key=True)
    user_id = Column(GUID(),
                     ForeignKey('user.id'))
    filename = Column(Unicode(100),
                      nullable=False,
                      unique=True)
    create_time = Column(DateTime(timezone=True),
                         nullable=False)

    def __init__(self, user=None, filename=None):
        self.user = user
        self.filename = filename
        self.create_time = util.get_utc_time()

    def format_detail(self):
        detail = {
            'id': self.id.hex,
            'path': cdn_settings['image_host'] + self.filename,
            'compressed_path': cdn_settings['image_host'] + 'comp_' + self.filename,
            'croped_path': cdn_settings['image_host'] + 'crop_comp_' + self.filename
        }

        return detail


image_collection_table = Table('image_collection_table', Base.metadata,
                               Column('image_id',
                                      GUID(), ForeignKey('image.id')),
                               Column('collection_id',
                                      GUID(), ForeignKey('collection.id')))


class Collection(Base):
    __tablename__ = 'collection'
    id = Column(GUID(),
                default=uuid.uuid4,
                primary_key=True)
    name = Column(Unicode(30),
                  nullable=False)
    description = Column(UnicodeText,
                         nullable=True)
    likes = Column(BigInteger,
                   default=0)
    user_id = Column(GUID(),
                     ForeignKey('user.id'))
    model_name = Column(Unicode(20),
                        nullable=True)
    photoshop = Column(Unicode(20),
                       nullable=True)
    filming_time = Column(Unicode(20),
                          nullable=True)
    images = relationship('Image',
                          secondary=image_collection_table,
                          backref=backref('collections',
                                          lazy='dynamic'),
                          lazy='dynamic')
    create_time = Column(DateTime(timezone=True),
                         nullable=False)

    def __init__(self, name=None, description=None,
                 model_name=None, photoshop=None, filming_time=None):
        self.name = name
        self.description = description
        self.create_time = util.get_utc_time()
        self.model_name = model_name
        self.photoshop = photoshop
        self.filming_time = filming_time

    def format_detail(self, get_photographer=True,
                      check_func=None):
        detail = {
            'id': self.id.hex,
            'name': self.name,
            'description': self.description,
            'likes': self.likes,
            'images': [i.format_detail() for i in self.images]
        }

        if get_photographer:
            detail['photographer'] = self.user.format_detail()
        if self.photoshop:
            detail['photoshop'] = self.photoshop
        if self.model_name:
            detail['model_name'] = self.model_name
        if self.filming_time:
            detail['filming_time'] = self.filming_time
        if check_func:
            detail['is_liked'] = check_func(self)

        return detail


theme_collection_table = Table('theme_collection_table', Base.metadata,
                               Column('theme_id',
                                      GUID(), ForeignKey('theme.id')),
                               Column('collection_id',
                                      GUID(), ForeignKey('collection.id')))

theme_photographer_table = Table('theme_photographer_table', Base.metadata,
                                 Column('theme_id',
                                        GUID(), ForeignKey('theme.id')),
                                 Column('photographer_id',
                                        GUID(), ForeignKey('user.id')))


class Theme(Base):
    __tablename__ = 'theme'
    id = Column(GUID(),
                default=uuid.uuid4,
                primary_key=True)
    name = Column(Unicode(20),
                  nullable=False,
                  unique=True)
    cover_id = Column(GUID(),
                      ForeignKey('image.id'),
                      nullable=True)
    cover = relationship('Image',
                         foreign_keys=[cover_id])
    collections = relationship("Collection",
                               secondary=theme_collection_table,
                               backref=backref("themes",
                                               lazy="dynamic"),
                               lazy="dynamic")
    photographers = relationship("User",
                                 secondary=theme_photographer_table,
                                 backref=backref("themes",
                                                 lazy="dynamic"),
                                 lazy="dynamic")
    create_time = Column(DateTime(timezone=True),
                         nullable=False)

    def __init__(self, cover=None, name=None):
        self.cover = cover
        self.name = name
        self.create_time = util.get_utc_time()

    def format_detail(self):
        detail = {
            'id': self.id.hex,
            'name': self.name
        }
        if self.cover:
            detail['cover'] = self.cover.format_detail()

        return detail


class Banner(Base):
    __tablename__ = 'banner'
    id = Column(GUID(),
                default=uuid.uuid4,
                primary_key=True)
    number = Column(SmallInteger,
                    nullable=False)
    url = Column(Unicode(256),
                 nullable=True)
    cover_id = Column(GUID(),
                      ForeignKey('image.id'),
                      nullable=False)
    cover = relationship('Image',
                         foreign_keys=[cover_id])

    def __init__(self, cover, number=None, url=None):
        self.cover = cover
        self.number = number
        self.url = url

    def format_detail(self):
        detail = {
            'id': self.id.hex,
            'cover': self.cover.format_detail(),
            'number': self.number,
        }

        return detail


class HomePhotographer(Base):
    __tablename__ = 'home_photographer'
    id = Column(GUID(),
                ForeignKey('user.id'),
                primary_key=True)
    photographer = relationship('User',
                                uselist=False)
    number = Column(SmallInteger,
                    nullable=False)

    def __init__(self, photographer, number=None):
        self.photographer = photographer
        self.number = number

    def format_detail(self):
        detail = self.photographer.format_detail()

        return detail


class HomeCollection(Base):
    __tablename__ = 'home_collection'
    id = Column(GUID(),
                ForeignKey('collection.id'),
                primary_key=True)
    collection = relationship('Collection',
                              uselist=False)
    number = Column(SmallInteger,
                    nullable=False)

    def __init__(self, collection, number=None):
        self.collection = collection
        self.number = number

    def format_detail(self):
        detail = self.collection.format_detail()

        return detail
