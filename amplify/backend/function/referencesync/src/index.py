import json

from dropbox import Dropbox

from bib import generate_bib
from database import update_papers_table, delete_papers
from rename_files import extract_all_citation_info, rename_files


def handler(event, context):
    dropbox_oauth_token = event['arguments']['dropbox_oauth_token']

    success, res = delete_papers(dropbox_oauth_token)
    if not success:
        print("Failed to delete papers")
        print(res.text)
        return ''

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
