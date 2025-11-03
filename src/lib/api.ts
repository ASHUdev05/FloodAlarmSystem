import { createClient } from '@supabase/supabase-js';

// --- Supabase Client ---
// We also export this so the AuthContext can use it
export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL!,
  import.meta.env.VITE_SUPABASE_ANON_KEY!
);

// --- API Client ---
// Use the correct environment variable VITE_API_URL
const apiUrl = import.meta.env.VITE_API_URL;

if (!apiUrl) {
  console.error(
    'VITE_API_URL is not set. Please check your .env file or GitHub secrets.'
  );
}

// --- Types ---
export interface Subscription {
  location_id: string;
  name: string;
  lat: number; // Use 'number' for TypeScript
  lon: number; // Use 'number' for TypeScript
}

interface SubscriptionPayload {
  name: string;
  lat: number;
  lon: number;
}

export interface PredictionResult {
  latitude: number;
  longitude: number;
  flood_percentage: number;
}

// --- API Functions ---

/**
 * Fetches the on-demand prediction for a location
 */
export const getLivePrediction = async (
  lat: number,
  lon: number,
  userId: string
): Promise<PredictionResult> => {
  const response = await fetch(
    `${apiUrl}/predict?lat=${lat}&lon=${lon}`, // Pass lat/lon as query params
    {
      headers: {
        'user-id': userId,
      },
    }
  );
  if (!response.ok) {
    throw new Error('Failed to fetch live prediction');
  }
  return response.json();
};

/**
 * Fetches all subscriptions for a user
 */
export const getSubscriptions = async (
  userId: string
): Promise<Subscription[]> => {
  const response = await fetch(`${apiUrl}/subscriptions`, {
    headers: {
      'user-id': userId,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to fetch subscriptions');
  }
  return response.json();
};

/**
 * Creates a new subscription
 */
export const createSubscription = async (
  payload: SubscriptionPayload,
  userId: string
) => {
  const response = await fetch(`${apiUrl}/subscribe`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'user-id': userId,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to create subscription');
  }
  return response.json();
};

/**
 * Deletes a subscription
 */
export const deleteSubscription = async (locationId: string, userId: string) => {
  const response = await fetch(`${apiUrl}/subscribe/${locationId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'user-id': userId,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to delete subscription');
  }
  return response.json();
};