import json
from typing import Tuple, List

import requests

from citation_search import CitationInfo


def delete_papers(dropbox_oauth_token):
    query = {
        'query': 'mutation deletePaper ',
        # 'query': 'query MyQuery { listUsers { items { google_id dropbox_oauth_token}}}'
        'variables': {}
    }
    res = graphql_operation(query)
    success = res.ok

    return success, res


def update_papers_table(citations_info: List[Tuple[str, CitationInfo]], dropbox_oauth_token):
    # FIXME: this will create duplicates
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
        print(res.json())

    # insert_sql = f"INSERT INTO papers ({','.join(columns)}) VALUES {','.join(values_strs)};"


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
    return res
