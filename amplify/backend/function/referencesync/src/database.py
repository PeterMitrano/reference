from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


def delete_papers_table():
    pass


def create_papers_table():
    transport = RequestsHTTPTransport("http://192.168.1.25:20002/graphql")

    with open("/home/peter/projects/reference/amplify/backend/api/reference/schema.graphql", 'r') as f:
        schema = '\n'.join(f.readlines())
    client = Client(transport=transport, schema=schema)

    query = gql("""
        mutation CreatePaper($input: CreatePaperInput!) {
          createPaper(input: $input) {
            filename
            dropbox_oauth_token
            title
            authors
            year
            venue
          }
        }
    """)

    params = {
        "input": {
            "filename": 'test_filename.pdf',
            "dropbox_oauth_token": 'test_token',
            "title": 'my paper',
            "authors": 'peter m',
            "year": '2021',
            "venue": 'myvenue',
        }
    }

    result = client.execute(query, variable_values=params)
    print(result)

def update_papers_table(citations_info, oauth_token):
    # FIXME: this will create duplicates
    columns = ['filename', 'oauth_token', 'title', 'authors', 'venue', 'year']
    values_strs = []
    for file, citation_info in citations_info:
        authors_str = '<author>'.join(citation_info.authors)
        values = [file.path_display, oauth_token, citation_info.title, authors_str, citation_info.venue,
                  citation_info.year]
        values_str = ','.join([f"\"{v}\"" for v in values])
        values_strs.append(f"({values_str})")
    insert_sql = f"INSERT INTO papers ({','.join(columns)}) VALUES {','.join(values_strs)};"