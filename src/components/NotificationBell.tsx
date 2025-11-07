import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL;

// 1. Define the shape of a single notification
// This matches the Pydantic model in your Python API
interface Notification {
  id: string;
  created_at: string; // JSON converts datetimes to strings
  location_id: string;
  location_name: string;
  flood_percentage: number;
  is_read: boolean;
}

// 2. Define the props this component accepts
interface NotificationBellProps {
  // The user's ID from Supabase auth.
  // It's 'null' if the user is not logged in.
  userId: string | null;
}

// --- The Component ---

const NotificationBell: React.FC<NotificationBellProps> = ({ userId }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // --- 1. Function to Fetch Notifications ---
  const fetchNotifications = async () => {
    // Don't try to fetch if the user isn't logged in
    if (!userId) {
      setNotifications([]); // Clear any old notifications
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/notifications`, {
        method: 'GET',
        headers: {
          'User-ID': userId, // Send the required auth header
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch notifications');
      }
      
      const data = await response.json();
      setNotifications(data as Notification[]); // Cast data to our type

    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // --- 2. Function to Mark Notifications as Read ---
  const markAsRead = async () => {
    if (!userId) return;

    try {
      await fetch(`${API_BASE_URL}/notifications/read`, {
        method: 'POST',
        headers: {
          'User-ID': userId,
        },
      });

      // Optimistic update: Mark all as read in the UI instantly
      setNotifications(
        notifications.map(n => ({ ...n, is_read: true }))
      );

    } catch (err) {
      console.error('Failed to mark as read:', err);
    }
  };

  // --- 3. Fetch data when the component loads or user changes ---
  useEffect(() => {
    fetchNotifications();
  }, [userId]); // Re-run if the user logs in or out

  // --- 4. Helper to get unread count ---
  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="notification-container">
      
      {/* --- The Bell Icon --- */}
      <div className="bell-icon" onClick={() => setIsOpen(!isOpen)}>
        🔔
        {unreadCount > 0 && (
          <span className="unread-badge">{unreadCount}</span>
        )}
      </div>

      {/* --- The Notification Panel --- */}
      {isOpen && (
        <div className="notification-panel">
          <div className="panel-header">
            <h3>Notifications</h3>
            {unreadCount > 0 && (
              <button onClick={markAsRead}>Mark all as read</button>
            )}
          </div>

          {isLoading && <p className="loading-text">Loading...</p>}
          {error && <p className="error-text">{error}</p>}
          
          <div className="notification-list">
            {!isLoading && notifications.length === 0 && (
              <p className="empty-text">No notifications yet.</p>
            )}

            {notifications.map(notif => (
              <div 
                key={notif.id} 
                className={`notification-item ${notif.is_read ? 'read' : 'unread'}`}
              >
                <strong>🚨 {notif.location_name}</strong>
                <p>
                  High flood risk detected: {notif.flood_percentage.toFixed(2)}%
                </p>
                <small>
                  {new Date(notif.created_at).toLocaleString()}
                </small>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default NotificationBell;