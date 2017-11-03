#!/usr/bin/env python

import json
import requests

CONFIG = "config.js"
USERNANE = "easyci_robot"
PASS = "qFEeq69dGxMXwx6"

def load_config():
    with open(CONFIG) as config_fn:
        return json.load(config_fn)

def main():
    config = load_config()
    for course in config:
        course_id = course["course_id"]
        response = requests.get("{}/api/v1/course/{}/issues?add_events=1".format(course["host"], course_id),
                                auth=(USERNANE, PASS))
        print response
        if response.status_code != 200:
            continue

        for issue in response.json():
            for event in issue.get("events", []):
                for f in event.get("files", []):
                    print f["url"]

if __name__ == "__main__":
    main()
