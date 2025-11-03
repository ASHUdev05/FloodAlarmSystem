import { useState } from 'react';
import { useAuth } from '../AuthContext';
import { getLivePrediction, subscribeToLocation } from '../lib/api'; // Use createSubscription
import { useNavigate } from 'react-router-dom';

// Type for the geocoding API results
interface GeoResult {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  country: string;
}

// Type for our prediction result
interface Prediction {
  name: string;
  lat: number;
  lon: number;
  percentage: number | null; // Allow null for "No Data"
}

export default function LiveCheckPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  
  // States for search
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<GeoResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // State for prediction results
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  // 1. Search for a city
  const handleSearch = async () => {
    if (!searchTerm) return;
    setIsSearching(true);
    setError(null);
    setPrediction(null); // Clear old results
    setSearchResults([]);
    try {
      const response = await fetch(
        `https://geocoding-api.open-meteo.com/v1/search?name=${searchTerm}&count=5`
      );
      const data = await response.json();
      if (data.results) {
        setSearchResults(data.results);
      } else {
        setError('No cities found for that name.');
      }
    } catch (err) {
      setError('Failed to fetch city data.');
    }
    setIsSearching(false);
  };

  // 2. Get Live Prediction
  const handleCheckNow = async (location: {
    name: string;
    lat: number;
    lon: number;
  }) => {
    if (!user) {
      setError('You must be logged in.');
      return;
    }
    setIsChecking(true);
    setError(null);
    setPrediction(null);

    try {
      // --- FIX: Catch errors from the API ---
      const result = await getLivePrediction(location.lat, location.lon, user.id);
      setPrediction({
        name: location.name,
        lat: location.lat,
        lon: location.lon,
        percentage: result.flood_percentage,
      });
    } catch (err: any) {
      // The API now sends a 503 error with a "detail" message
      if (err.message && err.message.includes('503')) {
         setError('Satellite data not available for this location. Please try again later.');
      } else {
         setError('An error occurred while checking the prediction.');
      }
      // Set percentage to null to show "Data not available"
      setPrediction({
        name: location.name,
        lat: location.lat,
        lon: location.lon,
        percentage: null, // This is the key change
      });
    }
    // --- END FIX ---

    setIsChecking(false);
    setSearchResults([]); // Clear search results
    setSearchTerm(''); // Clear search box
  };

  // 3. Subscribe to the location
  const handleSubscribe = async () => {
    if (!prediction || !user) return;

    setError(null);
    try {
      await subscribeToLocation(
        {
          name: prediction.name,
          lat: prediction.lat,
          lon: prediction.lon,
        },
        user.id
      );
      // On success, redirect to the dashboard to see the new subscription
      navigate('/dashboard');
    } catch (err: any) {
      if (err.message && err.message.includes('400')) {
        setError('You are already subscribed to this location.');
      } else {
        setError('Failed to add subscription.');
      }
    }
  };

  return (
    <div className="flex-grow flex flex-col items-center p-4 bg-gray-50">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-xl border border-gray-200">
        <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">
          Live Flood Check
        </h2>
        
        {/* --- City Search Form --- */}
        <div className="mb-4">
          <label
            className="block text-gray-700 text-sm font-bold mb-2"
            htmlFor="city-search"
          >
            Search for a location
          </label>
          <div className="flex">
            <input
              id="city-search"
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="e.g., Kolkata, India"
              className="flex-grow shadow-sm appearance-none border rounded-l-lg w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            />
            <button
              onClick={handleSearch}
              disabled={isSearching}
              className="bg-gray-700 hover:bg-gray-800 text-white font-bold py-3 px-4 rounded-r-lg disabled:opacity-50"
            >
              {isSearching ? '...' : 'Search'}
            </button>
          </div>
        </div>

        {/* --- Search Results --- */}
        {searchResults.length > 0 && (
          <div className="mb-4 max-h-48 overflow-y-auto border rounded-lg">
            <ul className="divide-y divide-gray-200">
              {searchResults.map((result) => (
                <li
                  key={result.id}
                  className="p-3 hover:bg-gray-100 cursor-pointer flex justify-between items-center"
                  onClick={() =>
                    handleCheckNow({
                      name: result.name,
                      lat: result.latitude,
                      lon: result.longitude,
                    })
                  }
                >
                  <div>
                    <span className="font-medium text-gray-800">
                      {result.name}
                    </span>
                    <span className="text-sm text-gray-500">
                      , {result.country}
                    </span>
                  </div>
                  <span className="text-xs bg-blue-100 text-blue-800 font-medium px-2 py-0.5 rounded-full">
                    Check
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* --- Prediction Result Card --- */}
      {isChecking && <div className="mt-4 text-blue-600">Checking...</div>}
      
      {prediction && !isChecking && (
        <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-xl border border-gray-200 mt-6">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">
            Result for: {prediction.name}
          </h3>
          
          {prediction.percentage !== null ? (
            // --- Data is available ---
            <div className="text-center">
              <div className="text-6xl font-bold text-blue-600 mb-2">
                {prediction.percentage}%
              </div>
              <div className="text-lg text-gray-600 mb-6">Flood Risk</div>
            </div>
          ) : (
            // --- Data is NOT available ---
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-500 mb-2">
                Data Not Available
              </div>
              <div className="text-md text-gray-500 mb-6">
                Satellite imagery is not yet processed for this location. Please try again later.
              </div>
            </div>
          )}

          <button
            onClick={handleSubscribe}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-150 ease-in-out disabled:opacity-50"
          >
            Subscribe to this location
          </button>
        </div>
      )}

      {/* --- Global Error Display --- */}
      {error && (
        <div className="max-w-md w-full bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-6">
          {error}
        </div>
      )}
    </div>
  );
}