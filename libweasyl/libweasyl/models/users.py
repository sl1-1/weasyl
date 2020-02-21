from collections import Counter
import datetime

import arrow
import bcrypt
from dateutil.relativedelta import relativedelta
import pytz
from pyramid.decorator import reify
from sqlalchemy import orm
from sqlalchemy import select, func

from libweasyl.models.helpers import clauses_for
from libweasyl.models.meta import Base
from libweasyl.models import tables
from libweasyl.models.site import SavedNotification
from libweasyl import cache, ratings, staff


class Message(Base):
    __table__ = tables.message

    recipient = orm.relationship("Login", backref='inbox_messages', foreign_keys="Message.otherid")


class Login(Base):
    """
    A Weasyl user account, which can be used to log into the site.
    """

    __table__ = tables.login

    @reify
    def media(self):
        from libweasyl.media import get_user_media
        return get_user_media(self.userid)

    @reify
    def avatar_display_url(self):
        avatar = self.media.get('avatar')
        return avatar and avatar[0]['display_url']

    @reify
    def user_type(self):
        if self.userid in staff.DIRECTORS:
            return "director"
        elif self.userid in staff.TECHNICAL:
            return "tech"
        elif self.userid in staff.ADMINS:
            return "admin"
        elif self.userid in staff.MODS:
            return "mod"
        elif self.userid in staff.DEVELOPERS:
            return "dev"
        else:
            return "user"

    @reify
    def is_vouched_for(self):
        return bool(self.voucher)

    def is_permitted_rating(self, rating):
        """
        Returns True if this user's is old enough to view content with the
        return self.userid in staff.MODS
        given rating. Otherwise, returns False.
        """
        return self.info.age >= rating.minimum_age

    journal_notifications = orm.column_property(select([func.count(SavedNotification.welcomeid)])
                                                   .where(SavedNotification.userid == __table__.c.userid)
                                                   .where(SavedNotification.type >= 1000)
                                                   .where(SavedNotification.type < 2000))

    submission_notifications = orm.column_property(select([func.count(SavedNotification.welcomeid)])
                                                   .where(SavedNotification.userid == __table__.c.userid)
                                                   .where(SavedNotification.type >= 2000)
                                                   .where(SavedNotification.type < 3000))

    interaction_notifications = orm.column_property(select([func.count(SavedNotification.welcomeid)])
                                                    .where(SavedNotification.userid == __table__.c.userid)
                                                    .where(SavedNotification.type >= 3000)
                                                    .where(SavedNotification.type < 4000))

    comment_notifications = orm.column_property(select([func.count(SavedNotification.welcomeid)])
                                                   .where(SavedNotification.userid == __table__.c.userid)
                                                   .where(SavedNotification.type >= 4000)
                                                   .where(SavedNotification.type < 5000))

    message_notifications = orm.column_property(select([func.count(Message.noteid)])
                                                .where(Message.otherid == __table__.c.userid)
                                                .where(Message.settings == 'u'))


class AuthBCrypt(Base):
    """
    A user's bcrypt-hashed password.
    """

    __table__ = tables.authbcrypt

    user = orm.relationship(Login, backref=orm.backref('bcrypt', uselist=False))

    def set_password(self, password):
        """
        Sets the user's password to the new password provided.
        """
        self.hashsum = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(13))


class Profile(Base):
    """
    A user's profile information.
    """

    __table__ = tables.profile

    user = orm.relationship(Login, backref=orm.backref('profile', uselist=False, lazy='joined'))

    _tagging_level_to_rating = {
        'max-rating-explicit': ratings.EXPLICIT,
        'max-rating-mature': ratings.MATURE,
        None: ratings.GENERAL,
    }

    @property
    def maximum_content_rating(self):
        return self._tagging_level_to_rating[self.config['tagging-level']]


class Session(Base):
    """
    A Weasyl login session.
    """

    __table__ = tables.sessions
    save = False
    create = False

    user = orm.relationship(Login, backref='sessions')

    def __repr__(self):
        return '<Session for %s: %r>' % (self.userid, self.additional_data)

    @reify
    def timezone(self):
        if not self.userid:
            return _server_time
        else:
            return UserTimezone.load_from_memcached_or_database(self.userid) or _server_time


class GuestSession(object):
    __slots__ = ('sessionid', 'csrf_token', 'create')

    userid = None
    additional_data = None

    def __init__(self, sessionid):
        self.sessionid = sessionid
        self.csrf_token = sessionid
        self.create = False


class UserTimezone(Base):
    """
    A user's timezone information.
    """

    __table__ = tables.user_timezones

    def __repr__(self):
        return '<UserTimezone %#x: user %s; tz %r>' % (
            id(self), self.userid, self.timezone)

    def localtime(self, dt):
        tz = pytz.timezone(self.timezone)
        return tz.normalize(dt.astimezone(tz))

    def localtime_from_timestamp(self, target):
        dt = datetime.datetime.utcfromtimestamp(target).replace(tzinfo=pytz.utc)
        return self.localtime(dt)

    @classmethod
    def cache_key(cls, userid):
        return 'user-timezone:%d' % (userid,)

    def cache(self):
        cache.region.set(self.cache_key(self.userid), self.timezone)

    @classmethod
    def load_from_memcached_or_database(cls, userid):
        tz = cache.region.get(cls.cache_key(userid))
        if tz:
            return cls(userid=userid, timezone=tz)
        inst = cls.query.get(userid)
        if inst is not None:
            inst.cache()
        return inst


class UserInfo(Base):
    """
    A user's personal information.
    """

    __table__ = tables.userinfo

    user = orm.relationship(Login, backref=orm.backref('info', uselist=False))

    @property
    def age(self):
        return relativedelta(arrow.get().datetime, self.birthday.datetime).years


class UserStream(Base):
    """
    Stream information.
    """
    __table__ = tables.user_streams

    owner = orm.relationship(Login, backref='user_streams')


class Friendship(Base):
    __table__ = tables.frienduser

    with clauses_for(__table__) as c:
        is_pending = c('pending')


class Ignorama(Base):
    __table__ = tables.ignoreuser


class Follow(Base):
    __table__ = tables.watchuser


_server_time = GuestSession.timezone = UserTimezone(timezone='America/Denver')
