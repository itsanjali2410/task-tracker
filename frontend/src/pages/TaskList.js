import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, Calendar, User } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TaskList = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    assigned_to: '',
    due_date: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [tasksRes, usersRes] = await Promise.all([
        axios.get(`${API}/tasks`),
        axios.get(`${API}/users`)
      ]);
      setTasks(tasksRes.data);
      setUsers(usersRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/tasks`, formData);
      toast.success('Task created successfully');
      setShowModal(false);
      setFormData({ title: '', description: '', priority: 'medium', assigned_to: '', due_date: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create task');
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

  return (
    <div className="space-y-6" data-testid="task-list">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-heading font-bold text-text-primary mb-2">All Tasks</h2>
          <p className="text-text-secondary">Manage and assign tasks to team members</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-primary hover:bg-primary-hover text-white px-6 py-3 rounded-md font-medium flex items-center gap-2 transition-all active:scale-95"
          data-testid="create-task-btn"
        >
          <Plus size={20} />
          Create Task
        </button>
      </div>

      {/* Tasks Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tasks.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <p className="text-text-secondary">No tasks yet. Create your first task!</p>
          </div>
        ) : (
          tasks.map((task) => (
            <div
              key={task.id}
              className="bg-white border border-slate-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow"
              data-testid={`task-card-${task.id}`}
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-heading font-semibold text-text-primary text-lg">{task.title}</h3>
                <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold border ${getPriorityBadge(task.priority)}`}>
                  {task.priority}
                </span>
              </div>
              <p className="text-text-secondary text-sm mb-4 line-clamp-2">{task.description}</p>
              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 text-sm text-text-secondary">
                  <User size={16} />
                  <span>{task.assigned_to_name}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-text-secondary">
                  <Calendar size={16} />
                  <span>{new Date(task.due_date).toLocaleDateString()}</span>
                </div>
              </div>
              <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold border ${getStatusBadge(task.status)}`}>
                {task.status.replace('_', ' ')}
              </span>
            </div>
          ))
        )}
      </div>

      {/* Create Task Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" data-testid="create-task-modal">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <h3 className="text-2xl font-heading font-semibold text-text-primary mb-6">Create New Task</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                  data-testid="task-title-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  rows={3}
                  required
                  data-testid="task-description-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Priority</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  data-testid="task-priority-select"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Assign To</label>
                <select
                  value={formData.assigned_to}
                  onChange={(e) => setFormData({ ...formData, assigned_to: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                  data-testid="task-assign-select"
                >
                  <option value="">Select user...</option>
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.full_name} ({user.role.replace('_', ' ')})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Due Date</label>
                <input
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                  data-testid="task-due-date-input"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 border border-slate-200 text-text-primary rounded-md hover:bg-slate-50 transition-colors"
                  data-testid="cancel-task-btn"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-md transition-all active:scale-95"
                  data-testid="submit-task-btn"
                >
                  Create Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskList;
