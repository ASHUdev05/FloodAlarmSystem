import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL;

// --- TypeScript Types ---
interface Notification {
  id: string;
  created_at: string;
  location_id: string;
  location_name: string;
  flood_percentage: number;
  is_read: boolean;
}

interface NotificationBellProps {
  userId: string | null;
}

const NotificationBell: React.FC<NotificationBellProps> = ({ userId }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNotifications = async () => {
    if (!userId) {
      setNotifications([]);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/notifications`, {
        method: 'GET',
        headers: { 'User-ID': userId },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch notifications');
      }
      
      const data = await response.json();
      setNotifications(data as Notification[]);

    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const markAsRead = async () => {
    if (!userId) return;
    try {
      await fetch(`${API_BASE_URL}/notifications/read`, {
        method: 'POST',
        headers: { 'User-ID': userId },
      });
      setNotifications(
        notifications.map(n => ({ ...n, is_read: true }))
      );
    } catch (err) {
      console.error('Failed to mark as read:', err);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [userId]);

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="notification-container">
      <div className="bell-icon" onClick={() => setIsOpen(!isOpen)}>
        🔔
        {unreadCount > 0 && (
          <span className="unread-badge">{unreadCount}</span>
        )}
      </div>

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