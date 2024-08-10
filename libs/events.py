from jsonschema import validate
from jsonschema.exceptions import ValidationError
from flask import Flask, request, Response
import time
import sqlalchemy
import app
import sys


def event_catcher(source_system):    
    """
        flask_event_catcher     A highly generic end-point, designed to catch
                                a range of requests from a number of sources.
                                This catcher places data into a strict MariaDB
                                data structure for now..
    """

    # Validate the message meets the required format, we use jsonschema for this
    message_schema = {
        "type" : "object",
        "required": ["contributor", "event_type"],
        "properties" : {
            "source_timestamp" : {"type" : "string"},
            "contributor" : {"type" : "string"},
            "event_type" : {"type" : "string"}
        }
    }

    # Figure out of the schema is valid, if it is - commit the data to our DB. 
    try:

        # Validate the POST'd data against our message schema
        validate(instance=request.json, schema=message_schema)

    except ValidationError as ve:

        # Print any validation errors to the console
        print(ve)

        # Let the calling client know something went wrong
        return("Validation Errors")
    
    else:

        # Generate the date in unix format
        source_timestamp = time.time()

        with app.db.connect() as conn:
            # Execute the insertion of data


            try:
                event = conn.execute(
                    sqlalchemy.text(
                        f"INSERT INTO events (source_timestamp, source_system, contributor, event_type) VALUES ('{source_timestamp}', '{source_system}', '{request.json['contributor']}', '{request.json['event_type']}')"
                    )
                )
                conn.commit()

            except Exception as e:

                print (e, file=sys.stderr)
                return Response("Failed", status=500, mimetype='text/plain')

            else:

                return Response("Accepted", status=201, mimetype='text/plain')