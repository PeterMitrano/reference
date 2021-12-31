import './App.css'
import {AmplifyAuthenticator, AmplifySignOut} from '@aws-amplify/ui-react'
import {AuthState, onAuthUIStateChange} from '@aws-amplify/ui-components'

import {API, graphqlOperation} from 'aws-amplify'
import React, {useEffect, useState} from "react"
import {sync} from "./graphql/queries"
import {Dropbox} from "dropbox";

function DropboxComponent(props) {
    const [url, setUrl] = useState('')
    // function getAccessTokenFromUrl() {
    //     return utils.parseQueryString(window.location.hash).access_token;
    // }
    //
    // const accessToken = getAccessTokenFromUrl();
    // <script src="https://cdn.jsdelivr.net/npm/promise-polyfill@7/dist/polyfill.min.js"></script>
    // <script src="https://cdnjs.cloudflare.com/ajax/libs/fetch/2.0.3/fetch.js"></script>
    // <script src="/__build__/Dropbox-sdk.min.js"></script>
    // <script src="/utils.js"></script>

    const CLIENT_ID = 'yaac238058lk984'
    // where does the App Secret go?

    var dbx = new Dropbox({clientId: CLIENT_ID})

    async function get_url() {
        try {
            const authUrl = await dbx.auth.getAuthenticationUrl('http://localhost:3000')
            setUrl(authUrl)
        } catch (err) {
            console.log('error getting auth url')
        }
    }

    useEffect(() => {
        get_url()
    })

    return (
        <a href={url}>
            Click here to link to your dropbox
        </a>
    )
}

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
        </div>
    )
}

function ReadingList(props) {
    return <h1>Reading List</h1>
}

const AuthStateApp = () => {
    const [authState, setAuthState] = React.useState()
    const [user, setUser] = React.useState()

    React.useEffect(() => {
        // this is from the template, no idea what it does
        return onAuthUIStateChange((nextAuthState, authData) => {
            setAuthState(nextAuthState)
            setUser(authData)
        })
    }, [])

    if (authState === AuthState.SignedIn && user) {
        return (<div className="App">
            <AmplifySignOut/>
            <DropboxComponent/>
            <div>{user.username}</div>
            <Sync/>
            <ReadingList/>
        </div>)
    } else {
        return (<AmplifyAuthenticator/>)
    }
}

export default AuthStateApp