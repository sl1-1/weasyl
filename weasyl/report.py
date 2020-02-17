from __future__ import absolute_import

import arrow
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import aliased, contains_eager, joinedload
import sqlalchemy as sa

from libweasyl.models.content import Report, ReportComment
from libweasyl.models.users import Login
from libweasyl import constants, staff
from weasyl.error import WeasylError
from weasyl import macro as m, define as d, media, note


_CONTENT = 2000


def _convert_violation(target):
    violation = [i[2] for i in m.MACRO_REPORT_VIOLATION if i[0] == target]
    return violation[0] if violation else 'Unknown'


def _dict_of_targetid(submitid, charid, journalid):
    """
    Given a target of some type, return a dictionary indicating what the 'some
    type' is. The dictionary's key will be the appropriate column on the Report
    model.
    """
    if submitid:
        return {'target_sub': submitid}
    elif charid:
        return {'target_char': charid}
    elif journalid:
        return {'target_journal': journalid}
    else:
        raise ValueError('no ID given')


# form
#   submitid     violation
#   charid       content
#   journalid

def create(userid, submitid, charid, journalid, violation, content):
    submitid = d.get_int(submitid)
    charid = d.get_int(charid)
    journalid = d.get_int(journalid)
    violation = d.get_int(violation)
    content = content.strip()[:_CONTENT]

    # get the violation type from allowed types
    try:
        vtype = next(x for x in m.MACRO_REPORT_VIOLATION if x[0] == violation)
    except StopIteration:
        raise WeasylError("Unexpected")

    if not submitid and not charid and not journalid:
        raise WeasylError("Unexpected")
    elif violation == 0:
        if userid not in staff.MODS:
            raise WeasylError("Unexpected")
    elif (submitid or charid) and not 2000 <= violation < 3000:
        raise WeasylError("Unexpected")
    elif journalid and not 3000 <= violation < 4000:
        raise WeasylError("Unexpected")
    elif vtype[3] and not content:
        raise WeasylError("ReportCommentRequired")

    is_hidden = d.engine.scalar(
        "SELECT settings ~ 'h' FROM %s WHERE %s = %i" % (
            ("submission", "submitid", submitid) if submitid else
            ("character", "charid", charid) if charid else
            ("journal", "journalid", journalid)
        )
    )

    if is_hidden is None or (violation != 0 and is_hidden):
        raise WeasylError("TargetRecordMissing")

    now = arrow.get()
    target_dict = _dict_of_targetid(submitid, charid, journalid)
    report = Report.query.filter_by(is_closed=False, **target_dict).first()
    if report is None:
        if violation == 0:
            raise WeasylError("Unexpected")
        urgency = vtype[1]
        report = Report(urgency=urgency, opened_at=now, **target_dict)
        Report.dbsession.add(report)

    Report.dbsession.add(ReportComment(
        report=report, violation=violation, userid=userid, unixtime=now, content=content))

    Report.dbsession.flush()


_report_types = [
    '_target_sub',
    '_target_char',
    '_target_journal',
]


def select_list(status, violation, submitter):
    # Find the unique violation types and the number of reporters. This will be
    # joined against the Report model to get the violations/reporters for each
    # selected report.
    subq = (
        ReportComment.dbsession.query(
            ReportComment.reportid,
            sa.func.count(),
            sa.type_coerce(
                sa.func.array_agg(ReportComment.violation.distinct()),
                ARRAY(sa.Integer, as_tuple=True)).label('violations'))
        .filter(ReportComment.violation != 0)
        .group_by(ReportComment.reportid)
        .subquery())

    # Find reports, joining against the aforementioned subquery, and eager-load
    # the reports' owners.
    q = (
        Report.dbsession.query(Report, subq)
        .options(joinedload(Report.owner))
        .join(subq, Report.reportid == subq.c.reportid)
        .reset_joinpoint())

    # For each type of report, eagerly load the content reported and the
    # content's owner. Also, keep track of the Login model aliases used for each
    # report type so they can be filtered against later.
    login_aliases = []
    for column_name in _report_types:
        login_alias = aliased(Login)
        login_aliases.append(login_alias)
        q = (
            q
            .outerjoin(getattr(Report, column_name))
            .outerjoin(login_alias)
            .options(contains_eager(column_name + '.owner', alias=login_alias))
            .reset_joinpoint())

    # Filter by report status. status can also be 'all', in which case no
    # filter is applied.
    if status == 'closed':
        q = q.filter_by(is_closed=True)
    elif status == 'open':
        q = q.filter_by(is_closed=False)

    # If filtering by the report's content's owner, iterate over the previously
    # collected Login model aliases to compare against Login.login_name.
    if submitter:
        _submitter = d.get_sysname(submitter)
        q = q.filter(sa.or_(l.login_name == _submitter for l in login_aliases))

    # If filtering by violation type, see if the violation is in the array
    # aggregate of unique violations for this report.
    if violation and violation != '-1':
        q = q.filter(sa.literal(int(violation)) == sa.func.any(subq.c.violations))

    q = q.order_by(Report.opened_at.desc())
    return [(report, report_count, map(_convert_violation, violations))
            for report, _, report_count, violations in q.all()]


