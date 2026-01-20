import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { CheckSquare, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({ total_tasks: 0, todo: 0, in_progress: 0, completed: 0 });
  const [recentTasks, setRecentTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, tasksRes] = await Promise.all([
        axios.get(`${API}/stats`),
        axios.get(`${API}/tasks`)
      ]);
      setStats(statsRes.data);
      setRecentTasks(tasksRes.data.slice(0, 5));
    } catch (error) {
      toast.error('Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    { label: 'Total Tasks', value: stats.total_tasks, icon: CheckSquare, color: 'bg-blue-500' },
    { label: 'To Do', value: stats.todo, icon: AlertCircle, color: 'bg-slate-500' },
    { label: 'In Progress', value: stats.in_progress, icon: Clock, color: 'bg-status-warning' },
    { label: 'Completed', value: stats.completed, icon: CheckCircle2, color: 'bg-status-success' },
  ];

  const getStatusBadge = (status) => {
    const styles = {
      todo: 'bg-slate-100 text-slate-800 border-slate-200',
      in_progress: 'bg-blue-50 text-blue-700 border-blue-200',
      completed: 'bg-green-50 text-green-700 border-green-200'
    };
    return styles[status] || styles.todo;
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'text-green-600',
      medium: 'text-yellow-600',
      high: 'text-red-600'
    };
    return colors[priority] || colors.medium;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="dashboard">
      {/* Welcome */}
      <div>
        <h2 className="text-3xl font-heading font-bold text-text-primary mb-2">Welcome back, {user?.full_name}!</h2>
        <p className="text-text-secondary">Here's an overview of your tasks</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <div
            key={index}
            className="bg-white border border-slate-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow"
            data-testid={`stat-card-${stat.label.toLowerCase().replace(/\s+/g, '-')}`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`${stat.color} w-12 h-12 rounded-lg flex items-center justify-center`}>
                <stat.icon className="text-white" size={24} />
              </div>
            </div>
            <p className="text-3xl font-heading font-bold text-text-primary mb-1">{stat.value}</p>
            <p className="text-sm text-text-secondary">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Recent Tasks */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-heading font-semibold text-text-primary mb-4">Recent Tasks</h3>
        {recentTasks.length === 0 ? (
          <p className="text-text-secondary text-center py-8">No tasks yet</p>
        ) : (
          <div className="space-y-3">
            {recentTasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center justify-between p-4 border border-slate-200 rounded-lg hover:border-primary/30 transition-colors"
                data-testid={`task-item-${task.id}`}
              >
                <div className="flex-1">
                  <h4 className="font-medium text-text-primary mb-1">{task.title}</h4>
                  <div className="flex items-center gap-3 text-sm text-text-secondary">
                    <span>Assigned to: {task.assigned_to_name}</span>
                    <span>•</span>
                    <span className={getPriorityColor(task.priority)}>Priority: {task.priority}</span>
                  </div>
                </div>
                <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold border ${getStatusBadge(task.status)}`}>
                  {task.status.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
