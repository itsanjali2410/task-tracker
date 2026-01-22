import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Bell, X, Check } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NotificationBell = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchUnreadCount();
    // Poll for new notifications every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const response = await axios.get(`${API}/notifications/unread-count`);
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  };

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/notifications?limit=20`);
      setNotifications(response.data);
    } catch (error) {
      toast.error('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (notificationId) => {
    try {
      await axios.post(`${API}/notifications/mark-read/${notificationId}`);
      setNotifications(notifications.map(n => 
        n.id === notificationId ? { ...n, is_read: true } : n
      ));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      toast.error('Failed to mark as read');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await axios.post(`${API}/notifications/mark-all-read`);
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
      toast.success('All notifications marked as read');
    } catch (error) {
      toast.error('Failed to mark all as read');
    }
  };

  const handleNotificationClick = (notification) => {
    if (!notification.is_read) {
      handleMarkAsRead(notification.id);
    }
    
    // Navigate to related task if available
    if (notification.related_task_id) {
      navigate(`/tasks/${notification.related_task_id}`);
      setIsOpen(false);
    }
  };

  const getNotificationIcon = (type) => {
    const iconClass = 'w-4 h-4';
    switch (type) {
      case 'task_assigned':
        return <Check className={iconClass} />;
      case 'task_overdue':
        return <Bell className={iconClass} />;
      case 'comment_added':
        return <span className={iconClass}>💬</span>;
      case 'file_uploaded':
        return <span className={iconClass}>📎</span>;
      case 'status_changed':
        return <span className={iconClass}>🔄</span>;
      default:
        return <Bell className={iconClass} />;
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'task_assigned':
        return 'bg-blue-100 text-blue-700';
      case 'task_overdue':
        return 'bg-red-100 text-red-700';
      case 'comment_added':
        return 'bg-green-100 text-green-700';
      case 'file_uploaded':
        return 'bg-purple-100 text-purple-700';
      case 'status_changed':
        return 'bg-yellow-100 text-yellow-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className=\"relative\" ref={dropdownRef}>
      {/* Bell Icon */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className=\"relative p-2 hover:bg-slate-100 rounded-full transition-colors\"
        data-testid=\"notification-bell\"
      >
        <Bell size={20} className=\"text-text-primary\" />
        {unreadCount > 0 && (
          <span className=\"absolute top-0 right-0 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full\">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className=\"absolute right-0 mt-2 w-96 bg-white border border-slate-200 rounded-lg shadow-lg z-50\" data-testid=\"notification-dropdown\">
          {/* Header */}
          <div className=\"flex items-center justify-between p-4 border-b border-slate-200\">
            <h3 className=\"font-heading font-semibold text-text-primary\">Notifications</h3>
            <div className=\"flex items-center gap-2\">
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  className=\"text-xs text-primary hover:text-primary-hover\"
                  data-testid=\"mark-all-read-btn\"
                >
                  Mark all read
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className=\"p-1 hover:bg-slate-100 rounded\"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Notifications List */}
          <div className=\"max-h-96 overflow-y-auto\">
            {loading ? (
              <div className=\"flex items-center justify-center py-8\">
                <div className=\"animate-spin rounded-full h-8 w-8 border-b-2 border-primary\"></div>
              </div>
            ) : notifications.length === 0 ? (
              <div className=\"text-center py-8 text-text-secondary\">
                No notifications
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification)}
                  className={`p-4 border-b border-slate-100 cursor-pointer transition-colors ${
                    !notification.is_read ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-slate-50'
                  }`}
                  data-testid={`notification-${notification.id}`}
                >
                  <div className=\"flex items-start gap-3\">
                    <div className={`p-2 rounded-full ${getTypeColor(notification.type)}`}>
                      {getNotificationIcon(notification.type)}
                    </div>
                    <div className=\"flex-1 min-w-0\">
                      <p className={`text-sm ${!notification.is_read ? 'font-medium' : ''} text-text-primary`}>
                        {notification.message}
                      </p>
                      <p className=\"text-xs text-text-secondary mt-1\">
                        {new Date(notification.created_at).toLocaleString()}
                      </p>
                    </div>
                    {!notification.is_read && (
                      <div className=\"w-2 h-2 bg-primary rounded-full flex-shrink-0 mt-1\"></div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
