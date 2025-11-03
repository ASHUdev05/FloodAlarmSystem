import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import CitySelectionPage from './pages/CitySelectionPage';
import DataDisplayPage from './pages/DataDisplayPage';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Navbar is rendered ONCE here, outside the router */}
      <Navbar />
      <main className="flex-grow">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          
          {/* Protected Routes */}
          <Route
            path="/select-city"
            element={
              <ProtectedRoute>
                <CitySelectionPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DataDisplayPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
      {/* Footer is rendered ONCE here */}
      <Footer />
    </div>
  );
}

export default App;

