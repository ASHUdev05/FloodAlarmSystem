import { useState, useMemo } from 'react';
import { useAuth } from '../AuthContext';
import { subscribeToLocation } from '../lib/api'; // We don't need getLivePrediction
import { useNavigate } from 'react-router-dom';

// Type for the geocoding API results
interface GeoResult {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  country: string;
}

// This will now hold our selected location
interface SelectedLocation {
  name: string;
  lat: number;
  lon: number;
}

// Helper to get the date from 2 days ago
const getNasaDate = () => {
  const date = new Date();
  date.setDate(date.getDate() - 2);
  return date.toISOString().split('T')[0];
};

export default function LiveCheckPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  // States for search
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<GeoResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // State for the selected location to show on the map
  const [selectedLocation, setSelectedLocation] = useState<SelectedLocation | null>(null);

  // 1. Search for a city (no change)
  const handleSearch = async () => {
    if (!searchTerm) return;
    setIsSearching(true);
    setError(null);
    setSelectedLocation(null); // Clear old map
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

  // 2. Handle "Check" - This is now synchronous and just sets the state
  const handleShowOnMap = (location: {
    name: string;
    lat: number;
    lon: number;
  }) => {
    if (!user) {
      setError('You must be logged in.');
      return;
    }
    setError(null);
    setSelectedLocation({
      name: location.name,
      lat: location.lat,
      lon: location.lon,
    });
    setSearchResults([]); // Clear search results
    setSearchTerm(''); // Clear search box
  };

  // 3. Subscribe to the location (no change)
  const handleSubscribe = async () => {
    if (!selectedLocation || !user) return;

    setError(null);
    try {
      await subscribeToLocation(
        {
          name: selectedLocation.name,
          lat: selectedLocation.lat,
          lon: selectedLocation.lon,
        },
        user.id
      );
      // On success, redirect to the dashboard
      navigate('/dashboard');
    } catch (err: any) {
      if (err.message && err.message.includes('400')) {
        setError('You are already subscribed to this location.');
      } else {
        setError('Failed to add subscription.');
      }
    }
  };

  // 4. Memoize the map URL
  const mapUrl = useMemo(() => {
    if (!selectedLocation) return '';
    const date = getNasaDate();
    const lon = selectedLocation.lon;
    const lat = selectedLocation.lat;
    
    // This is the URL for the embedded NASA Worldview map
    return `https://worldview.earthdata.nasa.gov/?v=${lon},${lat}&l=MODIS_Terra_CorrectedReflectance_TrueColor&t=${date}&z=8`;
  }, [selectedLocation]);

  return (
    <div className="flex-grow flex flex-col items-center p-4 bg-gray-50">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-xl border border-gray-200">
        <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">
          Live Satellite Map
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
              placeholder="e.g., Patna, India"
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
                    handleShowOnMap({
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
                    Show on Map
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* --- Live Map Card --- */}
      {selectedLocation && (
        <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-xl border border-gray-200 mt-6">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">
            Live Map: {selectedLocation.name}
          </h3>
          
          {/* --- THIS IS THE FIX --- */}
          {/* We replace the <iframe> with a styled <a> tag that acts as a button */}
          <a
            href={mapUrl}
            target="_blank" // This opens it in a new tab
            rel="noopener noreferrer" // Good practice for security
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-150 ease-in-out text-center block"
          >
            View Live Map
          </a>
          {/* --- END FIX --- */}
          
          <p className="text-sm text-gray-500 my-4">
            Use the map to visually check for flooding. Data is from MODIS (Terra) satellite, approx. 2 days ago.
          </p>

          <button
            onClick={handleSubscribe}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-150 ease-in-out"
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

