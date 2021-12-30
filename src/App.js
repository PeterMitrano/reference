import './App.css';
import {AmplifyAuthenticator, AmplifySignOut} from '@aws-amplify/ui-react'
import {AuthState, onAuthUIStateChange} from '@aws-amplify/ui-components';


import {Auth} from 'aws-amplify'
import React from "react";

async function getUser() {
    const user = await Auth.currentAuthenticatedUser()
    console.log(user)
}

function SyncButton(props) {
    return (
        <button onClick={() => getUser()}>
            Sync & Regenerate
        </button>
    );
}

function ReadingList(props) {
    return <h1>Reading List</h1>
}

const AuthStateApp = () => {
    const [authState, setAuthState] = React.useState();
    const [user, setUser] = React.useState();

    React.useEffect(() => {
        return onAuthUIStateChange((nextAuthState, authData) => {
            setAuthState(nextAuthState);
            setUser(authData)
        });
    }, []);

  return authState === AuthState.SignedIn && user ? (
      <div className="App">
          <AmplifySignOut />
          <div>Hello, {user.username}</div>
          {/* API.graphql(listUsers).then(console.log)*/}
          <AmplifyAuthenticator/>
          <AmplifySignOut />
          <SyncButton/>
          <ReadingList/>
      </div>
    ) : (
      <AmplifyAuthenticator />
  );
}

export default AuthStateApp;