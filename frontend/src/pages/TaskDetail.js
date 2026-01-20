import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Calendar, User, MessageSquare, Send } from 'lucide-react';
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
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [submittingComment, setSubmittingComment] = useState(false);

  useEffect(() => {
    fetchTaskAndComments();
  }, [taskId]);

  const fetchTaskAndComments = async () => {
    try {
      const [taskRes, commentsRes] = await Promise.all([
        axios.get(`${API}/tasks/${taskId}`),
        axios.get(`${API}/comments/task/${taskId}`)
      ]);
      setTask(taskRes.data);
      setComments(commentsRes.data);
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

  const getStatusBadge = (status) => {
    const styles = {
      todo: 'bg-slate-100 text-slate-800 border-slate-200',
      in_progress: 'bg-blue-50 text-blue-700 border-blue-200',
      completed: 'bg-green-50 text-green-700 border-green-200'
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!task) return null;

  const canUpdateStatus = user?.role === 'team_member' && task.assigned_to === user.id;
  const canUpdateAllFields = ['admin', 'manager'].includes(user?.role);

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

          {/* Comments Section */}
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-6">
            <div className="flex items-center gap-2 mb-4">
              <MessageSquare size={20} className="text-primary" />
              <h4 className="text-xl font-heading font-semibold text-text-primary">Comments</h4>
              <span className="text-sm text-text-secondary">({comments.length})</span>
            </div>

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
