import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { AuthProvider } from './AuthContext.tsx';
import { HashRouter } from 'react-router-dom'; // <-- 1. IMPORT HashRouter

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <HashRouter> {/* <-- 2. USE HashRouter */}
        <App />
      </HashRouter> {/* <-- 3. USE HashRouter */}
    </AuthProvider>
  </React.StrictMode>
);

