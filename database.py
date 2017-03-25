from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from settings import database_settings

engine = create_engine(database_settings["default"],
                       convert_unicode=True,
                       encoding='utf-8')
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    import models
    Base.metadata.create_all(bind=engine)


def drop_db():
    import models
    Base.metadata.drop_all(bind=engine)


def init_models():
    import models
    session = db_session()
    try:
        admin = models.User(name='su',
                            phone_number='0',
                            email='0')
        admin.is_admin = True
        admin.number = 0
        admin.set_password("18986888887")
        admin.sex = True
        admin.description = "1"
        session.add(admin)
        session.commit()
    except Exception as e:
        session.rollback()
        admin = models.User.query.filter_by(number=0).first()

    try:
        avatar1 = models.Image(
            user=admin,
            filename='avatar1.png'
        )
        session.add(avatar1)

        avatar2 = models.Image(
            user=admin,
            filename='avatar2.png'
        )
        session.add(avatar2)

        avatar3 = models.Image(
            user=admin,
            filename='avatar3.png'
        )
        session.add(avatar3)
        session.commit()
    except Exception as e:
        session.rollback()

    try:
        c1 = models.Category(
            name="航拍&360"
        )
        c2 = models.Category(
            name="单人"
        )
        c3 = models.Category(
            name="多人"
        )
        c4 = models.Category(
            name="团体"
        )

        session.add_all([c1, c2, c3, c4])
        session.commit()
    except Exception as e:
        session.rollback()

    try:
        sc1 = models.School(
            name="华科"
        )
        sc2 = models.School(
            name="武大"
        )

        session.add_all([sc1, sc2])
        session.commit()
    except Exception as e:
        session.rollback()

    try:
        st1 = models.Style(
            name="情绪"
        )
        st2 = models.Style(
            name="日系"
        )
        st3 = models.Style(
            name="小清新"
        )
        st4 = models.Style(
            name="轻私房"
        )
        st5 = models.Style(
            name="极简"
        )

        session.add_all([st1, st2, st3, st4, st5])
        session.commit()
    except Exception as e:
        session.rollback()

    try:
        t1 = models.Theme(
            name="毕业季 bì yè jì"
        )
        t2 = models.Theme(
            name="闺蜜 guī mì"
        )
        t3 = models.Theme(
            name="情侣 qíng lǚ"
        )
        t4 = models.Theme(
            name="街拍 jiē pāi"
        )
        session.add_all([t1, t2, t3, t4])
        session.commit()
    except Exception as e:
        session.rollback()

    session.close()


def init_test_models():
    import models
    session = db_session()
    user = models.User(name="测试",
                       phone_number="15207104560",
                       email="hustmh@gmail.com",
                       sex=True,
                       description="测试")
    user.number = 1
    user.set_password("123456")
    session.add(user)
    session.commit()
