import { useState } from 'react';
import { useAuth } from '../AuthContext';
import { subscribeToLocation } from '../lib/api'; // Uses the unified function
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default Leaflet icon not showing up in React
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;


interface Position {
  lat: number;
  lng: number;
}

// Internal component to handle map click events
function MapClickHandler({ onMapClick, position }: { onMapClick: (pos: Position) => void, position: Position | null }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng); // Send the lat/lng object up
    },
  });

  // Render the marker here based on the parent's state
  return position === null ? null : (
    <Marker position={position}></Marker>
  );
}

export default function CitySelectionPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // State for the selected location
  const [position, setPosition] = useState<Position | null>(null);
  const [locationName, setLocationName] = useState("");

  const handleMapClick = (pos: Position) => {
    setPosition(pos);
    setError(null); // Clear error when user selects a new point
  };

  const handleSubscribe = async () => {
    if (!user) {
      setError('You must be logged in.');
      return;
    }
    if (!position) {
      setError('Please select a location on the map by clicking it.');
      return;
    }
    if (!locationName.trim()) {
      setError('Please give your location a name.');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      // Use the createSubscription function
      await subscribeToLocation(
        {
          name: locationName,
          lat: position.lat,
          lon: position.lng,
        },
        user.id
      );
      navigate('/dashboard'); // Redirect to dashboard on success
    } catch (err: any) {
      // Check for the specific 400 error from our API
      if (err.message && err.message.includes('400')) {
        setError('You are already subscribed to this location.');
      } else {
        setError('Failed to add subscription. Please try again.');
      }
    }
    setIsLoading(false);
  };

  return (
    <div className="flex-grow flex flex-col items-center p-4 bg-gray-50">
      <div className="max-w-4xl w-full bg-white p-8 rounded-lg shadow-xl border border-gray-200">
        <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">
          Add New Subscription
        </h2>
        <p className="text-center text-gray-600 mb-4">Click anywhere on the map to drop a pin on the location you want to monitor.</p>

        {/* --- Leaflet Map Container --- */}
        <div style={{ height: '400px', width: '100%', borderRadius: '8px', overflow: 'hidden' }} className="mb-4 shadow-lg">
          <MapContainer 
            center={[22.5726, 88.3639]} // Default center (Kolkata)
            zoom={10} 
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            <MapClickHandler onMapClick={handleMapClick} position={position} />
          </MapContainer>
        </div>

        {/* --- Form for subscribing (only appears after pin is dropped) --- */}
        {position && (
          <div className="animate-fade-in">
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="location-name">
                Location Name
              </label>
              <input
                id="location-name"
                type="text"
                value={locationName}
                onChange={(e) => setLocationName(e.target.value)}
                placeholder="e.g., 'Home', 'Office', 'Kolkata Riverside'"
                className="shadow-sm appearance-none border rounded w-full py-3 px-4 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              />
            </div>
            <p className="text-sm text-gray-500 mb-4">
              Selected Coordinates: {position.lat.toFixed(4)}, {position.lng.toFixed(4)}
            </p>
            <button
              onClick={handleSubscribe}
              disabled={isLoading}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-150 ease-in-out disabled:opacity-50"
            >
              {isLoading ? 'Subscribing...' : 'Subscribe to this Location'}
            </button>
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-6 text-center">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}