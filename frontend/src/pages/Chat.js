import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import { toast } from 'sonner';
import ConversationList from '../components/ConversationList';
import MessageList from '../components/MessageList';
import MessageInput from '../components/MessageInput';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Chat = () => {
  const { user } = useAuth();
  const { chatMessages, typingUsers, sendTyping, addLocalMessage } = useWebSocket();

  // Main state
  const [conversations, setConversations] = useState([]);
  const [selectedConv, setSelectedConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [activePanel, setActivePanel] = useState('conversations');
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);

  // UI state
  const [editingMessageId, setEditingMessageId] = useState(null);
  const [editContent, setEditContent] = useState('');
  const [replyingTo, setReplyingTo] = useState(null);
  const [messageMenuId, setMessageMenuId] = useState(null);
  const [contextMenu, setContextMenu] = useState(null);
  const [showNewChatModal, setShowNewChatModal] = useState(false);
  const [showNewGroupModal, setShowNewGroupModal] = useState(false);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [groupName, setGroupName] = useState('');
  const [editingGroupId, setEditingGroupId] = useState(null);
  const [editingGroupName, setEditingGroupName] = useState('');

  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const fileInputRef = useRef(null);

  // Fetch data
  useEffect(() => {
    fetchConversations();
    fetchAvailableUsers();
  }, []);

  // Merge WebSocket messages
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

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // API calls
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

  // Message operations
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedConv) return;

    setSendingMessage(true);
    try {
      const messageData = {
        content: newMessage,
        message_type: 'text',
        ...(replyingTo && {
          reply_to_id: replyingTo.id,
          reply_to_content: replyingTo.content,
          reply_to_sender: replyingTo.sender_name
        })
      };

      const response = await axios.post(
        `${API}/chat/conversations/${selectedConv.id}/messages`,
        messageData
      );

      addLocalMessage(selectedConv.id, response.data);
      setNewMessage('');
      clearReply();

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

  const editMessage = async (messageId, content) => {
    if (!selectedConv) return;
    try {
      const response = await axios.put(
        `${API}/chat/conversations/${selectedConv.id}/messages/${messageId}`,
        { content }
      );
      setMessages(prev => prev.map(m => m.id === messageId ? response.data : m));
      setEditingMessageId(null);
      setEditContent('');
      toast.success('Message updated');
    } catch (error) {
      toast.error('Failed to edit message');
    }
  };

  const deleteMessage = async (messageId) => {
    if (!selectedConv) return;
    try {
      await axios.delete(`${API}/chat/conversations/${selectedConv.id}/messages/${messageId}`);
      setMessages(prev => prev.map(m =>
        m.id === messageId ? { ...m, is_deleted: true, content: 'This message was deleted' } : m
      ));
      setMessageMenuId(null);
      toast.success('Message deleted');
    } catch (error) {
      toast.error('Failed to delete message');
    }
  };

  // Conversation operations
  const selectConversation = (conv) => {
    setSelectedConv(conv);
    fetchMessages(conv.id);
    setActivePanel('chat');
  };

  const deleteConversation = async (convId) => {
    try {
      await axios.delete(`${API}/chat/conversations/${convId}`);
      setConversations(prev => prev.filter(c => c.id !== convId));
      if (selectedConv?.id === convId) {
        setSelectedConv(null);
        setActivePanel('conversations');
      }
      toast.success('Conversation deleted');
    } catch (error) {
      toast.error('Failed to delete conversation');
    }
  };

  const updateGroupName = async (convId, newName) => {
    if (!newName.trim()) {
      toast.error('Group name cannot be empty');
      return;
    }

    try {
      await axios.patch(`${API}/chat/conversations/${convId}`, { name: newName });
      setConversations(prev => prev.map(c =>
        c.id === convId ? { ...c, name: newName } : c
      ));
      if (selectedConv?.id === convId) {
        setSelectedConv({ ...selectedConv, name: newName });
      }
      setEditingGroupId(null);
      toast.success('Group name updated');
    } catch (error) {
      toast.error('Failed to update group name');
    }
  };

  // UI handlers
  const selectConversation_withReset = (conv) => {
    selectConversation(conv);
    setContextMenu(null);
  };

  const handleTyping = useCallback((e) => {
    setNewMessage(e.target.value);
    if (selectedConv) {
      sendTyping(selectedConv.id, true);
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = setTimeout(() => {
        sendTyping(selectedConv.id, false);
      }, 2000);
    }
  }, [selectedConv, sendTyping]);

  const handleContextMenu = (e, conv) => {
    e.preventDefault();
    setContextMenu({
      convId: conv.id,
      x: e.clientX,
      y: e.clientY,
      close: () => setContextMenu(null)
    });
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !selectedConv) return;

    const allowedTypes = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.mp3', '.wav', '.m4a'];
    const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowedTypes.includes(fileExt)) {
      toast.error(`File type not allowed`);
      return;
    }

    setUploadingFile(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const attachmentRes = await axios.post(
        `${API}/chat/conversations/${selectedConv.id}/attachments`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      const response = await axios.post(
        `${API}/chat/conversations/${selectedConv.id}/messages`,
        {
          content: file.name,
          message_type: 'attachment',
          attachment_id: attachmentRes.data.id
        }
      );

      addLocalMessage(selectedConv.id, response.data);
      toast.success('File sent');
    } catch (error) {
      toast.error('Failed to upload file');
    } finally {
      setUploadingFile(false);
      e.target.value = '';
    }
  };

  const handleVoiceMessage = async (audioBlob) => {
    if (!selectedConv) return;
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'voice-message.webm');

      const attachmentRes = await axios.post(
        `${API}/chat/conversations/${selectedConv.id}/attachments`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      const response = await axios.post(
        `${API}/chat/conversations/${selectedConv.id}/messages`,
        {
          content: '🎤 Voice message',
          message_type: 'attachment',
          attachment_id: attachmentRes.data.id
        }
      );

      addLocalMessage(selectedConv.id, response.data);
      toast.success('Voice message sent');
    } catch (error) {
      toast.error('Failed to send voice message');
    }
  };

  const getReadStatus = (message) => {
    if (message.sender_id !== user.id) return null;
    return message.read_by.length > 1 ? '✓✓' : '✓';
  };

  // Modals
  const createDirectMessage = async (userId) => {
    try {
      const response = await axios.post(`${API}/chat/conversations`, {
        participant_ids: [userId],
        is_group: false
      });

      setConversations(prev => {
        const exists = prev.find(c => c.id === response.data.id);
        return exists ? prev : [response.data, ...prev];
      });

      selectConversation(response.data);
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
      selectConversation(response.data);
      setShowNewGroupModal(false);
      setGroupName('');
      setSelectedUsers([]);
      toast.success('Group created');
    } catch (error) {
      toast.error('Failed to create group');
    }
  };

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

  const handleDownloadAttachment = async (attachmentId, fileName) => {
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
    } catch (error) {
      toast.error('Failed to download file');
    }
  };

  // Event listeners for custom events
  useEffect(() => {
    const handleEditGroup = (e) => {
      const conv = e.detail;
      setEditingGroupId(conv.id);
      setEditingGroupName(conv.name);
    };

    const handleDeleteConv = (e) => {
      const conv = e.detail;
      if (window.confirm(`Delete chat "${conv.name || conv.participant_names[0]}"?`)) {
        deleteConversation(conv.id);
      }
    };

    window.addEventListener('editGroupName', handleEditGroup);
    window.addEventListener('deleteConversation', handleDeleteConv);

    return () => {
      window.removeEventListener('editGroupName', handleEditGroup);
      window.removeEventListener('deleteConversation', handleDeleteConv);
    };
  }, []);

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col md:flex-row">
      {/* Left Panel */}
      <div className={`${activePanel === 'chat' ? 'hidden md:flex' : 'flex'} flex-col w-full md:w-80`}>
        <ConversationList
          conversations={conversations}
          selectedConv={selectedConv}
          searchQuery={''}
          setSearchQuery={() => {}}
          setShowSearchModal={() => {}}
          setShowNewChatModal={setShowNewChatModal}
          setShowNewGroupModal={setShowNewGroupModal}
          selectConversation={selectConversation_withReset}
          pinConversation={pinConversation}
          onContextMenu={handleContextMenu}
          contextMenu={contextMenu}
        />

        {/* Edit Group Name Modal */}
        {editingGroupId && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-bold mb-4">Edit Group Name</h2>
              <input
                type="text"
                value={editingGroupName}
                onChange={(e) => setEditingGroupName(e.target.value)}
                className="w-full px-4 py-2 border border-slate-200 rounded focus:outline-none focus:ring-2 focus:ring-primary mb-4"
              />
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setEditingGroupId(null)}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded"
                >
                  Cancel
                </button>
                <button
                  onClick={() => updateGroupName(editingGroupId, editingGroupName)}
                  className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-hover"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        )}

        {/* New Chat Modal */}
        {showNewChatModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-96 overflow-y-auto">
              <h2 className="text-xl font-bold mb-4">Start New Chat</h2>
              {availableUsers.map(u => (
                <button
                  key={u.id}
                  onClick={() => createDirectMessage(u.id)}
                  className="w-full text-left p-3 hover:bg-slate-100 rounded border-b border-slate-100"
                >
                  <p className="font-medium">{u.full_name}</p>
                  <p className="text-sm text-text-secondary">{u.email}</p>
                </button>
              ))}
              <button
                onClick={() => setShowNewChatModal(false)}
                className="w-full mt-4 px-4 py-2 text-slate-600 hover:bg-slate-100 rounded"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* New Group Modal */}
        {showNewGroupModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-bold mb-4">Create Group</h2>
              <input
                type="text"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                placeholder="Group name"
                className="w-full px-4 py-2 border border-slate-200 rounded mb-4 focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <div className="max-h-40 overflow-y-auto mb-4 border border-slate-200 rounded">
                {availableUsers.map(u => (
                  <label key={u.id} className="flex items-center p-3 hover:bg-slate-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedUsers.includes(u.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedUsers([...selectedUsers, u.id]);
                        } else {
                          setSelectedUsers(selectedUsers.filter(id => id !== u.id));
                        }
                      }}
                      className="w-4 h-4 text-primary rounded focus:ring-2"
                    />
                    <div className="ml-3">
                      <p className="font-medium">{u.full_name}</p>
                      <p className="text-sm text-text-secondary">{u.email}</p>
                    </div>
                  </label>
                ))}
              </div>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowNewGroupModal(false)}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded"
                >
                  Cancel
                </button>
                <button
                  onClick={createGroupChat}
                  className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-hover"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Right Panel */}
      <div className={`${activePanel === 'conversations' ? 'hidden md:flex' : 'flex'} flex-1 flex-col`}>
        <MessageList
          messages={messages}
          user={user}
          selectedConv={selectedConv}
          editingMessageId={editingMessageId}
          editContent={editContent}
          messageMenuId={messageMenuId}
          typingUsers={typingUsers}
          messagesEndRef={messagesEndRef}
          setActivePanel={setActivePanel}
          setEditingMessageId={setEditingMessageId}
          setEditContent={setEditContent}
          setMessageMenuId={setMessageMenuId}
          onEditMessage={editMessage}
          onDeleteMessage={deleteMessage}
          onReply={(msg) => setReplyingTo({ id: msg.id, content: msg.content, sender_name: msg.sender_name })}
          onPinMessage={() => {}}
          onDownloadAttachment={handleDownloadAttachment}
          getReadStatus={getReadStatus}
        />

        {selectedConv && (
          <MessageInput
            newMessage={newMessage}
            setNewMessage={setNewMessage}
            replyingTo={replyingTo}
            clearReply={() => setReplyingTo(null)}
            onSendMessage={handleSendMessage}
            onFileUpload={handleFileUpload}
            onTyping={handleTyping}
            sendingMessage={sendingMessage}
            uploadingFile={uploadingFile}
            onVoiceMessage={handleVoiceMessage}
          />
        )}
      </div>
    </div>
  );
};

export default Chat;
