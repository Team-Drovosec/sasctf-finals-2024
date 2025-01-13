// script.js

document.addEventListener('DOMContentLoaded', () => {
    // Variables to store the JWT token and username
    let token = localStorage.getItem('token') || null;
    let username = localStorage.getItem('username') || null;

    // DOM Elements
    const mainContent = document.getElementById('main-content');
    const navRegister = document.getElementById('nav-register');
    const navLogin = document.getElementById('nav-login');
    const navLogout = document.getElementById('nav-logout');

    // Event Listeners for Navigation Links
    navRegister.addEventListener('click', (e) => {
        e.preventDefault();
        showRegisterForm();
    });

    navLogin.addEventListener('click', (e) => {
        e.preventDefault();
        showLoginForm();
    });

    navLogout.addEventListener('click', (e) => {
        e.preventDefault();
        logoutUser();
    });

    // Check if token exists and is valid
    if (token) {
        updateNavForLoggedInUser();
        showDashboard();
    } else {
        showHomePage();
    }

    /** Function Definitions **/

    // Show Home Page with Stock Prices and Candlestick Graph
    function showHomePage() {
        mainContent.innerHTML = `
            <h2>Welcome to stocks++</h2>
            <section>
                <h3>Stock Prices</h3>
                <div id="stock-chart"></div>
            </section>
            <section>
                <h3>Users Trade History</h3>
                <table id="trade-history-table">
                    <thead>
                        <tr>
                            <th>Trade ID</th>
                            <th>Status</th>
                            <th>Net Profit</th>
                            <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Trade history will be populated here -->
                    </tbody>
                </table>
            </section>
        `;
        loadStockPricesChart('stock-chart');
        loadTradeHistory(false); // false indicates not to highlight user trades
    }

    // Show Dashboard
    function showDashboard() {
        // Fetch user info first
        fetch('/api/user/info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({}),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.stocks !== undefined && data.balance !== undefined) {
                    // Update the dashboard content with balance and stocks
                    mainContent.innerHTML = `
                    <div class="dashboard">
                        <h2>Welcome, ${username}</h2>
                        <p>Balance: $${data.balance}</p>
                        <p>Stocks: ${data.stocks}</p>
                        <section>
                            <h3>Submit a Trade</h3>
                            <form id="trade-form">
                                <input type="text" id="trade-name" placeholder="Strategy Name" required>
                                <textarea id="trade-description" placeholder="Strategy Description" required></textarea>
                                <textarea id="trade-strategy" placeholder="Strategy Code" required></textarea>
                                <button type="submit">Submit Trade</button>
                            </form>
                            <div id="trade-message"></div>
                        </section>
                        <section>
                            <h3>Your Trades</h3>
                            <table id="user-trades-table">
                                <thead>
                                    <tr>
                                        <th>Trade ID</th>
                                        <th>Status</th>
                                        <th>Net Profit</th>
                                        <th>Timestamp</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- User trades will be populated here -->
                                </tbody>
                            </table>
                        </section>
                        <section>
                            <h3>Trade History</h3>
                            <table id="trade-history-table">
                                <thead>
                                    <tr>
                                        <th>Trade ID</th>
                                        <th>Status</th>
                                        <th>Net Profit</th>
                                        <th>Timestamp</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- Trade history will be populated here -->
                                </tbody>
                            </table>
                        </section>
                        <section>
                            <h3>Stock Prices</h3>
                            <div id="stock-chart-dashboard"></div>
                        </section>
                    </div>
                `;

                    // Initialize the dashboard components
                    loadStockPricesChart('stock-chart-dashboard');
                    loadUserTrades();
                    loadTradeHistory(true); // true indicates to highlight user trades

                    // Event Listener for Trade Submission
                    const tradeForm = document.getElementById('trade-form');
                    tradeForm.addEventListener('submit', submitTrade);

                } else if (data.message) {
                    console.error('Error fetching user info:', data.message);
                    mainContent.innerHTML = `<p>Error fetching user info: ${data.message}</p>`;
                } else {
                    console.error('Unexpected response:', data);
                    mainContent.innerHTML = `<p>An unexpected error occurred while fetching user info.</p>`;
                }
            })
            .catch((error) => {
                console.error('Error fetching user info:', error);
                mainContent.innerHTML = `<p>An error occurred while fetching user info.</p>`;
            });
    }

    // Load and Update Stock Prices Chart using ApexCharts
    function loadStockPricesChart(elementId) {
        let chart;
        let dataSeries = [];
        const maxDataPoints = 100; // Adjust as needed

        // Fetch initial data and initialize the chart
        fetchInitialData();

        function fetchInitialData() {
            fetch('/api/stock_price', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ limit: maxDataPoints }),
            })
                .then((res) => res.json())
                .then((data) => {
                    if (data.prices && data.prices.length > 0) {
                        dataSeries = data.prices.map(price => ({
                            x: Number(price.time) / 1e6, // time in seconds
                            y: [
                                Number(price.open),
                                Number(price.high),
                                Number(price.low),
                                Number(price.close)
                            ]
                        })).sort((a, b) => a.x - b.x);

                        initializeChart();
                    } else {
                        console.warn('No initial price data available.');
                        initializeChart(); // Initialize with empty data
                    }
                })
                .catch((error) => {
                    console.error('Error fetching initial stock prices:', error);
                    initializeChart(); // Initialize with empty data
                });
        }

        function initializeChart() {
            const options = {
                series: [{
                    data: dataSeries
                }],
                chart: {
                    type: 'candlestick',
                    height: 350,
                    animations: {
                        enabled: false
                    },
                    toolbar: {
                        show: true,
                        tools: {
                            download: false
                        }
                    }
                },
                xaxis: {
                    type: 'datetime',
                    labels: {
                        datetimeUTC: false,
                        format: 'dd MMM HH:mm:ss'
                    }
                },
                yaxis: {
                    tooltip: {
                        enabled: true
                    }
                },
                noData: {
                    text: 'Loading...'
                }
            };

            chart = new ApexCharts(document.querySelector(`#${elementId}`), options);
            chart.render().then(() => {
                // Start fetching new data after chart initialization
                setInterval(fetchStockPrices, 1000);
            });
        }

        function fetchStockPrices() {
            fetch('/api/stock_price', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ limit: 5 }),
            })
                .then((res) => res.json())
                .then((data) => {
                    if (data.prices && data.prices.length > 0) {
                        const newDataPoint = {
                            x: Number(data.prices[0].time / 1e6), // time in seconds
                            y: [
                                Number(data.prices[0].open),
                                Number(data.prices[0].high),
                                Number(data.prices[0].low),
                                Number(data.prices[0].close)
                            ]
                        };

                        // Add new data point to the data series
                        dataSeries.push(newDataPoint);

                        // Maintain fixed dataset length
                        if (dataSeries.length > maxDataPoints) {
                            dataSeries.shift(); // Remove the oldest data point
                        }

                        // Update the chart
                        chart.updateSeries([{
                            data: dataSeries
                        }]);
                    } else {
                        console.warn('No new price data available.');
                    }
                })
                .catch((error) => {
                    console.error('Error fetching stock prices:', error);
                });
        }
    }

    // Load Trade History
    function loadTradeHistory(highlightUserTrades) {
        fetch('/api/trade_history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit: 100 }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.trades) {
                    const historyTableBody = document.querySelector('#trade-history-table tbody');
                    historyTableBody.innerHTML = '';
                    data.trades.forEach((trade) => {
                        const row = historyTableBody.insertRow();
                        row.insertCell(0).textContent = trade.trade_id;
                        row.insertCell(1).textContent = trade.status;
                        row.insertCell(2).textContent = trade.net_profit;
                        row.insertCell(3).textContent = new Date(Number(trade.timestamp) / 1e6).toLocaleString();

                        if (highlightUserTrades && userTrades.includes(trade.trade_id)) {
                            row.classList.add('highlight');
                        }
                    });
                }
            })
            .catch((error) => {
                console.error('Error fetching trade history:', error);
            });
    }

    let userTrades = [];

    // Load User Trades
    function loadUserTrades() {
        fetch('/api/user/info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({}),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.trades) {
                    userTrades = data.trades;
                    const tradesTableBody = document.querySelector('#user-trades-table tbody');
                    tradesTableBody.innerHTML = '';
                    data.trades.forEach((trade_id) => {
                        fetchTradeStatus(trade_id, tradesTableBody);
                    });

                    // Reload trade history to highlight user trades
                    loadTradeHistory(true);
                }
            })
            .catch((error) => {
                console.error('Error fetching user info:', error);
            });
    }

    // Fetch Individual Trade Status
    function fetchTradeStatus(trade_id, tableBody) {
        fetch('/api/user/trade/status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ trade_id }),
        })
            .then((res) => res.json())
            .then((tradeData) => {
                const row = tableBody.insertRow();
                row.insertCell(0).textContent = trade_id;
                row.insertCell(1).textContent = tradeData.status || 'N/A';
                row.insertCell(2).textContent = tradeData.net_profit || 'N/A';
                row.insertCell(3).textContent = new Date(Number(tradeData.timestamp) / 1e6).toLocaleString();
            })
            .catch((error) => {
                console.error('Error fetching trade status:', error);
            });
    }

    // Submit Trade
    function submitTrade(event) {
        event.preventDefault();
        const name = document.getElementById('trade-name').value.trim();
        const description = document.getElementById('trade-description').value.trim();
        const strategy = document.getElementById('trade-strategy').value.trim();
        const messageDiv = document.getElementById('trade-message');

        fetch('/api/user/trade/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({ name, description, strategy }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.trade_id) {
                    messageDiv.textContent = `Trade submitted successfully. Trade ID: ${data.trade_id}`;
                    loadUserTrades();
                    // Reload trade history to highlight user trades
                    setTimeout(loadUserTrades, 11000);
                } else if (data.message) {
                    messageDiv.textContent = data.message;
                } else {
                    messageDiv.textContent = 'An unexpected error occurred while submitting the trade.';
                }
            })
            .catch((error) => {
                messageDiv.textContent = 'An error occurred while submitting the trade.';
                console.error('Error:', error);
            });
    }

    // Show Registration Form
    function showRegisterForm() {
        mainContent.innerHTML = `
            <h2>Register</h2>
            <form id="register-form">
                <input type="text" id="register-username" placeholder="Username" required>
                <input type="password" id="register-password" placeholder="Password" required>
                <button type="submit">Register</button>
            </form>
            <div id="register-message"></div>
        `;

        const registerForm = document.getElementById('register-form');
        registerForm.addEventListener('submit', registerUser);
    }

    // Register User
    function registerUser(event) {
        event.preventDefault();
        const usernameInput = document.getElementById('register-username').value.trim();
        const password = document.getElementById('register-password').value.trim();
        const messageDiv = document.getElementById('register-message');

        fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: usernameInput, password }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.message && data.message.includes('registered successfully')) {
                    messageDiv.textContent = 'Registration successful. Please log in.';
                } else if (data.message) {
                    messageDiv.textContent = data.message;
                } else {
                    messageDiv.textContent = 'An unexpected error occurred.';
                }
            })
            .catch((error) => {
                messageDiv.textContent = 'An error occurred during registration.';
                console.error('Error:', error);
            });
    }

    // Show Login Form
    function showLoginForm() {
        mainContent.innerHTML = `
            <h2>Login</h2>
            <form id="login-form">
                <input type="text" id="login-username" placeholder="Username" required>
                <input type="password" id="login-password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <div id="login-message"></div>
        `;
        const loginForm = document.getElementById('login-form');
        loginForm.addEventListener('submit', loginUser);
    }

    // Login User
    function loginUser(event) {
        event.preventDefault();
        const usernameInput = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value.trim();
        const messageDiv = document.getElementById('login-message');

        fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: usernameInput, password }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.token) {
                    token = data.token;
                    username = usernameInput;
                    // Store token and username in localStorage
                    localStorage.setItem('token', token);
                    localStorage.setItem('username', username);
                    messageDiv.textContent = '';
                    updateNavForLoggedInUser();
                    showDashboard(data.balance, data.stocks);
                } else if (data.message) {
                    messageDiv.textContent = data.message;
                } else {
                    messageDiv.textContent = 'An unexpected error occurred during login.';
                }
            })
            .catch((error) => {
                messageDiv.textContent = 'An error occurred during login.';
                console.error('Error:', error);
            });
    }

    // Update Navigation Bar for Logged-in User
    function updateNavForLoggedInUser() {
        navRegister.style.display = 'none';
        navLogin.style.display = 'none';
        navLogout.style.display = 'inline-block';
    }

    // Logout User
    function logoutUser() {
        token = null;
        username = null;
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        navRegister.style.display = 'inline-block';
        navLogin.style.display = 'inline-block';
        navLogout.style.display = 'none';
        showHomePage();
    }

});
