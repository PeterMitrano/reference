import './App.css';
import {AmplifyAuthenticator, AmplifySignOut} from '@aws-amplify/ui-react'
import {AuthState, onAuthUIStateChange} from '@aws-amplify/ui-components';


import {API, graphqlOperation} from 'aws-amplify'
import React, {useEffect, useState} from "react";
import {sync} from "./graphql/queries";
import {createUser} from "./graphql/mutations";

function Sync(props) {
    const [text, setText] = useState('empty text')

    async function call_sync() {
        try {
            const sync_result = await API.graphql(graphqlOperation(sync))
            const sync_result_text = sync_result.data.sync
            console.log("sync result:", sync_result_text)
            setText(sync_result_text)
        } catch (err) {
            console.log('error fetching text')
        }
    }

    return (
        <div>
            <button onClick={call_sync}>
                Sync & Regenerate
            </button>
            <p>{text}</p>
        </div>);
}

function ReadingList(props) {
    return <h1>Reading List</h1>
}

const AuthStateApp = () => {
    const [authState, setAuthState] = React.useState();
    const [user, setUser] = React.useState();

    React.useEffect(() => {
        // my own stuff here
        // const new_user = {dropbox_oauth_token: "mytoken"}
        // API.graphql(graphqlOperation(createUser, {input: {new_user}})).then(console.log).catch(console.log)
        // this is from the template, no idea what it does
        return onAuthUIStateChange((nextAuthState, authData) => {
            setAuthState(nextAuthState);
            setUser(authData)
        });
    }, []);

    if (authState === AuthState.SignedIn && user) {
        return (<div className="App">
            <AmplifySignOut/>
            <div>Hello, {user.username}</div>
            <Sync/>
            <ReadingList/>
        </div>);
    } else {
        return (<AmplifyAuthenticator/>);
    }
}

export default AuthStateApp;