const API_BASE_URL = window.location.origin + '/api';

// Token storage
let authToken = localStorage.getItem('twitter_clone_token');
let currentUser = null;

// DOM elements (to be assigned once DOM is ready)
let tweetFeed,
    tweetContent,
    postTweetBtn,
    sidebarUserInfo,
    followSuggestions,
    loginModal,
    registerModal,
    loginForm,
    registerForm;

document.addEventListener('DOMContentLoaded', () => {
  // cache DOM nodes
  tweetFeed         = document.getElementById('tweet-feed');
  tweetContent      = document.getElementById('tweet-content');
  postTweetBtn      = document.getElementById('post-tweet-btn');
  sidebarUserInfo   = document.getElementById('sidebar-user-info');
  followSuggestions = document.getElementById('follow-suggestions');
  loginModal        = document.getElementById('login-modal');
  registerModal     = document.getElementById('register-modal');
  loginForm         = document.getElementById('login-form');
  registerForm      = document.getElementById('register-form');

  // enable/disable post button based on textarea
  tweetContent.addEventListener('input', () => {
    if (tweetContent.value.trim()) postTweetBtn.removeAttribute('disabled');
    else postTweetBtn.setAttribute('disabled', 'true');
  });

  // post tweet
  postTweetBtn.addEventListener('click', postTweet);

  // sidebar logout
  sidebarUserInfo.addEventListener('click', () => {
    if (confirm('Do you want to logout?')) {
      logout();
    }
  });

  // auth modals
  document.getElementById('show-login').addEventListener('click', e => {
    e.preventDefault();
    registerModal.style.display = 'none';
    loginModal.style.display    = 'flex';
  });
  document.getElementById('show-register').addEventListener('click', e => {
    e.preventDefault();
    loginModal.style.display    = 'none';
    registerModal.style.display = 'flex';
  });
  document.querySelectorAll('.close-modal').forEach(btn =>
    btn.addEventListener('click', () => {
      loginModal.style.display    = 'none';
      registerModal.style.display = 'none';
    })
  );

  // forms
  loginForm.addEventListener('submit', handleLogin);
  registerForm.addEventListener('submit', handleRegister);

  // kick things off
  initApp();
});


// ----------------- CORE APP FLOW -----------------

async function initApp() {
  if (authToken) {
    try {
      await getCurrentUser();
      fetchTweets();
      fetchUserSuggestions();
    } catch {
      showAuthModal();
    }
  } else {
    showAuthModal();
  }
}

function showAuthModal() {
  loginModal.style.display = 'flex';
}

function logout() {
  localStorage.removeItem('twitter_clone_token');
  authToken   = null;
  currentUser = null;
  showAuthModal();
}


// ----------------- AUTH -----------------

async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;

  const resp = await fetch(`${API_BASE_URL}/accounts/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      username: username,
      password: password
    }).toString(),
  });

  if (!resp.ok) {
    alert('Login failed');
    return;
  }
  const data = await resp.json();
  authToken = data.access_token;
  localStorage.setItem('twitter_clone_token', authToken);

  loginModal.style.display = 'none';
  await getCurrentUser();
  fetchTweets();
  fetchUserSuggestions();
}

async function handleRegister(e) {
  e.preventDefault();
  const username = document.getElementById('register-username').value;
  const email    = document.getElementById('register-email').value;
  const password = document.getElementById('register-password').value;

  const resp = await fetch(`${API_BASE_URL}/accounts/`, {
    method:  'POST',
    headers: {'Content-Type': 'application/json'},
    body:    JSON.stringify({username, email, password})
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    alert(`Registration failed: ${err.detail || resp.statusText}`);
    return;
  }

  // auto-login
  await handleLogin(new Event('submit'));
}


// ----------------- USER INFO -----------------

async function getCurrentUser() {
  const resp = await fetch(`${API_BASE_URL}/accounts/me`, {
    headers: {'Authorization': `Bearer ${authToken}`}
  });
  if (!resp.ok) throw new Error();
  currentUser = await resp.json();
  sidebarUserInfo.innerHTML = `
    <img src="/api/placeholder/40/40" alt="${currentUser.username}">
    <div class="user-details">
      <span>${currentUser.username}</span>
      <span>@${currentUser.username.toLowerCase()}</span>
    </div>
  `;
}


// ----------------- TWEETS -----------------

async function fetchTweets() {
  const resp = await fetch(`${API_BASE_URL}/tweets/`, {
    headers: {'Authorization': `Bearer ${authToken}`}
  });
  if (!resp.ok) throw new Error();
  const tweets = await resp.json();
  renderTweets(tweets);
}

function renderTweets(tweets) {
  if (!tweets.length) {
    tweetFeed.innerHTML = '<div class="no-tweets">No tweets yet.</div>';
    return;
  }
  tweetFeed.innerHTML = '';
  tweets.forEach(t => {
    const el = document.createElement('div');
    el.className = 'tweet';
    el.innerHTML = `
      <div class="tweet-header">
        <strong>${t.user.username}</strong> @${t.user.username.toLowerCase()} · ${formatDate(new Date(t.created_at))}
      </div>
      <div class="tweet-body">${t.content}</div>
    `;
    tweetFeed.appendChild(el);
  });
}

async function postTweet() {
  const content = tweetContent.value.trim();
  if (!content) return;
  const resp = await fetch(`${API_BASE_URL}/tweets/`, {
    method:  'POST',
    headers: {
      'Content-Type':  'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({content})
  });
  if (!resp.ok) {
    alert('Failed to post tweet');
    return;
  }
  tweetContent.value = '';
  fetchTweets();
}


// ----------------- SUGGESTIONS -----------------

async function fetchUserSuggestions() {
  const resp = await fetch(`${API_BASE_URL}/accounts/`, {
    headers: {'Authorization': `Bearer ${authToken}`}
  });
  if (!resp.ok) return;
  const users = await resp.json();
  renderUserSuggestions(users.filter(u => u.id !== currentUser.id).slice(0, 3));
}

function renderUserSuggestions(users) {
  followSuggestions.innerHTML = users.length
    ? users.map(u => `
      <div class="follow-suggestion">
        <span>${u.username}</span>
        <button data-user-id="${u.id}">Follow</button>
      </div>
    `).join('')
    : '<p>No suggestions</p>';
}


// ----------------- UTIL -----------------

function formatDate(d) {
  const diff = (Date.now() - d) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s`;
  if (diff < 3600) return `${Math.floor(diff/60)}m`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h`;
  return d.toLocaleDateString();
}
