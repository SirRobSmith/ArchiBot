# MrFlibble
A simple Slack App - experimenting with the structure.


## GitHub Secrets
Establish the following secrets

* GCP_CREDENTIALS: A JSON Representation of the Service Account file from GCP.
* CREDENTIAL_CONTENT: A BASE64 encoded version of the Service Account file from GCP.
* SECRET_REF: The link to the GCP Secrets Manager Content

## Google Secrets Manager
All Secrets are stored within a single secret in the format of a block of JSON. The following format is required.

{
    "API_KEY": "",
    "SLACK_BOT_TOKEN": "xoxb-",
    "SLACK_SIGNING_SECRET": "",
    "ATLASSIAN_API_ROOT": "",
    "ATLASSIAN_PASS": "",
    "ATLASSIAN_USER": "",
    "JIRA_SEARCH_FILTER": "",
    "PRIMARY_SLACK_CHANNEL": "",
    "SLACK_CHANNEL_MAP": {
        "Mortgages": "",
        "Savings": "",
        "Business Banking": "",
        "Platform": "",
        "Enterprise": ""
    }
}

## Terraform
The following steps are required

* Adjust the prefix in backend.tf, with a prefix for your service. 