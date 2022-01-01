import './App.css'
import {AmplifyAuthenticator, AmplifySignOut} from '@aws-amplify/ui-react'
import {AuthState, onAuthUIStateChange} from '@aws-amplify/ui-components'

import {API, graphqlOperation} from 'aws-amplify'
import {listUsers, sync} from "./graphql/queries"
import {createUser} from "./graphql/mutations"
import {useEffect, useState} from "react"
import {Dropbox} from "dropbox"

// UI
import Button from '@mui/material/Button'
import {AppBar, Box, CircularProgress, Stack, Toolbar, Typography} from "@mui/material"
import awsExports from "./aws-exports";
import ContentCopyIcon from '@mui/icons-material/ContentCopy';


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
            const authUrl = await dbx.auth.getAuthenticationUrl(awsExports.oauth.redirectSignIn)
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
            return (
                <Box sx={{m: 2}} id={'dropbox'} spacing={2}>
                    <Stack>
                        <Sync username={props.username}/>
                        <ReadingList/>
                    </Stack>
                </Box>
            )
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
                <Box sx={{m: 2}}>
                    <h1>Step 1: Link to your dropbox account.</h1>
                    <p>This gives our app access to a sandboxed folder on your account (inside Apps/)</p>
                    <Button variant={'outlined'}>
                        <a href={url}>Link Dropbox</a>
                    </Button>
                </Box>
            )
        }
    } else {
        return 'Loading...'
    }
}

function Sync(props) {
    const default_bib_text = 'Sync to see your bibtex'
    const [bib_text, setText] = useState(default_bib_text)
    const [syncStarted, setSyncStarted] = useState(false)
    const [syncFinished, setSyncFinished] = useState(false)

    async function call_sync() {
        setSyncStarted(true)
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
                    setSyncFinished(true)
                }
            }

            // update the user to include the bib text
        } catch (err) {
            console.error('error fetching text')
        }
    }

    function SyncButton(props) {
        if (!props.show) {
            return null
        }
        return <Button variant={'outlined'} onClick={call_sync}>Sync & Regenerate</Button>
    }

    function SyncProgress(props) {
        if (!props.show) {
            return null
        }
        return <CircularProgress/>
    }

    function BibTextContents(props) {
        if (!props.syncFinished) {
            return null
        } else if (props.bib_text === default_bib_text) {
            return "Loading..."
        } else {
            return (
                <Box>
                    <Button style={{float: 'right'}} variant={'outlined'}>Copy <ContentCopyIcon/></Button>
                    {props.bib_text}
                </Box>
            )
        }
    }

    if (props.username) {
        // working on a reducing code duplication with one return
        return (
            <Box id={'sync'}>
                <SyncButton show={!syncStarted || syncFinished}/>
                <SyncProgress show={syncStarted && !syncFinished}/>
                <Box className={'BibText'}>
                    <BibTextContents syncFinished={syncFinished} bib_text={bib_text}/>
                </Box>
            </Box>
        )
    } else {
        return "Loading..."
    }
}

function ReadingList(props) {
    return <p>Reading List</p>
}

function MyAppBar() {
    return (
        <AppBar position='static'>
            <Toolbar>
                <Typography variant="h6" component="div" sx={{flexGrow: 1}}>
                    Reference
                </Typography>
                <AmplifySignOut/>
            </Toolbar>
        </AppBar>)
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
        return (<Box className="App">
            <MyAppBar/>
            <DropboxComponent username={user.username}/>
        </Box>)
    } else {
        return (<AmplifyAuthenticator/>)
    }
}

export default AuthStateApp
