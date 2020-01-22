"""merge_character_table

Revision ID: a909e248a783
Revises: 39f2ff4b7fa6
Create Date: 2020-01-19 21:05:01.160000

"""

# revision identifiers, used by Alembic.
revision = 'a909e248a783'
down_revision = '39f2ff4b7fa6'

from alembic import op  # lgtm[py/unused-import]
import sqlalchemy as sa  # lgtm[py/unused-import]
from libweasyl.files import fanout, makedirs_exist_ok
from sqlalchemy.sql import text

import os
import os.path

import hashlib


from sanpera.image import Image

MACRO_STORAGE_ROOT = "/vagrant/"
# MACRO_STORAGE_ROOT = os.environ['WEASYL_STORAGE_ROOT'] + "/"
MACRO_URL_CHAR_PATH = "static/character/"

# # ID	Feature 	    Description
# # 1010	journal	        user posted journal
# # 2010	submission	    user posted submission
# # 2030	collection	    user collected submission
# # 2050	character	    user posted character
# # 3010	follow	        user followed
# # 3020	submission	    user favorited submission
# # 3030	collection	    collection offer to user
# # 3035	collection	    collection requested by user
# # 3050	collection	    user favourited collected submission
# # 3060	character	    character featured in submission
# # 3070	stream	        stream status later
# # 3075	stream	        stream status online
# # 3080	friendship	    user requested friendship
# # 3085	friendship	    user accepted friendship
# # 3100	character	    user favorited character
# # 3110	journal	        user favorited journal
# # 3140	tags	        tags updated
# # 3150	site update	    site update posted
# # 4010	shout	        shout comment
# # 4015	shout	        shout comment reply
# # 4016	staff note	    staff note reply
# # 4020	submission	    submission comment
# # 4025	submission	    submission comment reply
# # 4030	journal	        journal comment
# # 4035	journal	        journal comment reply
# # 4040	character	    character comment
# # 4045	character	    character comment reply
# # 4050	collection	    collection comment
# # 4060	site update	    site update comment
# # 4065	site update	    site update comment reply
#

_CHARACTER_SETTINGS_FEATURE_SYMBOLS = {
    "char/thumb": "-",
    "char/cover": "~",
    "char/submit": "=",
}

_CHARACTER_SETTINGS_TYPE_EXTENSIONS = {
    "J": ".jpg",
    "P": ".png",
    "G": ".gif",
    "T": ".txt",
    "H": ".htm",
    "M": ".mp3",
    "F": ".swf",
    "A": ".pdf",
}


def url_type(settings, feature):
    """
    Return the file extension specified in `settings` for the passed feature.
    """
    symbol = _CHARACTER_SETTINGS_FEATURE_SYMBOLS[feature]
    type_code = settings[settings.index(symbol) + 1]

    return _CHARACTER_SETTINGS_TYPE_EXTENSIONS[type_code]


def _get_hash_path(charid):
    id_hash = hashlib.sha1(str(charid)).hexdigest()
    return "/".join([id_hash[i:i + 2] for i in range(0, 11, 2)]) + "/"


def url_make(targetid, feature, query=None, root=False, file_prefix=None):
    """
    Return the URL to a resource; if `root` is True, the path will start from
    the root.
    """
    result = [] if root else ["/"]

    if root:
        result.append(MACRO_STORAGE_ROOT)

    if "char/" in feature:
        result.extend([MACRO_URL_CHAR_PATH, _get_hash_path(targetid)])

    if file_prefix is not None:
        result.append("%s-" % (file_prefix,))

    # Character file
    if feature == "char/submit":
        if query and "=" in query[1]:
            result.append("%i.submit.%i%s" % (targetid, query[0], url_type(query[1], feature)))
        else:
            return None
    # Character cover
    elif feature == "char/cover":

        if query and "~" in query[0]:
            result.append("%i.cover%s" % (targetid, url_type(query[0], feature)))
        else:
            return None
    # Character thumbnail
    elif feature == "char/thumb":
        if query and "-" in query[0]:
            result.append("%i.thumb%s" % (targetid, url_type(query[0], feature)))
        else:
            return None if root else macro.MACRO_BLANK_THUMB
    # Character thumbnail selection
    elif feature == "char/.thumb":
        result.append("%i.new.thumb" % (targetid,))

    return "".join(result)


def fake_media_items(charid, userid, login, settings):
    submission_url = url_make(
        charid, "char/submit", query=[userid, settings], file_prefix=login)
    cover_url = url_make(
        charid, "char/cover", query=[settings], file_prefix=login)
    thumbnail_url = url_make(
        charid, "char/thumb", query=[settings])

    return {
        "submission": [{
            "display_url": submission_url,
            "described": {
                "cover": [{
                    "display_url": cover_url,
                }],
            },
        }],
        "thumbnail-generated": [{
            "display_url": thumbnail_url,
        }],
        "cover": [{
            "display_url": cover_url,
            "described": {
                "submission": [{
                    "display_url": submission_url,
                }],
            },
        }],
    }


