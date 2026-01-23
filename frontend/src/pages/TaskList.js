import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plus, Calendar, User, Search, Filter, X, ChevronDown, AlertTriangle, LayoutGrid, List, Trash2, XCircle, Edit3, CheckSquare, Square } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import KanbanBoard from '../components/KanbanBoard';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TaskList = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [stats, setStats] = useState(null);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'kanban'
  
  // Bulk selection state
  const [selectedTasks, setSelectedTasks] = useState(new Set());
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkAction, setBulkAction] = useState(null); // 'edit', 'cancel', 'delete'
  const [bulkEditData, setBulkEditData] = useState({ status: '', priority: '', assigned_to: '' });
  
  // Check if user can do bulk operations
  const canBulkEdit = user?.role === 'admin' || user?.role === 'manager';
  
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

  // Clear selection when tasks change
  useEffect(() => {
    setSelectedTasks(new Set());
  }, [tasks]);

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
      if (filters.status && viewMode !== 'kanban') params.append('status', filters.status);
      if (filters.priority) params.append('priority', filters.priority);
      if (filters.assigned_to) params.append('assigned_to', filters.assigned_to);
      if (filters.due_date_from) params.append('due_date_from', filters.due_date_from);
      if (filters.due_date_to) params.append('due_date_to', filters.due_date_to);
      if (filters.overdue && viewMode !== 'kanban') params.append('overdue', 'true');
      params.append('sort_by', filters.sort_by);
      params.append('sort_order', filters.sort_order);
      params.append('limit', '500');
      
      const response = await axios.get(`${API}/tasks?${params}`);
      setTasks(response.data);
    } catch (error) {
      toast.error('Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  }, [filters, viewMode]);

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

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      await axios.patch(`${API}/tasks/${taskId}`, { status: newStatus });
      toast.success('Task status updated');
      fetchTasks();
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update task');
    }
  };

  // Bulk operations
  const handleSelectAll = () => {
    if (selectedTasks.size === tasks.length) {
      setSelectedTasks(new Set());
    } else {
      setSelectedTasks(new Set(tasks.map(t => t.id)));
    }
  };

  const handleSelectTask = (taskId, e) => {
    e.stopPropagation();
    const newSelected = new Set(selectedTasks);
    if (newSelected.has(taskId)) {
      newSelected.delete(taskId);
    } else {
      newSelected.add(taskId);
    }
    setSelectedTasks(newSelected);
  };

  const openBulkModal = (action) => {
    setBulkAction(action);
    setBulkEditData({ status: '', priority: '', assigned_to: '' });
    setShowBulkModal(true);
  };

  const handleBulkEdit = async () => {
    if (!bulkEditData.status && !bulkEditData.priority && !bulkEditData.assigned_to) {
      toast.error('Please select at least one field to update');
      return;
    }

    try {
      const payload = {
        task_ids: Array.from(selectedTasks),
        ...(bulkEditData.status && { status: bulkEditData.status }),
        ...(bulkEditData.priority && { priority: bulkEditData.priority }),
        ...(bulkEditData.assigned_to && { assigned_to: bulkEditData.assigned_to })
      };
      
      const response = await axios.post(`${API}/tasks/bulk/update`, payload);
      toast.success(response.data.message);
      setShowBulkModal(false);
      setSelectedTasks(new Set());
      fetchTasks();
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update tasks');
    }
  };

  const handleBulkCancel = async () => {
    try {
      const response = await axios.post(`${API}/tasks/bulk/cancel`, {
        task_ids: Array.from(selectedTasks)
      });
      toast.success(response.data.message);
      setShowBulkModal(false);
      setSelectedTasks(new Set());
      fetchTasks();
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to cancel tasks');
    }
  };

  const handleBulkDelete = async () => {
    try {
      const response = await axios.delete(`${API}/tasks/bulk/delete`, {
        data: { task_ids: Array.from(selectedTasks) }
      });
      toast.success(response.data.message);
      setShowBulkModal(false);
      setSelectedTasks(new Set());
      fetchTasks();
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete tasks');
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
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-3xl font-heading font-bold text-text-primary mb-2">All Tasks</h2>
          <p className="text-text-secondary">View and manage all tasks across the organization</p>
        </div>
        <div className="flex items-center gap-3">
          {/* View Toggle */}
          <div className="flex items-center bg-slate-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 rounded-md flex items-center gap-2 text-sm font-medium transition-colors ${
                viewMode === 'list' ? 'bg-white shadow text-primary' : 'text-text-secondary hover:text-text-primary'
              }`}
              data-testid="view-list-btn"
            >
              <List size={16} />
              List
            </button>
            <button
              onClick={() => setViewMode('kanban')}
              className={`px-3 py-1.5 rounded-md flex items-center gap-2 text-sm font-medium transition-colors ${
                viewMode === 'kanban' ? 'bg-white shadow text-primary' : 'text-text-secondary hover:text-text-primary'
              }`}
              data-testid="view-kanban-btn"
            >
              <LayoutGrid size={16} />
              Kanban
            </button>
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
            {/* Status Filter - hidden in Kanban */}
            {viewMode !== 'kanban' && (
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
            )}

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

            {/* Overdue Only - hidden in Kanban */}
            {viewMode !== 'kanban' && (
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
            )}
          </div>
        )}
      </div>

      {/* Bulk Action Bar - Only for Admin/Manager */}
      {canBulkEdit && selectedTasks.size > 0 && viewMode === 'list' && (
        <div className="bg-primary/10 border border-primary/30 rounded-lg p-4 flex items-center justify-between" data-testid="bulk-action-bar">
          <div className="flex items-center gap-3">
            <span className="font-medium text-primary">{selectedTasks.size} task(s) selected</span>
            <button
              onClick={() => setSelectedTasks(new Set())}
              className="text-sm text-text-secondary hover:text-text-primary"
            >
              Clear selection
            </button>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => openBulkModal('edit')}
              className="px-4 py-2 bg-white border border-slate-200 rounded-md hover:bg-slate-50 flex items-center gap-2 text-sm font-medium"
              data-testid="bulk-edit-btn"
            >
              <Edit3 size={16} />
              Edit
            </button>
            <button
              onClick={() => openBulkModal('cancel')}
              className="px-4 py-2 bg-yellow-50 border border-yellow-200 text-yellow-700 rounded-md hover:bg-yellow-100 flex items-center gap-2 text-sm font-medium"
              data-testid="bulk-cancel-btn"
            >
              <XCircle size={16} />
              Cancel
            </button>
            <button
              onClick={() => openBulkModal('delete')}
              className="px-4 py-2 bg-red-50 border border-red-200 text-red-700 rounded-md hover:bg-red-100 flex items-center gap-2 text-sm font-medium"
              data-testid="bulk-delete-btn"
            >
              <Trash2 size={16} />
              Delete
            </button>
          </div>
        </div>
      )}

      {/* Results Count & Select All */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-text-secondary">
          Showing {tasks.length} task{tasks.length !== 1 ? 's' : ''}
          {filters.search && ` matching "${filters.search}"`}
        </div>
        {canBulkEdit && viewMode === 'list' && tasks.length > 0 && (
          <button
            onClick={handleSelectAll}
            className="text-sm text-primary hover:underline flex items-center gap-1"
            data-testid="select-all-btn"
          >
            {selectedTasks.size === tasks.length ? <CheckSquare size={16} /> : <Square size={16} />}
            {selectedTasks.size === tasks.length ? 'Deselect All' : 'Select All'}
          </button>
        )}
      </div>

      {/* Tasks View */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : viewMode === 'kanban' ? (
        <KanbanBoard 
          tasks={tasks} 
          onStatusChange={handleStatusChange}
          onTaskClick={(taskId) => navigate(`/tasks/${taskId}`)}
        />
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
                className={`bg-white border rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow ${
                  isOverdue(task) ? 'border-red-300 bg-red-50/30' : 'border-slate-200'
                } ${selectedTasks.has(task.id) ? 'ring-2 ring-primary' : ''}`}
                data-testid={`task-card-${task.id}`}
              >
                {/* Selection Checkbox */}
                {canBulkEdit && (
                  <div className="flex items-center justify-between mb-3">
                    <button
                      onClick={(e) => handleSelectTask(task.id, e)}
                      className="p-1 hover:bg-slate-100 rounded"
                      data-testid={`select-task-${task.id}`}
                    >
                      {selectedTasks.has(task.id) ? (
                        <CheckSquare size={20} className="text-primary" />
                      ) : (
                        <Square size={20} className="text-slate-400" />
                      )}
                    </button>
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold border ${getPriorityBadge(task.priority)}`}>
                      {task.priority}
                    </span>
                  </div>
                )}
                
                <div 
                  onClick={() => navigate(`/tasks/${task.id}`)}
                  className="cursor-pointer"
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
                    {!canBulkEdit && (
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold border ml-2 ${getPriorityBadge(task.priority)}`}>
                        {task.priority}
                      </span>
                    )}
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
                  <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold border ${getStatusBadge(task.status)}`}>
                    {task.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

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

      {/* Bulk Action Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" data-testid="bulk-action-modal">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md p-6">
            {bulkAction === 'edit' && (
              <>
                <h3 className="text-xl font-heading font-semibold text-text-primary mb-4">
                  Edit {selectedTasks.size} Task(s)
                </h3>
                <p className="text-text-secondary text-sm mb-6">
                  Select the fields you want to update. Only selected fields will be changed.
                </p>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-text-primary mb-2">Status</label>
                    <select
                      value={bulkEditData.status}
                      onChange={(e) => setBulkEditData({ ...bulkEditData, status: e.target.value })}
                      className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option value="">Don't change</option>
                      <option value="todo">To Do</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary mb-2">Priority</label>
                    <select
                      value={bulkEditData.priority}
                      onChange={(e) => setBulkEditData({ ...bulkEditData, priority: e.target.value })}
                      className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option value="">Don't change</option>
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text-primary mb-2">Reassign To</label>
                    <select
                      value={bulkEditData.assigned_to}
                      onChange={(e) => setBulkEditData({ ...bulkEditData, assigned_to: e.target.value })}
                      className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option value="">Don't change</option>
                      {users.map((user) => (
                        <option key={user.id} value={user.id}>{user.full_name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => setShowBulkModal(false)}
                    className="flex-1 px-4 py-2 border border-slate-200 text-text-primary rounded-md hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleBulkEdit}
                    className="flex-1 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-md"
                    data-testid="confirm-bulk-edit"
                  >
                    Update Tasks
                  </button>
                </div>
              </>
            )}

            {bulkAction === 'cancel' && (
              <>
                <h3 className="text-xl font-heading font-semibold text-text-primary mb-4">
                  Cancel {selectedTasks.size} Task(s)?
                </h3>
                <p className="text-text-secondary mb-6">
                  This will set the status of selected tasks to "Cancelled". The tasks will remain in the system for audit purposes.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowBulkModal(false)}
                    className="flex-1 px-4 py-2 border border-slate-200 text-text-primary rounded-md hover:bg-slate-50"
                  >
                    No, Keep Tasks
                  </button>
                  <button
                    onClick={handleBulkCancel}
                    className="flex-1 px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-md"
                    data-testid="confirm-bulk-cancel"
                  >
                    Yes, Cancel Tasks
                  </button>
                </div>
              </>
            )}

            {bulkAction === 'delete' && (
              <>
                <h3 className="text-xl font-heading font-semibold text-red-600 mb-4">
                  Delete {selectedTasks.size} Task(s) Permanently?
                </h3>
                <p className="text-text-secondary mb-2">
                  <strong className="text-red-600">Warning:</strong> This action cannot be undone!
                </p>
                <p className="text-text-secondary mb-6">
                  All selected tasks, their comments, and attachments will be permanently removed from the system.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowBulkModal(false)}
                    className="flex-1 px-4 py-2 border border-slate-200 text-text-primary rounded-md hover:bg-slate-50"
                  >
                    No, Keep Tasks
                  </button>
                  <button
                    onClick={handleBulkDelete}
                    className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md"
                    data-testid="confirm-bulk-delete"
                  >
                    Yes, Delete Forever
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskList;
