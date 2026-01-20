import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await login(email, password);
    if (result.success) {
      toast.success('Login successful!');
      navigate('/dashboard');
    } else {
      toast.error(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen login-bg">
      <div className="min-h-screen login-overlay flex items-center justify-center p-4">
        <div className="glass-card w-full max-w-md rounded-lg shadow-2xl p-8">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-lg mb-4">
              <span className="text-white font-bold text-3xl">T</span>
            </div>
            <h1 className="text-3xl font-heading font-bold text-text-primary mb-2">TripStars</h1>
            <p className="text-text-secondary">Task Management System</p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-text-primary mb-2">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                placeholder="you@tripstars.com"
                required
                data-testid="email-input"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-text-primary mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                placeholder="••••••••"
                required
                data-testid="password-input"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary hover:bg-primary-hover text-white font-medium py-3 rounded-md transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="login-btn"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Demo credentials */}
          <div className="mt-8 p-4 bg-slate-50 rounded-lg">
            <p className="text-xs font-semibold text-text-secondary mb-2">Demo Credentials:</p>
            <div className="space-y-1 text-xs text-text-secondary">
              <p><strong>Admin:</strong> admin@tripstars.com / Admin@123</p>
              <p><strong>Manager:</strong> manager@tripstars.com / Manager@123</p>
              <p><strong>Member:</strong> member@tripstars.com / Member@123</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
