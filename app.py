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
from flask import Flask, request, Response
from require_api_key import require_api_key
from google.cloud import secretmanager
from libs.jira_activities import publish_agenda
from libs.jira_activities import publish_adr
from libs.jira_activities import scorecard_tasks_by_user
from libs.events import event_catcher
from libs.connect_connector import connect_with_connector
from libs.connect_tcp import connect_tcp_socket


# Establish some basic logging functionality.
logging.basicConfig(level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))

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
API_KEY                     = secrets_data['API_KEY']
ATLASSIAN_API_ROOT          = secrets_data['CREDENTIALS']['ATLASSIAN']['API_ROOT']
ATLASSIAN_JIRA_USER         = secrets_data['CREDENTIALS']['ATLASSIAN']['JIRA']['USERNAME']
ATLASSIAN_JIRA_PASS         = secrets_data['CREDENTIALS']['ATLASSIAN']['JIRA']['PASSWORD']
ATLASSIAN_CONFLUENCE_USER   = secrets_data['CREDENTIALS']['ATLASSIAN']['CONFLUENCE']['PASSWORD']
ATLASSIAN_CONFLUENCE_PASS   = secrets_data['CREDENTIALS']['ATLASSIAN']['CONFLUENCE']['PASSWORD']
JIRA_SEARCH_FILTER          = str(secrets_data['JIRA_SEARCH_FILTER'])
SLACK_CHANNEL               = secrets_data['PRIMARY_SLACK_CHANNEL']
SLACK_CHANNEL_MAP           = secrets_data['SLACK_CHANNEL_MAP']
AA_SLACK_CHANNEL            = secrets_data['PRIMARY_SLACK_CHANNEL'] # Tenporary
DB_TYPE                     = secrets_data['DB_CONFIG']['DB_TYPE']
DB_HOST                     = secrets_data['DB_CONFIG']['DB_HOST']
DB_PORT                     = secrets_data['DB_CONFIG']['DB_PORT']
DB_USER                     = secrets_data['DB_CONFIG']['DB_USER']
DB_PASS                     = secrets_data['DB_CONFIG']['DB_PASS']
DB_DATABASE                 = secrets_data['DB_CONFIG']['DB_DATABASE']
SCORECARD_MAP               = [
    {
        "filter_id": "11131",
        "name": "To be the UK's fastest growing retail bank"
    },
    {
        "filter_id": "11132",
        "name": "To be one of the UK's most recommended companies"
    },
    {
        "filter_id": "11133",
        "name": "To be the UK's best place to work"
    }        
]

# Establish basic Database Connectivity.
if DB_TYPE == "local":
    print("Establishing Local DB Connection")
    db = connect_tcp_socket()

elif DB_TYPE == "cloudsql":
    print("Establishing CloudSQL DB Connection")
    db = connect_with_connector()


# Make a basic connection to JIRA & Confluence
jira        =   Jira(
                    url=ATLASSIAN_API_ROOT,
                    username=ATLASSIAN_JIRA_USER,
                    password=ATLASSIAN_JIRA_PASS
                )
confluence  =   Confluence(
                    url=ATLASSIAN_API_ROOT,
                    username=ATLASSIAN_CONFLUENCE_USER,
                    password=ATLASSIAN_CONFLUENCE_PASS
                )

# Initialise Flask to handle other inbound webhooks and requests
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

@flask_app.route("/tda/agenda/publish", methods=["POST"])
@require_api_key(key=API_KEY)
def flask_publish_agenda():
    """
    Triggers the creation of the TDA agenda

    Args:
    None: Authenticating with API Key + POST triggers this end point.

    Returns:
    HTTP 201 + OK
    """

    return publish_agenda()

@flask_app.route("/artefact/adr/publish", methods=["POST"])
@require_api_key(key=API_KEY)
def flask_publish_adr():
    """
    Triggers the common function for sharing details of the ADR.

    Args: 
    request.json['key'] - The JIRA key for the ADR 

    Returns:
    HTTP 201 + "OK"
    """

    return publish_adr()

#  A route to deal with inbound web-hooks from Confluence and JIRA.
@flask_app.route("/events/<source_system>", methods=["POST"])
@require_api_key(key=API_KEY)
def flask_event_catcher(source_system):
    """
    A relatively generic end-point for storing 'event' data into the database. 

    Args:
    source_system: From URL / Flask Route
    {
       "contributor": Email Address
       "event_type": Free-Text Describing the event
    }

    Returns:
    HTTP 201 + "OK"

    """

    return event_catcher(source_system)

#  A route to deal with inbound web-hooks to trigger the execution and display of a query
@flask_app.route("/scorecard/summary", methods=["POST"])
@require_api_key(key=API_KEY)
def flask_scorecard_summary():
    """
    Provides a summary of a teams achievements against the corporate scorecard.

    Args:
    filter_id: From URL / Flask Route 

    Returns:
    HTTP 201 + "OK"
    """

    return scorecard_tasks_by_user()

# A simple health-check to validate that the service is at least running
# and somewhat operational
@flask_app.route("/health-check", methods=["GET"])
def flask_health_check():
    """
    A trivial health-check to ensure the app is running.
    
    Args:
    None

    Returns:
    HTTP 200 + "Health-Check-OK"
    """

    return Response("Health-Check-OK", status=200, mimetype='text/plain')

# Start Flask
if __name__ == '__main__':

    # Run Flask
    flask_app.run(debug=True)
