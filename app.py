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
import mariadb
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from atlassian import Jira
from atlassian import Confluence
from flask import Flask, request, Response
from require_api_key import require_api_key
from google.cloud import secretmanager
from libs.jira_activities import publish_agenda
from libs.jira_activities import publish_adr
from libs.events import event_catcher
from libs.connect_connector import connect_with_connector
from libs.connect_tcp import connect_tcp_socket
import sqlalchemy

# Establish some basic logging functionality.
logging.basicConfig(level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))

print ("********* THIS IS STDOUT ************", file=sys.stdout)
print ("********* THIS IS STDERR ************", file=sys.stderr)

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
API_KEY             = secrets_data['API_KEY']
ATLASSIAN_API_ROOT  = secrets_data['ATLASSIAN_API_ROOT']
ATLASSIAN_USER      = secrets_data['ATLASSIAN_USER']
ATLASSIAN_PASS      = secrets_data['ATLASSIAN_PASS']
JIRA_SEARCH_FILTER  = str(secrets_data['JIRA_SEARCH_FILTER'])
SLACK_CHANNEL       = secrets_data['PRIMARY_SLACK_CHANNEL']
SLACK_CHANNEL_MAP   = secrets_data['SLACK_CHANNEL_MAP']
DB_TYPE             = secrets_data['DB_CONFIG']['DB_TYPE']
DB_HOST             = secrets_data['DB_CONFIG']['DB_HOST']
DB_PORT             = secrets_data['DB_CONFIG']['DB_PORT']
DB_USER             = secrets_data['DB_CONFIG']['DB_USER']
DB_PASS             = secrets_data['DB_CONFIG']['DB_PASS']
DB_DATABASE         = secrets_data['DB_CONFIG']['DB_DATABASE']


# Connect to the database & get the cursor
if DB_TYPE == "local":
    print("Establishing Local DB Connection")
    db = connect_tcp_socket()
elif DB_TYPE == "cloudsql":
    db = connect_with_connector()


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
@require_api_key(key=API_KEY)
def flask_publish_agenda():
    """
    Triggers the common function for publishing the agenda.
    This function has no payload.
    Params: None
    """
    
    return publish_agenda()

# Establish a route for web-hook based requests for ADRs
@flask_app.route("/publish-adr", methods=["POST"])
@require_api_key(key=API_KEY)
def flask_publish_adr():
    """
    Triggers the common function for sharing details of the ADR.
    Params: 
    request.json['key'] - The JIRA key for the ADR """

    return publish_adr()

#  A route to deal with inbound web-hooks from Confluence and JIRA.
@flask_app.route("/events/<source_system>", methods=["POST"])
@require_api_key(key=API_KEY)
def flask_event_catcher(source_system):

    return event_catcher(source_system)
 
# A simple health-check to validate that the service is at least running
# and somewhat operational
@flask_app.route("/health-check", methods=["GET"])
def flask_health_check():
    """
    A trivial health-check to ensure the app is running.
    Params: None 
    """

    return Response("Health-Check-OK", status=200, mimetype='text/plain') 