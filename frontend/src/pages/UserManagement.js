import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, User, Edit2, Key, UserX, UserCheck, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'team_member'
  });

  const [editData, setEditData] = useState({
    email: '',
    full_name: '',
    role: ''
  });

  const [passwordData, setPasswordData] = useState({
    new_password: ''
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      toast.error('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/users`, formData);
      toast.success('User created successfully');
      setShowModal(false);
      setFormData({ email: '', full_name: '', password: '', role: 'team_member' });
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create user');
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.patch(`${API}/users/${selectedUser.id}`, editData);
      toast.success('User updated successfully');
      setShowEditModal(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update user');
    }
  };

  const handlePasswordReset = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/users/${selectedUser.id}/reset-password`, passwordData);
      toast.success('Password reset successfully');
      setShowPasswordModal(false);
      setSelectedUser(null);
      setPasswordData({ new_password: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    }
  };

  const handleDeactivate = async (user) => {
    if (!window.confirm(`Are you sure you want to deactivate ${user.full_name}?`)) return;
    
    try {
      await axios.post(`${API}/users/${user.id}/deactivate`);
      toast.success('User deactivated successfully');
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to deactivate user');
    }
  };

  const handleActivate = async (user) => {
    try {
      await axios.post(`${API}/users/${user.id}/activate`);
      toast.success('User activated successfully');
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to activate user');
    }
  };

  const openEditModal = (user) => {
    setSelectedUser(user);
    setEditData({
      email: user.email,
      full_name: user.full_name,
      role: user.role
    });
    setShowEditModal(true);
  };

  const openPasswordModal = (user) => {
    setSelectedUser(user);
    setPasswordData({ new_password: '' });
    setShowPasswordModal(true);
  };

  // All available roles
  const availableRoles = [
    { value: 'admin', label: 'Admin', color: 'bg-purple-100 text-purple-700 border-purple-200' },
    { value: 'manager', label: 'Manager', color: 'bg-blue-100 text-blue-700 border-blue-200' },
    { value: 'team_member', label: 'Team Member', color: 'bg-green-100 text-green-700 border-green-200' },
    { value: 'sales', label: 'Sales', color: 'bg-orange-100 text-orange-700 border-orange-200' },
    { value: 'operations', label: 'Operations', color: 'bg-teal-100 text-teal-700 border-teal-200' },
    { value: 'marketing', label: 'Marketing', color: 'bg-pink-100 text-pink-700 border-pink-200' },
    { value: 'accounts', label: 'Accounts', color: 'bg-indigo-100 text-indigo-700 border-indigo-200' }
  ];

  const getRoleBadge = (role) => {
    const roleConfig = availableRoles.find(r => r.value === role);
    return roleConfig?.color || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="user-management">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-heading font-bold text-text-primary mb-2">User Management</h2>
          <p className="text-text-secondary">Manage users and their roles</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-primary hover:bg-primary-hover text-white px-6 py-3 rounded-md font-medium flex items-center gap-2 transition-all active:scale-95"
          data-testid="create-user-btn"
        >
          <Plus size={20} />
          Create User
        </button>
      </div>

      {/* Users Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-6 py-4 text-sm font-semibold text-text-primary">Name</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-text-primary">Email</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-text-primary">Role</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-text-primary">Status</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-text-primary">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-slate-50 transition-colors" data-testid={`user-row-${user.id}`}>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
                        <span className="text-white font-semibold">{user.full_name.charAt(0)}</span>
                      </div>
                      <span className="font-medium text-text-primary">{user.full_name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-text-secondary">{user.email}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold border ${getRoleBadge(user.role)}`}>
                      {user.role.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {user.is_active ? (
                      <span className="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold bg-green-100 text-green-700 border-green-200">
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold bg-red-100 text-red-700 border-red-200">
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => openEditModal(user)}
                        className="p-2 hover:bg-blue-50 rounded-md transition-colors"
                        title="Edit User"
                        data-testid={`edit-btn-${user.id}`}
                      >
                        <Edit2 size={16} className="text-blue-600" />
                      </button>
                      <button
                        onClick={() => openPasswordModal(user)}
                        className="p-2 hover:bg-yellow-50 rounded-md transition-colors"
                        title="Reset Password"
                        data-testid={`password-btn-${user.id}`}
                      >
                        <Key size={16} className="text-yellow-600" />
                      </button>
                      {user.is_active ? (
                        <button
                          onClick={() => handleDeactivate(user)}
                          className="p-2 hover:bg-red-50 rounded-md transition-colors"
                          title="Deactivate User"
                          data-testid={`deactivate-btn-${user.id}`}
                        >
                          <UserX size={16} className="text-red-600" />
                        </button>
                      ) : (
                        <button
                          onClick={() => handleActivate(user)}
                          className="p-2 hover:bg-green-50 rounded-md transition-colors"
                          title="Activate User"
                          data-testid={`activate-btn-${user.id}`}
                        >
                          <UserCheck size={16} className="text-green-600" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create User Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" data-testid="create-user-modal">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md p-6">
            <h3 className="text-2xl font-heading font-semibold text-text-primary mb-6">Create New User</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Full Name</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                  data-testid="full-name-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                  data-testid="email-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Password</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                  data-testid="password-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Role</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  data-testid="role-select"
                >
                  {availableRoles.map((role) => (
                    <option key={role.value} value={role.value}>{role.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 border border-slate-200 text-text-primary rounded-md hover:bg-slate-50 transition-colors"
                  data-testid="cancel-btn"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-md transition-all active:scale-95"
                  data-testid="submit-user-btn"
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md p-6">
            <h3 className="text-2xl font-heading font-semibold text-text-primary mb-6">Edit User</h3>
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Full Name</label>
                <input
                  type="text"
                  value={editData.full_name}
                  onChange={(e) => setEditData({ ...editData, full_name: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Email</label>
                <input
                  type="email"
                  value={editData.email}
                  onChange={(e) => setEditData({ ...editData, email: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">Role</label>
                <select
                  value={editData.role}
                  onChange={(e) => setEditData({ ...editData, role: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {availableRoles.map((role) => (
                    <option key={role.value} value={role.value}>{role.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setShowEditModal(false); setSelectedUser(null); }}
                  className="flex-1 px-4 py-2 border border-slate-200 text-text-primary rounded-md hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-md transition-all active:scale-95"
                >
                  Update User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Password Reset Modal */}
      {showPasswordModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-md p-6">
            <h3 className="text-2xl font-heading font-semibold text-text-primary mb-6">Reset Password</h3>
            <p className="text-text-secondary mb-4">Reset password for: <strong>{selectedUser.full_name}</strong></p>
            <form onSubmit={handlePasswordReset} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">New Password</label>
                <input
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ new_password: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                  minLength="6"
                  placeholder="Enter new password"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setShowPasswordModal(false); setSelectedUser(null); }}
                  className="flex-1 px-4 py-2 border border-slate-200 text-text-primary rounded-md hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary hover:bg-primary-hover text-white rounded-md transition-all active:scale-95"
                >
                  Reset Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
