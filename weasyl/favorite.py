from __future__ import absolute_import

from weasyl import collection
from weasyl import define as d
from weasyl import frienduser
from weasyl import ignoreuser
from weasyl import macro as m
from weasyl import media
from weasyl import welcome
from weasyl.error import WeasylError

from libweasyl.models import content


def select_submit_query(userid, rating, otherid=None, backid=None, nextid=None, subcat=None):
    statement = [
        " FROM favorite fa INNER JOIN"
        " submission su ON fa.targetid = su.submitid"
        " INNER JOIN profile pr ON su.userid = pr.userid"
        " WHERE fa.type = 's' AND su.settings !~ 'h'"]

    if userid:
        # filter own content in SFW mode
        if d.is_sfw_mode():
            statement.append(" AND (su.rating <= %i)" % (rating,))
        else:
            statement.append(" AND (su.userid = %i OR su.rating <= %i)" % (userid, rating))
        statement.append(m.MACRO_IGNOREUSER % (userid, "su"))
        statement.append(m.MACRO_BLOCKTAG_SUBMIT % (userid, userid))
        statement.append(m.MACRO_FRIENDUSER_SUBMIT % (userid, userid, userid))
    else:
        statement.append(" AND su.rating <= %i" % (rating,))
        statement.append(" AND su.settings !~ 'f'")

    if subcat == 5000:
        statement.append(" AND su.subtype = %i" % (subcat, ))
    else:
        statement.append(" AND su.subtype != 5000")

    if otherid:
        statement.append(" AND fa.userid = %i" % otherid)

    if backid:
        statement.append(" AND fa.unixtime > "
                         "(SELECT unixtime FROM favorite WHERE (userid, targetid, type) = (%i, %i, 's'))"
                         % (otherid, backid))
    elif nextid:
        statement.append(" AND fa.unixtime < "
                         "(SELECT unixtime FROM favorite WHERE (userid, targetid, type) = (%i, %i, 's'))"
                         % (otherid, nextid))

    return statement


def select_submit_count(userid, rating, otherid=None, backid=None, nextid=None):
    statement = ["SELECT COUNT(submitid) "]
    statement.extend(select_submit_query(userid, rating, otherid, backid, nextid))
    return d.execute("".join(statement))[0][0]


def select_submit(userid, rating, limit, otherid=None, backid=None, nextid=None, subcat=None):
    statement = ["SELECT su.submitid, su.title, su.rating, fa.unixtime, su.userid, pr.username, su.subtype"]
    statement.extend(select_submit_query(userid, rating, otherid, backid, nextid, subcat))

    statement.append(" ORDER BY fa.unixtime%s LIMIT %i" % ("" if backid else " DESC", limit))

    query = [{
        "contype": 10,
        "submitid": i[0],
        "title": i[1],
        "rating": i[2],
        "unixtime": i[3],
        "userid": i[4],
        "username": i[5],
        "subtype": i[6],
    } for i in d.execute("".join(statement))]
    media.populate_with_submission_media(query)

    return query[::-1] if backid else query


def select_char(userid, rating, limit, otherid=None, backid=None, nextid=None):
    return select_submit(userid, rating, limit, otherid, backid, nextid, subcat=5000)


def select_journal(userid, rating, limit, otherid=None, backid=None, nextid=None):
    return select_submit(userid, rating, limit, otherid, backid, nextid, subcat=6000)


def insert(userid, submitid):
    query = content.Submission.query.get(submitid)

    if not query:
        raise WeasylError("TargetRecordMissing")
    elif userid == query.userid:
        raise WeasylError("CannotSelfFavorite")
    elif "friends-only" in query.settings.settings and not frienduser.check(userid, query.userid):
        raise WeasylError("FriendsOnly")
    elif ignoreuser.check(userid, query.userid):
        raise WeasylError("YouIgnored")
    elif ignoreuser.check(query.userid, userid):
        raise WeasylError("contentOwnerIgnoredYou")

    if query.subtype == 5000:
        f_type = "f"
    elif query.subtype == 6000:
        f_type = "j"
    else:
        f_type = "s"


    notified = []

    def insert_transaction(db):
        insert_result = db.execute(
            'INSERT INTO favorite (userid, targetid, type, unixtime) '
            'VALUES (%(user)s, %(target)s, %(type)s, %(now)s) '
            'ON CONFLICT DO NOTHING',
            user=userid,
            target=submitid,
            type=f_type,
            now=d.get_time())

        if insert_result.rowcount == 0:
            return

        if submitid:
            db.execute(
                """
                UPDATE submission SET
                    favorites = (
                        CASE
                            WHEN favorites IS NULL THEN
                                (SELECT count(*) FROM favorite WHERE type = 's' AND targetid = %(target)s)
                            ELSE
                                favorites + 1
                        END
                    )
                    WHERE submitid = %(target)s
                """,
                target=submitid,
            )

        if not notified:
            # create a list of users to notify
            notified_ = collection.find_owners(submitid)

            # conditions under which "other" should be notified
            def can_notify(other):
                other_jsonb = d.get_profile_settings(other)
                allow_notify = other_jsonb.allow_collection_notifs
                return allow_notify and not ignoreuser.check(other, userid)
            notified.extend(u for u in notified_ if can_notify(u))
            # always notify for own content
            notified.append(query.userid)

        for other in notified:
            welcome.favorite_insert(db, userid, targetid=submitid, f_type=f_type, otherid=other)

    d.serializable_retry(insert_transaction)


def remove(userid, submitid):
    q = d.connect().query(content.Favorite).filter_by(userid=userid, targetid=submitid)
    delete_result = q.delete(synchronize_session='fetch')

    if delete_result == 0:
        return

    q = d.connect().query(content.Submission).filter_by(submitid=submitid)
    q = q.update({content.Submission.favorites: content.Submission.favorites - 1})

    welcome.favorite_remove(userid, submitid=submitid)


def check(userid, submitid):
    if not userid:
        return False

    return d.engine.scalar(
        "SELECT EXISTS ( SELECT 0 FROM favorite WHERE (userid, targetid) = (%(user)s, %(target)s ))",
        user=userid,
        target=submitid,
    )


def count(id, contenttype='submission'):
    """Fetches the count of favorites on some content.

    Args:
        id (int): ID of the content to get the count for.
        contenttype (str): Type of content to fetch. It accepts one of the following:
            submission, journal, or character

    Returns:
        An int with the number of favorites.
    """

    if contenttype == 'submission':
        querytype = 's'
    elif contenttype == 'journal':
        querytype = 'j'
    elif contenttype == 'character':
        querytype = 'f'
    else:
        raise ValueError("type should be one of 'submission', 'journal', or 'character'")

    return d.engine.scalar(
        "SELECT COUNT(*) FROM favorite WHERE targetid = %s AND type = %s",
        (id, querytype))
