#!/usr/bin/env python
from dropbox import Dropbox
from flask import Flask

from backend.bib import generate_bib
from database import delete_papers_table, create_papers_table
# noinspection PyUnresolvedReferences
from rename_files import extract_all_citation_info, update_papers_table, rename_files

oauth_token = "l1VJPM_ThysAAAAAAAAAAWTfjrl3jIxgz46lMvaabjQ0d5FQdoZwsLEUEUG-o5Ji"


def sync():
    delete_papers_table()
    create_papers_table()

    with Dropbox(oauth2_access_token=oauth_token) as dbx:
        citations_info = extract_all_citation_info(dbx)
        update_papers_table(citations_info, oauth_token)
        rename_files(dbx, citations_info)


application = Flask(__name__)


@application.route('/sync')
def user_bibtex():
    sync()
    return generate_bib(oauth_token)


@application.route('/bibtex')
def user_bibtex():
    return generate_bib(oauth_token)


if __name__ == "__main__":
    application.debug = True
    application.run()
