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
  // ... login POST as before ...
  authToken = data.access_token;
  localStorage.setItem('twitter_clone_token', authToken);

  // load user & tweets
  await getCurrentUser();
  await fetchTweets();

  loginModal.style.display = 'none';
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
  const token = localStorage.getItem('twitter_clone_token');
  if (!token) {
    loginModal.style.display = 'block';
    return;
  }

  const resp = await fetch(`${API_BASE_URL}/accounts/me`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (resp.status === 401) {
    localStorage.removeItem('twitter_clone_token');
    authToken = null;
    loginModal.style.display = 'block';
    return;
  }
  if (!resp.ok) throw new Error(`Failed to fetch current user: ${resp.status}`);

  const data = await resp.json();
  currentUser = data;
  loginModal.style.display = 'none';
  renderUserProfile(currentUser);
}



// ----------------- TWEETS -----------------

async function fetchTweets() {
  const resp = await fetch(`${API_BASE_URL}/tweets/`, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    }
  });

  if (!resp.ok) {
    console.error('Failed to load tweets', resp.status);
    return;
  }
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
//
}

function renderUserSuggestions(users) {
  //
}


// ----------------- UTIL -----------------

function formatDate(d) {
  const diff = (Date.now() - d) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s`;
  if (diff < 3600) return `${Math.floor(diff/60)}m`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h`;
  return d.toLocaleDateString();
}
