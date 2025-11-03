import { useState } from 'react';
import { useAuth } from '../AuthContext';
import { subscribeToLocation, type NewLocation } from '../lib/api';

// Interface for the results from the free OpenStreetMap API
interface NominatimResult {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
}

const CitySelectionPage = () => {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<NominatimResult[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<NewLocation | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  /**
   * Fetches locations from OpenStreetMap's free Nominatim API
   */
  const handleSearch = async () => {
    if (!searchQuery) return;
    setLoading(true);
    setError(null);
    setSearchResults([]);
    setSelectedLocation(null);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery)}&format=json&limit=5`
      );
      if (!response.ok) throw new Error('Failed to fetch from Nominatim');
      const data: NominatimResult[] = await response.json();
      setSearchResults(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Asks the browser for the user's current location
   */
  const handleGetMyLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      return;
    }
    setLoading(true);
    setError(null);
    setSearchResults([]);
    setSelectedLocation(null);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        // Need to reverse-geocode to get a name
        try {
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`
          );
          if (!response.ok) throw new Error('Failed to reverse-geocode');
          const data = await response.json();
          const locationName = data.display_name || `My Location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`;

          setSelectedLocation({
            lat: latitude,
            lon: longitude,
            name: locationName,
          });
        } catch (e: any) {
          setError(e.message);
        } finally {
          setLoading(false);
        }
      },
      () => {
        setError('Unable to retrieve your location. Please grant permission.');
        setLoading(false);
      }
    );
  };

  /**
   * Sets a location from the search results as the one to be subscribed
   */
  const handleSelectResult = (result: NominatimResult) => {
    setSelectedLocation({
      lat: parseFloat(result.lat),
      lon: parseFloat(result.lon),
      name: result.display_name.split(',')[0] || 'Selected Location', // Get the simple name
    });
    setSearchResults([]);
    setSearchQuery('');
  };

  /**
   * Calls our backend API to subscribe
   */
  const handleSubscribe = async () => {
    if (!user) {
      setError('You must be logged in to subscribe.');
      return;
    }
    if (!selectedLocation) {
      setError('Please select a location first.');
      return;
    }

    setError(null);
    setStatus('Subscribing...');
    try {
      await subscribeToLocation(selectedLocation, user.id);
      setStatus(`Successfully subscribed to ${selectedLocation.name}!`);
      setSelectedLocation(null); // Clear after success
    } catch (e: any) {
      setError(e.message);
      setStatus(null);
    }
  };

  return (
    <div className="container mx-auto p-4 max-w-2xl">
      <h1 className="text-2xl font-bold mb-4">Add a New Location</h1>
      
      {/* --- Step 1: Get Location --- */}
      <div className="p-4 border rounded-lg shadow mb-6">
        <h2 className="text-lg font-semibold mb-2">1. Find Your Location</h2>
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search for a city or address..."
            className="flex-grow p-2 border rounded"
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className="bg-blue-500 text-white p-2 rounded disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
          <button
            onClick={handleGetMyLocation}
            disabled={loading}
            className="bg-gray-500 text-white p-2 rounded disabled:opacity-50"
          >
            {loading ? '...' : 'Use My Location'}
          </button>
        </div>

        {/* --- Search Results --- */}
        {searchResults.length > 0 && (
          <div className="mt-4 border-t pt-4">
            <h3 className="font-semibold">Search Results:</h3>
            <ul className="divide-y">
              {searchResults.map((result) => (
                <li
                  key={result.place_id}
                  onClick={() => handleSelectResult(result)}
                  className="p-2 hover:bg-gray-100 cursor-pointer"
                >
                  {result.display_name}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* --- Step 2: Subscribe --- */}
      {selectedLocation && (
        <div className="p-4 border rounded-lg shadow-lg bg-green-50 mb-6">
          <h2 className="text-lg font-semibold mb-2">2. Confirm and Subscribe</h2>
          <p className="font-bold">{selectedLocation.name}</p>
          <p className="text-sm text-gray-600">Lat: {selectedLocation.lat.toFixed(6)}</p>
          <p className="text-sm text-gray-600">Lon: {selectedLocation.lon.toFixed(6)}</p>
          <button
            onClick={handleSubscribe}
            className="mt-4 bg-green-500 text-white p-2 rounded"
          >
            Subscribe to {selectedLocation.name}
          </button>
        </div>
      )}

      {status && <p className="text-green-500 mt-4">{status}</p>}
      {error && <p className="text-red-500 mt-4">{error}</p>}
    </div>
  );
};

export default CitySelectionPage;

