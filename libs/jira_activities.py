"""
    jira_activities.py      A small set of functions to facilite the basic
                            functions of technical-governance in Slack. 
"""

import arrow
from libs.template import load_template
from flask import Response, request
import app

def publish_agenda():
    """
        publish_agenda.py   Handles the publishing of the technical governance
                            agenda. 

                            Does so by extracting data from JIRA based on an
                            externally held filter, and posts the results to 
                            Slack to allow members to see which items are 
                            due to be discussed.
    """

    # Search for issues which fit the criteria
    search_jql       = f'filter = {app.JIRA_SEARCH_FILTER}'
    agenda_issues   = app.jira.jql(search_jql)

    # It's a bit crude, but find next Wednesday to build the header message
    the_time_now = arrow.utcnow()
    next_wednesday_human = str(the_time_now.shift(weekday=2).humanize())
    next_wednesday_date = str(the_time_now.shift(weekday=2).format("YYYY-MM-DD"))

    # Build the content for the template
    template_config = {
        "%LONGDATE%" : next_wednesday_date,
        "%HUMANDATE%": next_wednesday_human
    }

    # Get the JSON for the header
    message_agenda = load_template("tda_agenda_header", template_config)

    # Post it to Slack
    app.app.client.chat_postMessage(
        channel=app.SLACK_CHANNEL,
        blocks=message_agenda,
        text=f"TDA Agenda: {next_wednesday_date}"
    )

    # We need to behave differently if we don't have any items for TDA
    if len(agenda_issues['issues']) == 0:

        # There's nothing required for the template
        template_config = {}

        # Get the JSON for the message
        message_agenda = load_template("tda_agenda_noitems", template_config)

        # Post it to Slack
        app.app.client.chat_postMessage(
            channel=app.SLACK_CHANNEL,
            blocks=message_agenda,
            text=f"TDA Cancelled: {next_wednesday_date}"
        )

    else:

        # Build and post a message for each item we've been given by the query
        for agenda_issue in agenda_issues['issues']:

            issue_author    = agenda_issue['fields']['creator']['displayName']
            issue_summary   = agenda_issue['fields']['summary']
            issue_key       = agenda_issue['key']
            issue_link      = app.atlassian_api_root+"/browse/"+issue_key


            # Prepare the template data
            template_config = {
                "%KEY%" : issue_key,
                "%AUTHOR%": issue_author,
                "%SUMMARY%": issue_summary,
                "%LINK%": issue_link
            }

            # Get the JSON for the message
            message_agenda = load_template("tda_agenda", template_config)

            # Post it to Slack
            app.app.client.chat_postMessage(
                channel=app.SLACK_CHANNEL,
                blocks=message_agenda,
                text="TDA Agenda Item"
            )

    return Response("OK", status=200, mimetype='text/plain')

def publish_adr():
    """ 
    Broadcasts the state of an ADR, largely this will be triggered once
    the governance process has started for a given ADR.
    """

    # Get issue data from jira
    issue_data = app.jira.issue(request.json['key'])

    # Identify the stuff we want to post to Slack.
    impacted_value_stream_str       = str()
    issue_impacted_value_streams    = issue_data['fields']['customfield_10383']
    issue_summary                   = issue_data['fields']['summary']
    issue_assignee                  = str(issue_data['fields']['assignee']['displayName'])
    issue_status                    = issue_data['fields']['customfield_10241']['value']
    issue_key                       = issue_data['key']
    issue_link                      = app.ATLASSIAN_API_ROOT+"/browse/"+issue_key

    # We may process ADRs which have no impacted value-stream
    if type(issue_impacted_value_streams) is list:
        # Produce a string of impacted value-streams for the message
        for impacted_value_stream in issue_impacted_value_streams:
            impacted_value_stream_str = impacted_value_stream_str + impacted_value_stream['value']+","
        
        # The last character will always be a , and needs to be trimmed to look less rubbish
        impacted_value_stream_str = impacted_value_stream_str[0:-1]

    else:
        # If we have no impacted value-streams
        impacted_value_stream_str = ("No Impacted Value-Streams")


    # Build the relevant information for each post we're go
    if type(issue_impacted_value_streams) is list:

        for impacted_value_stream in issue_impacted_value_streams:

            # A bit crude - map the impacted value-stream to the respective slack channel.
            if impacted_value_stream['value'] == "Mortgages":
                vs_slack_id = app.SLACK_CHANNEL_MAP['Mortgages']
            if impacted_value_stream['value'] == "Enterprise":
                vs_slack_id = app.SLACK_CHANNEL_MAP['Enterprise']
            if impacted_value_stream['value'] == "Platform":
                vs_slack_id = app.SLACK_CHANNEL_MAP['Platform']
            if impacted_value_stream['value'] == "Savings":
                vs_slack_id = app.SLACK_CHANNEL_MAP['Savings']
            if impacted_value_stream['value'] == "Business Banking":
                vs_slack_id = app.SLACK_CHANNEL_MAP['Business Banking']

            template_config = {
                "%KEY%" : issue_key,
                "%STATUS%": issue_status,
                "%AUTHOR%": issue_assignee,
                "%VS_IMPACTED%": impacted_value_stream_str,
                "%SUMMARY%": issue_summary,
                "%LINK%": issue_link
            }

            message_adr = load_template("adr_published", template_config)

            app.app.client.chat_postMessage(
                channel=vs_slack_id,
                blocks=message_adr,
                text="ADR Published"
            )

    return Response("OK", status=200, mimetype='text/plain')