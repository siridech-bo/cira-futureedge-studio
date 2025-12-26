// Authentication Manager
class AuthManager {
    constructor() {
        this.token = sessionStorage.getItem('auth_token') || '';
        this.authEnabled = true;
    }

    async login(username, password) {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                const data = await response.json();
                this.token = data.token;
                this.authEnabled = data.auth_enabled;
                sessionStorage.setItem('auth_token', this.token);
                return { success: true };
            } else {
                const error = await response.json();
                return { success: false, error: error.error || 'Login failed' };
            }
        } catch (error) {
            return { success: false, error: 'Connection error' };
        }
    }

    logout() {
        this.token = '';
        sessionStorage.removeItem('auth_token');
        sessionStorage.removeItem('dashboard_config');
        window.location.reload();
    }

    getHeaders() {
        if (!this.authEnabled || !this.token) {
            return {};
        }

        return {
            'Authorization': `Bearer ${this.token}`
        };
    }

    isAuthenticated() {
        return !this.authEnabled || (this.token && this.token.length > 0);
    }
}

// Initialize auth manager
const authManager = new AuthManager();

// Handle login form
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        const result = await authManager.login(username, password);

        if (result.success) {
            showDashboard();
        } else {
            loginError.textContent = result.error;
            loginError.classList.add('show');
        }
    });

    // Check if already authenticated
    if (authManager.isAuthenticated()) {
        showDashboard();
    }

    // Logout button
    const logoutBtn = document.getElementById('btn-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            authManager.logout();
        });
    }
});

function showDashboard() {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard-screen').style.display = 'block';

    // Initialize dashboard
    if (typeof initializeDashboard === 'function') {
        initializeDashboard();
    }
}
