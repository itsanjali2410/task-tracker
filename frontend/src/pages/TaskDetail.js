import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Calendar, User, MessageSquare, Send, Paperclip, Upload, Download, Trash2, RefreshCw, X, History, ChevronLeft, ChevronRight, Info } from 'lucide-react';
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
  const [showReassignPrompt, setShowReassignPrompt] = useState(false);
  const [showCommentsModal, setShowCommentsModal] = useState(false);
  const [replyingTo, setReplyingTo] = useState(null);
  const [quotedText, setQuotedText] = useState('');
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loadingAudit, setLoadingAudit] = useState(false);
  const [commentAttachments, setCommentAttachments] = useState([]);
  const [uploadingCommentFile, setUploadingCommentFile] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    fetchUsers();
    fetchTaskData();
  }, [taskId]);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users/assignable`);
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users');
    }
  };

  const fetchTaskData = async () => {
    try {
      const [taskRes, commentsRes, attachmentsRes, auditRes] = await Promise.all([
        axios.get(`${API}/tasks/${taskId}`),
        axios.get(`${API}/comments/task/${taskId}`),
        axios.get(`${API}/attachments/task/${taskId}`),
        fetchAuditLogs()
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

  const fetchAuditLogs = async () => {
    try {
      setLoadingAudit(true);
      const response = await axios.get(`${API}/audit-logs/task/${taskId}`);
      setAuditLogs(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch audit logs');
      return [];
    } finally {
      setLoadingAudit(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await axios.patch(`${API}/tasks/${taskId}`, { status: newStatus });
      toast.success('Task status updated');
      setTask({ ...task, status: newStatus });
      // Show reassign prompt after status update if user can reassign
      if ((user?.role === 'admin' || user?.role === 'owner') && task?.created_by !== task?.assigned_to) {
        setShowReassignPrompt(true);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update task');
    }
  };

  const handleReassign = async () => {
    try {
      await axios.patch(`${API}/tasks/${taskId}`, { assigned_to: task.created_by });
      toast.success(`Task reassigned to ${task.created_by_name}`);
      setShowReassignPrompt(false);
      fetchTaskData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reassign task');
    }
  };

  const handleOwnedByChange = async (newOwnedBy) => {
    try {
      await axios.patch(`${API}/tasks/${taskId}`, { owned_by: newOwnedBy });
      toast.success('Task owner updated');
      setTask({ ...task, owned_by: newOwnedBy, owned_by_name: users.find(u => u.id === newOwnedBy)?.full_name });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update task owner');
    }
  };

  const handleDueDateChange = async (newDate) => {
    try {
      await axios.patch(`${API}/tasks/${taskId}`, { due_date: newDate });
      toast.success('Due date updated');
      setTask({ ...task, due_date: newDate });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update due date');
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim() && commentAttachments.length === 0) return;

    setSubmittingComment(true);
    try {
      let content = newComment;
      if (replyingTo) {
        content = `> **Re: ${replyingTo.user_name}**\n> ${replyingTo.content}\n\n${newComment}`;
      }

      // Append attachment references to comment content if there are attachments
      if (commentAttachments.length > 0) {
        const attachmentRefs = commentAttachments.map(att => `📎 ${att.file_name}`).join('\n');
        content += `\n\n${attachmentRefs}`;
      }

      const response = await axios.post(`${API}/comments`, {
        task_id: taskId,
        content: content
      });
      setComments([...comments, response.data]);
      setNewComment('');
      setReplyingTo(null);
      setQuotedText('');
      setCommentAttachments([]);
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

  const handleCommentFileUpload = async (e) => {
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

    setUploadingCommentFile(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/attachments?task_id=${taskId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Add to comment attachments
      setCommentAttachments([...commentAttachments, response.data]);
      toast.success('File attached to comment');
      e.target.value = ''; // Reset input
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to attach file');
    } finally {
      setUploadingCommentFile(false);
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
      open: 'bg-slate-100 text-slate-800 border-slate-200',
      closed: 'bg-red-50 text-red-700 border-red-200',
      completed: 'bg-green-50 text-green-700 border-green-200'
    };
    return styles[status] || styles.open;
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

  const canEditTask = user?.role === 'admin' || user?.role === 'owner' || task?.created_by === user?.id;
  const canUpdateStatus = canEditTask;
  const canReassign = user?.role === 'admin' || user?.role === 'owner';

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

      <div className={`grid grid-cols-1 gap-6 ${sidebarCollapsed ? 'lg:grid-cols-1' : 'lg:grid-cols-3'}`}>
        {/* Task Details */}
        <div className={`space-y-6 ${sidebarCollapsed ? 'lg:col-span-1' : 'lg:col-span-2'}`}>
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
                <div className="text-text-primary whitespace-pre-wrap break-words bg-slate-50 p-3 rounded border border-slate-200">{task.description}</div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Assigned To</label>
                  <div className="flex items-center gap-2">
                    <User size={16} className="text-text-secondary" />
                    <span className="text-text-primary">{task.assigned_to_name}</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-1">Owned By</label>
                  <select
                    value={task.owned_by || ''}
                    onChange={(e) => handleOwnedByChange(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    data-testid="owned-by-select"
                  >
                    <option value="">Unassigned</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.full_name}
                      </option>
                    ))}
                  </select>
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
                <input
                  type="date"
                  value={task.due_date}
                  onChange={(e) => handleDueDateChange(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  data-testid="due-date-input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Assigned Date</label>
                <div className="flex items-center gap-2">
                  <Calendar size={16} className="text-text-secondary" />
                  <span className="text-text-primary">{task.assigned_date ? new Date(task.assigned_date).toLocaleDateString() : new Date(task.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">Status</label>
                <select
                  value={task.status}
                  onChange={(e) => handleStatusChange(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  data-testid="status-select"
                >
                  <option value="open">Open</option>
                  <option value="closed">Closed</option>
                  <option value="completed">Completed</option>
                </select>
              </div>

              {canReassign && (
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Reassign Task</label>
                  <button
                    onClick={handleReassign}
                    className="w-full px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-md flex items-center justify-center gap-2 transition-colors"
                    data-testid="reassign-btn"
                  >
                    <RefreshCw size={16} />
                    Reassign to {task.created_by_name}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Comments Button and History */}
          <div className="flex gap-4">
            <button
              onClick={() => setShowCommentsModal(true)}
              className="flex-1 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-lg shadow-sm p-4 font-medium flex items-center justify-center gap-2 transition-colors"
              data-testid="comments-btn"
            >
              <MessageSquare size={20} />
              Comments ({comments.length})
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className="flex-1 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded-lg shadow-sm p-4 font-medium flex items-center justify-center gap-2 transition-colors"
              data-testid="history-btn"
            >
              <History size={20} />
              Task History
            </button>
          </div>

          {/* Attachments Section */}
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm">
            {/* Attachment Header */}
            <div className="border-b border-slate-200 px-6 py-4">
              <h4 className="font-medium text-text-primary flex items-center gap-2">
                <Paperclip size={20} />
                Attachments ({attachments.length})
              </h4>
            </div>

            {/* Attachment Content */}
            <div className="p-6">
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
                    Supported: PDF, JPG, PNG, DOC, DOCX (Max 10MB)
                  </p>
                </div>

                {/* Files List */}
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
            </div>
          </div>
        </div>

        {/* Sidebar Info - Collapsible */}
        {!sidebarCollapsed && (
          <div>
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-4">
              {/* Sidebar Header with Toggle */}
              <div className="flex items-center justify-between mb-3">
                <h5 className="font-heading font-semibold text-text-primary">Task Information</h5>
                <button
                  onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                  className="p-1 hover:bg-slate-100 rounded-md transition-colors"
                  title="Collapse sidebar"
                  data-testid="sidebar-toggle"
                >
                  <ChevronRight size={20} className="text-text-primary" />
                </button>
              </div>

            {/* Sidebar Content */}
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-text-secondary">Assigned To:</span>
                  <p className="text-text-primary font-medium">{task.assigned_to_name}</p>
                </div>
                <div>
                  <span className="text-text-secondary">Assigned Date:</span>
                  <p className="text-text-primary font-medium">
                    {task.assigned_date ? new Date(task.assigned_date).toLocaleDateString() : new Date(task.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <span className="text-text-secondary">Due Date:</span>
                  <p className="text-text-primary font-medium">{new Date(task.due_date).toLocaleDateString()}</p>
                </div>
                <div>
                  <span className="text-text-secondary">Priority:</span>
                  <p className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-semibold border ${getPriorityBadge(task.priority)}`}>
                    {task.priority}
                  </p>
                </div>
                <div>
                  <span className="text-text-secondary">Created By:</span>
                  <p className="text-text-primary font-medium">{task.created_by_name}</p>
                </div>
                <div className="border-t border-slate-200 pt-3">
                  <span className="text-text-secondary">Created:</span>
                  <p className="text-text-primary font-medium text-xs">{new Date(task.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <span className="text-text-secondary">Last Updated:</span>
                  <p className="text-text-primary font-medium text-xs">{new Date(task.updated_at).toLocaleString()}</p>
                </div>
                <div>
                  <span className="text-text-secondary">Task ID:</span>
                  <p className="text-text-primary font-mono text-xs">{task.id}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Collapsed Sidebar - Icon Bar */}
        {sidebarCollapsed && (
          <div className="lg:col-span-1">
            <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-3 h-fit sticky top-6">
              {/* Expand Button */}
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="p-2 hover:bg-slate-100 rounded transition-colors w-full mb-3 flex justify-center"
                title="Expand sidebar"
              >
                <ChevronLeft size={20} className="text-text-primary" />
              </button>

              {/* Icon Buttons with Hover Tooltips */}
              <div className="space-y-2 border-t border-slate-200 pt-3">
                <div className="group relative">
                  <button className="p-2 hover:bg-slate-100 rounded transition-colors w-full flex justify-center" title="Assigned To">
                    <User size={18} className="text-primary" />
                  </button>
                  <div className="absolute left-full ml-2 hidden group-hover:block bg-slate-900 text-white px-2 py-1 rounded text-xs whitespace-nowrap z-10">
                    {task.assigned_to_name}
                  </div>
                </div>
                <div className="group relative">
                  <button className="p-2 hover:bg-slate-100 rounded transition-colors w-full flex justify-center" title="Assigned Date">
                    <Calendar size={18} className="text-primary" />
                  </button>
                  <div className="absolute left-full ml-2 hidden group-hover:block bg-slate-900 text-white px-2 py-1 rounded text-xs whitespace-nowrap z-10">
                    {task.assigned_date ? new Date(task.assigned_date).toLocaleDateString() : new Date(task.created_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="group relative">
                  <button className="p-2 hover:bg-slate-100 rounded transition-colors w-full flex justify-center" title="Priority">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold border ${getPriorityBadge(task.priority)}`}>
                      {task.priority.charAt(0).toUpperCase()}
                    </span>
                  </button>
                  <div className="absolute left-full ml-2 hidden group-hover:block bg-slate-900 text-white px-2 py-1 rounded text-xs whitespace-nowrap z-10">
                    {task.priority}
                  </div>
                </div>
                <div className="group relative">
                  <button className="p-2 hover:bg-slate-100 rounded transition-colors w-full flex justify-center" title="Created By">
                    <Info size={18} className="text-primary" />
                  </button>
                  <div className="absolute left-full ml-2 hidden group-hover:block bg-slate-900 text-white px-2 py-1 rounded text-xs whitespace-nowrap z-10">
                    {task.created_by_name}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Comments Modal - Email Style */}
      {showCommentsModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl h-[90vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="border-b border-slate-200 px-6 py-4 flex items-center justify-between bg-gradient-to-r from-primary/5 to-transparent">
              <div>
                <h3 className="text-xl font-heading font-semibold text-text-primary flex items-center gap-2">
                  <MessageSquare size={24} />
                  Comments Thread ({comments.length})
                </h3>
                <p className="text-sm text-text-secondary mt-1">{task?.title}</p>
              </div>
              <button
                onClick={() => {
                  setShowCommentsModal(false);
                  setReplyingTo(null);
                  setNewComment('');
                }}
                className="text-text-secondary hover:text-text-primary transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Comments Thread */}
            <div className="flex-1 overflow-y-auto bg-slate-50">
              <div className="p-6 space-y-4">
                {comments.length === 0 ? (
                  <p className="text-center text-text-secondary py-12">No comments yet. Start the conversation!</p>
                ) : (
                  comments.map((comment) => {
                    const hasQuote = comment.content.includes('> **Re:');
                    return (
                      <div
                        key={comment.id}
                        className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-all"
                        data-testid={`comment-${comment.id}`}
                      >
                        {/* Comment Header */}
                        <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center gap-3">
                          <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
                            {comment.user_name.charAt(0).toUpperCase()}
                          </div>
                          <div className="flex-1">
                            <p className="font-semibold text-text-primary">{comment.user_name}</p>
                            <p className="text-xs text-text-secondary">
                              {new Date(comment.created_at).toLocaleString()}
                            </p>
                          </div>
                          <button
                            onClick={() => {
                              setReplyingTo(comment);
                              setNewComment('');
                            }}
                            className="px-3 py-1 text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 rounded border border-blue-200 transition-colors"
                          >
                            Reply
                          </button>
                        </div>

                        {/* Comment Body */}
                        <div className="px-4 py-4">
                          {hasQuote ? (
                            <div className="space-y-3">
                              {/* Quoted Section */}
                              <div className="bg-slate-100 border-l-4 border-slate-400 pl-3 py-2 text-sm text-text-secondary whitespace-pre-wrap break-words font-mono">
                                {comment.content
                                  .split('\n\n')[0]
                                  .split('\n')
                                  .map((line, idx) => (
                                    <div key={idx} className="text-slate-600">
                                      {line}
                                    </div>
                                  ))}
                              </div>
                              {/* Reply Text */}
                              <div className="text-text-primary whitespace-pre-wrap break-words">
                                {comment.content.split('\n\n').slice(1).join('\n\n')}
                              </div>
                            </div>
                          ) : (
                            <div className="text-text-primary whitespace-pre-wrap break-words leading-relaxed">
                              {comment.content}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Reply Composition Area */}
            <div className="border-t border-slate-200 bg-white px-6 py-4 space-y-3">
              {replyingTo && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-3">
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-blue-900">Replying to {replyingTo.user_name}</p>
                    <p className="text-xs text-blue-700 mt-1 line-clamp-2">
                      {replyingTo.content.includes('> **Re:')
                        ? replyingTo.content.split('\n\n').slice(1).join('\n\n').substring(0, 100)
                        : replyingTo.content.substring(0, 100)}
                      {replyingTo.content.length > 100 ? '...' : ''}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setReplyingTo(null);
                      setNewComment('');
                    }}
                    className="text-blue-600 hover:text-blue-800 font-semibold"
                  >
                    ✕
                  </button>
                </div>
              )}
              <form onSubmit={handleAddComment} className="space-y-3">
                <div className="flex gap-2">
                  <textarea
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder={replyingTo ? `Reply to ${replyingTo.user_name}...` : 'Add a comment...'}
                    rows={3}
                    className="flex-1 px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                    disabled={submittingComment}
                    data-testid="comment-input"
                  />
                  <div className="flex flex-col gap-2">
                    <button
                      type="submit"
                      disabled={submittingComment || !newComment.trim()}
                      className="px-6 py-3 bg-primary hover:bg-primary-hover text-white rounded-lg font-semibold flex items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                      data-testid="submit-comment-btn"
                    >
                      <Send size={18} />
                      {replyingTo ? 'Send Reply' : 'Post'}
                    </button>
                  </div>
                </div>

                {/* Comment File Attachments */}
                <div className="flex items-center gap-2">
                  <label className="flex items-center gap-2 px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-lg font-medium cursor-pointer transition-colors text-sm">
                    <Paperclip size={16} />
                    {uploadingCommentFile ? 'Attaching...' : 'Attach File'}
                    <input
                      type="file"
                      onChange={handleCommentFileUpload}
                      disabled={uploadingCommentFile}
                      className="hidden"
                      accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                      data-testid="comment-file-upload"
                    />
                  </label>
                  <span className="text-xs text-text-secondary">
                    {commentAttachments.length > 0 && `${commentAttachments.length} file(s) attached`}
                  </span>
                </div>

                {/* Attached Files Preview */}
                {commentAttachments.length > 0 && (
                  <div className="space-y-2">
                    {commentAttachments.map((file) => (
                      <div key={file.id} className="flex items-center justify-between p-2 bg-blue-50 border border-blue-200 rounded text-sm">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <Paperclip size={14} className="text-blue-600 flex-shrink-0" />
                          <span className="text-blue-700 truncate">{file.file_name}</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setCommentAttachments(commentAttachments.filter(f => f.id !== file.id))}
                          className="text-blue-600 hover:text-blue-800 ml-2 flex-shrink-0"
                          title="Remove attachment"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Reassign Prompt Modal */}
      {showReassignPrompt && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md p-6">
            <h3 className="text-xl font-heading font-semibold text-text-primary mb-4">Reassign Task?</h3>
            <p className="text-text-secondary mb-6">
              Would you like to reassign this task back to {task?.created_by_name}?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowReassignPrompt(false)}
                className="flex-1 px-4 py-2 border border-slate-200 text-text-primary rounded-md hover:bg-slate-50 transition-colors font-medium"
                data-testid="cancel-reassign-btn"
              >
                No, Keep It
              </button>
              <button
                onClick={handleReassign}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors font-medium flex items-center justify-center gap-2"
                data-testid="confirm-reassign-btn"
              >
                <RefreshCw size={16} />
                Yes, Reassign
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Task History Modal */}
      {activeTab === 'history' && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-3xl h-[90vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="border-b border-slate-200 px-6 py-4 flex items-center justify-between bg-gradient-to-r from-purple-50 to-transparent">
              <div>
                <h3 className="text-xl font-heading font-semibold text-text-primary flex items-center gap-2">
                  <History size={24} />
                  Task History ({auditLogs.length})
                </h3>
                <p className="text-sm text-text-secondary mt-1">{task?.title}</p>
              </div>
              <button
                onClick={() => setActiveTab('comments')}
                className="text-text-secondary hover:text-text-primary transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* History Timeline */}
            <div className="flex-1 overflow-y-auto bg-slate-50">
              <div className="p-6 space-y-4">
                {loadingAudit ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : auditLogs.length === 0 ? (
                  <p className="text-center text-text-secondary py-12">No changes recorded yet</p>
                ) : (
                  auditLogs.map((log) => (
                    <div
                      key={log.id}
                      className="bg-white border border-slate-200 rounded-lg shadow-sm p-4 hover:shadow-md transition-all"
                      data-testid={`audit-log-${log.id}`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <p className="font-semibold text-text-primary">{log.user_name}</p>
                          <p className="text-xs text-text-secondary">
                            {new Date(log.created_at).toLocaleString()}
                          </p>
                        </div>
                        <span className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-semibold rounded-full">
                          {log.action_type.replace('_', ' ')}
                        </span>
                      </div>
                      {log.metadata && (
                        <div className="text-sm text-text-secondary mt-3 bg-slate-50 p-3 rounded border border-slate-200">
                          {Object.entries(log.metadata).map(([key, value]) => (
                            <div key={key} className="flex justify-between py-1">
                              <span className="font-medium">{key.replace(/_/g, ' ')}:</span>
                              <span className="text-right">{String(value)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskDetail;