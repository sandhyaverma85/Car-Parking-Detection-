import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { login as apiLogin } from '../api';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  // Inputs start completely blank — manual user entry verified against the database
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const cleanEmail = email.trim();
    if (!cleanEmail || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setLoading(true);
    try {
      // Query backend to verify credentials directly against the database
      const res = await apiLogin(cleanEmail, password);
      await login(res.data.access_token);
      navigate('/', { replace: true });
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Invalid email or password. Please verify your credentials.');
      } else if (err.response?.status === 403) {
        setError('Account is disabled or inactive. Contact administrator.');
      } else if (err.response?.data?.detail) {
        setError(typeof err.response.data.detail === 'string' ? err.response.data.detail : 'Invalid credentials.');
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        setError('Cannot connect to authentication service. Please ensure the backend server is running on port 8000.');
      } else {
        setError('Authentication failed. Please check credentials and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at 50% 30%, #0d1629 0%, #050811 100%)',
      padding: '24px',
    }}>
      <div className="login-card">
        {/* MallPark AI Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '52px',
            height: '52px',
            borderRadius: 'var(--radius-sm)',
            background: 'linear-gradient(135deg, #090D18 0%, #152238 100%)',
            border: '1.5px solid var(--color-cyan)',
            boxShadow: '0 0 24px rgba(156, 219, 221, 0.45)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '24px',
            fontWeight: 800,
            color: 'var(--color-cyan)',
            marginBottom: '16px',
          }}>
            M
          </div>
          <h1 style={{ fontSize: '20px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.025em' }}>
            MallPark AI
          </h1>
          <div style={{ fontSize: '11px', color: 'var(--color-cyan)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700, marginTop: '2px' }}>
            Floor-Level Command Dashboard
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '6px' }}>
            Multi-Level Facility Surveillance & Automated Curb Management
          </p>
        </div>

        {/* Credentials Form — clean manual entry verified directly against database */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label
              htmlFor="login-email-input"
              style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '6px' }}
            >
              Operator Email
            </label>
            <input
              id="login-email-input"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="Enter your email address"
              required
              autoComplete="username"
            />
          </div>

          <div style={{ marginBottom: '22px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label
                htmlFor="login-password-input"
                style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}
              >
                Secure Password
              </label>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--color-cyan)',
                  fontSize: '10px',
                  cursor: 'pointer',
                  fontWeight: 600,
                }}
              >
                {showPassword ? 'Hide Password' : 'Show Password'}
              </button>
            </div>
            <input
              id="login-password-input"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              autoComplete="current-password"
            />
          </div>

          {error && (
            <div style={{
              background: 'var(--color-crimson-subtle)',
              border: '1px solid var(--border-crimson)',
              color: '#fca5a5',
              padding: '10px 14px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              marginBottom: '16px',
            }}>
              {error}
            </div>
          )}

          <button
            id="login-submit-button"
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px', fontSize: '13px', justifyContent: 'center', letterSpacing: '0.04em' }}
            disabled={loading}
          >
            {loading ? 'Verifying with Database…' : 'AUTHENTICATE & ENTER COMMAND DASHBOARD →'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '24px', fontSize: '10px', color: 'var(--text-dim)', letterSpacing: '0.04em' }}>
          MALLPARK AI NEURAL CORE v2.4 · SECURE OPERATOR ACCESS GATEWAY
        </p>
      </div>
    </div>
  );
}
