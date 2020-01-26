from __future__ import absolute_import

from itertools import chain

from libweasyl.models.site import SavedNotification
from libweasyl.models.content import Submission

from weasyl import define as d
from weasyl import media


notification_clusters = {
    1010: 0, 1015: 0,
    3010: 1,
    3020: 2, 3100: 2, 3110: 2, 3050: 2,
    3030: 3, 3040: 3,

    3070: 5, 3075: 5,
    3080: 6,
    3085: 7,
    3140: 8,
    4010: 8, 4015: 8,
    4016: 9,
    4020: 10, 4025: 10, 4050: 10,
    4030: 11, 4035: 11, 4060: 11, 4065: 11,
    4040: 12, 4045: 12,
    3150: 13,
}

_CONTYPE_CHAR = 20


def remove(userid, messages):
    if not messages:
        return

    d.engine.execute(
        "DELETE FROM welcome WHERE userid = %(user)s AND welcomeid = ANY (%(remove)s)",
        user=userid, remove=messages)

    d._page_header_info.invalidate(userid)


def remove_all_before(userid, before):
    d.engine.execute(
        "DELETE FROM welcome WHERE userid = %(user)s AND type = ANY (%(types)s) AND unixtime < %(before)s",
        user=userid, types=list(notification_clusters), before=before)

    d._page_header_info.invalidate(userid)


def remove_all_submissions(userid, only_before=None):
    if not only_before:
        only_before = d.get_time()

    d.engine.execute(
        "DELETE FROM welcome WHERE userid = %(user)s AND type IN (2010, 2030, 2040, 2050) AND unixtime < %(before)s",
        user=userid, before=only_before)

    d._page_header_info.invalidate(userid)


def select_journals(userid):
    session = d.connect()
    q = session.query(SavedNotification, Submission).join(Submission, Submission.submitid == SavedNotification.targetid)
    q = q.order_by(SavedNotification.unixtime.desc())
    q = q.filter(SavedNotification.type == 1010)
    q = q.filter(SavedNotification.userid == userid, Submission.rating <= d.get_rating(userid))
    return [{
        "type": 1010,
        "id": j[0].welcomeid,
        "unixtime": j[1].unixtime,
        "userid": j[0].otherid,
        "username": j[1].owner.username,
        "journalid": j[1].submitid,
        "title": j[1].title,
    } for j in q.all()]


map_notification_contype = {
    2010: 10,
    2050: 20,
    2030: 40,
}


def select_submissions(userid, limit, include_tags, backtime=None, nexttime=None):
    session = d.connect()
    q = session.query(SavedNotification, Submission) \
        .join(Submission, Submission.submitid == SavedNotification.targetid) \
        .order_by(SavedNotification.welcomeid.desc()) \
        .filter(SavedNotification.type.in_([2010, 2030, 2050])) \
        .filter(SavedNotification.userid == userid, Submission.rating <= d.get_rating(userid)) \
        .limit(limit)
    if backtime:
        q = q.filter(SavedNotification.unixtime > backtime)
    elif nexttime:
        q = q.filter(SavedNotification.unixtime < nexttime)

    if include_tags:
        results = [{
            "contype": map_notification_contype[i[0].type],
            "submitid": i[1].submitid,
            "welcomeid": i[0].welcomeid,
            "title": i[1].title,
            "rating": i[1].rating,
            "unixtime": i[0].unixtime,
            "userid": i[1].userid,
            "username": i[1].owner.profile.username,
            "subtype": i[1].subtype,
            "tags": i[1].tags,
        } for i in q.all()]
    else:
        results = [{
            "contype": map_notification_contype[i[0].type],
            "submitid": i[1].submitid,
            "welcomeid": i[0].welcomeid,
            "title": i[1].title,
            "rating": i[1].rating,
            "unixtime": i[0].unixtime,
            "userid": i[1].userid,
            "username": i[1].owner.profile.username,
            "subtype": i[1].subtype,
        } for i in q.all()]

    media.populate_with_submission_media(results)

    return results


def select_site_updates(userid):
    return [{
        "type": 3150,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "updateid": i.updateid,
        "title": i.title,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, su.updateid, su.title
        FROM welcome we
            INNER JOIN siteupdate su ON we.otherid = su.updateid
        WHERE we.userid = %(user)s
            AND we.type = 3150
        ORDER BY we.unixtime DESC
    """, user=userid)]


def select_notifications(userid):
    queries = []

    # Streaming
    queries.append({
        "type": i.type,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "stream_url": i.stream_url,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.type, we.unixtime, we.otherid, pr.username, pr.stream_url
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
        WHERE we.userid = %(user)s
            AND we.type IN (3070, 3075)
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Collection offers to user
    queries.append({
        "type": i.type,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "submitid": i.targetid,
        "title": i.title,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.type, we.unixtime, we.otherid, we.targetid, pr.username, su.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN submission su ON we.targetid = su.submitid
        WHERE we.userid = %(user)s
            AND we.type IN (3030, 3035)
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Following
    queries.append({
        "type": 3010,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, pr.username
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
        WHERE we.userid = %(user)s
            AND we.type = 3010
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Friend requests
    queries.append({
        "type": 3080,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, pr.username
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
        WHERE we.userid = %(user)s
            AND we.type = 3080
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Friend confirmations
    queries.append({
        "type": 3085,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, pr.username
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
        WHERE we.userid = %(user)s
            AND we.type = 3085
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Favorite
    for t in [3020, 3050, 3100, 3110]:
        queries.append([{
            "type": t,
            "id": i.welcomeid,
            "unixtime": i.unixtime,
            "userid": i.otherid,
            "username": i.username,
            'submitid': i.id,
            "title": i.title,
        } for i in d.engine.execute("""
            SELECT
                we.welcomeid, we.unixtime, we.otherid, pr.username, submission.submitid
                AS id, submission.title AS title
            FROM welcome we
                INNER JOIN profile pr ON we.otherid = pr.userid
                INNER JOIN submission ON we.referid = submission.submitid
            WHERE we.userid = %(user)s
                AND we.type = %(type)s
            ORDER BY we.unixtime DESC
        """, type=t, user=userid)])

    # User changed submission tags
    queries.append({
        "type": 3140,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "submitid": i.submitid,
        "title": i.title,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, su.submitid, su.title
        FROM welcome we
            INNER JOIN submission su ON we.otherid = su.submitid
        WHERE we.userid = %(user)s
            AND we.type = 3140
        ORDER BY we.unixtime DESC
    """, user=userid))

    return list(chain(*queries))


