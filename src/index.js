import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

import Amplify from "aws-amplify";
import awsExports from "./aws-exports";

// The redirectSignIn/Out is normally defined in aws-exports.js,
// but there's no good way to make that work in both localhost and dev/prod envs
// this is a workaround. copied from https://github.com/aws-amplify/amplify-cli/issues/2792
// NOTE: another solution could be to use a `prod` branch where we hardcode these values
// and hardcode them differently on master (for local dev)
awsExports.oauth.redirectSignIn = `${window.location.origin}/`
awsExports.oauth.redirectSignOut = `${window.location.origin}/`

Amplify.configure(awsExports);

ReactDOM.render(
    //  TODO: turn strict mode back on
    <App/>,
    document.getElementById('root')
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
