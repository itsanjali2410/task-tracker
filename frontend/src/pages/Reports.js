import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TrendingUp, Users, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Reports = () => {
  const [teamOverview, setTeamOverview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await axios.get(`${API}/reports/team-overview`);
      setTeamOverview(response.data);
    } catch (error) {
      toast.error('Failed to fetch reports');
    } finally {
      setLoading(false);
    }
  };

  const getProductivityColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getProductivityBadge = (score) => {
    if (score >= 80) return 'bg-green-100 text-green-700 border-green-200';
    if (score >= 60) return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    return 'bg-red-100 text-red-700 border-red-200';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!teamOverview) return null;

  return (
    <div className="space-y-6" data-testid="reports-page">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-heading font-bold text-text-primary mb-2">Team Productivity Reports</h2>
        <p className="text-text-secondary">Overview of team performance and individual metrics</p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-6" data-testid="stat-total-users">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-blue-500 w-12 h-12 rounded-lg flex items-center justify-center">
              <Users className="text-white" size={24} />
            </div>
          </div>
          <p className="text-3xl font-heading font-bold text-text-primary mb-1">{teamOverview.total_users}</p>
          <p className="text-sm text-text-secondary">Team Members</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-6" data-testid="stat-total-tasks">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-purple-500 w-12 h-12 rounded-lg flex items-center justify-center">
              <CheckCircle2 className="text-white" size={24} />
            </div>
          </div>
          <p className="text-3xl font-heading font-bold text-text-primary mb-1">{teamOverview.total_tasks}</p>
          <p className="text-sm text-text-secondary">Total Tasks</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-6" data-testid="stat-completed">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-green-500 w-12 h-12 rounded-lg flex items-center justify-center">
              <CheckCircle2 className="text-white" size={24} />
            </div>
          </div>
          <p className="text-3xl font-heading font-bold text-text-primary mb-1">{teamOverview.total_completed}</p>
          <p className="text-sm text-text-secondary">Completed Tasks</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-6" data-testid="stat-overdue">
          <div className="flex items-center justify-between mb-4">
            <div className="bg-red-500 w-12 h-12 rounded-lg flex items-center justify-center">
              <AlertCircle className="text-white" size={24} />
            </div>
          </div>
          <p className="text-3xl font-heading font-bold text-text-primary mb-1">{teamOverview.total_overdue}</p>
          <p className="text-sm text-text-secondary">Overdue Tasks</p>
        </div>
      </div>

      {/* Average Productivity Score */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-6">
        <div className="flex items-center gap-3 mb-4">
          <TrendingUp size={24} className="text-primary" />
          <h3 className="text-xl font-heading font-semibold text-text-primary">
            Team Average Productivity Score
          </h3>
        </div>
        <div className="flex items-center gap-4">
          <div className={`text-6xl font-heading font-bold ${getProductivityColor(teamOverview.average_productivity_score)}`}>
            {teamOverview.average_productivity_score}
          </div>
          <div className="text-text-secondary">
            <p className="text-sm">out of 100</p>
            <p className="text-xs mt-1">Based on completion rate, on-time delivery, and overdue tasks</p>
          </div>
        </div>
      </div>

      {/* Individual User Stats */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-200">
          <h3 className="text-xl font-heading font-semibold text-text-primary">Individual Performance</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-6 py-4 text-sm font-semibold text-text-primary">User</th>
                <th className="text-center px-6 py-4 text-sm font-semibold text-text-primary">Total Tasks</th>
                <th className="text-center px-6 py-4 text-sm font-semibold text-text-primary">Completed</th>
                <th className="text-center px-6 py-4 text-sm font-semibold text-text-primary">On Time</th>
                <th className="text-center px-6 py-4 text-sm font-semibold text-text-primary">Overdue</th>
                <th className="text-center px-6 py-4 text-sm font-semibold text-text-primary">Avg Time (hrs)</th>
                <th className="text-center px-6 py-4 text-sm font-semibold text-text-primary">Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {teamOverview.user_stats.map((userStat) => (
                <tr key={userStat.user_id} className="hover:bg-slate-50 transition-colors" data-testid={`user-stat-${userStat.user_id}`}>
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-medium text-text-primary">{userStat.user_name}</p>
                      <p className="text-sm text-text-secondary">{userStat.user_email}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center text-text-primary font-medium">
                    {userStat.total_tasks_assigned}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-green-600 font-medium">{userStat.tasks_completed}</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-blue-600 font-medium">{userStat.tasks_completed_on_time}</span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-red-600 font-medium">{userStat.overdue_tasks}</span>
                  </td>
                  <td className="px-6 py-4 text-center text-text-primary">
                    <div className="flex items-center justify-center gap-1">
                      <Clock size={14} className="text-text-secondary" />
                      {userStat.average_completion_time_hours}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold border ${getProductivityBadge(userStat.productivity_score)}`}>
                      {userStat.productivity_score}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Reports;