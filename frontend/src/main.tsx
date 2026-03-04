import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { initOffice } from './services/office';
import './index.css';

// Initialize Office.js before rendering — works both inside Outlook and standalone browser
initOffice().then(() => {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
});
