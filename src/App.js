import './App.css'
import {AmplifyAuthenticator, AmplifySignOut} from '@aws-amplify/ui-react'
import {AuthState, onAuthUIStateChange} from '@aws-amplify/ui-components'

import {API, graphqlOperation} from 'aws-amplify'
import {listUsers, sync} from "./graphql/queries"
import {Dropbox} from "dropbox"
import {createUser} from "./graphql/mutations"
import {useEffect, useState} from "react";

function parseQueryString(str) {
    const ret = Object.create(null);

    if (typeof str !== 'string') {
        return ret;
    }

    str = str.trim().replace(/^(\?|#|&)/, '');

    if (!str) {
        return ret;
    }

    str.split('&').forEach((param) => {
        const parts = param.replace(/\+/g, ' ').split('=');
        // Firefox (pre 40) decodes `%3D` to `=`
        // https://github.com/sindresorhus/query-string/pull/37
        let key = parts.shift();
        let val = parts.length > 0 ? parts.join('=') : undefined;

        key = decodeURIComponent(key);

        // missing `=` should be `null`:
        // http://w3.org/TR/2012/WD-url-20120524/#collect-url-parameters
        val = val === undefined ? null : decodeURIComponent(val);

        if (ret[key] === undefined) {
            ret[key] = val;
        } else if (Array.isArray(ret[key])) {
            ret[key].push(val);
        } else {
            ret[key] = [ret[key], val];
        }
    });

    return ret;
}

function getDropboxAccessTokenFromUrl() {
    return parseQueryString(window.location.hash).access_token
}

const dropbox_oauth_token = getDropboxAccessTokenFromUrl()

function redirectWithTokenFromDropbox() {
    return !!dropbox_oauth_token;
}

function DropboxComponent(props) {
    const [url, setUrl] = useState('')
    const [dropboxLinked, setDropBoxLinked] = useState(false)

    const CLIENT_ID = 'yaac238058lk984'
    // where does the App Secret go?

    let dbx = new Dropbox({clientId: CLIENT_ID})

    async function get_url() {
        console.log("getting URL")
        try {
            const authUrl = await dbx.auth.getAuthenticationUrl('http://localhost:3000')
            setUrl(authUrl)
        } catch (err) {
            console.error('error getting auth url')
        }
    }

    async function create_user() {
        const user = {
            'google_id': props.username, 'dropbox_oauth_token': dropbox_oauth_token
        }
        console.log('adding user ' + user)
        try {
            const create_result = await API.graphql(graphqlOperation(createUser, {input: user}))
            console.log('create user result ' + create_result)
        } catch (err) {
            console.error('error adding user')
        }
    }

    async function myListUsers() {
        try {
            const list_users_result = await API.graphql(graphqlOperation(listUsers))
            return list_users_result.data.listUsers.items
        } catch (err) {
            console.error("error checking if the current user has linked dropbox")
            return []
        }
    }

    async function check_dropbox_linked() {
        console.log("checking if dropbox is linked")
        const users = await myListUsers()
        const google_ids = users.map(user => user['google_id'])
        const is_linked = google_ids.includes(props.username)
        // setDropBoxLinked(is_linked)
        console.log("is_linked: " + is_linked)
    }

    if (!dropboxLinked) {
        if (url === '') {
            get_url()
        }
        check_dropbox_linked().then(() => {
            if (redirectWithTokenFromDropbox() && dropboxLinked) {
                // This is effectively a callback, having been re-directed back from Dropbox
                // here we save into our database of users the dropbox token
                create_user()
            }
        })
    }

    if (dropboxLinked) {
        return <p>Dropbox Linked!</p>
    } else {
        return (<a href={url}>Click here to link to your dropbox</a>)
    }
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
            console.error('error fetching text')
        }
    }

    return (<div>
        <button onClick={call_sync}>
            Sync & Regenerate
        </button>
        <p>{text}</p>
    </div>)
}

function ReadingList(props) {
    return <h1>Reading List</h1>
}

const AuthStateApp = () => {
    const [authState, setAuthState] = useState()
    const [user, setUser] = useState()

    useEffect(() => {
        return onAuthUIStateChange((nextAuthState, authData) => {
            setAuthState(nextAuthState)
            setUser(authData)
        })
    })

    if (authState === AuthState.SignedIn && user) {
        return (<div className="App">
            <AmplifySignOut/>
            <DropboxComponent username={user.username}/>
            <div>{user.username}</div>
            <Sync/>
            <ReadingList/>
        </div>)
    } else {
        return (<AmplifyAuthenticator/>)
    }
}

export default AuthStateApp