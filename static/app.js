const API_BASE_URL = window.location.origin + '/api';

// Token storage
let authToken = 'simplified_token'; // Always use a static token
let currentUser = { username: 'default_user' }; // Default user

// DOM elements (to be assigned once DOM is ready)
let tweetFeed,
    tweetContent,
    postTweetBtn,
    sidebarUserInfo;

document.addEventListener('DOMContentLoaded', () => {
  // cache DOM nodes
  tweetFeed         = document.getElementById('tweet-feed');
  tweetContent      = document.getElementById('tweet-content');
  postTweetBtn      = document.getElementById('post-tweet-btn');
  sidebarUserInfo   = document.getElementById('sidebar-user-info');

  // enable/disable post button based on textarea
  tweetContent.addEventListener('input', () => {
    if (tweetContent.value.trim()) postTweetBtn.removeAttribute('disabled');
    else postTweetBtn.setAttribute('disabled', 'true');
  });

  // post tweet
  postTweetBtn.addEventListener('click', postTweet);

  // Initialize the app - no need for login flow
  initApp();
  
  // Show the user profile immediately
  renderUserProfile(currentUser);
});


// ----------------- CORE APP FLOW -----------------

async function initApp() {
  console.log("Initializing app...");
  await fetchTweets();
}


// ----------------- USER INFO -----------------
function renderUserProfile(user) {
  sidebarUserInfo.innerHTML = `
    <div class="user-info">
      <strong>${user.username}</strong>
    </div>
  `;
}


// ----------------- TWEETS -----------------

async function fetchTweets() {
  try {
    console.log("Fetching tweets...");
    const resp = await fetch(`${API_BASE_URL}/tweets`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });

    console.log(`Tweets response status: ${resp.status}`);
    
    if (!resp.ok) {
      console.error('Failed to load tweets', resp.status);
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
  
  try {
    const resp = await fetch(`${API_BASE_URL}/tweets/`, {
      method:  'POST',
      headers: {
        'Content-Type':  'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({content})
    });
    
    if (!resp.ok) {
      console.error('Failed to post tweet', resp.status);
      return;
    }
    
    tweetContent.value = '';
    await fetchTweets();
  } catch (error) {
    console.error('Error posting tweet:', error);
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
  const liked   = true;
  const method  = liked ? "DELETE" : "POST";
  const url     = `${API_BASE_URL}/tweets/${tweetId}/like`;

  try {
    const resp = await fetch(url, {
      method,
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    
    if (!resp.ok) {
      console.error(`Error ${liked ? "unliking" : "liking"} tweet (${resp.status})`);
      return;
    }
    
    // refresh the tweets
    await fetchTweets();
  } catch (error) {
    console.error(`Error ${liked ? "unliking" : "liking"} tweet:`, error);
  }
}