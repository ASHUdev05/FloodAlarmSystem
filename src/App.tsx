import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DataDisplayPage from './pages/DataDisplayPage';
import CitySelectionPage from './pages/CitySelectionPage';
import ProtectedRoute from './components/ProtectedRoute';
import LiveCheckPage from './pages/LiveCheckPage'; // Import the new page

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
        {/* New Route for Live Check */}
        <Route
          path="/live-check"
          element={
            <ProtectedRoute>
              <LiveCheckPage />
            </ProtectedRoute>
          }
        />
      </Routes>
      <Footer />
    </div>
  );
}

export default App;