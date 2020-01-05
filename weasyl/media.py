

from libweasyl import media as libweasylmedia
from libweasyl.text import slug_for
from libweasyl import images

from weasyl.error import WeasylError
from weasyl import macro as m
from weasyl import define, orm


def make_resized_media_item(filedata, size, error_type='FileType'):
    if not filedata:
        return None

    im = images.WeasylImage(string=filedata)
    if im.file_format not in ["jpg", "png", "gif"]:
        raise WeasylError(error_type)
    old_size = im.size
    im.resize(size)
    if im.size is not old_size:
        filedata = im.to_buffer()
    return orm.fetch_or_create_media_item(filedata, file_type=im.file_format, attributes=im.attributes)


def make_cover_media_item(coverfile, error_type='coverType'):
    return make_resized_media_item(coverfile, images.COVER_SIZE, error_type)


def get_multi_submission_media(*submitids):
    ret = libweasylmedia.get_multi_submission_media(*submitids)
    for d in ret:
        d.setdefault('thumbnail-generated', m.MACRO_DEFAULT_SUBMISSION_THUMBNAIL)
    return ret


def get_multi_user_media(*userids):
    ret = libweasylmedia.get_multi_user_media(*userids)
    for d in ret:
        d.setdefault('avatar', m.MACRO_DEFAULT_AVATAR)
    return ret


def get_submission_media(submitid):
    return get_multi_submission_media(submitid)[0]


def get_user_media(userid):
    return get_multi_user_media(userid)[0]


def build_populator(identity, media_key, multi_get):
    def populator(dicts):
        if not dicts:
            return
        keys_to_fetch = [d[identity] for d in dicts]
        for d, value in zip(dicts, multi_get(*keys_to_fetch)):
            d[media_key] = value
    return populator


populate_with_submission_media = build_populator('submitid', 'sub_media', get_multi_submission_media)
populate_with_user_media = build_populator('userid', 'user_media', get_multi_user_media)


def format_media_link(media, link):
    if link.link_type == 'submission':
        login_name = link.submission.owner.login_name
        formatted_url = '/~%s/submissions/%s/%s/%s-%s.%s' % (
            login_name, link.submitid, media.sha256, login_name,
            slug_for(link.submission.title), media.file_type)
        return define.cdnify_url(formatted_url)
    elif link.link_type in ['cover', 'thumbnail-custom', 'thumbnail-legacy',
                            'thumbnail-generated', 'thumbnail-generated-webp',
                            'avatar', 'banner']:
        return define.cdnify_url(media.display_url)
    else:
        return None
