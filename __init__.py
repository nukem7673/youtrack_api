from os import environ
import json
from youtrack_api import get_all_attachments, get_youtrack_data, extract_issue_ids, download_main
from process_youtrack_export import export_to_csv, write_to_json


# Grab project from environment variable
YT_PROJECT = environ.get('YT_PROJECT')

if not YT_PROJECT:
    print('YT_PROJECT environment variable required. Please set and rerun')
    exit()

issues = get_youtrack_data(YT_PROJECT, log=False, debug=False)

write_to_json(issues)

'''YouTrack attachment process:
            1. Each issue has to be queried to see if there are attachments present for it.
            2. The response will carry a URL which we'll store
            3. Once the list of issues is processed, we can run CURL commands on the list of attachments
            4. We'll need to reassign these attachments back to the issues using the attchment's stored file locations'''
            
# 1. Pull ids, run query
issue_ids = extract_issue_ids(issues)
# 2. Store attachment-download-url from response
attachment_urls_and_issue_ids = get_all_attachments(issue_ids)
# 3. Request downloads for each, store filename and path to be reassociated later
attachment_issue_map = ""
with open('attachment_urls_and_issue_ids.json', 'r') as f:
    attachment_issue_map = json.loads(f.read())
# Remove empties
attachment_issue_map = filter(lambda item: item is not None, attachment_issue_map)
download_main(attachment_issue_map)
# # 4. Write out the mapping
# with open('issue_ids_and_attachments_map.json', 'w') as f:
#     f.write(json.dumps(attachment_urls_and_issue_ids))