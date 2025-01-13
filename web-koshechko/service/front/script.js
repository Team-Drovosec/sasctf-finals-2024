const BASE_URL = '';
let sessionToken = localStorage.getItem('sessionToken') || '';
let username = localStorage.getItem('username') || '';

function calcHash(tx) {
    const e = BigInt(65537);
    const n = BigInt('28757011453696365537010943219256697514126823462382199267523807215656057927126938852532938273735278647439093723114415999527098723727976475936319155015427799997213003664499422631017367287332875193524677851189982495235297707215042033048262623778358190536462998154798211571895963976626619781876160386784876909081999350085274414471035318193235136484576917339366720845318413892930365483764728962401235587394114713997688753422002084296070311024847072828816942070893651675293360209965132732838522510660772870550822829094375086110109463351493357171504313446493634012225805624774006426508038811853036507008224435127381274346463');
    let p = BigInt(1);
    for (let i = 0; i < tx.length; i++) {
        p *= BigInt(tx.charCodeAt(i));
    }
    return (p ** e % n).toString();
}

function apiFetch(url, options = {}) {
    return fetch(url, options).then(response => {
        if (response.status === 300) {
            sessionToken = '';
            username = '';
            localStorage.removeItem('sessionToken');
            localStorage.removeItem('username');
            alert('Session expired');
            navigate('');
            throw new Error('Session expired');
        }
        return response;
    });
}

function navigate(hash) {
    window.location.hash = hash;
    router();
}

function router() {
    const app = document.getElementById('app');
    const route = window.location.hash.substring(1);
    app.innerHTML = '';

    const isLoggedIn = sessionToken !== '';

    if (route === '' || route === '/') {
        if (isLoggedIn) {
            navigate('home');
            return;
        } else {
            renderHome();
            return;
        }
    }

    if (!isLoggedIn && (['dashboard', 'create', 'top_users', 'top_koshechko', 'home'].includes(route) || route.startsWith('view_koshechko') || route.startsWith('view_user'))) {
        navigate('login');
        return;
    }

    if (isLoggedIn && ['login', 'register'].includes(route)) {
        navigate('home');
        return;
    }

    if (route === 'register') {
        renderRegister();
    } else if (route === 'login') {
        renderLogin();
    } else if (route === 'home') {
        renderHome();
    } else if (route === 'dashboard') {
        renderDashboard();
    } else if (route === 'create') {
        renderCreateKoshechko();
    } else if (route.startsWith('view_koshechko')) {
        renderViewKoshechko(route.substring('view_koshechko/'.length));
    } else if (route.startsWith('view_user')) {
        renderViewUser(route.substring('view_user/'.length));
    } else if (route === 'top_users') {
        renderTopUsers();
    } else if (route === 'top_koshechko') {
        renderTopKoshechko();
    } else {
        renderHome();
    }
}

function renderNavbar() {
    const isLoggedIn = sessionToken !== '';
    return `
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
      <span class="navbar-brand" onclick="navigate('')">Koshechko</span>
      <div class="collapse navbar-collapse">
        <ul class="navbar-nav me-auto">
          ${isLoggedIn ? `
          <li class="nav-item"><span class="nav-link" onclick="navigate('home')">Home</span></li>
          <li class="nav-item"><span class="nav-link" onclick="navigate('dashboard')">Dashboard</span></li>
          <li class="nav-item"><span class="nav-link" onclick="navigate('top_users')">Top Users</span></li>
          <li class="nav-item"><span class="nav-link" onclick="navigate('top_koshechko')">Top Koshechko</span></li>
          <li class="nav-item"><span class="nav-link" onclick="logout()">Logout</span></li>
          ` : `
          <li class="nav-item"><span class="nav-link" onclick="navigate('login')">Login</span></li>
          <li class="nav-item"><span class="nav-link" onclick="navigate('register')">Register</span></li>
          `}
        </ul>
      </div>
    </nav>`;
}

function renderHome() {
    const isLoggedIn = sessionToken !== '';
    if (isLoggedIn) {
        app.innerHTML = `
        ${renderNavbar()}
        <h2>Home</h2>
        <div id="user_info"></div>`;
        loadUserInfo(username, 'user_info');
    } else {
        app.innerHTML = `
        ${renderNavbar()}
        <div class="jumbotron">
          <h1 class="display-4">Welcome to Koshechko Service</h1>
          <p class="lead">Manage your Koshechko entities efficiently.</p>
          <hr class="my-4">
          <p>Please login or register to continue.</p>
          <button class="btn btn-primary btn-lg" onclick="navigate('login')">Login</button>
          <button class="btn btn-secondary btn-lg" onclick="navigate('register')">Register</button>
        </div>`;
    }
}

function renderRegister() {
    app.innerHTML = `
    ${renderNavbar()}
    <h2>Register</h2>
    <form onsubmit="register(event)">
      <div class="mb-3">
        <label class="form-label">Username</label>
        <input type="text" class="form-control" id="reg_username" required>
      </div>
      <div class="mb-3">
        <label class="form-label">Password</label>
        <input type="password" class="form-control" id="reg_password" required>
      </div>
      <div class="mb-3">
        <label class="form-label">Description</label>
        <textarea class="form-control" id="reg_desc"></textarea>
      </div>
      <button type="submit" class="btn btn-primary">Register</button>
    </form>`;
}

