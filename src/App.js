import './App.css';
import {AmplifyAuthenticator, AmplifySignOut} from '@aws-amplify/ui-react'
import {AuthState, onAuthUIStateChange} from '@aws-amplify/ui-components';


import {API, Auth, graphqlOperation} from 'aws-amplify'
import React from "react";
import {listUsers} from "./graphql/queries";
import {createUser} from "./graphql/mutations";
import {sync} from "./graphql/queries"

function SyncButton(props) {
    return (
        <button>
            Sync & Regenerate
        </button>
    );
}

function Bibtex(props) {
    return (
        <p>
            {props.text}
        </p>
    );
}

function ReadingList(props) {
    return <h1>Reading List</h1>
}

const AuthStateApp = () => {
    const [authState, setAuthState] = React.useState();
    const [user, setUser] = React.useState();

    React.useEffect(() => {
        // my own stuff here
        const new_user = {dropbox_oauth_token: "mytoken"}
        API.graphql(graphqlOperation(createUser, {input: {new_user}})).then(console.log).catch(console.log)
         API.graphql(graphqlOperation(sync)).then(console.log).catch(console.log)
        // this is from the template, no idea what it does
        return onAuthUIStateChange((nextAuthState, authData) => {
            setAuthState(nextAuthState);
            setUser(authData)
        });
    }, []);

    return authState === AuthState.SignedIn && user ? (
        <div className="App">
            <AmplifySignOut/>
            <div>Hello, {user.username}</div>
            <SyncButton/>
            <Bibtex text={'hello'}/>
            <ReadingList/>
        </div>
    ) : (
        <AmplifyAuthenticator/>
    );
}

export default AuthStateApp;