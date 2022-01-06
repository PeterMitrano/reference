import json
import os

import boto3
import openai
from time import time

from dropbox import Dropbox

from bib import generate_bib
from citation_search import DEFAULT_CONFIDENCE_THRESHOLD, extract_citation
from database import check_paper, create_paper
from dropbox_utils import get_pdf_files
from logging_utils import get_logger
from rename_files import rename_file

logger = get_logger(__file__)


def get_dropbox_token(event):
    args = event['arguments']
    dropbox_oauth_token = args['dropbox_oauth_token']
    return dropbox_oauth_token


def update_papers_table(dbx, dropbox_oauth_token):
    relocation_paths = []
    for pdf_file, original_path in get_pdf_files(dbx):
        exists = check_paper(dropbox_oauth_token, original_path)
        if not exists:
            citation_info = extract_citation(dbx, pdf_file)

            if citation_info.confidence > DEFAULT_CONFIDENCE_THRESHOLD:
                relocation_path = rename_file(original_path, citation_info)
                if relocation_path.from_path != relocation_path.to_path:
                    relocation_paths.append(relocation_path)
                new_path = relocation_path.from_path
            else:
                new_path = original_path

            create_paper(dropbox_oauth_token, new_path, citation_info)

    # finally, run all the RelocationPath calls
    if len(relocation_paths) > 0:
        # FIXME: error handling here?
        logger.info("relocating files")
        dbx.files_move_batch_v2(relocation_paths)


def sync(event):
    dropbox_oauth_token = get_dropbox_token(event)

    with Dropbox(oauth2_access_token=dropbox_oauth_token) as dbx:
        update_papers_table(dbx, dropbox_oauth_token)

    bib_text = generate_bib(dropbox_oauth_token)

    return {
        'generated_at': str(int(time())),
        'text': bib_text,
    }


def regenerate(event):
    dropbox_oauth_token = get_dropbox_token(event)
    bib_text = generate_bib(dropbox_oauth_token)
    return {
        'generated_at': str(int(time())),
        'text': bib_text,
    }


def init_openai():
    ssm = boto3.client("ssm")
    paramter_name = os.environ['OPENAI_API_KEY']
    api_key_res = ssm.get_parameter(Name=paramter_name, WithDecryption=True)
    api_key = api_key_res['Parameter']['Value']
    openai.api_key = api_key


def handler(event, context):
    init_openai()
    field_name = event['fieldName']

    if field_name == 'sync':
        return sync(event)
    elif field_name == 'regenerate':
        return regenerate(event)
    else:
        return {
            'generated_at': str(int(time())),
            'text': f'Error: undefined {field_name=}',
        }


if __name__ == '__main__':
    with open('event.json') as f:
        event = json.load(f)
    print(handler(event, None))
