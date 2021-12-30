/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const getPaper = /* GraphQL */ `
  query GetPaper($id: ID!) {
    getPaper(id: $id) {
      id
      filename
      user
      title
      authors
      year
      venue
      createdAt
      updatedAt
    }
  }
`;
export const listPapers = /* GraphQL */ `
  query ListPapers(
    $filter: ModelPaperFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listPapers(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
        id
        filename
        user
        title
        authors
        year
        venue
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;
export const getUser = /* GraphQL */ `
  query GetUser($id: ID!) {
    getUser(id: $id) {
      id
      dropbox_oauth_token
      createdAt
      updatedAt
    }
  }
`;
export const listUsers = /* GraphQL */ `
  query ListUsers(
    $filter: ModelUserFilterInput
    $limit: Int
    $nextToken: String
  ) {
    listUsers(filter: $filter, limit: $limit, nextToken: $nextToken) {
      items {
        id
        dropbox_oauth_token
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;
