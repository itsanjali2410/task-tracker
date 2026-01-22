import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';

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

  // Sound notification
  const playNotificationSound = useCallback(() => {
    const soundEnabled = localStorage.getItem('notificationSoundEnabled');
    if (soundEnabled === null || JSON.parse(soundEnabled)) {
      try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 880;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.15);
        
        setTimeout(() => {
          const osc2 = audioContext.createOscillator();
          const gain2 = audioContext.createGain();
          osc2.connect(gain2);
          gain2.connect(audioContext.destination);
          osc2.frequency.value = 1100;
          osc2.type = 'sine';
          gain2.gain.setValueAtTime(0.3, audioContext.currentTime);
          gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
          osc2.start(audioContext.currentTime);
          osc2.stop(audioContext.currentTime + 0.15);
        }, 120);
      } catch (e) {
        console.warn('Audio not supported');
      }
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
