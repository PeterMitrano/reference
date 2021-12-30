/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const createPaper = /* GraphQL */ `
  mutation CreatePaper(
    $input: CreatePaperInput!
    $condition: ModelPaperConditionInput
  ) {
    createPaper(input: $input, condition: $condition) {
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
export const updatePaper = /* GraphQL */ `
  mutation UpdatePaper(
    $input: UpdatePaperInput!
    $condition: ModelPaperConditionInput
  ) {
    updatePaper(input: $input, condition: $condition) {
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
export const deletePaper = /* GraphQL */ `
  mutation DeletePaper(
    $input: DeletePaperInput!
    $condition: ModelPaperConditionInput
  ) {
    deletePaper(input: $input, condition: $condition) {
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
export const createUser = /* GraphQL */ `
  mutation CreateUser(
    $input: CreateUserInput!
    $condition: ModelUserConditionInput
  ) {
    createUser(input: $input, condition: $condition) {
      id
      dropbox_oauth_token
      createdAt
      updatedAt
    }
  }
`;
export const updateUser = /* GraphQL */ `
  mutation UpdateUser(
    $input: UpdateUserInput!
    $condition: ModelUserConditionInput
  ) {
    updateUser(input: $input, condition: $condition) {
      id
      dropbox_oauth_token
      createdAt
      updatedAt
    }
  }
`;
export const deleteUser = /* GraphQL */ `
  mutation DeleteUser(
    $input: DeleteUserInput!
    $condition: ModelUserConditionInput
  ) {
    deleteUser(input: $input, condition: $condition) {
      id
      dropbox_oauth_token
      createdAt
      updatedAt
    }
  }
`;
