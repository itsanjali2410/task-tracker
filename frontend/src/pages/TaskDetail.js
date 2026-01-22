import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Calendar, User, MessageSquare, Send, Paperclip, Upload, Download, Trash2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TaskDetail = () => {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [task, setTask] = useState(null);
  const [comments, setComments] = useState([]);
  const [attachments, setAttachments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [submittingComment, setSubmittingComment] = useState(false);
  const [activeTab, setActiveTab] = useState('comments'); // 'comments' or 'attachments'
  const [uploadingFile, setUploadingFile] = useState(false);

  useEffect(() => {
    fetchTaskData();
  }, [taskId]);

  const fetchTaskData = async () => {
    try {
      const [taskRes, commentsRes, attachmentsRes] = await Promise.all([
        axios.get(`${API}/tasks/${taskId}`),
        axios.get(`${API}/comments/task/${taskId}`),
        axios.get(`${API}/attachments/task/${taskId}`)
      ]);
      setTask(taskRes.data);
      setComments(commentsRes.data);
      setAttachments(attachmentsRes.data);
    } catch (error) {
      toast.error('Failed to fetch task details');
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await axios.patch(`${API}/tasks/${taskId}`, { status: newStatus });
      toast.success('Task status updated');
      setTask({ ...task, status: newStatus });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update task');
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setSubmittingComment(true);
    try {
      const response = await axios.post(`${API}/comments`, {
        task_id: taskId,
        content: newComment
      });
      setComments([...comments, response.data]);
      setNewComment('');
      toast.success('Comment added');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add comment');
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    // Validate file type
    const allowedTypes = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'];
    const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowedTypes.includes(fileExt)) {
      toast.error(`File type not allowed. Allowed types: ${allowedTypes.join(', ')}`);
      return;
    }

    setUploadingFile(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/attachments?task_id=${taskId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setAttachments([response.data, ...attachments]);
      toast.success('File uploaded successfully');
      e.target.value = ''; // Reset input
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploadingFile(false);
    }
  };

  const handleDownloadFile = async (attachmentId, fileName) => {
    try {
      const response = await axios.get(`${API}/attachments/${attachmentId}/download`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('File downloaded');
    } catch (error) {
      toast.error('Failed to download file');
    }
  };

  const handleDeleteAttachment = async (attachmentId) => {
    if (!window.confirm('Are you sure you want to delete this attachment?')) return;

    try {
      await axios.delete(`${API}/attachments/${attachmentId}`);
      setAttachments(attachments.filter(a => a.id !== attachmentId));
      toast.success('Attachment deleted');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete attachment');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      todo: 'bg-slate-100 text-slate-800 border-slate-200',
      in_progress: 'bg-blue-50 text-blue-700 border-blue-200',
      completed: 'bg-green-50 text-green-700 border-green-200',
      cancelled: 'bg-red-50 text-red-700 border-red-200'
    };
    return styles[status] || styles.todo;
  };

  const getPriorityBadge = (priority) => {
    const styles = {
      low: 'bg-green-100 text-green-700 border-green-200',
      medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      high: 'bg-red-100 text-red-700 border-red-200'
    };
    return styles[priority] || styles.medium;
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!task) return null;

  const canUpdateStatus = user?.role === 'team_member' && task.assigned_to === user.id;

  return (
    <div className="space-y-6" data-testid="task-detail">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-slate-100 rounded-md transition-colors"
          data-testid="back-btn"
        >
          <ArrowLeft size={20} className="text-text-primary" />
        </button>
        <h2 className="text-3xl font-heading font-bold text-text-primary">Task Details</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Task Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Main Info Card */}
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-2xl font-heading font-semibold text-text-primary mb-2">{task.title}</h3>
                <div className="flex items-center gap-3">
                  <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold border ${getPriorityBadge(task.priority)}`}>
                    {task.priority} priority
                  </span>
                  <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold border ${getStatusBadge(task.status)}`}>
                    {task.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Description</label>
                <p className="text-text-primary">{task.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Assigned To</label>
                  <div className="flex items-center gap-2">
                    <User size={16} className="text-text-secondary" />
                    <span className="text-text-primary">{task.assigned_to_name}</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Created By</label>
                  <div className="flex items-center gap-2">
                    <User size={16} className="text-text-secondary" />
                    <span className="text-text-primary">{task.created_by_name}</span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Due Date</label>
                <div className="flex items-center gap-2">
                  <Calendar size={16} className="text-text-secondary" />
                  <span className="text-text-primary">{new Date(task.due_date).toLocaleDateString()}</span>
                </div>
              </div>

              {canUpdateStatus && (
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Update Status</label>
                  <select
                    value={task.status}
                    onChange={(e) => handleStatusChange(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    data-testid="status-select"
                  >
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                  </select>
                </div>
              )}
            </div>
          </div>

          {/* Tabs for Comments and Attachments */}
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm">
            {/* Tab Headers */}
            <div className="flex border-b border-slate-200">
              <button
                onClick={() => setActiveTab('comments')}
                className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors ${
                  activeTab === 'comments'
                    ? 'text-primary border-b-2 border-primary'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
                data-testid="comments-tab"
              >
                <MessageSquare size={20} />
                Comments ({comments.length})
              </button>
              <button
                onClick={() => setActiveTab('attachments')}
                className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors ${
                  activeTab === 'attachments'
                    ? 'text-primary border-b-2 border-primary'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
                data-testid="attachments-tab"
              >
                <Paperclip size={20} />
                Attachments ({attachments.length})
              </button>
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {activeTab === 'comments' ? (
                <>
                  {/* Comment Form */}
                  <form onSubmit={handleAddComment} className="mb-6">
                    <div className="flex gap-3">
                      <input
                        type="text"
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder="Add a comment..."
                        className="flex-1 px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                        disabled={submittingComment}
                        data-testid="comment-input"
                      />
                      <button
                        type="submit"
                        disabled={submittingComment || !newComment.trim()}
                        className="px-6 py-2 bg-primary hover:bg-primary-hover text-white rounded-md font-medium flex items-center gap-2 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                        data-testid="submit-comment-btn"
                      >
                        <Send size={16} />
                        Post
                      </button>
                    </div>
                  </form>

                  {/* Comments List */}
                  <div className="space-y-4">
                    {comments.length === 0 ? (
                      <p className="text-center text-text-secondary py-8">No comments yet. Be the first to comment!</p>
                    ) : (
                      comments.map((comment) => (
                        <div
                          key={comment.id}
                          className="border-l-2 border-primary pl-4 py-2"
                          data-testid={`comment-${comment.id}`}
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-text-primary">{comment.user_name}</span>
                            <span className="text-xs text-text-secondary">
                              {new Date(comment.created_at).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-text-primary">{comment.content}</p>
                        </div>
                      ))
                    )}
                  </div>
                </>
              ) : (
                <>
                  {/* File Upload */}
                  <div className="mb-6">
                    <label
                      htmlFor="file-upload"
                      className="flex items-center justify-center gap-2 px-6 py-3 bg-primary hover:bg-primary-hover text-white rounded-md font-medium cursor-pointer transition-all active:scale-95"
                    >
                      <Upload size={20} />
                      {uploadingFile ? 'Uploading...' : 'Upload File'}
                    </label>
                    <input
                      id="file-upload"
                      type="file"
                      onChange={handleFileUpload}
                      disabled={uploadingFile}
                      className="hidden"
                      accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                      data-testid="file-upload-input"
                    />
                    <p className="text-xs text-text-secondary mt-2">
                      Allowed: PDF, JPG, PNG, DOC, DOCX (Max 10MB)
                    </p>
                  </div>

                  {/* Attachments List */}
                  <div className="space-y-3">
                    {attachments.length === 0 ? (
                      <p className="text-center text-text-secondary py-8">No attachments yet</p>
                    ) : (
                      attachments.map((attachment) => (
                        <div
                          key={attachment.id}
                          className="flex items-center justify-between p-4 border border-slate-200 rounded-lg hover:border-primary/30 transition-colors"
                          data-testid={`attachment-${attachment.id}`}
                        >
                          <div className="flex items-center gap-3 flex-1">
                            <Paperclip size={20} className="text-text-secondary" />
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-text-primary truncate">{attachment.file_name}</p>
                              <div className="flex items-center gap-3 text-xs text-text-secondary">
                                <span>{formatFileSize(attachment.file_size)}</span>
                                <span>•</span>
                                <span>{attachment.uploaded_by_name}</span>
                                <span>•</span>
                                <span>{new Date(attachment.uploaded_at).toLocaleDateString()}</span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleDownloadFile(attachment.id, attachment.file_name)}
                              className="p-2 hover:bg-slate-100 rounded-md transition-colors"
                              data-testid={`download-btn-${attachment.id}`}
                              title="Download"
                            >
                              <Download size={18} className="text-primary" />
                            </button>
                            {(user?.id === attachment.uploaded_by || user?.role === 'admin') && (
                              <button
                                onClick={() => handleDeleteAttachment(attachment.id)}
                                className="p-2 hover:bg-red-50 rounded-md transition-colors"
                                data-testid={`delete-btn-${attachment.id}`}
                                title="Delete"
                              >
                                <Trash2 size={18} className="text-red-600" />
                              </button>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-4">
            <h5 className="font-heading font-semibold text-text-primary mb-3">Task Information</h5>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-text-secondary">Created:</span>
                <p className="text-text-primary font-medium">{new Date(task.created_at).toLocaleString()}</p>
              </div>
              <div>
                <span className="text-text-secondary">Last Updated:</span>
                <p className="text-text-primary font-medium">{new Date(task.updated_at).toLocaleString()}</p>
              </div>
              <div>
                <span className="text-text-secondary">Task ID:</span>
                <p className="text-text-primary font-mono text-xs">{task.id}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskDetail;