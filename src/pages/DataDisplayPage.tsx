import { useEffect, useState } from 'react';
import { useAuth } from '../AuthContext';
import {
  getMySubscriptions,
  deleteSubscription,
  type LocationSubscription,
} from '../lib/api';

const DataDisplayPage = () => {
  const { user } = useAuth();
  const [subscriptions, setSubscriptions] = useState<LocationSubscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;

    const loadSubscriptions = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getMySubscriptions(user.id);
        setSubscriptions(data);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    loadSubscriptions();
  }, [user]);

  const handleDelete = async (locationId: string) => {
    if (!user) return;

    try {
      await deleteSubscription(locationId, user.id);
      // Optimistic update: remove the subscription from state
      setSubscriptions((prev) =>
        prev.filter((sub) => sub.location_id !== locationId)
      );
    } catch (e: any) {
      setError('Failed to delete: ' + e.message);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Your Subscriptions</h1>

      {loading && <p>Loading your subscriptions...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && subscriptions.length === 0 && (
        <p>You are not subscribed to any locations yet.</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {subscriptions.map((sub) => (
          <div key={sub.location_id} className="border p-4 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold">{sub.name}</h2>
            <p className="text-sm text-gray-600">Lat: {sub.lat}</p>
            <p className="text-sm text-gray-600">Lon: {sub.lon}</p>
            <button
              onClick={() => handleDelete(sub.location_id)}
              className="mt-4 bg-red-500 text-white p-2 rounded text-sm"
            >
              Delete
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DataDisplayPage;