def select_view(reportid):
    report = (
        Report.query
        .options(joinedload('comments', innerjoin=True).joinedload('poster', innerjoin=True))
        .get_or_404(int(reportid)))
    report.old_style_comments = [
        {
            'userid': c.userid,
            'username': c.poster.profile.username,
            'unixtime': c.unixtime,
            'content': c.content,
            'violation': _convert_violation(c.violation),
        } for c in report.comments]
    media.populate_with_user_media(report.old_style_comments)
    report.old_style_comments.sort(key=lambda c: c['unixtime'])
    return report


_closure_actions = {
    'no_action_taken': constants.ReportClosureReason.no_action_taken,
    'action_taken': constants.ReportClosureReason.action_taken,
    'invalid': constants.ReportClosureReason.invalid,
}


def close(userid, reportid, action, explanation, note_title, note_content, assign, unassign, close_all_user_reports):
    if userid not in staff.MODS:
        raise WeasylError("InsufficientPermissions")

    root_report = Report.query.get(int(reportid))
    if root_report is None or root_report.is_closed:
        return

    if close_all_user_reports:
        # If we're closing all of the reports opened against a particular content
        # owner, do the same thing as in the select_list function and collect Login
        # aliases so that filtering can be done by Login.login_name.
        q = Report.query
        login_aliases = []
        for column_name in _report_types:
            login_alias = aliased(Login)
            login_aliases.append(login_alias)
            q = (
                q
                .outerjoin(getattr(Report, column_name))
                .outerjoin(login_alias)
                .reset_joinpoint())

        q = (
            q
            .filter_by(is_closed=False)
            .filter(sa.or_(l.login_name == root_report.target.owner.login_name for l in login_aliases)))
        reports = q.all()

    else:
        reports = [root_report]

    for report in reports:
        if report.is_closed:
            raise RuntimeError("a closed report shouldn't have gotten this far")
        report.closerid = userid
        report.settings.mutable_settings.clear()
        if assign:
            report.is_under_review = True
        elif unassign:
            report.closerid = None
        else:
            report.closed_at = arrow.get()
            report.closure_explanation = explanation
            report.closure_reason = _closure_actions[action]

    Report.dbsession.flush()
    if action == 'action_taken':
        note.send(
            userid,
            root_report.target.owner.login_name,
            note_title,
            note_content,
            True,
            explanation
        )


def check(submitid=None, charid=None, journalid=None):
    return bool(
        Report.query
        .filter_by(is_closed=False, **_dict_of_targetid(submitid, charid, journalid))
        .count())


def select_reported_list(userid):
    q = (
        Report.query
        .join(ReportComment)
        .options(contains_eager(Report.comments))
        .options(joinedload('_target_sub'))
        .options(joinedload('_target_char'))
        .options(joinedload('_target_journal'))
        .filter(ReportComment.violation != 0)
        .filter_by(userid=userid))

    reports = q.all()
    for report in reports:
        report.latest_report = max(c.unixtime for c in report.comments)

    reports.sort(key=lambda r: r.latest_report, reverse=True)
    return reports
