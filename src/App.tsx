import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DataDisplayPage from './pages/DataDisplayPage';
import CitySelectionPage from './pages/CitySelectionPage'; // This is your map page
import ProtectedRoute from './components/ProtectedRoute';
// We no longer import LiveCheckPage

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
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
        {/* The /live-check route has been removed */}
      </Routes>
      <Footer />
    </div>
  );
}

export default App;