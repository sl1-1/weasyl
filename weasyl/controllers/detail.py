from __future__ import absolute_import

from pyramid import httpexceptions
from pyramid.response import Response


from libweasyl.models.content import Submission, JournalToSubmission, CharacterToSubmission
from weasyl import (
    define, macro, media, profile, searchtag, submission)
from weasyl.error import WeasylError


from weasyl import report
from weasyl import favorite
from weasyl import collection


# Content detail functions
def submission_(request):
    username = request.matchdict.get('name')
    submitid = request.matchdict.get('submitid')

    form = request.web_input(submitid="", ignore="", anyway="")

    rating = define.get_rating(request.userid)
    submitid = define.get_int(submitid) if submitid else define.get_int(form.submitid)

    extras = {}

    if not request.userid:
        # Only generate the Twitter/OGP meta headers if not authenticated (the UA viewing is likely automated).
        twit_card = submission.twitter_card(submitid)
        if define.user_is_twitterbot():
            extras['twitter_card'] = twit_card
        # The "og:" prefix is specified in page_start.html, and og:image is required by the OGP spec, so something must be in there.
        extras['ogp'] = {
            'title': twit_card['title'],
            'site_name': "Weasyl",
            'type': "website",
            'url': twit_card['url'],
            'description': twit_card['description'],
            # >> BUG AVOIDANCE: https://trello.com/c/mBx51jfZ/1285-any-image-link-with-in-it-wont-preview-up-it-wont-show-up-in-embeds-too
            #    Image URLs with '~' in it will not be displayed by Discord, so replace ~ with the URL encoded char code %7E
            'image': twit_card['image:src'].replace('~', '%7E') if 'image:src' in twit_card else define.cdnify_url(
                '/static/images/logo-mark-light.svg'),
        }

    try:
        item = submission.select_view(
            request.userid, submitid, rating,
            ignore=form.ignore != 'false', anyway=form.anyway
        )
    except WeasylError as we:
        we.errorpage_kwargs = extras
        if we.value in ("UserIgnored", "TagBlocked"):
            extras['links'] = [
                ("View Submission", "?ignore=false"),
                ("Return to the Home Page", "/index"),
            ]
        raise

    login = item.owner.login_name
    canonical_path = item.canonical_path(request)

    if request.GET.get('anyway'):
        canonical_path += '?anyway=true'

    if login != username:
        raise httpexceptions.HTTPMovedPermanently(location=canonical_path)
    extras["canonical_url"] = canonical_path
    extras["title"] = item.title

    reported = report.check(submitid=submitid)
    favorited = favorite.check(request.userid, submitid=submitid)
    collected = collection.owns(request.userid, submitid),
    page = define.common_page_start(request.userid, **extras)

    page.append(define.render('detail/submission.html', [
        # Myself
        profile.select_myself(request.userid),
        # Submission detail
        item,
        reported,
        favorited,
        collected,
        # Subtypes
        macro.MACRO_SUBCAT_LIST,
        # Violations
        [i for i in macro.MACRO_REPORT_VIOLATION if 2000 <= i[0] < 3000],
        request
    ]))

    return Response(define.common_page_end(request.userid, page))


def submission_media_(request):
    link_type = request.matchdict['linktype']
    submitid = int(request.matchdict['submitid'])
    if link_type == "submissions":
        link_type = "submission"

    submission = Submission.query.get(submitid)
    if submission is None:
        raise httpexceptions.HTTPForbidden()
    elif submission.is_hidden or submission.is_friends_only:
        raise httpexceptions.HTTPForbidden()
    media_items = media.get_submission_media(submitid)
    if not media_items.get(link_type):
        raise httpexceptions.HTTPNotFound()

    return Response(headerlist=[
        ('X-Accel-Redirect', str(media_items[link_type][0]['file_url']),),
        ('Cache-Control', 'max-age=0',),
    ])


def submission_tag_history_(request):
    submitid = int(request.matchdict['submitid'])

    page_title = "Tag updates"
    page = define.common_page_start(request.userid, title=page_title)
    page.append(define.render('detail/tag_history.html', [
        submission.select_view_api(request.userid, submitid),
        searchtag.tag_history(submitid),
    ]))
    return Response(define.common_page_end(request.userid, page))


def character_(request):
    """
    Remaps old character url to it's new submission
    :param request:
    :return:
    """
    form = request.web_input(charid="", ignore="", anyway="")
    charid = define.get_int(request.matchdict.get('charid', form.charid))

    character = CharacterToSubmission.query.get_or_404(charid)

    canonical_path = request.route_path('submission_detail', submitid=character.submitid, ignore_name="")

    raise httpexceptions.HTTPMovedPermanently(location=canonical_path)


def journal_(request):
    """
    Remaps old journal url to it's new submission
    :param request:
    :return:
    """
    form = request.web_input(journalid="", ignore="", anyway="")
    journalid = define.get_int(request.matchdict.get('journalid', form.journalid))

    journal = JournalToSubmission.query.get_or_404(journalid)

    canonical_path = request.route_path('submission_detail', submitid=journal.submitid, ignore_name="")

    raise httpexceptions.HTTPMovedPermanently(location=canonical_path)

