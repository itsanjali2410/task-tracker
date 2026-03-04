import React, { useRef, useState } from 'react';
import { Send, Paperclip, X, Mic } from 'lucide-react';

const MessageInput = ({
  newMessage,
  setNewMessage,
  replyingTo,
  clearReply,
  onSendMessage,
  onFileUpload,
  onTyping,
  sendingMessage,
  uploadingFile,
  onVoiceMessage
}) => {
  const fileInputRef = useRef(null);
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);

  const handleStartVoiceRecord = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      const chunks = [];

      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        await onVoiceMessage(blob);
        stream.getTracks().forEach(t => t.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Microphone access denied:', err);
    }
  };

  const handleStopVoiceRecord = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <div className="bg-white border-t border-slate-200 p-4">
      {/* Reply Preview Bar */}
      {replyingTo && (
        <div className="mb-3 p-3 bg-slate-50 border border-slate-200 rounded flex items-center justify-between">
          <div className="flex-1">
            <p className="text-xs text-text-secondary font-medium">Replying to {replyingTo.sender_name}</p>
            <p className="text-sm text-text-primary truncate">{replyingTo.content}</p>
          </div>
          <button
            type="button"
            onClick={clearReply}
            className="ml-2 p-1 hover:bg-slate-200 rounded"
          >
            <X size={16} className="text-text-secondary" />
          </button>
        </div>
      )}

      {/* Message Input Form */}
      <form onSubmit={onSendMessage} className="flex items-center gap-3">
        <input
          type="file"
          ref={fileInputRef}
          onChange={onFileUpload}
          className="hidden"
          accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.mp3,.wav,.m4a"
        />

        {/* Attach File Button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploadingFile || isRecording}
          className="p-2 hover:bg-slate-100 rounded-md transition-colors disabled:opacity-50"
          title="Attach file"
        >
          <Paperclip size={20} className="text-text-secondary" />
        </button>

        {/* Voice Message Button */}
        <button
          type="button"
          onClick={isRecording ? handleStopVoiceRecord : handleStartVoiceRecord}
          disabled={sendingMessage || uploadingFile}
          className={`p-2 rounded-md transition-colors disabled:opacity-50 ${
            isRecording ? 'bg-red-100 hover:bg-red-200' : 'hover:bg-slate-100'
          }`}
          title={isRecording ? 'Stop recording' : 'Send voice message'}
        >
          <Mic size={20} className={isRecording ? 'text-red-600 animate-pulse' : 'text-text-secondary'} />
        </button>

        {/* Message Input */}
        <input
          type="text"
          value={newMessage}
          onChange={(e) => {
            setNewMessage(e.target.value);
            onTyping();
          }}
          placeholder="Type a message..."
          className="flex-1 px-4 py-2 border border-slate-200 rounded-full focus:outline-none focus:ring-2 focus:ring-primary"
          disabled={sendingMessage || isRecording}
        />

        {/* Send Button */}
        <button
          type="submit"
          disabled={!newMessage.trim() || sendingMessage || isRecording}
          className="p-2 bg-primary text-white rounded-full hover:bg-primary-hover transition-colors disabled:opacity-50"
          title="Send message"
        >
          <Send size={20} />
        </button>
      </form>
    </div>
  );
};

export default MessageInput;
