const API_BASE_URL = window.location.origin + '/api';

// Token storage
let authToken = localStorage.getItem('twitter_clone_token');
let currentUser = null;

// DOM elements (to be assigned once DOM is ready)
let tweetFeed,
    tweetContent,
    postTweetBtn,
    sidebarUserInfo,
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
  console.log("Initializing app...");
  await checkApiEndpoints();
  
  authToken = localStorage.getItem('twitter_clone_token');
  
  if (authToken) {
    console.log("Token found, trying to get current user");
    try {
      await getCurrentUser();
      console.log("Fetching tweets...");
      await fetchTweets();
    } catch (error) {
      console.error("Error during init:", error);
      showAuthModal();
    }
  } else {
    console.log("No token found, showing auth modal");
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
  e.preventDefault();  // stop the native form submit

  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;

  // 1) Send the form-encoded login request
  const resp = await fetch(`${API_BASE_URL}/accounts/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username, password }).toString(),
  });

  // 2) If login failed, bail out
  if (!resp.ok) {
    alert(`Login failed (${resp.status})`);
    return;
  }

  // 3) Parse the JSON _into_ `data` before using it
  const data = await resp.json();

  // 4) Store the token
  authToken = data.access_token;
  localStorage.setItem('twitter_clone_token', authToken);

  // 5) Fetch the current user & tweets
  await getCurrentUser();
  await fetchTweets();

  // 6) Hide the login modal
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
  console.log("Getting current user...");
  const token = localStorage.getItem('twitter_clone_token');
  
  if (!token) {
    console.log("No token found, showing login modal");
    loginModal.style.display = 'flex';
    return;
  }

  try {
    console.log("Sending request to /api/accounts/me");
    const resp = await fetch(`${API_BASE_URL}/accounts/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    console.log(`/accounts/me response status: ${resp.status}`);
    
    if (resp.status === 401) {
      console.log("401 Unauthorized, clearing token");
      localStorage.removeItem('twitter_clone_token');
      authToken = null;
      loginModal.style.display = 'flex';
      return;
    }
    
    if (!resp.ok) {
      console.error(`Failed to fetch user: ${resp.status}`);
      throw new Error(`Failed to fetch user: ${resp.status}`);
    }

    const data = await resp.json();
    console.log("User data received:", data);
    currentUser = data;
    loginModal.style.display = 'none';
    renderUserProfile(currentUser);
  } catch (error) {
    console.error("Error getting current user:", error);
    localStorage.removeItem('twitter_clone_token');
    authToken = null;
    loginModal.style.display = 'flex';
  }
}

function renderUserProfile(user) {
  sidebarUserInfo.innerHTML = `
    <div class="user-info">
      <strong>${user.username}</strong>
      <button id="logout-btn">Logout</button>
    </div>
  `;
  // wire up the logout button
  document.getElementById('logout-btn').addEventListener('click', () => {
    if (confirm('Do you want to logout?')) logout();
  });
}


// ----------------- TWEETS -----------------

async function fetchTweets() {
  try {
    const resp = await fetch(`${API_BASE_URL}/tweets/`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });

    console.log(`Tweets response status: ${resp.status}`);
    
    if (!resp.ok) {
      console.error('Failed to load tweets', resp.status);
      if (resp.status === 401) {
        // Authentication error, show login
        showAuthModal();
      }
      return;
    }
    
    const tweets = await resp.json();
    console.log(`Received ${tweets.length} tweets`);
    renderTweets(tweets);
  } catch (error) {
    console.error('Error fetching tweets:', error);
  }
}


function renderTweets(tweets) {
  tweetFeed.innerHTML = "";
  tweets.forEach(t => {
    const author    = t.username;
    const timeAgo   = formatDate(new Date(t.created_at));
    const liked     = t.liked_by_user;
    const count     = t.like_count;

    const el = document.createElement("div");
    el.className = "tweet";
    el.innerHTML = `
      <div class="tweet-header">
        <strong>${author}</strong> · ${timeAgo}
      </div>
      <div class="tweet-body">${t.content}</div>
      <div class="tweet-actions">
        <button class="like-btn" data-id="${t.id}">
          ${liked ? "❤️" : "🤍"} <span class="like-count">${count}</span>
        </button>
      </div>
    `;
    tweetFeed.appendChild(el);
  });

  // wire up all like buttons
  document.querySelectorAll(".like-btn").forEach(btn => {
    btn.addEventListener("click", () => handleLike(btn));
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


// ----------------- DEBUG -----------------

// Debug function to check API endpoint availability
async function checkApiEndpoints() {
  console.log("Checking API endpoints...");
  
  try {
    const healthResp = await fetch(`${window.location.origin}/health`);
    console.log(`Health endpoint: ${healthResp.status}`);

  } catch (error) {
    console.error("Error checking endpoints:", error);
  }
}


// ----------------- UTIL -----------------

function formatDate(d) {
  const diff = (Date.now() - d) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s`;
  if (diff < 3600) return `${Math.floor(diff/60)}m`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h`;
  return d.toLocaleDateString();
}

// ----------------- LIKE -----------------

async function handleLike(button) {
  const tweetId = button.dataset.id;
  const liked   = button.textContent.includes("❤️");
  const method  = liked ? "DELETE" : "POST";
  const url     = `${API_BASE_URL}/tweets/${tweetId}/like`;

  const resp = await fetch(url, {
    method,
    headers: { 'Authorization': `Bearer ${authToken}` }
  });
  if (!resp.ok) {
    alert(`Error ${liked ? "unliking" : "liking"} tweet (${resp.status})`);
    return;
  }
  // refresh the tweets (or update this one tweet in place)
  await fetchTweets();
}

