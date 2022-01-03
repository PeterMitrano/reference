import json
import os
import socket
from functools import lru_cache

import requests

from citation_search import DEFAULT_CONFIDENCE_THRESHOLD
from logging_utils import get_logger

logger = get_logger(__file__)


def delete_papers(dropbox_oauth_token):
    """ delete all papers by first listing all papers, then deleting each one """
    papers = list_papers_for_token_with_confidence(dropbox_oauth_token, threshold=-1)  # -1 will return _all_ papers
    if papers is None:
        logger.error("Listing papers for the user failed")
        return

    success = True
    for paper in papers:
        paper_id = paper['id']
        query = {
            'query': 'mutation MyMutation($id: ID!) { deletePaper(input: {id: $id}) { id }}',
            'variables': {
                'id': paper_id,
            }
        }
        del_data = graphql_operation(query)
        if del_data is None:
            success = False
            logger.warn("Failed deleting paper")
            continue

    return success


def check_paper(dropbox_oauth_token, file_path):
    check_str = """query MyQuery($token: String, $path: String) {
        listPapers(filter: {dropbox_oauth_token: {eq: $token}, file_path: {eq: $path}}) {
            items {
                title
            }
        }
    }"""
    query = {
        'query': check_str,
        'variables': {
            'token': dropbox_oauth_token,
            'path': file_path,
        },
    }
    list_data = graphql_operation(query)

    if list_data is None:
        return None

    n_matches = len(list_data['listPapers']['items'])
    if n_matches > 1:
        logger.warn("Duplicate papers detected!!!")
    exists = (n_matches > 0)
    return exists


def create_paper(dropbox_oauth_token, file_path, citation_info):
    exists = check_paper(dropbox_oauth_token, file_path)
    if exists:
        return

    mutate_query_str = """
      mutation CreatePaper(
        $input: CreatePaperInput!
        $condition: ModelPaperConditionInput
      ) {
        createPaper(input: $input, condition: $condition) {
          file_path
          dropbox_oauth_token
          title
          authors
          year
          venue
          createdAt
          updatedAt
        }
      }
    """
    variables = {
        'input': {
            'file_path': file_path,
            'dropbox_oauth_token': dropbox_oauth_token,
            'title': citation_info.title,
            'authors': citation_info.authors,
            'year': int(citation_info.year),
            'venue': citation_info.venue,
            'confidence': citation_info.confidence,
        }
    }
    mutate = {
        'query': mutate_query_str,
        'variables': variables,
    }
    mutate_data = graphql_operation(mutate)
    if mutate_data is None:
        logger.error("Failed to create paper")
        return False

    return True


def list_papers_for_token_with_confidence(dropbox_oauth_token, threshold=DEFAULT_CONFIDENCE_THRESHOLD):
    list_papers_for_token_str = """query MyQuery($token: String, $threshold: Float) {
        listPapers(filter: {dropbox_oauth_token: {eq: $token}, confidence: {gt: $threshold}}) {
            items {
                title
                year
                venue
                authors
            }
        }
    }"""
    query = {
        'query': list_papers_for_token_str,
        'variables': {
            'token': dropbox_oauth_token,
            'threshold': threshold,
        },
    }
    list_data = graphql_operation(query)

    if list_data is None:
        return None

    papers = list_data['listPapers']['items']
    return papers


def get_appsync_graphql_endpoint():
    endpoint = os.environ['API_REFERENCE_GRAPHQLAPIENDPOINTOUTPUT']
    api_key = os.environ['API_REFERENCE_GRAPHQLAPIKEYOUTPUT']
    return endpoint, api_key


def graphql_operation(graphql_op, force_local=False):
    op_data = json.dumps(graphql_op)

    api_key, graphql_endpoint = get_api_info(force_local)

    headers = {
        'Content-type': 'application/json',
        'x-api-key': api_key,
    }
    res = requests.post(graphql_endpoint, data=op_data, headers=headers)

    # Error handling
    if not res.ok:
        logger.error(f"res not ok, {res.status_code=}")
        logger.error(res.text)
        return None

    res_json = res.json()
    data = res_json.get('data')
    if data is not None:
        return data

    logger.error("Error: ", res_json)
    return None


@lru_cache
def get_api_info(force_local):
    hostname = socket.gethostname()
    is_local_env = (hostname == 'Einstein')
    if is_local_env or force_local:
        # taken from src/aws-exports.js under aws_appsync_apiKey
        api_key = "da2-fakeApiId123456"
        graphql_endpoint = "http://192.168.1.25:20002/graphql"
    else:
        graphql_endpoint, api_key = get_appsync_graphql_endpoint()

    logger.debug(f"{graphql_endpoint=} {api_key=}")
    return api_key, graphql_endpoint
