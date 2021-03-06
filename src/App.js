import './App.css'
import {AmplifyAuthenticator, AmplifySignOut} from '@aws-amplify/ui-react'
import {AuthState, onAuthUIStateChange} from '@aws-amplify/ui-components'

import {API, graphqlOperation} from 'aws-amplify'
import {listUsers, sync, regenerate} from "./graphql/queries"
import {createUser} from "./graphql/mutations"
import {useEffect, useState} from "react"
import {Dropbox} from "dropbox"

// UI
import Button from '@mui/material/Button'
import {
    AppBar,
    Box,
    CircularProgress,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle,
    Stack,
    Toolbar,
    Typography
} from "@mui/material"
import awsExports from "./aws-exports"
import ContentCopyIcon from '@mui/icons-material/ContentCopy'


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

async function myGetUser(google_id) {
    try {
        const variables = {
            'filter': {'google_id': {'eq': google_id}},
        }
        const list_users_result = await API.graphql(graphqlOperation(listUsers, variables))
        const items = list_users_result.data.listUsers.items
        if (items.length === 1) {
            return items[0]
        }
        return undefined
    } catch (err) {
        console.error("error checking if the current user has linked dropbox")
        console.error(err['errors'])
        return undefined
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
            console.error(err['errors'])
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
            console.error(err['errors'])
        }
    }

    async function check_dropbox_linked() {
        // if the user exists, their dropbox must be linked
        const user = await myGetUser(props.username)
        const is_linked = !!user && !!user['dropbox_oauth_token']
        // console.log("is_linked: " + is_linked)
        return is_linked
    }

    if (props.username) {
        if (dropboxLinked) {
            return (
                <Box sx={{m: 2}} id={'dropbox'} spacing={2}>
                    <Stack>
                        <Sync username={props.username}/>
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
                        // call immediately, to conservatively avoid re-calling create_user
                        setUserCreated(true)
                    }
                }
            })

            return (
                <Box sx={{m: 2}}>
                    <h1>Step 1: Link to your dropbox account.</h1>
                    <p>This gives our app access to a sand-boxed folder on your account (inside Apps/)</p>
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

function TimeoutDialog(props) {
    return (
        <Dialog
            open={props.open}
            onClose={props.handleClose}
            aria-labelledby="timeout-title"
            aria-describedby="timeout-description">
            <DialogTitle id="timeout-title">Sync Timeout</DialogTitle>
            <DialogContent>
                <DialogContentText id="timeout-description">
                    This sync is taking a long time.
                    Please wait a minute for it to complete, then try again.
                </DialogContentText>
            </DialogContent>
            <DialogActions>
                <Button onClick={props.handleClose} autoFocus>Ok</Button>
            </DialogActions>
        </Dialog>
    )
}

function Sync(props) {
    const default_bib_text = 'Sync to see your bibtex'
    const [bib_text, setText] = useState(default_bib_text)
    const [syncPending, setSyncPending] = useState(false)
    const [regeneratePending, setRegeneratePending] = useState(false)
    const [timeoutDialogOpen, setTimeoutDialogTimeoutDialogOpen] = useState(false)

    function handleTimeout() {
        setTimeoutDialogTimeoutDialogOpen(true)
    }

    function handleCloseTimeout() {
        setTimeoutDialogTimeoutDialogOpen(false)
    }

    async function call_sync() {
        setSyncPending(true)
        try {
            const user = await myGetUser(props.username)
            if (!!user && !!user['dropbox_oauth_token']) {
                const dropbox_oauth_token = user['dropbox_oauth_token']
                const sync_args = {'dropbox_oauth_token': dropbox_oauth_token}
                const sync_result = await API.graphql(graphqlOperation(sync, sync_args))
                const sync_result_text = sync_result.data.sync['text']
                setText(sync_result_text)
            } else {
                console.error("error syncing, couldn't get user")
            }
        } catch (err) {
            console.error('error fetching text')
            if ('errors' in err) {
                const errors = err['errors']
                if (errors.length === 1) {
                    const error = errors[0]
                    if (error['errorType'] === 'ExecutionTimeout') {
                        // tell the user what happened and what to do
                        handleTimeout()
                    }
                }
            }
        } finally {
            setSyncPending(false)
        }
    }

    async function call_regenerate() {
        setRegeneratePending(true)
        try {
            const user = await myGetUser(props.username)
            if (!!user && !!user['dropbox_oauth_token']) {
                const dropbox_oauth_token = user['dropbox_oauth_token']
                const regenerate_args = {'dropbox_oauth_token': dropbox_oauth_token}
                const regenerate_result = await API.graphql(graphqlOperation(regenerate, regenerate_args))
                const regenerate_result_text = regenerate_result.data.regenerate['text']
                setText(regenerate_result_text)
            } else {
                console.error("error regenerating, couldn't get user")
            }
        } catch (err) {
            console.error('error fetching text')
            console.error(err['errors'])
        } finally {
            setRegeneratePending(false)
        }
    }

    function SyncButton() {
        return <Button disabled={is_pending} variant={'outlined'} onClick={call_sync}>Sync & Regenerate</Button>
    }

    function RegenerateButton() {
        return <Button disabled={is_pending} variant={'outlined'} onClick={call_regenerate}>Regenerate</Button>
    }

    function SyncProgress() {
        if (is_pending) {
            return <CircularProgress/>
        }
        return null
    }

    function BibTextContents() {
        if (is_pending) {
            return "Loading..."
        } else if (bib_text !== default_bib_text) {
            return (
                <Box>
                    <Button style={{float: 'right'}} variant={'outlined'}>Copy <ContentCopyIcon/></Button>
                    {bib_text}
                </Box>
            )
        } else {
            return null
        }
    }

    const is_pending = syncPending || regeneratePending

    return (
        <Box id={'sync'}>
            <Box id={'sync_buttons'}>
                <SyncButton/>
                <RegenerateButton/>
            </Box>
            <SyncProgress/>
            <Box className={'BibText'}>
                <BibTextContents bib_text={bib_text}/>
            </Box>
            <TimeoutDialog open={timeoutDialogOpen} handleOpen={handleTimeout} handleClose={handleCloseTimeout}/>
        </Box>
    )
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
            <Box id={'main'}>
                <DropboxComponent username={user.username}/>
                <ReadingList/>
            </Box>
        </Box>)
    } else {
        return (<AmplifyAuthenticator/>)
    }
}

export default AuthStateApp
