import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { toast } from 'sonner';

const WebSocketContext = createContext(null);

export const useWebSocket = () => useContext(WebSocketContext);

export const WebSocketProvider = ({ children }) => {
  const { user, token } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [chatMessages, setChatMessages] = useState({});
  const [typingUsers, setTypingUsers] = useState({});
  const [readReceipts, setReadReceipts] = useState({});
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const notificationCacheRef = useRef(new Set());

  // Sound notification - plays a notification tone
  const playNotificationSound = useCallback(() => {
    const soundEnabled = localStorage.getItem('notificationSoundEnabled');
    // Play sound if not explicitly disabled
    if (soundEnabled === 'false') return;

    try {
      // Create audio context (resume if suspended due to browser policy)
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();

      // Resume audio context if suspended
      if (audioContext.state === 'suspended') {
        audioContext.resume().catch(() => {});
      }

      const now = audioContext.currentTime;

      // Create first beep (high frequency)
      const osc1 = audioContext.createOscillator();
      const gain1 = audioContext.createGain();
      osc1.connect(gain1);
      gain1.connect(audioContext.destination);
      osc1.frequency.value = 1000;
      osc1.type = 'sine';
      gain1.gain.setValueAtTime(0.4, now);
      gain1.gain.exponentialRampToValueAtTime(0.01, now + 0.12);
      osc1.start(now);
      osc1.stop(now + 0.12);

      // Create second beep (different frequency)
      const osc2 = audioContext.createOscillator();
      const gain2 = audioContext.createGain();
      osc2.connect(gain2);
      gain2.connect(audioContext.destination);
      osc2.frequency.value = 800;
      osc2.type = 'sine';
      gain2.gain.setValueAtTime(0.4, now + 0.15);
      gain2.gain.exponentialRampToValueAtTime(0.01, now + 0.27);
      osc2.start(now + 0.15);
      osc2.stop(now + 0.27);
    } catch (e) {
      console.warn('Audio notification failed:', e);
    }
  }, []);

  const connect = useCallback(() => {
    if (!token || !user) return;

    const wsUrl = process.env.REACT_APP_BACKEND_URL?.replace('https://', 'wss://').replace('http://', 'ws://');
    const ws = new WebSocket(`${wsUrl}/api/ws?token=${token}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'notification':
            // Check if already in cache
            if (!notificationCacheRef.current.has(data.data.id)) {
              notificationCacheRef.current.add(data.data.id);
              setNotifications(prev => [data.data, ...prev]);
              playNotificationSound();
            }
            break;
          
          case 'chat_message':
            setChatMessages(prev => ({
              ...prev,
              [data.data.conversation_id]: [
                ...(prev[data.data.conversation_id] || []),
                data.data
              ]
            }));
            // Play sound for chat messages from others
            if (data.data.sender_id !== user?.id) {
              playNotificationSound();
              // Show toast if not on chat page
              if (!window.location.pathname.startsWith('/chat')) {
                toast(`New message from ${data.data.sender_name}`, {
                  description: data.data.content.slice(0, 60),
                  action: {
                    label: 'Open',
                    onClick: () => {
                      window.location.href = '/chat';
                    }
                  }
                });
              }
            }
            break;
          
          case 'typing':
            setTypingUsers(prev => ({
              ...prev,
              [data.data.conversation_id]: data.data.is_typing 
                ? { user_id: data.data.user_id, user_name: data.data.user_name }
                : null
            }));
            break;
          
          case 'read_receipt':
            setReadReceipts(prev => ({
              ...prev,
              [data.data.conversation_id]: {
                user_id: data.data.user_id,
                message_ids: data.data.message_ids
              }
            }));
            break;
          
          case 'message_edit':
            // Update existing message
            setChatMessages(prev => ({
              ...prev,
              [data.data.conversation_id]: prev[data.data.conversation_id]?.map(msg =>
                msg.id === data.data.id ? data.data : msg
              ) || []
            }));
            break;

          case 'message_delete':
            // Mark message as deleted
            setChatMessages(prev => ({
              ...prev,
              [data.data.conversation_id]: prev[data.data.conversation_id]?.map(msg =>
                msg.id === data.data.message_id
                  ? { ...msg, is_deleted: true, content: 'This message was deleted' }
                  : msg
              ) || []
            }));
            break;

          case 'pong':
            // Heartbeat response
            break;

          default:
            console.log('Unknown WebSocket message:', data);
        }
      } catch (e) {
        console.error('WebSocket message error:', e);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      wsRef.current = null;
      
      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, [token, user, playNotificationSound]);

  // Connect when user logs in
  useEffect(() => {
    if (token && user) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [token, user, connect]);

  // Send typing indicator
  const sendTyping = useCallback((conversationId, isTyping) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'typing',
        conversation_id: conversationId,
        is_typing: isTyping
      }));
    }
  }, []);

  // Clear notifications for a conversation
  const clearChatMessages = useCallback((conversationId) => {
    setChatMessages(prev => ({
      ...prev,
      [conversationId]: []
    }));
  }, []);

  // Add message to local state
  const addLocalMessage = useCallback((conversationId, message) => {
    setChatMessages(prev => ({
      ...prev,
      [conversationId]: [
        ...(prev[conversationId] || []),
        message
      ]
    }));
  }, []);

  const value = {
    isConnected,
    notifications,
    chatMessages,
    typingUsers,
    readReceipts,
    sendTyping,
    clearChatMessages,
    addLocalMessage,
    clearNotificationCache: () => notificationCacheRef.current.clear()
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};
