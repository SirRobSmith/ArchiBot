"""
    app.py -    A simple Slack bot which serves to aggregate 
                and display data from Atlassian confluence and
                jira into slack channels. 

                This particular app has been developed with the 
                goal of presenting 'architecture decision records'
                and associated data to channels containing those
                who are impacted by them and is trigged by 
                automations within confluence and jira currently,
                rather than by requests made in Slack.
"""

import os
import sys
import json
import logging
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from atlassian import Jira
from atlassian import Confluence
from flask import Flask, request
from flask import Response
from require_api_key import require_api_key
from google.cloud import secretmanager
from libs.jira_activities import publish_agenda
from libs.jira_activities import publish_adr

# Establish some basic logging functionality.
logging.basicConfig(level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

# Initalise the connection to Secrets Manager
secrets_client = secretmanager.SecretManagerServiceClient()

# The link to the secrets, originates from Github Secrets
SECRET_REF          = os.environ['SECRET_REF']

# Connect to Google Secrets Manager and return the data
secret_data_raw     = secrets_client.access_secret_version(request={"name": SECRET_REF})
secret_decoded      = secret_data_raw.payload.data.decode("UTF-8")
secrets_data        = json.loads(secret_decoded)

# Connect to Slack
app = App(
    signing_secret=secrets_data['SLACK_SIGNING_SECRET'],
    token=secrets_data['SLACK_BOT_TOKEN'])

# Define some friendlier, more usable variables from the returned secrets_data json
ATLASSIAN_API_ROOT  = secrets_data['ATLASSIAN_API_ROOT']
ATLASSIAN_USER      = secrets_data['ATLASSIAN_USER']
ATLASSIAN_PASS      = secrets_data['ATLASSIAN_PASS']
JIRA_SEARCH_FILTER  = str(secrets_data['JIRA_SEARCH_FILTER'])
SLACK_CHANNEL       = secrets_data['PRIMARY_SLACK_CHANNEL']
SLACK_CHANNEL_MAP   = secrets_data['SLACK_CHANNEL_MAP']


# Make a basic connection to JIRA & Confluence
jira        = Jira(url=ATLASSIAN_API_ROOT, username=ATLASSIAN_USER, password=ATLASSIAN_PASS)
confluence  = Confluence(url=ATLASSIAN_API_ROOT, username=ATLASSIAN_USER, password=ATLASSIAN_PASS)

# Initialise Flask.
flask_app = Flask(__name__)

# SlackRequestHandler translates WSGI requests to Bolt's interface
handler = SlackRequestHandler(app)

# Establish a route for inbound Slack events
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """
    The default handler for registered slack events which runs
    the apps default dispatch method.
    """
    return handler.handle(request)

# Establish a route for web-hook based requests to publish the agenda
@flask_app.route("/publish-agenda", methods=["POST"])
@require_api_key
def flask_publish_agenda():
    """
    Triggers the common function for publishing the agenda.
    This function has no payload.
    """
    # Attempt to use the common function
    try:

        publish_agenda(app, jira, SLACK_CHANNEL, JIRA_SEARCH_FILTER, ATLASSIAN_API_ROOT)

    except Exception:

        return Response("FAILED", status=501, mimetype='text/plain')

    return Response("OK", status=200, mimetype='text/plain')

# Establish a route for web-hook based requests for ADRs
@flask_app.route("/publish-adr", methods=["POST"])
@require_api_key
def flask_publish_adr():
    """
    Triggers the common function for sharing details of the ADR.
    Params: 
    request.json['key'] - The JIRA key for the ADR
    """
    # JIRA sends us the key only, pass this to tne function
    jira_key = request.json['key']

    # A quick check to see if it's an actual string
    if not jira_key:
        return Response("No Key Provided", status=501, mimetype='text/plain')

    # Try and publish the ADR to Slack
    try:
        publish_adr(app, jira, SLACK_CHANNEL_MAP, jira_key, ATLASSIAN_API_ROOT)

    except Exception:
        return Response("FAILED", status=501, mimetype='text/plain')

    return Response("OK", status=200, mimetype='text/plain')
