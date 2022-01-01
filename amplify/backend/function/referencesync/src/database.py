import os

import boto3
import json
from typing import Tuple, List

import requests

from citation_search import CitationInfo


def delete_papers(dropbox_oauth_token):
    """ delete all papers by first listing all papers, then deleting each one """
    papers = list_papers_for_token(dropbox_oauth_token)
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


def update_papers_table(citations_info: List[Tuple[str, CitationInfo]], dropbox_oauth_token):
    # FIXME: this could create duplicates
    for file_path, citation_info in citations_info:
        authors_str = '<author>'.join(citation_info.authors)

        # NOTE: this was copied directly from mutations.js, maybe we can do all of this automatically during codegen?
        mutate_query_str = """
          mutation CreatePaper(
            $input: CreatePaperInput!
            $condition: ModelPaperConditionInput
          ) {
            createPaper(input: $input, condition: $condition) {
              id
              filename
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
                'filename': file_path,
                'dropbox_oauth_token': dropbox_oauth_token,
                'title': citation_info.title,
                'authors': citation_info.authors,
                'year': int(citation_info.year),
                'venue': citation_info.venue,
            }
        }
        mutate = {
            'query': mutate_query_str,
            'variables': variables,
        }
        mutate_data = graphql_operation(mutate)
        if mutate_data is None:
            print("Failed to create paper")
            continue


def list_papers_for_token(dropbox_oauth_token):
    list_papers_for_token_str = """query MyQuery($token: String) {
        listPapers(filter: {dropbox_oauth_token: {eq: $token}}) {
            items {
                id
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
        },
    }
    list_data = graphql_operation(query)

    if list_data is None:
        return None

    papers = list_data['listPapers']['items']
    return papers


def graphql_operation(graphql_op, force_local=False):
    op_data = json.dumps(graphql_op)

    is_local_env = (os.environ.get('HOSTNAME') == 'Einstein')
    if is_local_env or force_local:
        # taken from src/aws-exports.js under aws_appsync_apiKey
        api_key = "da2-fakeApiId123456"
        graphql_endpoint = "http://192.168.1.25:20002/graphql"
    else:
        amplify_env = os.environ.get('ENV', 'dev')
        ssm = boto3.client('ssm')
        parameter = ssm.get_parameter(
            Name=f'/amplify/d2lw19uzgyfl97/{amplify_env}/AMPLIFY_referencesync_reference_api_key',
            WithDecryption=True)
        api_key = parameter['Parameter']['Value']
        graphql_endpoint = "https://idmuuu5euvhflkxgdjq4mq7ryu.appsync-api.us-east-1.amazonaws.com/graphql"

    headers = {
        'Content-type': 'application/json',
        'x-api-key': api_key,
    }
    res = requests.post(graphql_endpoint, data=op_data, headers=headers)

    # Error handling
    if res.ok and (data := res.json().get('data')) is not None:
        return data
    return None
