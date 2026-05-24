import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { SessionProvider } from './context/SessionContext';
import { WorkspaceProvider } from './context/WorkspaceContext';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <SessionProvider>
        <WorkspaceProvider>
          <App />
        </WorkspaceProvider>
      </SessionProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
