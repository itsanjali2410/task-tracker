import React from 'react';
import { Check, CheckCheck, MoreVertical, Download, ArrowLeft, Pin, X } from 'lucide-react';

const MessageList = ({
  messages,
  user,
  selectedConv,
  editingMessageId,
  editContent,
  messageMenuId,
  typingUsers,
  messagesEndRef,
  setActivePanel,
  setEditingMessageId,
  setEditContent,
  setMessageMenuId,
  onEditMessage,
  onDeleteMessage,
  onReply,
  onPinMessage,
  onDownloadAttachment,
  getReadStatus
}) => {
  return (
    <div className="flex-1 flex flex-col bg-slate-50">
      {selectedConv ? (
        <>
          {/* Chat Header */}
          <div className="bg-white border-b border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setActivePanel('conversations')}
                  className="md:hidden p-2 hover:bg-slate-100 rounded-md transition-colors"
                  title="Back to conversations"
                >
                  <ArrowLeft size={20} className="text-primary" />
                </button>
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  selectedConv.is_group ? 'bg-purple-100' : 'bg-primary/20'
                }`}>
                  {selectedConv.is_group ? (
                    <span className="text-purple-600 font-bold">👥</span>
                  ) : (
                    <span className="text-primary font-semibold">
                      {(selectedConv.participant_names[0] || 'U').charAt(0)}
                    </span>
                  )}
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary">{selectedConv.name || selectedConv.participant_names[0]}</h3>
                  {selectedConv.is_group && (
                    <p className="text-sm text-text-secondary">
                      {selectedConv.participants.length} members
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map(message => (
              <div
                key={message.id}
                className={`flex ${message.sender_id === user.id ? 'justify-end' : 'justify-start'} group`}
              >
                <div className="relative">
                  {/* Message Menu Button */}
                  <button
                    onClick={() => setMessageMenuId(messageMenuId === message.id ? null : message.id)}
                    className={`absolute -top-1 ${message.sender_id === user.id ? '-left-6' : '-right-6'} opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-200 rounded transition-opacity`}
                  >
                    <MoreVertical size={14} className="text-slate-500" />
                  </button>

                  {/* Message Menu */}
                  {messageMenuId === message.id && (
                    <div className={`absolute top-6 ${message.sender_id === user.id ? '-left-20' : '-right-20'} bg-white shadow-lg rounded-md py-1 z-10 min-w-max`}>
                      {message.sender_id === user.id && !message.is_deleted && (
                        <>
                          <button
                            onClick={() => {
                              setEditingMessageId(message.id);
                              setEditContent(message.content);
                              setMessageMenuId(null);
                            }}
                            className="w-full px-4 py-2 text-sm text-left hover:bg-slate-100 flex items-center gap-2"
                          >
                            ✎ Edit
                          </button>
                          <button
                            onClick={() => onDeleteMessage(message.id)}
                            className="w-full px-4 py-2 text-sm text-left hover:bg-slate-100 flex items-center gap-2 text-red-600"
                          >
                            ✕ Delete
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => onReply(message)}
                        className="w-full px-4 py-2 text-sm text-left hover:bg-slate-100 flex items-center gap-2"
                      >
                        ↩ Reply
                      </button>
                    </div>
                  )}

                  {/* Message Bubble */}
                  <div className={`max-w-[70%] ${
                    message.sender_id === user.id
                      ? 'bg-primary text-white rounded-l-lg rounded-tr-lg'
                      : 'bg-white text-text-primary rounded-r-lg rounded-tl-lg shadow-sm'
                  } p-3`}>
                    {/* Reply preview */}
                    {message.reply_to_id && (
                      <div className={`border-l-2 pl-2 mb-2 text-xs ${
                        message.sender_id === user.id ? 'border-white/50 opacity-80' : 'border-primary/30 opacity-75'
                      }`}>
                        <p className="font-semibold">{message.reply_to_sender}</p>
                        <p className="truncate">{message.reply_to_content}</p>
                      </div>
                    )}

                    {message.sender_id !== user.id && selectedConv.is_group && (
                      <p className="text-xs font-medium mb-1 opacity-70">{message.sender_name}</p>
                    )}

                    {editingMessageId === message.id && message.sender_id === user.id ? (
                      <div className="flex flex-col gap-2">
                        <textarea
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          className="px-3 py-2 border border-slate-300 rounded text-text-primary resize-none"
                          rows="2"
                        />
                        <div className="flex gap-2 justify-end">
                          <button
                            onClick={() => {
                              setEditingMessageId(null);
                              setEditContent('');
                            }}
                            className="px-2 py-1 text-xs bg-slate-200 text-text-primary rounded hover:bg-slate-300"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={() => onEditMessage(message.id, editContent)}
                            className={`px-2 py-1 text-xs rounded ${message.sender_id === user.id ? 'bg-white text-primary hover:bg-slate-100' : 'bg-primary text-white hover:bg-primary-hover'}`}
                          >
                            Save
                          </button>
                        </div>
                      </div>
                    ) : message.is_deleted ? (
                      <p className="italic opacity-60">(Message deleted)</p>
                    ) : message.message_type === 'attachment' && message.attachment_id ? (
                      <button
                        onClick={() => onDownloadAttachment(message.attachment_id, message.attachment_name)}
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
                        {message.is_edited && ' · edited'}
                      </span>
                      {getReadStatus(message)}
                    </div>
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
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center text-text-secondary">
          <p>Select a conversation to start chatting</p>
        </div>
      )}
    </div>
  );
};

export default MessageList;
