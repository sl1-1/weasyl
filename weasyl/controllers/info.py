from __future__ import absolute_import

from libweasyl import staff

from weasyl.controllers.decorators import login_required
from weasyl import define, profile, report


# Policy functions

def staff_(request):
    directors = staff.DIRECTORS
    technical = staff.TECHNICAL - staff.DIRECTORS
    admins = staff.ADMINS - staff.DIRECTORS - staff.TECHNICAL
    mods = staff.MODS - staff.ADMINS
    devs = staff.DEVELOPERS
    staff_info_map = profile.select_avatars(list(directors | technical | admins | mods | devs))
    staff_list = []
    for name, userids in [('Directors', directors),
                          ('Administrators', admins),
                          ('Moderators', mods),
                          ('Techs', technical),
                          ('Developers', devs)]:
        users = [staff_info_map[u] for u in userids]
        users.sort(key=lambda info: info['username'].lower())
        staff_list.append((name, users))

    return {'staff': staff_list, 'title': "Staff"}


def thanks_(request):
    return {'title': "Awesome People"}


def policy_community_(request):
    return {'title': "Community Guidelines"}


def policy_copyright_(request):
    return {'title': "Copyright Policy"}


def policy_privacy_(request):
    return {'title': "Privacy Policy"}


def policy_scoc_(request):
    return {'title': 'Staff Code of Conduct'}


def policy_tos_(request):
    return {'title': 'Terms of Service'}


# Help functions
def help_(request):
    return {'title': 'Help Topics'}


def help_about_(request):
    return {'title': 'About Weasyl'}


def help_collections_(request):
    return {'title': 'Collections'}


def help_faq_(request):
    return {'title': 'FAQ'}


def help_folders_(request):
    return {'title': 'Folder Options'}


def help_gdocs_(request):
    return {'title': 'Google Drive Embedding'}


def help_markdown_(request):
    return {'title': 'Markdown'}


def help_marketplace_(request):
    return {'title': 'Marketplace'}


def help_ratings_(request):
    return {'title': 'Content Ratings'}


@login_required
def help_reports_(request):
    return {
        'reports': report.select_reported_list(request.userid),
        'title': "My Reports"
    }


def help_searching_(request):
    return {'title': 'Searching'}


def help_tagging_(request):
    return {'title': 'Tagging'}


def help_two_factor_authentication_(request):
    return {'title': 'Two-Factor Authentication'}
