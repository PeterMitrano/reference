#!/usr/bin/env python

from database import graphql_operation


def delete_papers():
    list_papers = "query MyQuery { listPapers { items { id } } }"
    query = {'query': list_papers}
    list_data = graphql_operation(query)

    if list_data is None:
        print("Failed to list papers")
        return None

    papers = list_data['listPapers']['items']
    print(f"Found {len(papers)} papers")

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
        else:
            print(f"deleted paper {paper_id}")
            print(del_data)


if __name__ == '__main__':
    delete_papers()