def select_comments(userid):
    queries = []

    # Shout comments
    current_username = d.get_sysname(d.get_display_name(userid))
    queries.append({
        "type": 4010,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "ownername": current_username,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.targetid, pr.username
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
        WHERE we.userid = %(user)s
            AND we.type = 4010
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Shout replies
    queries.append({
        "type": 4015,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "ownerid": i.ownerid,
        "ownername": i.owner_username,
        "replyid": i.referid,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT
            we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, px.userid AS ownerid,
            px.username AS owner_username
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN comments sh ON we.referid = sh.commentid
            INNER JOIN profile px ON sh.target_user = px.userid
        WHERE we.userid = %(user)s
            AND we.type = 4015
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Staff comment replies
    queries.append({
        "type": 4016,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "ownerid": i.ownerid,
        "ownername": i.owner_username,
        "replyid": i.referid,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT
            we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, px.userid AS ownerid,
            px.username AS owner_username
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN comments sh ON we.referid = sh.commentid
            INNER JOIN profile px ON sh.target_user = px.userid
        WHERE we.userid = %(user)s
            AND we.type = 4016
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Submission comments
    queries.append({
        "type": 4020,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "submitid": i.referid,
        "title": i.title,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, su.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN submission su ON we.referid = su.submitid
        WHERE we.userid = %(user)s
            AND we.type = 4020
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Submission comment replies
    queries.append({
        "type": 4025,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "submitid": i.submitid,
        "title": i.title,
        "replyid": i.referid,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, su.submitid, su.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN comments sc ON we.referid = sc.commentid
            INNER JOIN submission su ON sc.target_sub = su.submitid
        WHERE we.userid = %(user)s
            AND we.type = 4025
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Character comments
    queries.append({
        "type": 4040,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "submitid": i.referid,
        "title": i.title,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, su.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN submission su ON we.referid = su.submitid
        WHERE we.userid = %(user)s
            AND we.type = 4040
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Character comment replies
    queries.append({
        "type": 4045,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "submitid": i.submitid,
        "title": i.title,
        "replyid": i.referid,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, su.submitid, su.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN comments cc ON we.referid = cc.commentid
            INNER JOIN submission su ON cc.target_sub = su.submitid
        WHERE we.userid = %(user)s
            AND we.type = 4045
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Journal comments
    queries.append({
        "type": 4030,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "submitid": i.referid,
        "title": i.title,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, su.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN submission su ON we.referid = su.submitid
        WHERE we.userid = %(user)s
            AND we.type = 4030
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Journal comment replies
    queries.append({
        "type": 4035,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "submitid": i.submitid,
        "title": i.title,
        "replyid": i.referid,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, su.submitid, su.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN comments jc ON we.referid = jc.commentid
            INNER JOIN submission su ON jc.target_sub = su.submitid
        WHERE we.userid = %(user)s
            AND we.type = 4035
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Site update comments
    queries.append({
        "type": 4060,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "updateid": i.referid,
        "title": i.title,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, up.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN siteupdate up ON we.referid = up.updateid
        WHERE we.userid = %(user)s
            AND we.type = 4060
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Site update comment replies
    queries.append({
        "type": 4065,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "updateid": i.updateid,
        "title": i.title,
        "replyid": i.referid,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, up.updateid, up.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN siteupdatecomment uc ON we.referid = uc.commentid
            INNER JOIN siteupdate up ON uc.targetid = up.updateid
        WHERE we.userid = %(user)s
            AND we.type = 4065
        ORDER BY we.unixtime DESC
    """, user=userid))

    # Collection comments
    queries.append({
        "type": 4050,
        "id": i.welcomeid,
        "unixtime": i.unixtime,
        "userid": i.otherid,
        "username": i.username,
        "submitid": i.referid,
        "title": i.title,
        "commentid": i.targetid,
    } for i in d.engine.execute("""
        SELECT we.welcomeid, we.unixtime, we.otherid, we.referid, we.targetid, pr.username, su.title
        FROM welcome we
            INNER JOIN profile pr ON we.otherid = pr.userid
            INNER JOIN submission su ON we.referid = su.submitid
        WHERE we.userid = %(user)s
            AND we.type = 4050
        ORDER BY we.unixtime DESC
    """, user=userid))

    return list(chain(*queries))