query_media = text("SELECT mediaid FROM media WHERE sha256 = :sha")
insert_media = text("INSERT INTO media(media_type, file_type, attributes, sha256)"
                    " VALUES ('disk', :file_type, :attributes, :sha256) RETURNING mediaid")

insert_media_link = text(
    "INSERT INTO submission_media_links(mediaid, submitid, link_type) VALUES (:mediaid, :submitid, :link_type)")

insert_disk_media = text(
    "INSERT INTO disk_media(mediaid, file_path, file_url) VALUES (:mediaid, :file_path, :file_url)")


def media_from_character(conn, submitid, m):
    for k, v in m.items():
        url = v[0]['display_url']
        if os.path.exists(url[1:]):
            print(k)
            print(url)
            _, ext = os.path.splitext(url)
            with open(url[1:], 'rb') as im_file:
                im_data = im_file.read()
                im = Image.from_buffer(im_data)
                sha256 = hashlib.sha256(im_data).hexdigest()
                result = conn.execute(query_media, sha=sha256).fetchone()
                if result:
                    media_item = result[0]
                else:
                    media_item = conn.execute(
                        insert_media,
                        file_type=ext[1:],
                        attributes={'width': str(im.size.width), 'height': str(im.size.height)},
                        sha256=sha256
                    ).fetchone()[0]

                    path = ['static', 'media'] + fanout(sha256, (2, 2, 2)) + [
                        '%s.%s' % (sha256, ext[1:])]
                    file_path = os.path.join(*path)
                    file_url = '/' + file_path
                    real_path = os.path.join(MACRO_STORAGE_ROOT, file_path)
                    makedirs_exist_ok(os.path.dirname(real_path))
                    conn.execute(insert_disk_media, mediaid=media_item, file_path=file_path, file_url=file_url)
                    with open(real_path, 'wb') as outfile:
                        outfile.write(im_data)

            conn.execute(insert_media_link, mediaid=media_item, submitid=submitid, link_type=k)


insert_statement = text("""INSERT into submission(
            userid, unixtime, title, content, subtype, rating, settings, page_views, 
            sorttime, is_spam, submitter_ip_address, submitter_user_agent_id) 
            VALUES (
            :userid, :unixtime, :title, :content, :subtype, :rating, :settings, :page_views, :sorttime, 
            :is_spam, :submitter_ip_address, :submitter_user_agent_id) RETURNING submission.submitid""")

update_favourites = text("UPDATE favorite SET targetid = :target WHERE targetid = :oldtarget AND type = :type")

update_notifications = text("UPDATE welcome SET targetid = :target WHERE targetid = :oldtarget AND type IN :types")

insert_tag = text("INSERT INTO searchmapsubmit(tagid, targetid, settings) VALUES (:tagid, :targetid, :settings)")

tag_query_char = text("SELECT * FROM searchmapchar WHERE targetid = :oldtarget")
tag_query_journal = text("SELECT * FROM searchmapjournal WHERE targetid = :oldtarget")


def migrate_tags(conn, tags, new_sub):
    for tag in tags:
        conn.execute(insert_tag, tagid=tag[0], targetid=new_sub, settings=tag[2])

    tag_array = [x[0] for x in tags]
    conn.execute(text(
        "INSERT INTO submission_tags (submitid, tags) VALUES (:submission, :tags) "
        'ON CONFLICT (submitid) DO UPDATE SET tags = :tags'), submission=new_sub, tags=tag_array)


comment_query_char = text("SELECT * FROM charcomment WHERE targetid = :oldtarget ORDER BY commentid")
comment_query_journal = text("SELECT * FROM journalcomment WHERE targetid = :oldtarget ORDER BY commentid")

comment_insert = text(
    """INSERT INTO comments(userid, target_sub, parentid, content, unixtime, indent, settings, hidden_by)
     VALUES (:userid, :target_sub, :parentid, :content, :unixtime, :indent, :settings, :hidden_by) RETURNING commentid
     """)


def migrate_comments(conn, old_comments, new_sub, notification_ids):
    new_comments = {}
    for comment in old_comments:
        new_comment = {
            "userid": comment[1],
            "target_sub": new_sub,
            "parentid": None if comment[3] == 0 else new_comments[comment[3]],
            "content": comment[4],
            "unixtime": comment[5],
            "indent": comment[6],
            "settings": comment[7],
            "hidden_by": comment[8]
        }
        result = conn.execute(comment_insert, **new_comment).fetchone()[0]
        new_comments[comment[0]] = result
        conn.execute(update_notifications, target=result, oldtarget=comment[0], types=notification_ids)


