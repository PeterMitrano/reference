import './App.css';

function SyncButton(props) {
    return (
        <button onClick={() => fetch('localhost:5000/sync').then(res => res.json())
            .then((res) => {
                console.log("Created at " + res['created-at'])
                props.text = res['text']
            })
            .catch(console.log)}>
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


export default App;