import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { Send, Plus, Users, User, Paperclip, Download, Check, CheckCheck, X, Pin, Search, MoreVertical } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Chat = () => {
  const { user } = useAuth();
  const { chatMessages, typingUsers, readReceipts, sendTyping, addLocalMessage } = useWebSocket();
  
  const [conversations, setConversations] = useState([]);
  const [selectedConv, setSelectedConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [showNewChatModal, setShowNewChatModal] = useState(false);
  const [showNewGroupModal, setShowNewGroupModal] = useState(false);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [groupName, setGroupName] = useState('');
  const [uploadingFile, setUploadingFile] = useState(false);
  
  // Search and pin state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [searching, setSearching] = useState(false);
  const [pinnedMessages, setPinnedMessages] = useState([]);
  const [showPinnedMessages, setShowPinnedMessages] = useState(false);
  const [messageMenuId, setMessageMenuId] = useState(null);
  
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const fileInputRef = useRef(null);

  // Fetch conversations
  useEffect(() => {
    fetchConversations();
    fetchAvailableUsers();
  }, []);

  // Merge WebSocket messages with local messages
  useEffect(() => {
    if (selectedConv && chatMessages[selectedConv.id]) {
      setMessages(prev => {
        const wsMessages = chatMessages[selectedConv.id];
        const existingIds = new Set(prev.map(m => m.id));
        const newMessages = wsMessages.filter(m => !existingIds.has(m.id));
        return [...prev, ...newMessages];
      });
    }
  }, [chatMessages, selectedConv]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchConversations = async () => {
    try {
      const response = await axios.get(`${API}/chat/conversations`);
      setConversations(response.data);
    } catch (error) {
      toast.error('Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableUsers = async () => {
    try {
      const response = await axios.get(`${API}/chat/users/available`);
      setAvailableUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users');
    }
  };

  const fetchMessages = async (conversationId) => {
    try {
      const response = await axios.get(`${API}/chat/conversations/${conversationId}/messages`);
      setMessages(response.data);
      
      // Mark messages as read
      const unreadIds = response.data
        .filter(m => m.sender_id !== user.id && !m.read_by.includes(user.id))
        .map(m => m.id);
      
      if (unreadIds.length > 0) {
        await axios.post(`${API}/chat/conversations/${conversationId}/read`, {
          message_ids: unreadIds
        });
      }
    } catch (error) {
      toast.error('Failed to load messages');
    }
  };

  const selectConversation = (conv) => {
    setSelectedConv(conv);
    fetchMessages(conv.id);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedConv) return;

    setSendingMessage(true);
    try {
      const response = await axios.post(
        `${API}/chat/conversations/${selectedConv.id}/messages`,
        { content: newMessage, message_type: 'text' }
      );
      
      // Add to local messages (WebSocket will also receive it)
      addLocalMessage(selectedConv.id, response.data);
      setNewMessage('');
      
      // Update conversation last message
      setConversations(prev => prev.map(c => 
        c.id === selectedConv.id 
          ? { ...c, last_message: newMessage.slice(0, 100), last_message_at: new Date().toISOString() }
          : c
      ));
    } catch (error) {
      toast.error('Failed to send message');
    } finally {
      setSendingMessage(false);
    }
  };

  const handleTyping = useCallback((e) => {
    setNewMessage(e.target.value);
    
    if (selectedConv) {
      sendTyping(selectedConv.id, true);
      
      // Clear previous timeout
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      
      // Stop typing indicator after 2 seconds of no input
      typingTimeoutRef.current = setTimeout(() => {
        sendTyping(selectedConv.id, false);
      }, 2000);
    }
  }, [selectedConv, sendTyping]);

  const createDirectMessage = async (userId) => {
    try {
      const response = await axios.post(`${API}/chat/conversations`, {
        participant_ids: [userId],
        is_group: false
      });
      
      setConversations(prev => {
        const exists = prev.find(c => c.id === response.data.id);
        if (exists) return prev;
        return [response.data, ...prev];
      });
      
      setSelectedConv(response.data);
      fetchMessages(response.data.id);
      setShowNewChatModal(false);
      toast.success('Conversation created');
    } catch (error) {
      toast.error('Failed to create conversation');
    }
  };

  const createGroupChat = async () => {
    if (!groupName.trim() || selectedUsers.length < 2) {
      toast.error('Group name and at least 2 members required');
      return;
    }

    try {
      const response = await axios.post(`${API}/chat/conversations`, {
        name: groupName,
        participant_ids: selectedUsers,
        is_group: true
      });
      
      setConversations(prev => [response.data, ...prev]);
      setSelectedConv(response.data);
      fetchMessages(response.data.id);
      setShowNewGroupModal(false);
      setGroupName('');
      setSelectedUsers([]);
      toast.success('Group created');
    } catch (error) {
      toast.error('Failed to create group');
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !selectedConv) return;

    // Validate file
    const allowedTypes = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'];
    const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowedTypes.includes(fileExt)) {
      toast.error(`File type not allowed. Allowed: ${allowedTypes.join(', ')}`);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    setUploadingFile(true);
    try {
      // Upload file
      const formData = new FormData();
      formData.append('file', file);
      
      const uploadRes = await axios.post(
        `${API}/chat/conversations/${selectedConv.id}/attachments`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      // Send message with attachment
      const msgRes = await axios.post(
        `${API}/chat/conversations/${selectedConv.id}/messages`,
        {
          content: `📎 ${file.name}`,
          message_type: 'attachment',
          attachment_id: uploadRes.data.id
        }
      );

      addLocalMessage(selectedConv.id, msgRes.data);
      toast.success('File sent');
    } catch (error) {
      toast.error('Failed to upload file');
    } finally {
      setUploadingFile(false);
      e.target.value = '';
    }
  };

  const downloadAttachment = async (attachmentId, fileName) => {
    try {
      const response = await axios.get(`${API}/chat/attachments/${attachmentId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Failed to download file');
    }
  };

  // Pin conversation
  const pinConversation = async (convId, shouldPin) => {
    try {
      await axios.post(`${API}/chat/conversations/${convId}/pin`, { pin: shouldPin });
      setConversations(prev => prev.map(c => 
        c.id === convId ? { ...c, is_pinned: shouldPin } : c
      ).sort((a, b) => {
        if (a.is_pinned && !b.is_pinned) return -1;
        if (!a.is_pinned && b.is_pinned) return 1;
        return 0;
      }));
      toast.success(shouldPin ? 'Conversation pinned' : 'Conversation unpinned');
    } catch (error) {
      toast.error('Failed to pin conversation');
    }
  };

  // Pin message
  const pinMessage = async (messageId, shouldPin) => {
    if (!selectedConv) return;
    try {
      await axios.post(`${API}/chat/conversations/${selectedConv.id}/messages/${messageId}/pin`, { pin: shouldPin });
      setMessages(prev => prev.map(m => 
        m.id === messageId ? { ...m, is_pinned: shouldPin } : m
      ));
      setMessageMenuId(null);
      toast.success(shouldPin ? 'Message pinned' : 'Message unpinned');
    } catch (error) {
      toast.error('Failed to pin message');
    }
  };

  // Fetch pinned messages
  const fetchPinnedMessages = async () => {
    if (!selectedConv) return;
    try {
      const response = await axios.get(`${API}/chat/conversations/${selectedConv.id}/pinned-messages`);
      setPinnedMessages(response.data);
      setShowPinnedMessages(true);
    } catch (error) {
      toast.error('Failed to fetch pinned messages');
    }
  };

  // Search messages
  const searchMessages = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const params = new URLSearchParams({ q: searchQuery });
      if (selectedConv) params.append('conversation_id', selectedConv.id);
      const response = await axios.get(`${API}/chat/search?${params}`);
      setSearchResults(response.data);
    } catch (error) {
      toast.error('Search failed');
    } finally {
      setSearching(false);
    }
  };

  const getConversationName = (conv) => {
    if (conv.is_group) return conv.name;
    const otherName = conv.participant_names.find((_, i) => conv.participants[i] !== user.id);
    return otherName || 'Unknown';
  };

  const getReadStatus = (message) => {
    if (message.sender_id !== user.id) return null;
    const otherReaders = message.read_by.filter(id => id !== user.id);
    if (otherReaders.length > 0) {
      return <CheckCheck size={14} className="text-blue-500" />;
    }
    return <Check size={14} className="text-slate-400" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex" data-testid="chat-page">
      {/* Conversations List */}
      <div className="w-80 bg-white border-r border-slate-200 flex flex-col">
        <div className="p-4 border-b border-slate-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-heading font-bold text-text-primary">Messages</h2>
            <div className="flex gap-2">
              <button
                onClick={() => setShowSearchModal(true)}
                className="p-2 hover:bg-slate-100 rounded-md transition-colors"
                title="Search Messages"
                data-testid="search-btn"
              >
                <Search size={20} className="text-primary" />
              </button>
              <button
                onClick={() => setShowNewChatModal(true)}
                className="p-2 hover:bg-slate-100 rounded-md transition-colors"
                title="New Chat"
                data-testid="new-chat-btn"
              >
                <User size={20} className="text-primary" />
              </button>
              <button
                onClick={() => setShowNewGroupModal(true)}
                className="p-2 hover:bg-slate-100 rounded-md transition-colors"
                title="New Group"
                data-testid="new-group-btn"
              >
                <Users size={20} className="text-primary" />
              </button>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <div className="text-center py-8 text-text-secondary">
              <p>No conversations yet</p>
              <p className="text-sm mt-2">Start a new chat!</p>
            </div>
          ) : (
            conversations.map(conv => (
              <div
                key={conv.id}
                className={`p-4 border-b border-slate-100 cursor-pointer transition-colors ${
                  selectedConv?.id === conv.id ? 'bg-primary/10' : 'hover:bg-slate-50'
                }`}
                data-testid={`conv-${conv.id}`}
              >
                <div className="flex items-center gap-3" onClick={() => selectConversation(conv)}>
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    conv.is_group ? 'bg-purple-100' : 'bg-primary/20'
                  }`}>
                    {conv.is_group ? (
                      <Users size={20} className="text-purple-600" />
                    ) : (
                      <span className="text-primary font-semibold">
                        {getConversationName(conv).charAt(0)}
                      </span>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        {conv.is_pinned && <Pin size={12} className="text-primary" />}
                        <span className="font-medium text-text-primary truncate">
                          {getConversationName(conv)}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        {conv.unread_count > 0 && (
                          <span className="bg-primary text-white text-xs rounded-full px-2 py-0.5">
                            {conv.unread_count}
                          </span>
                        )}
                        <button
                          onClick={(e) => { e.stopPropagation(); pinConversation(conv.id, !conv.is_pinned); }}
                          className={`p-1 rounded hover:bg-slate-200 ${conv.is_pinned ? 'text-primary' : 'text-slate-400'}`}
                          title={conv.is_pinned ? 'Unpin' : 'Pin'}
                        >
                          <Pin size={14} />
                        </button>
                      </div>
                    </div>
                    {conv.last_message && (
                      <p className="text-sm text-text-secondary truncate">{conv.last_message}</p>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-slate-50">
        {selectedConv ? (
          <>
            {/* Chat Header */}
            <div className="bg-white border-b border-slate-200 p-4">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  selectedConv.is_group ? 'bg-purple-100' : 'bg-primary/20'
                }`}>
                  {selectedConv.is_group ? (
                    <Users size={20} className="text-purple-600" />
                  ) : (
                    <span className="text-primary font-semibold">
                      {getConversationName(selectedConv).charAt(0)}
                    </span>
                  )}
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary">{getConversationName(selectedConv)}</h3>
                  {selectedConv.is_group && (
                    <p className="text-sm text-text-secondary">
                      {selectedConv.participants.length} members
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map(message => (
                <div
                  key={message.id}
                  className={`flex ${message.sender_id === user.id ? 'justify-end' : 'justify-start'}`}
                  data-testid={`message-${message.id}`}
                >
                  <div className={`max-w-[70%] ${
                    message.sender_id === user.id 
                      ? 'bg-primary text-white rounded-l-lg rounded-tr-lg' 
                      : 'bg-white text-text-primary rounded-r-lg rounded-tl-lg shadow-sm'
                  } p-3`}>
                    {message.sender_id !== user.id && selectedConv.is_group && (
                      <p className="text-xs font-medium mb-1 opacity-70">{message.sender_name}</p>
                    )}
                    
                    {message.message_type === 'attachment' && message.attachment_id ? (
                      <button
                        onClick={() => downloadAttachment(message.attachment_id, message.attachment_name)}
                        className={`flex items-center gap-2 ${
                          message.sender_id === user.id ? 'text-white/90 hover:text-white' : 'text-primary hover:text-primary-hover'
                        }`}
                      >
                        <Download size={16} />
                        <span className="underline">{message.attachment_name || 'Download'}</span>
                      </button>
                    ) : (
                      <p className="break-words">{message.content}</p>
                    )}
                    
                    <div className={`flex items-center justify-end gap-1 mt-1 ${
                      message.sender_id === user.id ? 'text-white/70' : 'text-text-secondary'
                    }`}>
                      <span className="text-xs">
                        {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                      {getReadStatus(message)}
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Typing Indicator */}
              {typingUsers[selectedConv.id] && (
                <div className="flex justify-start">
                  <div className="bg-white text-text-secondary rounded-lg p-3 shadow-sm">
                    <p className="text-sm italic">{typingUsers[selectedConv.id].user_name} is typing...</p>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <div className="bg-white border-t border-slate-200 p-4">
              <form onSubmit={handleSendMessage} className="flex items-center gap-3">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  className="hidden"
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadingFile}
                  className="p-2 hover:bg-slate-100 rounded-md transition-colors disabled:opacity-50"
                  title="Attach file"
                  data-testid="attach-btn"
                >
                  <Paperclip size={20} className="text-text-secondary" />
                </button>
                <input
                  type="text"
                  value={newMessage}
                  onChange={handleTyping}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-2 border border-slate-200 rounded-full focus:outline-none focus:ring-2 focus:ring-primary"
                  disabled={sendingMessage}
                  data-testid="message-input"
                />
                <button
                  type="submit"
                  disabled={sendingMessage || !newMessage.trim()}
                  className="p-2 bg-primary hover:bg-primary-hover text-white rounded-full transition-colors disabled:opacity-50"
                  data-testid="send-btn"
                >
                  <Send size={20} />
                </button>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-text-secondary">
            <div className="text-center">
              <Users size={48} className="mx-auto mb-4 opacity-50" />
              <p>Select a conversation to start chatting</p>
            </div>
          </div>
        )}
      </div>

      {/* New Chat Modal */}
      {showNewChatModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-heading font-semibold text-text-primary">New Chat</h3>
              <button onClick={() => setShowNewChatModal(false)} className="p-1 hover:bg-slate-100 rounded">
                <X size={20} />
              </button>
            </div>
            <p className="text-text-secondary mb-4">Select a user to start chatting</p>
            <div className="max-h-64 overflow-y-auto space-y-2">
              {availableUsers.map(u => (
                <button
                  key={u.id}
                  onClick={() => createDirectMessage(u.id)}
                  className="w-full flex items-center gap-3 p-3 hover:bg-slate-50 rounded-lg transition-colors text-left"
                  data-testid={`user-${u.id}`}
                >
                  <div className="w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center">
                    <span className="text-primary font-semibold">{u.full_name.charAt(0)}</span>
                  </div>
                  <div>
                    <p className="font-medium text-text-primary">{u.full_name}</p>
                    <p className="text-sm text-text-secondary">{u.email}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* New Group Modal */}
      {showNewGroupModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-heading font-semibold text-text-primary">Create Group</h3>
              <button onClick={() => { setShowNewGroupModal(false); setSelectedUsers([]); setGroupName(''); }} className="p-1 hover:bg-slate-100 rounded">
                <X size={20} />
              </button>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-text-primary mb-2">Group Name</label>
              <input
                type="text"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                placeholder="Enter group name"
                className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                data-testid="group-name-input"
              />
            </div>
            
            <p className="text-sm text-text-secondary mb-2">Select members ({selectedUsers.length} selected)</p>
            <div className="max-h-48 overflow-y-auto space-y-2 mb-4">
              {availableUsers.map(u => (
                <label
                  key={u.id}
                  className="flex items-center gap-3 p-3 hover:bg-slate-50 rounded-lg cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedUsers.includes(u.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedUsers(prev => [...prev, u.id]);
                      } else {
                        setSelectedUsers(prev => prev.filter(id => id !== u.id));
                      }
                    }}
                    className="rounded border-slate-300 text-primary focus:ring-primary"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-text-primary">{u.full_name}</p>
                    <p className="text-sm text-text-secondary">{u.role}</p>
                  </div>
                </label>
              ))}
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => { setShowNewGroupModal(false); setSelectedUsers([]); setGroupName(''); }}
                className="flex-1 px-4 py-2 border border-slate-200 text-text-primary rounded-md hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={createGroupChat}
                disabled={!groupName.trim() || selectedUsers.length < 2}
                className="flex-1 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-md disabled:opacity-50"
                data-testid="create-group-btn"
              >
                Create Group
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;
