import { useState } from 'react';
import { useAuth } from '../AuthContext';
import { subscribeToLocation, getLivePrediction } from '../lib/api';
import { useNavigate } from 'react-router-dom';

// Type for the geocoding API results
interface GeoResult {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  country: string;
}

// Type for our new prediction result
interface PredictionResult {
  latitude: number;
  longitude: number;
  flood_percentage: number;
  name: string; // We'll add this from the search result
}

export default function LiveCheckPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<GeoResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // This holds the final prediction result
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);

  const handleSearch = async () => {
    if (!searchTerm) return;
    setIsSearching(true);
    setError(null);
    setSearchResults([]);
    setPrediction(null); // Clear old prediction
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

  const handleCurrentLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      return;
    }
    setIsLoading(true);
    setError(null);
    setPrediction(null);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        handleCheckPrediction({
          name: 'My Current Location',
          latitude,
          longitude,
        });
      },
      (err) => {
        setError(`Failed to get location: ${err.message}`);
        setIsLoading(false);
      }
    );
  };

  // --- NEW: Handle the "Check" action ---
  const handleCheckPrediction = async (location: {
    name: string;
    latitude: number;
    longitude: number;
  }) => {
    if (!user) return;
    setIsLoading(true);
    setError(null);
    setPrediction(null);
    try {
      const result = await getLivePrediction(
        location.latitude,
        location.longitude,
        user.id
      );
      setPrediction({ ...result, name: location.name });
    } catch (err) {
      setError('Failed to get live prediction.');
    }
    setIsLoading(false);
  };

  // --- NEW: Handle the "Subscribe" action ---
  const handleSubscribe = async () => {
    if (!user || !prediction) return;
    setIsLoading(true);
    setError(null);
    try {
      await subscribeToLocation(
        {
          name: prediction.name,
          lat: prediction.latitude,
          lon: prediction.longitude,
        },
        user.id
      );
      navigate('/dashboard'); // Go to dashboard after subscribing
    } catch (err) {
      setError('Failed to subscribe. You may already be subscribed.');
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-grow flex flex-col items-center p-4 bg-gray-50">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-xl border border-gray-200">
        <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">
          Live Flood Check
        </h2>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <button
          onClick={handleCurrentLocation}
          disabled={isLoading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition duration-150 ease-in-out mb-4 disabled:opacity-50"
        >
          {isLoading ? 'Checking...' : 'Check My Current Location'}
        </button>

        <div className="relative flex items-center justify-center my-4">
          <div className="flex-grow border-t border-gray-300"></div>
          <span className="flex-shrink mx-4 text-gray-500">OR</span>
          <div className="flex-grow border-t border-gray-300"></div>
        </div>

        <div className="mb-4">
          <label
            className="block text-gray-700 text-sm font-bold mb-2"
            htmlFor="city-search"
          >
            Search for a city to check
          </label>
          <div className="flex">
            <input
              id="city-search"
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="e.g., Kolkata"
              className="flex-grow shadow-sm border rounded-l-lg w-full py-3 px-4"
            />
            <button
              onClick={handleSearch}
              disabled={isSearching}
              className="bg-gray-700 hover:bg-gray-800 text-white font-bold py-3 px-4 rounded-r-lg"
            >
              {isSearching ? '...' : 'Search'}
            </button>
          </div>
        </div>

        {searchResults.length > 0 && (
          <div className="mb-4 max-h-48 overflow-y-auto border rounded-lg">
            <ul className="divide-y divide-gray-200">
              {searchResults.map((result) => (
                <li
                  key={result.id}
                  className="p-3 hover:bg-gray-100 cursor-pointer flex justify-between items-center"
                  onClick={() =>
                    handleCheckPrediction({
                      name: result.name,
                      latitude: result.latitude,
                      longitude: result.longitude,
                    })
                  }
                >
                  <span>
                    {result.name}, {result.country}
                  </span>
                  <span className="text-xs bg-blue-100 text-blue-800 font-medium px-2 py-0.5 rounded-full">
                    Check Now
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* --- NEW: Prediction Result Card --- */}
      {prediction && (
        <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-xl border border-gray-200 mt-6">
          <h3 className="text-2xl font-bold text-gray-900 mb-4 text-center">
            Live Result
          </h3>
          <div className="text-center">
            <div className="text-lg font-medium text-gray-700">
              {prediction.name}
            </div>
            <div className="text-sm text-gray-500">
              ({prediction.latitude.toFixed(4)}, {prediction.longitude.toFixed(4)})
            </div>
            
            <div className="my-4">
              <span className="text-6xl font-bold text-blue-600">
                {prediction.flood_percentage.toFixed(1)}%
              </span>
              <span className="text-xl text-gray-600"> Risk</span>
            </div>
            
            <button
              onClick={handleSubscribe}
              disabled={isLoading}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg disabled:opacity-50"
            >
              {isLoading ? 'Subscribing...' : 'Subscribe to this Location'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
