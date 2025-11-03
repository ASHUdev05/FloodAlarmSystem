import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { supabase } from '../lib/api';

const Navbar = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };

  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">
          FloodAlarm
        </Link>
        <div className="space-x-4">
          <Link to="/">Home</Link>
          {user ? (
            <>
              <Link to="/select-city">Add Location</Link>
              <Link to="/dashboard">My Dashboard</Link>
              <button onClick={handleLogout} className="hover:text-gray-300">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/signup">Signup</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
