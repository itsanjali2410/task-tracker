import React from 'react';
import { Search, Plus, Users, User, MoreVertical, X } from 'lucide-react';

const ConversationList = ({
  conversations,
  selectedConv,
  searchQuery,
  setSearchQuery,
  setShowSearchModal,
  setShowNewChatModal,
  setShowNewGroupModal,
  selectConversation,
  pinConversation,
  onContextMenu,
  contextMenu
}) => {
  return (
    <div className="w-full md:w-80 bg-white border-r border-slate-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-heading font-bold text-text-primary">Messages</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setShowSearchModal(true)}
              className="p-2 hover:bg-slate-100 rounded-md transition-colors"
              title="Search messages"
            >
              <Search size={20} className="text-text-secondary" />
            </button>
            <button
              onClick={() => setShowNewChatModal(true)}
              className="p-2 hover:bg-slate-100 rounded-md transition-colors"
              title="New Chat"
            >
              <User size={20} className="text-primary" />
            </button>
            <button
              onClick={() => setShowNewGroupModal(true)}
              className="p-2 hover:bg-slate-100 rounded-md transition-colors"
              title="New Group"
            >
              <Users size={20} className="text-primary" />
            </button>
          </div>
        </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="text-center py-8 text-text-secondary">
            <p className="text-sm">No conversations yet</p>
          </div>
        ) : (
          conversations.map(conv => (
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
                  <p className="text-sm text-text-secondary truncate">{conv.last_message || 'No messages yet'}</p>
                </div>
                {conv.unread_count > 0 && (
                  <span className="ml-2 bg-primary text-white text-xs px-2 py-1 rounded-full">
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
                        // Will trigger edit modal in parent
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
      </div>
    </div>
  );
};

export default ConversationList;
