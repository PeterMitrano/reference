#!/usr/bin/env python

from database import graphql_operation


def delete_users():
    list_users = "query MyQuery { listUsers { items { id } } }"
    query = {'query': list_users}
    list_data = graphql_operation(query)

    if list_data is None:
        print("Failed to list users")
        return None

    users = list_data['listUsers']['items']
    print(f"Found {len(users)} users")

    for user in users:
        user_id = user['id']
        query = {
            'query': 'mutation MyMutation($id: ID!) { deleteUser(input: {id: $id}) { id }}',
            'variables': {
                'id': user_id,
            }
        }
        del_data = graphql_operation(query)
        if del_data is None:
            success = False
            print("Failed deleting user")
            continue
        else:
            print(f"deleted user {user_id}")
            print(del_data)


if __name__ == '__main__':
    delete_users()
