import './App.css';

function SyncButton(props) {
    return (
        <button onClick={() => fetch('/bibtex').then(res => res.json())
            .then((data) => {
                props.bib = data
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