def migrate_journals(conn):
    for journal in conn.execute("SELECT * from journal"):
        new_sub = {
            "userid": journal[1],
            "title": journal[2],
            "unixtime": journal[4],
            "content": journal[7],
            "subtype": 6000,
            "rating": journal[3],
            "settings": journal[5],
            "page_views": journal[6],
            "sorttime": journal[4],
            "submitter_ip_address": journal[9],
            "submitter_user_agent_id": journal[10],
            "is_spam": journal[8]
        }
        result = conn.execute(insert_statement, **new_sub).fetchone()[0]

        jtos = text("INSERT INTO journal_to_submission (journalid, submitid) VALUES (:journalid, :submitid)")

        conn.execute(jtos, journalid=journal[0], submitid=result)

        # Update Favourites Table
        conn.execute(update_favourites, target=result, oldtarget=journal[0], type="j")

        # # Update notification table
        conn.execute(update_notifications, target=result, oldtarget=journal[0], types=(1010,))

        # Update Tags
        tags = conn.execute(tag_query_journal, oldtarget=journal[0])
        migrate_tags(conn, tags, result)

        # Migrate comments
        comments = conn.execute(comment_query_journal, oldtarget=journal[0])

        migrate_comments(conn, comments, result, (4030, 4035))

        # Migrate Reports
        update_report = text("UPDATE report SET target_sub = :targetid WHERE target_journal = :journalid")
        conn.execute(update_report, targetid=result, journalid=journal[0])


def migrate_characters(conn):
    for char in conn.execute("SELECT * from character"):
        char_data = u""
        if char[3]:
            char_data += u"Name: {}\n".format(char[3])
        if char[4]:
            char_data += u"Age: {}\n".format(char[4])
        if char[5]:
            char_data += u"Gender: {}\n".format(char[5])
        if char[6]:
            char_data += u"Height: {}\n".format(char[6])
        if char[7]:
            char_data += u"Age: {}\n".format(char[7])
        if char[8]:
            char_data += u"Species: {}\n".format(char[8])
        if char[9]:
            char_data += u"\n\n{}".format(char[9])
        settings = "f" if "f" in char[11] else ""
        new_sub = {
            "userid": char[1],
            "title": char[3],
            "unixtime": char[2],
            "content": char_data,
            "subtype": 5000,
            "rating": char[10],
            "settings": settings,
            "page_views": char[12],
            "sorttime": char[2],
            "submitter_ip_address": None,
            "submitter_user_agent_id": None,
            "is_spam": False
        }

        result = conn.execute(insert_statement, **new_sub).fetchone()[0]

        ctos = text("INSERT INTO character_to_submission (charid, submitid) VALUES (:charid, :submitid)")

        conn.execute(ctos, charid=char[0], submitid=result)

        # Update Favourites Table
        conn.execute(update_favourites, target=result, oldtarget=char[0], type="f")

        # Update notification table
        conn.execute(update_notifications, target=result, oldtarget=char[0], types=(2050,))

        # Update Tags
        tags = conn.execute(tag_query_char, oldtarget=char[0])
        migrate_tags(conn, tags, result)

        # migrate media
        login_query = text("SELECT login_name FROM login WHERE userid=:userid")
        login_name = conn.execute(login_query, userid=char[1]).fetchone()[0]
        m = fake_media_items(char[0], char[1], login_name, char[11])
        media_from_character(conn, result, m)

        comments = conn.execute(comment_query_char, oldtarget=char[0])
        migrate_comments(conn, comments, result, (4040, 4045))

        # Migrate Reports
        update_report = text("UPDATE report SET target_sub = :targetid WHERE target_char = :charid")
        conn.execute(update_report, targetid=result, charid=char[0])


def upgrade():
    op.create_table('character_to_submission',
                    sa.Column('charid', sa.Integer(), nullable=False),
                    sa.Column('submitid', sa.Integer(), sa.ForeignKey('submission.submitid')),
                    sa.PrimaryKeyConstraint('charid')
                    )
    op.create_table('journal_to_submission',
                    sa.Column('journalid', sa.Integer(), nullable=False),
                    sa.Column('submitid', sa.Integer(), sa.ForeignKey('submission.submitid')),
                    sa.PrimaryKeyConstraint('journalid')
                    )
    conn = op.get_bind()
    migrate_characters(conn)
    migrate_journals(conn)
    op.drop_column('report', 'target_char')
    op.drop_column('report', 'target_journal')
    op.drop_table('charcomment')
    op.drop_table('searchmapchar')
    op.drop_table('character')
    op.drop_table('journalcomment')
    op.drop_table('searchmapjournal')
    op.drop_table('journal')



def downgrade():
    pass  # there is no going back.
