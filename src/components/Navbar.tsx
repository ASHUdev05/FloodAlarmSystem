import React from 'react';
import { Link } from 'react-router-dom';
import NotificationBell from './NotificationBell'; // Import the bell

// --- 1. Define the props interface ---
interface NavbarProps {
  userId: string | null;
}

// 2. Accept the props
const Navbar: React.FC<NavbarProps> = ({ userId }) => {

  const handleLogout = async () => {
    // You would add your Supabase logout logic here
    // const { error } = await supabase.auth.signOut();
    // if (error) console.error("Error logging out:", error);
    // (The auth listener in App.tsx will automatically set userId to null)
    console.log("User logged out");
  };

  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        <Link to="/" className="text-2xl font-bold text-blue-600">
          🌊 FloodAlarm
        </Link>
        
        <div className="flex items-center space-x-4">
          {userId ? (
            // --- User is LOGGED IN ---
            <>
              <Link to="/dashboard" className="text-gray-600 hover:text-blue-500">
                Dashboard
              </Link>
              <Link to="/add-location" className="text-gray-600 hover:text-blue-500">
                Add Location
              </Link>
              
              {/* --- 3. ADD THE NOTIFICATION BELL --- */}
              <NotificationBell userId={userId} />
              
              <button 
                onClick={handleLogout} 
                className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded"
              >
                Logout
              </button>
            </>
          ) : (
            // --- User is LOGGED OUT ---
            <>
              <Link to="/login" className="text-gray-600 hover:text-blue-500">
                Login
              </Link>
              <Link 
                to="/signup" 
                className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded"
              >
                Sign Up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;