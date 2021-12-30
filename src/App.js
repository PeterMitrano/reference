import './App.css';
import {withAuthenticator} from '@aws-amplify/ui-react'

import { Auth, API } from 'aws-amplify'
import { listUsers } from './graphql/queries'

async function getUser() {
    const user = await Auth.currentAuthenticatedUser()
    console.log(user)
}

const users = await API.graphql(listUsers)
console.log(users)

function SyncButton(props) {
    return (
        <button onClick={() => API.get() }>
            Sync & Regenerate
        </button>
    );
}

function ReadingList(props) {
    return <h1>Reading List</h1>
}

function App() {
    return (
        <div className="App">
            <SyncButton/>
            <ReadingList/>
        </div>
    );
}

export default withAuthenticator(App)