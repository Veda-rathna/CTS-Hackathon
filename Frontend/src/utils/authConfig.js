/**
 * Centralized Demo Authentication Configuration
 * 
 * Enterprise Prior Authorization Platform - Provider-Only Authentication
 * For hackathon demo purposes, maintains two authorized clinical reviewer identities.
 * Patient accounts and patient logins are explicitly NOT supported.
 */

export const DEMO_PROVIDERS = [
  {
    id: 'PROV-001',
    name: 'Dr. John wick',
    role: 'Clinical Reviewer',
    username: 'provider1@pa-demo.local',
    password: 'Provider@123',
    initials: 'JW',
    organization: 'Prior Auth Review Board',
    specialty: 'Clinical UM Reviewer',
  },
  {
    id: 'PROV-002',
    name: 'Dr. Ananya Rao',
    role: 'Clinical Reviewer',
    username: 'provider2@pa-demo.local',
    password: 'Provider@456',
    initials: 'AR',
    organization: 'Prior Auth Review Board',
    specialty: 'Clinical UM Reviewer',
  },
];

export const AUTH_STORAGE_KEY = 'pa_auth_provider_session_v1';

/**
 * Authenticates a provider using username and password.
 * Returns a sanitized provider object (excluding credentials).
 * 
 * @param {string} username 
 * @param {string} password 
 * @returns {Promise<{success: boolean, provider?: object, error?: string}>}
 */
export async function authenticateProvider(username, password) {
  // Simulate standard enterprise auth network latency (300ms)
  await new Promise((resolve) => setTimeout(resolve, 300));

  const trimmedUsername = (username || '').trim().toLowerCase();
  const trimmedPassword = (password || '').trim();

  if (!trimmedUsername || !trimmedPassword) {
    return {
      success: false,
      error: 'Please enter both your provider username and password.',
    };
  }

  const matched = DEMO_PROVIDERS.find(
    (p) => p.username.toLowerCase() === trimmedUsername && p.password === trimmedPassword
  );

  if (matched) {
    // Strip sensitive password field before storing in session state
    const { password: _, ...sanitizedProvider } = matched;
    return {
      success: true,
      provider: {
        ...sanitizedProvider,
        authenticatedAt: new Date().toISOString(),
      },
    };
  }

  return {
    success: false,
    error: 'Invalid provider credentials. Please verify your username and password.',
  };
}
