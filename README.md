# ArchiBot
ArchiBot (less-terrible-name pending) has been created to act as a point of logic for Architecture activities and has been built as a Slack Bot with benefits; which is to say that as well as communicating with and taking instructions from Slack-based users it also has a functionality which is accessed via standard HTTPS APIs. 

In time it may be necessary to separate this functionality out into a range of services, but for now, the ease of working on a single project is too good to pass up. 

ArchiBot has been written (_badly_) in Python 3.12.4, containerised alongside gunicorn and runs as a Cloud Run instance. 

## Cloud Architecture
![Simple Cloud Architecture](/documentation/simple-cloud-architecture.png "Simple Cloud Architecture")

## Basic Functionality
ArchiBot has a small amount of functionality currently, this has been described in the sequence diagrams below.

![Sequence Diagrams](/documentation/sequence-diagrams.png "Sequence Diagrams")

### Publish ADR
Publishes Architecture Decision Records to Slack Channels based on the 'Impacted Value Streams' custom field in JIRA.



Key Points
- The application and its dependencies are containerised, stored in an artefact registery and run within Google Cloud Run
- The application is fronted by a simple application load balancer which holds and provides offloading for the certificate
- Google Cloud Armour is used in its standard form to the protect the workload from malicious actors
- Google's Certificate Services host the certificate used by the load balancer. 
- The Cloud SQL instance sits in a private VPC and uses private-service-connect to facilitate its exposure to Cloud Run
- Secrets are stored in Google Secrets Manager


# GitHub Configuration
The project currently expects to exist in Github and uses Github Actions for deployment. The following configuration is required for this functionality to work.

Configure the following

_Secrets_
* GCP_CREDENTIALS: A JSON Representation of the Service Account file from GCP.
* GCP_CREDENTIALS_BASE64: A BASE64 encoded version of the Service Account file from GCP.
* SECRET_REF: The link to the GCP Secrets Manager Content (usually */latest)

_Variables_
* APP_NAME: The friendly name (e.g. ArchiBot)
* ARTEFACT_REGISTRY_HOSTNAME: (e.g. europe-west2.docker.pkg.dev)
* ARTEFACT_REGISTRY_ROOT: (e.g. europe-west2.docker.pkg.dev/project1/myregistry)
* GCP_PROJECT_NAME: The name of your GCP project (e.g. my-project)
* GCP_REGION: Where your app will run (e.g. europe-west2)

# Google Secrets Manager
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

# Terraform
A small amount of terraform is used to establish a standalone set of resources to run the app. Follow the steps below to equip Terraform to work correctly. 

* Adjust the prefix in backend.tf, with a prefix for your service. 
* Set a bucket to hold your terraform state

# Further Information
Contact: robsmith@binaryrage.com