function renderLogin() {
    app.innerHTML = `
    ${renderNavbar()}
    <h2>Login</h2>
    <form onsubmit="identify(event)">
      <div class="mb-3">
        <label class="form-label">Username</label>
        <input type="text" class="form-control" id="login_username" required>
      </div>
      <button type="submit" class="btn btn-primary">Next</button>
    </form>`;
}

function renderPasswordStep() {
    app.innerHTML = `
    ${renderNavbar()}
    <h2>Login - Step 2</h2>
    <form onsubmit="authenticate(event)">
      <div class="mb-3">
        <label class="form-label">Password</label>
        <input type="password" class="form-control" id="login_password" required>
      </div>
      <button type="submit" class="btn btn-primary">Login</button>
    </form>`;
}

function renderDashboard() {
    app.innerHTML = `
    ${renderNavbar()}
    <h2>Dashboard</h2>
    <button class="btn btn-success mb-3" onclick="navigate('create')">Create Koshechko</button>
    <div id="koshechko_list"></div>`;
    loadKoshechkoList();
}

function renderCreateKoshechko() {
    app.innerHTML = `
    ${renderNavbar()}
    <h2>Create Koshechko</h2>
    <form onsubmit="createKoshechko(event)">
      <div class="mb-3">
        <label class="form-label">Koshechko Name</label>
        <input type="text" class="form-control" id="kosh_name" required>
      </div>
      <div class="mb-3">
        <label class="form-label">Description</label>
        <textarea class="form-control" id="kosh_text" required></textarea>
      </div>
      <div class="mb-3">
        <label class="form-label">Share With (comma-separated usernames)</label>
        <input type="text" class="form-control" id="kosh_shared_with">
      </div>
      <button type="submit" class="btn btn-primary">Create</button>
    </form>`;
}

function renderViewKoshechko(name) {
    app.innerHTML = `
    ${renderNavbar()}
    <h2>Koshechko: ${name}</h2>
    <div id="koshechko_details"></div>`;
    loadKoshechkoDetails(name);
}

function renderViewUser(name) {
    app.innerHTML = `
    ${renderNavbar()}
    <h2>User: ${name}</h2>
    <div id="user_details"></div>`;
    loadUserInfo(name, 'user_details');
}

function renderTopUsers() {
    app.innerHTML = `
    ${renderNavbar()}
    <h2>Top Users</h2>
    <ul class="list-group" id="top_users_list"></ul>`;
    loadTopUsers();
}

function renderTopKoshechko() {
    app.innerHTML = `
    ${renderNavbar()}
    <h2>Top Koshechko</h2>
    <ul class="list-group" id="top_koshechko_list"></ul>`;
    loadTopKoshechko();
}

function register(event) {
    event.preventDefault();
    const username = document.getElementById('reg_username').value;
    const password = document.getElementById('reg_password').value;
    const desc = document.getElementById('reg_desc').value;

    apiFetch(`${BASE_URL}/api/register`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password, desc})
    })
    .then(response => {
        if (response.status === 200) {
            alert('Registration successful');
            navigate('login');
        } else {
            alert('Registration failed');
        }
    });
}

let loginUsername = '';
let sessionTokenTmp = '';
let loginToken = '';

function identify(event) {
    event.preventDefault();
    loginUsername = document.getElementById('login_username').value;

    apiFetch(`${BASE_URL}/api/identify`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: loginUsername})
    })
    .then(response => response.json())
    .then(data => {
        if (data.token && data.session) {
            loginToken = data.token;
            sessionTokenTmp = data.session;
            renderPasswordStep();
        } else {
            alert('Identification failed');
        }
    });
}

function authenticate(event) {
    event.preventDefault();
    const password = document.getElementById('login_password').value;
    const hashedPassword = calcHash(password + loginToken);

    apiFetch(`${BASE_URL}/api/login`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'token': sessionTokenTmp},
        body: JSON.stringify({password: hashedPassword})
    })
    .then(response => {
        if (response.status === 200) {
            sessionToken = sessionTokenTmp;
            username = loginUsername;
            localStorage.setItem('sessionToken', sessionToken);
            localStorage.setItem('username', username);
            alert('Login successful');
            navigate('home');
        } else {
            alert('Authentication failed');
        }
    });
}

function createKoshechko(event) {
    event.preventDefault();
    const name = document.getElementById('kosh_name').value;
    const text = document.getElementById('kosh_text').value;
    const shared_with = document.getElementById('kosh_shared_with').value.split(',').map(s => s.trim()).filter(s => s);

    apiFetch(`${BASE_URL}/api/koshechko/create`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'token': sessionToken},
        body: JSON.stringify({name, text, shared_with})
    })
    .then(response => {
        if (response.status === 200) {
            alert('Koshechko created');
            navigate('dashboard');
        } else {
            alert('Failed to create Koshechko');
        }
    });
}

