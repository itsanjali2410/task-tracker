import React, { useState } from 'react';
import { Search, Plus, Users, User, MoreVertical, MessageCircle, MessageSquare } from 'lucide-react';

const ConversationList = ({
  conversations,
  selectedConv,
  availableUsers = [],
  searchQuery,
  setSearchQuery,
  setShowSearchModal,
  setShowNewChatModal,
  setShowNewGroupModal,
  selectConversation,
  pinConversation,
  onContextMenu,
  contextMenu,
  onStartDM
}) => {
  const [showPeople, setShowPeople] = useState(false);

  // Sort conversations by last message time (most recent first)
  const sortedConversations = [...conversations].sort((a, b) => {
    const timeA = a.last_message_at ? new Date(a.last_message_at).getTime() : 0;
    const timeB = b.last_message_at ? new Date(b.last_message_at).getTime() : 0;
    return timeB - timeA;
  });

  // Find users who don't have active conversations
  const conversationUserIds = new Set();
  conversations.forEach(conv => {
    if (!conv.is_group) {
      conv.participants.forEach(pid => {
        if (pid !== localStorage.getItem('userId')) {
          conversationUserIds.add(pid);
        }
      });
    }
  });

  const suggestedUsers = availableUsers.filter(u => !conversationUserIds.has(u.id));

  return (
    <div className="w-full md:w-80 bg-white border-r border-slate-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-heading font-bold text-text-primary">
            {showPeople ? 'People' : 'Messages'}
          </h2>
          <div className="flex gap-2">
            <button
              onClick={() => setShowSearchModal(true)}
              className="p-2 hover:bg-slate-100 rounded-md transition-colors"
              title="Search"
            >
              <Search size={20} className="text-text-secondary" />
            </button>
            <button
              onClick={() => setShowPeople(!showPeople)}
              className={`p-2 rounded-md transition-colors ${showPeople ? 'bg-primary/10 text-primary' : 'hover:bg-slate-100'}`}
              title="View people"
            >
              <Users size={20} />
            </button>
            <button
              onClick={() => setShowNewGroupModal(true)}
              className="p-2 hover:bg-slate-100 rounded-md transition-colors"
              title="New Group"
            >
              <Plus size={20} className="text-primary" />
            </button>
          </div>
        </div>
      </div>

      {/* Conversations or People List */}
      <div className="flex-1 overflow-y-auto">
        {showPeople ? (
          // People Section
          <div>
            {suggestedUsers.length === 0 ? (
              <div className="text-center py-8 text-text-secondary">
                <p className="text-sm">No more people to chat with</p>
              </div>
            ) : (
              suggestedUsers.map(user => (
                <div
                  key={user.id}
                  className="border-b border-slate-100 p-4 cursor-pointer hover:bg-slate-50 transition-colors flex items-center justify-between group"
                  onClick={() => {
                    onStartDM(user.id);
                    setShowPeople(false);
                  }}
                >
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-text-primary">{user.full_name}</h3>
                    <p className="text-sm text-text-secondary truncate">{user.email}</p>
                  </div>
                  <MessageCircle size={18} className="text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              ))
            )}

            {/* All Conversations Users */}
            {conversationUserIds.size > 0 && (
              <>
                <div className="px-4 py-2 text-xs font-semibold text-text-secondary bg-slate-50 sticky top-0">
                  RECENT CONTACTS
                </div>
                {availableUsers
                  .filter(u => conversationUserIds.has(u.id))
                  .map(user => (
                    <div
                      key={user.id}
                      className="border-b border-slate-100 p-4 cursor-pointer hover:bg-slate-50 transition-colors flex items-center justify-between group"
                      onClick={() => {
                        onStartDM(user.id);
                        setShowPeople(false);
                      }}
                    >
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-text-primary">{user.full_name}</h3>
                        <p className="text-sm text-text-secondary truncate">{user.email}</p>
                      </div>
                      <span className="text-xl">●</span>
                    </div>
                  ))}
              </>
            )}
          </div>
        ) : (
          // Conversation List (sorted by last message)
          <>
            {sortedConversations.length === 0 ? (
              <div className="text-center py-8 text-text-secondary">
                <p className="text-sm">No conversations yet</p>
                <p className="text-xs mt-2">Click a person to start chatting</p>
              </div>
            ) : (
              sortedConversations.map(conv => (
                <div
                  key={conv.id}
                  className={`border-b border-slate-100 cursor-pointer transition-colors relative group ${
                    selectedConv?.id === conv.id ? 'bg-primary/10' : 'hover:bg-slate-50'
                  }`}
                  onClick={() => selectConversation(conv)}
                  onContextMenu={(e) => onContextMenu(e, conv)}
                >
                  <div className="p-4 flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-text-primary truncate">
                        {conv.is_group ? conv.name : conv.participant_names.find((_, i) => conv.participants[i] !== localStorage.getItem('userId')) || 'Unknown'}
                      </h3>
                      <div className="flex items-center justify-between">
                        <p className="text-sm text-text-secondary truncate flex-1">{conv.last_message || 'No messages yet'}</p>
                        {conv.last_message_at && (
                          <span className="text-xs text-text-secondary ml-2 flex-shrink-0">
                            {new Date(conv.last_message_at).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                        )}
                      </div>
                    </div>
                    {conv.unread_count > 0 && (
                      <span className="ml-2 bg-primary text-white text-xs px-2 py-1 rounded-full flex-shrink-0">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>

                  {/* Context Menu Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onContextMenu(e, conv);
                    }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-200 rounded transition-opacity"
                  >
                    <MoreVertical size={16} className="text-slate-500" />
                  </button>

                  {/* Right-click Context Menu */}
                  {contextMenu?.convId === conv.id && (
                    <div
                      className="absolute right-0 top-full mt-1 bg-white shadow-lg rounded-md py-1 z-20 min-w-max"
                      style={{
                        left: contextMenu?.x,
                        top: contextMenu?.y
                      }}
                    >
                      {conv.is_group && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            window.dispatchEvent(new CustomEvent('editGroupName', { detail: conv }));
                            contextMenu.close?.();
                          }}
                          className="w-full px-4 py-2 text-sm text-left hover:bg-slate-100 flex items-center gap-2"
                        >
                          ✎ Edit Group Name
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          window.dispatchEvent(new CustomEvent('deleteConversation', { detail: conv }));
                          contextMenu.close?.();
                        }}
                        className="w-full px-4 py-2 text-sm text-left hover:bg-slate-100 flex items-center gap-2 text-red-600"
                      >
                        🗑 Delete Chat
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          pinConversation(conv.id, !conv.is_pinned);
                          contextMenu.close?.();
                        }}
                        className="w-full px-4 py-2 text-sm text-left hover:bg-slate-100"
                      >
                        {conv.is_pinned ? '📌 Unpin' : '📌 Pin'}
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ConversationList;
