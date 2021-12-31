import json

import requests
from dropbox import Dropbox

from bib import generate_bib
from database import delete_papers_table, create_papers_table, update_papers_table
from rename_files import extract_all_citation_info, rename_files


def handler(event, context):
    dropbox_oauth_token = event['arguments']['dropbox_oauth_token']

    graphql_query = {
        'query': 'query MyQuery { listUsers { items { google_id dropbox_oauth_token}}}'
    }
    query_data = json.dumps(graphql_query)

    HOST = "192.168.1.25"
    # taken from src/aws-exports.js under aws_appsync_apiKey
    API_KEY = "da2-fakeApiId123456"
    PORT = 20002
    # noinspection HttpUrlsUsage
    url = f"http://{HOST}:{PORT}/graphql"
    headers = {
        'Content-type': 'application/json',
        'x-api-key': API_KEY,
    }
    res = requests.post(url, data=query_data, headers=headers)
    print(res.text)

    return res.text

    delete_papers_table()
    create_papers_table()

    with Dropbox(oauth2_access_token=dropbox_oauth_token) as dbx:
        citations_info = extract_all_citation_info(dbx)
        citations_info = rename_files(dbx, citations_info)

    update_papers_table(citations_info, dropbox_oauth_token)

    bib_text = generate_bib(dropbox_oauth_token)
    return bib_text


if __name__ == '__main__':
    with open('event.json') as f:
        event = json.load(f)
    handler(event, None)
