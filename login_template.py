# --- HTML Template ---
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - JobMatch</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --primary-color: #1976d2;
            --primary-hover: #1565c0;
            --error-color: #d32f2f;
            --error-bg: #ffebee;
            --text-color: #2a3b5d;
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --border-color: #e2e8f0;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body { 
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-color);
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            color: var(--text-color);
            line-height: 1.5;
        }

        .login-container {
            background: var(--card-bg);
            max-width: 400px;
            width: 90%;
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        .tagline {
            text-align: center;
            font-size: 1.25rem;
            color: var(--text-color);
            margin-bottom: 2rem;
            font-weight: 500;
        }

        h2 { 
            text-align: center; 
            color: var(--text-color);
            margin-bottom: 1.5rem;
            font-size: 1.75rem;
            font-weight: 600;
        }

        .input-group {
            margin-bottom: 1.25rem;
        }

        .input-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--text-color);
        }

        input[type=text], input[type=password] {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.2s ease;
            background: var(--card-bg);
        }

        input[type=text]:focus, input[type=password]:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
        }

        button {
            width: 100%;
            background: var(--primary-color);
            color: white;
            padding: 0.875rem;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        button:hover {
            background: var(--primary-hover);
            transform: translateY(-1px);
        }

        button:disabled { 
            background: #90caf9;
            cursor: not-allowed;
            transform: none;
        }

        .error { 
            color: var(--error-color);
            text-align: center;
            margin-bottom: 1rem;
            padding: 0.75rem;
            border-radius: 8px;
            background: var(--error-bg);
            font-size: 0.875rem;
        }

        .duo-code { 
            font-size: 1.5rem;
            color: var(--primary-color);
            margin: 1rem 0;
            text-align: center;
            font-weight: 600;
            letter-spacing: 0.05em;
        }

        .wait-section {
            display: none;
            text-align: center;
            margin-top: 1.5rem;
        }

        .spinner {
            font-size: 2rem;
            margin: 1rem 0;
            animation: spin 1s linear infinite;
            color: var(--primary-color);
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @media (max-width: 480px) {
            .login-container {
                padding: 1.5rem;
            }

            h2 {
                font-size: 1.5rem;
            }

            .tagline {
                font-size: 1.125rem;
            }
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>JobMatch Login</h2>
        <div class="tagline">We use WaterlooWorks so that you don't have to</div>
        <div id="error" class="error" style="display: none;"></div>
        <form id="loginForm">
            <div class="input-group">
                <label for="username">Username</label>
                <input name="username" id="username" type="text" placeholder="Enter your username" required>
            </div>
            <div class="input-group">
                <label for="password">Password</label>
                <input name="password" id="password" type="password" placeholder="Enter your password" required>
            </div>
            <button id="loginBtn" type="submit">Login</button>
        </form>
        <div id="waitSection" class="wait-section">
            <div id="waitMessage">Logging in...</div>
            <div id="waitSpinner" class="spinner">⏳</div>
            <div id="duoCode" class="duo-code"></div>
        </div>
    </div>

    <script>
        const loginForm = document.getElementById('loginForm');
        const waitSection = document.getElementById('waitSection');
        const waitMessage = document.getElementById('waitMessage');
        const errorDiv = document.getElementById('error');
        const duoCodeDiv = document.getElementById('duoCode');
        let loginPolling = null;
        let duoPolling = null;
        let isDuoRequired = false;
        let isPolling = false;  // Add flag to track polling state
        let duoPollingStarted = false;  // Add flag to track if DUO polling has started

        // Start DUO polling when form is interacted with
        loginForm.addEventListener('focusin', function(e) {
            if (!duoPollingStarted) {
                startDuoPolling();
                duoPollingStarted = true;
            }
        });

        // Also start DUO polling when clicking anywhere in the form
        loginForm.addEventListener('click', function(e) {
            if (!duoPollingStarted) {
                startDuoPolling();
                duoPollingStarted = true;
            }
        });

        // Check login status immediately
        checkLoginStatus();

        function clearAllPolling() {
            if (loginPolling) {
                clearInterval(loginPolling);
                loginPolling = null;
            }
            if (duoPolling) {
                clearInterval(duoPolling);
                duoPolling = null;
                duoPollingStarted = false;  // Reset the DUO polling started flag
            }
            isPolling = false;
        }

        function showWaitSection(message) {
            loginForm.style.display = "none";
            waitSection.style.display = "block";
            waitMessage.textContent = message;
        }

        function showLoginForm(errorMessage = null) {
            clearAllPolling();
            loginForm.style.display = "block";
            waitSection.style.display = "none";
            document.getElementById('loginBtn').disabled = false;
            if (errorMessage) {
                showError(errorMessage);
            }
            isDuoRequired = false;
            duoCodeDiv.style.display = "none";
            duoCodeDiv.textContent = "";
        }

        loginForm.onsubmit = async function(e) {
            e.preventDefault();
            errorDiv.style.display = "none";
            document.getElementById('loginBtn').disabled = true;

            // Ensure DUO polling is started before login attempt
            if (!duoPollingStarted) {
                startDuoPolling();
                duoPollingStarted = true;
            }

            try {
                const formData = new FormData(loginForm);
                const response = await fetch('/login', {
                    method: 'POST',
                    body: formData,
                    credentials: 'same-origin'
                });
                const data = await response.json();
                
                if (!data.success) {
                    showLoginForm(data.error || "Login failed");
                    return;
                }

                showWaitSection("Logging in...");
                startPolling();
            } catch (error) {
                showLoginForm("Login failed. Please try again.");
            }
        };

        function showError(message) {
            errorDiv.textContent = message;
            errorDiv.style.display = "block";
        }

        async function checkLoginStatus() {
            if (isPolling) return;  // Prevent multiple polling sessions
            
            try {
                const response = await fetch('/login_status', {
                    credentials: 'same-origin'
                });
                const data = await response.json();
                
                if (data.ready) {
                    clearAllPolling();
                    window.location.replace('/');
                    return;
                } else if (data.error) {
                    if (data.error === 'Login in progress') {
                        showWaitSection("Logging in...");
                        startPolling();
                    } else if (data.error.includes("DUO code")) {
                        showWaitSection("Incorrect DUO code. Please try again on your phone");
                        startPolling();
                    } else {
                        showLoginForm(data.error);
                    }
                } else if (data.duo_required) {
                    showWaitSection("Please complete DUO on your phone");
                    startPolling();
                }
            } catch (error) {
                console.error('Error checking login status:', error);
                showLoginForm("An error occurred while checking login status. Please try again.");
            }
        }

        function startPolling() {
            if (isPolling) return;  // Prevent multiple polling sessions
            isPolling = true;
            
            clearAllPolling();  // Clear any existing polling
            
            loginPolling = setInterval(async () => {
                try {
                    const response = await fetch('/login_status', {
                        credentials: 'same-origin'
                    });
                    const data = await response.json();
                    console.log("Login status:", data);
                    
                    if (data.ready) {
                        clearAllPolling();
                        window.location.replace('/');
                        return;
                    } else if (data.error) {
                        if (data.error.includes("DUO code") || data.duo_required) {
                            showWaitSection("Incorrect DUO code. Please try again on your phone");
                            if (!duoPolling) {
                                startDuoPolling();
                            }
                        } else {
                            showLoginForm(data.error);
                        }
                    } else if (data.duo_required) {
                        if (!isDuoRequired) {
                            isDuoRequired = true;
                            showWaitSection("Please complete DUO on your phone");
                            startDuoPolling();
                        } else if (data.duo_pending) {
                            showWaitSection("Incorrect DUO code. Please try again on your phone");
                            if (!duoPolling) {
                                startDuoPolling();
                            }
                        }
                    }
                } catch (error) {
                    console.error('Error polling login status:', error);
                    showLoginForm("An error occurred while checking login status. Please try again.");
                }
            }, 1000);
        }

        function startDuoPolling() {
            if (duoPolling) return;  // Prevent multiple DUO polling sessions
            
            // Clear any existing DUO polling first
            if (duoPolling) {
                clearInterval(duoPolling);
            }
            
            duoPolling = setInterval(async () => {
                try {
                    const response = await fetch('/get_duo_code');
                    const data = await response.json();
                    
                    if (data.success && data.code) {
                        console.log("Received DUO code in polling:", data.code);
                        duoCodeDiv.textContent = "DUO Code: " + data.code;
                        duoCodeDiv.style.display = "block";
                        // If we get a code, we can stop polling for new codes
                        clearInterval(duoPolling);
                        duoPolling = null;
                    }
                } catch (error) {
                    console.error('Error polling DUO code:', error);
                }
            }, 1000);
        }

        // Add a backup check for login status
        setInterval(checkLoginStatus, 5000);  // Reduced frequency of backup check
    </script>
</body>
</html>
""" 