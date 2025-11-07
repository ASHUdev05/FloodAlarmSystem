import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DataDisplayPage from './pages/DataDisplayPage';
import CitySelectionPage from './pages/CitySelectionPage';
import ProtectedRoute from './components/ProtectedRoute';

// --- 1. ADD IMPORTS ---
import { useState, useEffect } from 'react';
import type { Session } from '@supabase/supabase-js';
import { supabase } from './supabaseClient'; // <-- Import the single client

function App() {
  // --- 2. ADD AUTH STATE ---
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    // Check for an active session on load
    const checkSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUserId(session?.user?.id ?? null);
    };
    checkSession();

    // Listen for auth changes (login/logout)
    const { data: authListener } = supabase.auth.onAuthStateChange(
      (_event, session: Session | null) => {
        setUserId(session?.user?.id ?? null);
      }
    );

    // Cleanup listener
    return () => {
      authListener.subscription.unsubscribe();
    };
  }, []);
  // --- END OF ADDED CODE ---

  return (
    <div className="min-h-screen flex flex-col">
      
      {/* --- 3. PASS userId PROP TO NAVBAR --- */}
      <Navbar userId={userId} />

      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* Protected Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DataDisplayPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/add-location"
          element={
            <ProtectedRoute>
              <CitySelectionPage />
            </ProtectedRoute>
          }
        />
      </Routes>
      <Footer />
    </div>
  );
}

export default App;