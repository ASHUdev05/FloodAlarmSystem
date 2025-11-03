import { createClient } from '@supabase/supabase-js';

// --- 1. IMPORT ENV VARIABLES ---
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const apiUrl = import.meta.env.VITE_API_URL;

if (!supabaseUrl || !supabaseAnonKey || !apiUrl) {
  console.error(
    'VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, or VITE_API_URL is not set. Please check your environment variables.'
  );
}

// --- 2. INITIALIZE & EXPORT SUPABASE ---
export const supabase = createClient(supabaseUrl!, supabaseAnonKey!);

// --- 3. DEFINE API INTERFACES ---

// For existing subscriptions
export interface LocationSubscription {
  location_id: string;
  name: string;
  lat: number;
  lon: number;
}

// For creating a new subscription
export interface NewLocation {
  lat: number;
  lon: number;
  name: string;
}

// For the new "Live Check" feature
export interface PredictionResult {
  latitude: number;
  longitude: number;
  flood_percentage: number;
}

// --- 4. API FUNCTIONS FOR OUR MIDDLEWARE ---

/**
 * OLD: Fetches all subscriptions for a given user
 */
export const getMySubscriptions = async (
  userId: string
): Promise<LocationSubscription[]> => {
  const response = await fetch(`${apiUrl}/subscriptions`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'user-id': userId,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to fetch subscriptions');
  }
  return response.json();
};

/**
 * OLD: Subscribes a user to a new location
 */
export const subscribeToLocation = async (
  location: NewLocation,
  userId: string
) => {
  const response = await fetch(`${apiUrl}/subscribe`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'user-id': userId,
    },
    body: JSON.stringify(location),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to subscribe');
  }
  return response.json();
};

/**
 * OLD: Deletes a subscription
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

