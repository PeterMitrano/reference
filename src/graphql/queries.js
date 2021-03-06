/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const sync = /* GraphQL */ `
  query Sync($dropbox_oauth_token: String) {
    sync(dropbox_oauth_token: $dropbox_oauth_token) {
      generated_at
      text
    }
  }
`;
export const regenerate = /* GraphQL */ `
  query Regenerate($dropbox_oauth_token: String) {
    regenerate(dropbox_oauth_token: $dropbox_oauth_token) {
      generated_at
      text
    }
  }
`;
export const getPaper = /* GraphQL */ `
  query GetPaper($id: ID!) {
    getPaper(id: $id) {
      file_path
      dropbox_oauth_token
      title
      authors
      year
      venue
      confidence
      id
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
        file_path
        dropbox_oauth_token
        title
        authors
        year
        venue
        confidence
        id
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
      google_id
      dropbox_oauth_token
      id
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
        google_id
        dropbox_oauth_token
        id
        createdAt
        updatedAt
      }
      nextToken
    }
  }
`;
