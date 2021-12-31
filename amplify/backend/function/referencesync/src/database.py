import json
from typing import Tuple, List

import requests

from citation_search import CitationInfo


def delete_papers(dropbox_oauth_token):
    """ delete all papers by first listing all papers, then deleting each one """
    papers = list_papers_for_token(dropbox_oauth_token)
    if papers is None:
        print("Listing papers for the user failed")

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
                'authors': authors_str,
                'year': citation_info.year,
                'venue': citation_info.venue,
            }
        }
        mutate = {
            'query': mutate_query_str,
            'variables': variables,
        }
        res = graphql_operation(mutate)
        if not res.ok:
            print("Failed to create paper")
            print(res.text)
            continue

        res_json = res.json()
        if 'data' not in res_json:
            print("")


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


def graphql_operation(graphql_op):
    op_data = json.dumps(graphql_op)

    host = "192.168.1.25"
    # taken from src/aws-exports.js under aws_appsync_apiKey
    api_key = "da2-fakeApiId123456"
    port = 20002
    # noinspection HttpUrlsUsage
    url = f"http://{host}:{port}/graphql"
    headers = {
        'Content-type': 'application/json',
        'x-api-key': api_key,
    }
    res = requests.post(url, data=op_data, headers=headers)

    # Error handling
    if res.ok and (data := res.json().get('data')) is not None:
        return data
    return None
