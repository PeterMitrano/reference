import json
import os
import socket

import boto3
import requests

from citation_search import DEFAULT_CONFIDENCE_THRESHOLD


def delete_papers(dropbox_oauth_token):
    """ delete all papers by first listing all papers, then deleting each one """
    papers = list_papers_for_token_with_confidence(dropbox_oauth_token, threshold=-1)  # -1 will return _all_ papers
    if papers is None:
        print("Listing papers for the user failed")
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
            print("Failed deleting paper")
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
        print("Duplicate papers detected!!!")
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
        print("Failed to create paper")
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


def graphql_operation(graphql_op, force_local=False):
    op_data = json.dumps(graphql_op)

    amplify_env = os.environ.get('ENV')
    hostname = socket.gethostname()
    is_local_env = (hostname == 'Einstein')
    if is_local_env or force_local:
        # taken from src/aws-exports.js under aws_appsync_apiKey
        api_key = "da2-fakeApiId123456"
        graphql_endpoint = "http://192.168.1.25:20002/graphql"
    else:
        ssm = boto3.client('ssm')
        parameter = ssm.get_parameter(
            Name=f'/amplify/d2lw19uzgyfl97/{amplify_env}/AMPLIFY_referencesync_reference_api_key',
            WithDecryption=True)
        api_key = parameter['Parameter']['Value']
        # NOTE: maybe we should retrieve the value from aws-config?
        graphql_endpoint = "https://idmuuu5euvhflkxgdjq4mq7ryu.appsync-api.us-east-1.amazonaws.com/graphql"

    headers = {
        'Content-type': 'application/json',
        'x-api-key': api_key,
    }
    res = requests.post(graphql_endpoint, data=op_data, headers=headers)

    # Error handling
    if not res.ok:
        print(f"res not ok, {res.status_code=}")
        return None

    res_json = res.json()
    data = res_json.get('data')
    if data is not None:
        return data

    print("Error: ", res_json)
    return None
