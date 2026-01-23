import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, Calendar, User, Search, Filter, X, ChevronDown, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TaskList = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [stats, setStats] = useState(null);
  
  // Form data for creating tasks
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    assigned_to: '',
    due_date: ''
  });

  // Search and filter state
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    priority: '',
    assigned_to: '',
    due_date_from: '',
    due_date_to: '',
    overdue: false,
    sort_by: 'created_at',
    sort_order: 'desc'
  });

  // Debounced search
  const [searchInput, setSearchInput] = useState('');

  useEffect(() => {
    fetchUsers();
    fetchStats();
  }, []);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setFilters(prev => ({ ...prev, search: searchInput }));
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Fetch tasks when filters change
  useEffect(() => {
    fetchTasks();
  }, [filters]);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users/assignable`);
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users');
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/tasks/stats/summary`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats');
    }
  };

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      
      if (filters.search) params.append('search', filters.search);
      if (filters.status) params.append('status', filters.status);
      if (filters.priority) params.append('priority', filters.priority);
      if (filters.assigned_to) params.append('assigned_to', filters.assigned_to);
      if (filters.due_date_from) params.append('due_date_from', filters.due_date_from);
      if (filters.due_date_to) params.append('due_date_to', filters.due_date_to);
      if (filters.overdue) params.append('overdue', 'true');
      params.append('sort_by', filters.sort_by);
      params.append('sort_order', filters.sort_order);
      
      const response = await axios.get(`${API}/tasks?${params}`);
      setTasks(response.data);
    } catch (error) {
      toast.error('Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/tasks`, formData);
      toast.success('Task created successfully');
      setShowModal(false);
      setFormData({ title: '', description: '', priority: 'medium', assigned_to: '', due_date: '' });
      fetchTasks();
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create task');
    }
  };

  const clearFilters = () => {
    setSearchInput('');
    setFilters({
      search: '',
      status: '',
      priority: '',
      assigned_to: '',
      due_date_from: '',
      due_date_to: '',
      overdue: false,
      sort_by: 'created_at',
      sort_order: 'desc'
    });
  };

  const hasActiveFilters = filters.status || filters.priority || filters.assigned_to || 
    filters.due_date_from || filters.due_date_to || filters.overdue;

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

  const isOverdue = (task) => {
    if (task.status === 'completed' || task.status === 'cancelled') return false;
    return new Date(task.due_date) < new Date();
  };

  return (
    <div className="space-y-6" data-testid="task-list">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-heading font-bold text-text-primary mb-2">All Tasks</h2>
          <p className="text-text-secondary">View and manage all tasks across the organization</p>
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

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <p className="text-sm text-text-secondary">Total</p>
            <p className="text-2xl font-bold text-text-primary">{stats.total}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <p className="text-sm text-text-secondary">To Do</p>
            <p className="text-2xl font-bold text-slate-600">{stats.by_status.todo}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <p className="text-sm text-text-secondary">In Progress</p>
            <p className="text-2xl font-bold text-blue-600">{stats.by_status.in_progress}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <p className="text-sm text-text-secondary">Completed</p>
            <p className="text-2xl font-bold text-green-600">{stats.by_status.completed}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <p className="text-sm text-text-secondary">Overdue</p>
            <p className="text-2xl font-bold text-red-600">{stats.overdue}</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4">
            <p className="text-sm text-text-secondary">My Tasks</p>
            <p className="text-2xl font-bold text-primary">{stats.my_tasks}</p>
          </div>
        </div>
      )}

      {/* Search and Filter Bar */}
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Input */}
          <div className="flex-1 relative">
            <Search size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search tasks by title or description..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              data-testid="search-input"
            />
          </div>

          {/* Quick Filters */}
          <div className="flex gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 border rounded-md flex items-center gap-2 transition-colors ${
                hasActiveFilters ? 'border-primary bg-primary/10 text-primary' : 'border-slate-200 hover:bg-slate-50'
              }`}
              data-testid="toggle-filters-btn"
            >
              <Filter size={18} />
              Filters
              {hasActiveFilters && <span className="bg-primary text-white text-xs rounded-full px-2">!</span>}
              <ChevronDown size={16} className={`transition-transform ${showFilters ? 'rotate-180' : ''}`} />
            </button>

            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="px-4 py-2 border border-slate-200 rounded-md hover:bg-slate-50 flex items-center gap-2"
              >
                <X size={18} />
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Expanded Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">Status</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                data-testid="filter-status"
              >
                <option value="">All Statuses</option>
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            {/* Priority Filter */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">Priority</label>
              <select
                value={filters.priority}
                onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                data-testid="filter-priority"
              >
                <option value="">All Priorities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            {/* Assigned To Filter */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">Assigned To</label>
              <select
                value={filters.assigned_to}
                onChange={(e) => setFilters(prev => ({ ...prev, assigned_to: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                data-testid="filter-assigned"
              >
                <option value="">All Users</option>
                {users.map(user => (
                  <option key={user.id} value={user.id}>{user.full_name}</option>
                ))}
              </select>
            </div>

            {/* Due Date From */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">Due Date From</label>
              <input
                type="date"
                value={filters.due_date_from}
                onChange={(e) => setFilters(prev => ({ ...prev, due_date_from: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                data-testid="filter-date-from"
              />
            </div>

            {/* Due Date To */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">Due Date To</label>
              <input
                type="date"
                value={filters.due_date_to}
                onChange={(e) => setFilters(prev => ({ ...prev, due_date_to: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                data-testid="filter-date-to"
              />
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">Sort By</label>
              <select
                value={filters.sort_by}
                onChange={(e) => setFilters(prev => ({ ...prev, sort_by: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                data-testid="filter-sort"
              >
                <option value="created_at">Created Date</option>
                <option value="due_date">Due Date</option>
                <option value="priority">Priority</option>
                <option value="status">Status</option>
                <option value="title">Title</option>
              </select>
            </div>

            {/* Sort Order */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1">Order</label>
              <select
                value={filters.sort_order}
                onChange={(e) => setFilters(prev => ({ ...prev, sort_order: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="desc">Newest First</option>
                <option value="asc">Oldest First</option>
              </select>
            </div>

            {/* Overdue Only */}
            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.overdue}
                  onChange={(e) => setFilters(prev => ({ ...prev, overdue: e.target.checked }))}
                  className="rounded border-slate-300 text-primary focus:ring-primary"
                  data-testid="filter-overdue"
                />
                <span className="text-sm font-medium text-red-600 flex items-center gap-1">
                  <AlertTriangle size={16} />
                  Show Overdue Only
                </span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Results Count */}
      <div className="text-sm text-text-secondary">
        Showing {tasks.length} task{tasks.length !== 1 ? 's' : ''}
        {filters.search && ` matching "${filters.search}"`}
      </div>

      {/* Tasks Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tasks.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <p className="text-text-secondary">
                {hasActiveFilters || filters.search 
                  ? 'No tasks match your filters. Try adjusting your search criteria.'
                  : 'No tasks yet. Create your first task!'}
              </p>
            </div>
          ) : (
            tasks.map((task) => (
              <div
                key={task.id}
                onClick={() => navigate(`/tasks/${task.id}`)}
                className={`bg-white border rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow cursor-pointer ${
                  isOverdue(task) ? 'border-red-300 bg-red-50/30' : 'border-slate-200'
                }`}
                data-testid={`task-card-${task.id}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {isOverdue(task) && (
                        <AlertTriangle size={16} className="text-red-500 flex-shrink-0" />
                      )}
                      <h3 className="font-heading font-semibold text-text-primary text-lg truncate">{task.title}</h3>
                    </div>
                  </div>
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold border ml-2 ${getPriorityBadge(task.priority)}`}>
                    {task.priority}
                  </span>
                </div>
                <p className="text-text-secondary text-sm mb-4 line-clamp-2">{task.description}</p>
                <div className="space-y-2 mb-4">
                  <div className="flex items-center gap-2 text-sm text-text-secondary">
                    <User size={16} />
                    <span className="truncate">{task.assigned_to_name}</span>
                  </div>
                  <div className={`flex items-center gap-2 text-sm ${isOverdue(task) ? 'text-red-600 font-medium' : 'text-text-secondary'}`}>
                    <Calendar size={16} />
                    <span>{new Date(task.due_date).toLocaleDateString()}</span>
                    {isOverdue(task) && <span className="text-xs">(Overdue)</span>}
                  </div>
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
                      {user.full_name} ({user.email})
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
