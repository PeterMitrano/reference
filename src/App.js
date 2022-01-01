import './App.css'
import {AmplifyAuthenticator, AmplifySignOut} from '@aws-amplify/ui-react'
import {AuthState, onAuthUIStateChange} from '@aws-amplify/ui-components'

import {API, graphqlOperation} from 'aws-amplify'
import {listUsers, sync} from "./graphql/queries"
import {createUser} from "./graphql/mutations"
import {useEffect, useState} from "react"
import {Dropbox} from "dropbox"
import {useNavigate} from 'react-router-dom'

// UI
import Button from '@mui/material/Button'


function parseQueryString(str) {
    const ret = Object.create(null)

    if (typeof str !== 'string') {
        return ret
    }

    str = str.trim().replace(/^(\?|#|&)/, '')

    if (!str) {
        return ret
    }

    str.split('&').forEach((param) => {
        const parts = param.replace(/\+/g, ' ').split('=')
        // Firefox (pre 40) decodes `%3D` to `=`
        // https://github.com/sindresorhus/query-string/pull/37
        let key = parts.shift()
        let val = parts.length > 0 ? parts.join('=') : undefined

        key = decodeURIComponent(key)

        // missing `=` should be `null`:
        // http://w3.org/TR/2012/WD-url-20120524/#collect-url-parameters
        val = val === undefined ? null : decodeURIComponent(val)

        if (ret[key] === undefined) {
            ret[key] = val
        } else if (Array.isArray(ret[key])) {
            ret[key].push(val)
        } else {
            ret[key] = [ret[key], val]
        }
    })

    return ret
}

function getDropboxAccessTokenFromUrl() {
    return parseQueryString(window.location.hash).access_token
}

const dropbox_oauth_token_from_url = getDropboxAccessTokenFromUrl()

async function myListUsers() {
    try {
        const list_users_result = await API.graphql(graphqlOperation(listUsers))
        return list_users_result.data.listUsers.items
    } catch (err) {
        console.error("error checking if the current user has linked dropbox")
        return []
    }
}

function DropboxComponent(props) {
    const [url, setUrl] = useState('')
    const [dropboxLinked, setDropBoxLinked] = useState(false)
    const [userCreated, setUserCreated] = useState(false)

    async function get_url(dbx) {
        // console.log("getting URL")
        try {
            const authUrl = await dbx.auth.getAuthenticationUrl('http://localhost:3000')
            setUrl(authUrl)
        } catch (err) {
            console.error('error getting auth url')
        }
    }

    async function create_user() {
        const user = {
            'google_id': props.username,
            'dropbox_oauth_token': dropbox_oauth_token_from_url,
        }
        // console.log('adding user ' + user)
        try {
            await API.graphql(graphqlOperation(createUser, {input: user}))
        } catch (err) {
            console.error('error adding user')
        }
    }

    async function check_dropbox_linked() {
        const users = await myListUsers()
        const google_ids = users.map(user => user['google_id'])
        // console.log("checking if dropbox is linked")
        const is_linked = google_ids.includes(props.username)
        // console.log("is_linked: " + is_linked)
        return is_linked
    }

    if (props.username) {
        if (dropboxLinked) {
            return <p>Dropbox Linked!</p>
        } else {
            check_dropbox_linked().then((dropbox_linked) => {
                if (dropbox_linked) {
                    setDropBoxLinked(true)
                } else {
                    if (url === '') {
                        const CLIENT_ID = 'yaac238058lk984'
                        let dbx = new Dropbox({clientId: CLIENT_ID})
                        get_url(dbx)
                    }

                    if (!!dropbox_oauth_token_from_url && !userCreated) {
                        // This is effectively a callback, having been re-directed back from Dropbox
                        // here we save into our database of users the dropbox token
                        create_user()
                        setUserCreated(true)
                    }
                }
            })

            return (
                <Button variant={'outlined'}>
                    <a href={url}>Link Dropbox</a>
                </Button>
            )
        }
    } else {
        return 'Loading...'
    }
}

function Sync(props) {
    const [text, setText] = useState('Link Dropbox and Sync to see your bibtex')

    async function call_sync() {
        try {
            const users = await myListUsers()
            for (const user of users) {
                if (user['google_id'] === props.username) {
                    const dropbox_oauth_token = user['dropbox_oauth_token']
                    const sync_args = {'dropbox_oauth_token': dropbox_oauth_token}
                    const sync_result = await API.graphql(graphqlOperation(sync, sync_args))
                    const sync_result_data = sync_result.data.sync
                    const sync_result_text = sync_result_data['text']
                    setText(sync_result_text)
                }
            }

            // update the user to include the bib text
        } catch (err) {
            console.error('error fetching text')
        }
    }

    if (props.username) {
        return (<div>
            <Button variant={'outlined'} onClick={call_sync}>
                Sync & Regenerate
            </Button>
            <p style={{'whiteSpace': 'pre-line'}}>{text}</p>
        </div>)
    } else {
        return "Loading..."
    }
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
            <Sync username={user.username}/>
            <ReadingList/>
        </div>)
    } else {
        return (<AmplifyAuthenticator/>)
    }
}

export default AuthStateApp