function loadKoshechkoList() {
    apiFetch(`${BASE_URL}/api/top/koshechko`, {
        headers: {'token': sessionToken}
    })
    .then(response => response.json())
    .then(data => {
        const list = document.getElementById('koshechko_list');
        list.innerHTML = '';
        data.top.forEach(kosh => {
            const card = document.createElement('div');
            card.className = 'card koshechko-card';
            card.innerHTML = `
            <div class="card-body">
                <h5 class="card-title">${kosh.name}</h5>
                <p class="card-text">Rank: ${kosh.rank}, Score: ${kosh.score}</p>
                <button class="btn btn-primary" onclick="navigate('view_koshechko/${encodeURIComponent(kosh.name)}')">View</button>
            </div>`;
            list.appendChild(card);
        });
    });
}

function loadKoshechkoDetails(name) {
    apiFetch(`${BASE_URL}/api/koshechko/view`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'token': sessionToken},
        body: JSON.stringify({name})
    })
    .then(response => response.json())
    .then(data => {
        const details = document.getElementById('koshechko_details');
        details.innerHTML = `
        <p>Owner: <span onclick="navigate('view_user/${encodeURIComponent(data.owner)}')" style="cursor:pointer;color:blue;text-decoration:underline;">${data.owner}</span></p>
        <p>Text: ${data.text}</p>
        <p>Rank: ${data.rank}</p>
        <p>Score: ${data.score}</p>
        <p>Shared With: ${data.shared_with.join(', ')}</p>`;
        if (data.owner === username) {
            details.innerHTML += `
            <button class="btn btn-danger" onclick="deleteKoshechko('${encodeURIComponent(name)}')">Delete</button>`;
        }
    });
}

function deleteKoshechko(name) {
    if (confirm('Are you sure you want to delete this Koshechko?')) {
        apiFetch(`${BASE_URL}/api/koshechko/delete`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'token': sessionToken},
            body: JSON.stringify({name: decodeURIComponent(name)})
        })
        .then(response => {
            if (response.status === 200) {
                alert('Koshechko deleted');
                navigate('dashboard');
            } else {
                alert('Failed to delete Koshechko');
            }
        });
    }
}

function loadTopUsers() {
    apiFetch(`${BASE_URL}/api/top/users`, {
        headers: {'token': sessionToken}
    })
    .then(response => response.json())
    .then(data => {
        const list = document.getElementById('top_users_list');
        list.innerHTML = '';
        data.top.forEach(user => {
            const item = document.createElement('li');
            item.className = 'list-group-item';
            item.innerHTML = `
                <span onclick="navigate('view_user/${encodeURIComponent(user.username)}')" style="cursor:pointer;color:blue;text-decoration:underline;">
                    Username: ${user.username}, Rank: ${user.rank}, Score: ${user.score}
                </span>`;
            list.appendChild(item);
        });
    });
}

function loadTopKoshechko() {
    apiFetch(`${BASE_URL}/api/top/koshechko`, {
        headers: {'token': sessionToken}
    })
    .then(response => response.json())
    .then(data => {
        const list = document.getElementById('top_koshechko_list');
        list.innerHTML = '';
        data.top.forEach(kosh => {
            const item = document.createElement('li');
            item.className = 'list-group-item';
            item.innerHTML = `
                <span onclick="navigate('view_koshechko/${encodeURIComponent(kosh.name)}')" style="cursor:pointer;color:blue;text-decoration:underline;">
                    Name: ${kosh.name}, Rank: ${kosh.rank}, Score: ${kosh.score}
                </span>`;
            list.appendChild(item);
        });
    });
}

function loadUserInfo(name, elementId) {
    apiFetch(`${BASE_URL}/api/user/view`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'token': sessionToken},
        body: JSON.stringify({name})
    })
    .then(response => response.json())
    .then(data => {
        const userInfo = document.getElementById(elementId);
        userInfo.innerHTML = `
        <p>Username: ${data.name}</p>
        <p>Description: ${data.text}</p>
        <p>Rank: ${data.rank}</p>`;
        if (data.name === username) {
            userInfo.innerHTML += `
            <button class="btn btn-danger" onclick="deleteUser()">Delete Account</button>`;
        }
    });
}

function deleteUser() {
    if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
        apiFetch(`${BASE_URL}/api/user/delete`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'token': sessionToken},
            body: JSON.stringify({})
        })
        .then(response => {
            if (response.status === 200) {
                alert('Account deleted');
                sessionToken = '';
                username = '';
                localStorage.removeItem('sessionToken');
                localStorage.removeItem('username');
                navigate('');
            } else {
                alert('Failed to delete account');
            }
        });
    }
}

function logout() {
    sessionToken = '';
    username = '';
    localStorage.removeItem('sessionToken');
    localStorage.removeItem('username');
    alert('Logged out');
    navigate('');
}

window.addEventListener('load', router);
window.addEventListener('hashchange', router);
