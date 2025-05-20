document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'https://twitter-clone-v2.onrender.com';

    async function fetchUserSuggestions() {
        try {
            const response = await fetch(`${API_BASE_URL}/users/`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch user suggestions');
            }
            
            const users = await response.json();
            renderUserSuggestions(users.filter(user => user.id !== currentUser.id).slice(0, 3));
        } catch (error) {
            console.error('Error fetching user suggestions:', error);
        }
    }

    function renderUserSuggestions(users) {
        if (!users || users.length === 0) {
            followSuggestions.innerHTML = '<p>No user suggestions available.</p>';
            return;
        }
        
        followSuggestions.innerHTML = '';
        
        users.forEach(user => {
            const suggestionEl = document.createElement('div');
            suggestionEl.className = 'follow-suggestion';
            
            suggestionEl.innerHTML = `
                <img src="/api/placeholder/48/48" alt="${user.username}">
                <div class="follow-details">
                    <div class="follow-name">${user.username}</div>
                    <div class="follow-handle">@${user.username.toLowerCase()}</div>
                </div>
                <button class="follow-btn" data-user-id="${user.id}">Follow</button>
            `;
            
            // need to add event listener for follow button
            const followBtn = suggestionEl.querySelector('.follow-btn');
            followBtn.addEventListener('click', () => followUser(user.id, followBtn));
            
            followSuggestions.appendChild(suggestionEl);
        });
    }

    async function followUser(userId, followBtn) {
        if (!authToken) {
            showAuthModal();
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/users/${userId}/follow`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to follow user');
            }
            
            // Update UI
            followBtn.textContent = 'Following';
            followBtn.classList.add('following');
        } catch (error) {
            console.error('Error following user:', error);
        }
    }

    // Utility functions
    function formatDate(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) {
            return `${diffInSeconds}s`;
        }
        
        const diffInMinutes = Math.floor(diffInSeconds / 60);
        if (diffInMinutes < 60) {
            return `${diffInMinutes}m`;
        }
        
        const diffInHours = Math.floor(diffInMinutes / 60);
        if (diffInHours < 24) {
            return `${diffInHours}h`;
        }
        
        const diffInDays = Math.floor(diffInHours / 24);
        if (diffInDays < 7) {
            return `${diffInDays}d`;
        }
        
        // For older tweets, show actual date
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return `${months[date.getMonth()]} ${date.getDate()}`;
    }

    // Handle tweet textarea
    tweetContent.addEventListener('input', function() {
        if (this.value.trim().length > 0) {
            postTweetBtn.removeAttribute('disabled');
        } else {
            postTweetBtn.setAttribute('disabled', 'true');
        }
    });

    // Handle logout
    function logout() {
        localStorage.removeItem('twitter_clone_token');
        authToken = null;
        currentUser = null;
        showAuthModal();
    }

    // Add event listener to sidebar user info for logout
    sidebarUserInfo.addEventListener('click', () => {
        if (confirm('Do you want to logout?')) {
            logout();
        }
    });


    // Token storage
    let authToken = localStorage.getItem('twitter_clone_token');
    let currentUser = null;

    // DOM elements
    const tweetFeed = document.getElementById('tweet-feed');
    const tweetContent = document.getElementById('tweet-content');
    const postTweetBtn = document.getElementById('post-tweet-btn');
    const sidebarUserInfo = document.getElementById('sidebar-user-info');
    const followSuggestions = document.getElementById('follow-suggestions');
    const loginModal = document.getElementById('login-modal');
    const registerModal = document.getElementById('register-modal');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    // Event listeners
    document.addEventListener('DOMContentLoaded', initApp);
    postTweetBtn.addEventListener('click', postTweet);
    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        registerModal.style.display = 'none';
        loginModal.style.display = 'flex';
    });
    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        loginModal.style.display = 'none';
        registerModal.style.display = 'flex';
    });

    document.querySelectorAll('.close-modal').forEach(closeBtn => {
        closeBtn.addEventListener('click', () => {
            loginModal.style.display = 'none';
            registerModal.style.display = 'none';
        });
    });

    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);

    // Initialize application
    async function initApp() {
        if (authToken) {
            try {
                await getCurrentUser();
                fetchTweets();
                fetchUserSuggestions();
            } catch (error) {
                console.error('Error initializing app:', error);
                showAuthModal();
            }
        } else {
            showAuthModal();
        }
    }

    // Authentication functions
    function showAuthModal() {
        loginModal.style.display = 'flex';
    }

    async function handleLogin(e) {
        e.preventDefault();
        
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        
        try {
            const response = await fetch(`${API_BASE_URL}/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
            });
            
            if (!response.ok) {
                throw new Error('Login failed');
            }
            
            const data = await response.json();
            authToken = data.access_token;
            localStorage.setItem('twitter_clone_token', authToken);
            
            loginModal.style.display = 'none';
            await getCurrentUser();
            fetchTweets();
            fetchUserSuggestions();
            
        } catch (error) {
            alert('Login failed. Please check your credentials and try again.');
            console.error('Login error:', error);
        }
    }

    async function handleRegister(e) {
        e.preventDefault();
        
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        
        try {
            const response = await fetch(`${API_BASE_URL}/users/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username,
                    email,
                    password
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Registration failed');
            }
            
            // Auto login after successful registration
            const loginResponse = await fetch(`${API_BASE_URL}/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
            });
            
            if (!loginResponse.ok) {
                throw new Error('Auto login failed');
            }
            
            const loginData = await loginResponse.json();
            authToken = loginData.access_token;
            localStorage.setItem('twitter_clone_token', authToken);
            
            registerModal.style.display = 'none';
            await getCurrentUser();
            fetchTweets();
            fetchUserSuggestions();
            
        } catch (error) {
            alert(`Registration failed: ${error.message}`);
            console.error('Registration error:', error);
        }
    }

    async function getCurrentUser() {
        try {
            const response = await fetch(`${API_BASE_URL}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to get current user');
            }
            
            currentUser = await response.json();
            updateUserInfo();
            return currentUser;
        } catch (error) {
            console.error('Error fetching current user:', error);
            localStorage.removeItem('twitter_clone_token');
            authToken = null;
            throw error;
        }
    }

    function updateUserInfo() {
        if (!currentUser) return;
        
        sidebarUserInfo.innerHTML = `
            <img src="/api/placeholder/40/40" alt="${currentUser.username}">
            <div class="user-details">
                <span>${currentUser.username}</span>
                <span>@${currentUser.username.toLowerCase()}</span>
            </div>
        `;
    }

    // Tweet functions
    async function fetchTweets() {
        try {
            const response = await fetch(`${API_BASE_URL}/tweets/`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch tweets');
            }
            
            const tweets = await response.json();
            renderTweets(tweets);
        } catch (error) {
            console.error('Error fetching tweets:', error);
            tweetFeed.innerHTML = '<div class="error-message">Error loading tweets. Please try again later.</div>';
        }
    }

    function renderTweets(tweets) {
        if (!tweets || tweets.length === 0) {
            tweetFeed.innerHTML = '<div class="no-tweets">No tweets yet. Be the first to tweet!</div>';
            return;
        }
        
        tweetFeed.innerHTML = '';
        
        tweets.forEach(tweet => {
            const tweetEl = document.createElement('div');
            tweetEl.className = 'tweet';
            
            // Format the date
            const tweetDate = new Date(tweet.created_at);
            const formattedDate = formatDate(tweetDate);
            
            tweetEl.innerHTML = `
                <div class="user-avatar">
                    <img src="/api/placeholder/48/48" alt="${tweet.user.username}">
                </div>
                <div class="tweet-content">
                    <div class="tweet-header">
                        <a href="#" class="tweet-username">${tweet.user.username}</a>
                        <span class="tweet-handle">@${tweet.user.username.toLowerCase()}</span>
                        <span class="tweet-time"> · ${formattedDate}</span>
                    </div>
                    <div class="tweet-body">
                        ${tweet.content}
                    </div>
                    <div class="tweet-actions-menu">
                        <div class="tweet-action reply-action">
                            <i class="far fa-comment"></i> <span>0</span>
                        </div>
                        <div class="tweet-action retweet-action">
                            <i class="fas fa-retweet"></i> <span>0</span>
                        </div>
                        <div class="tweet-action like-action" data-tweet-id="${tweet.id}">
                            <i class="far fa-heart"></i> <span>${tweet.likes || 0}</span>
                        </div>
                    </div>
                </div>
            `;
            
            // Add event listener for the like button
            const likeAction = tweetEl.querySelector('.like-action');
            likeAction.addEventListener('click', () => likeTweet(tweet.id, likeAction));
            
            tweetFeed.appendChild(tweetEl);
        });
        
        // Add event listeners to all like buttons
        document.querySelectorAll('.like-action').forEach(likeBtn => {
            const tweetId = likeBtn.getAttribute('data-tweet-id');
            likeBtn.addEventListener('click', () => likeTweet(tweetId, likeBtn));
        });
    }

    async function postTweet() {
        if (!authToken) {
            showAuthModal();
            return;
        }
        
        const content = tweetContent.value.trim();
        if (!content) return;
        
        try {
            const response = await fetch(`${API_BASE_URL}/tweets/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({ content })
            });
            
            if (!response.ok) {
                throw new Error('Failed to post tweet');
            }
            
            // Clear the input field
            tweetContent.value = '';
            
            // Refresh the tweet feed
            fetchTweets();
        } catch (error) {
            console.error('Error posting tweet:', error);
            alert('Failed to post tweet. Please try again.');
        }
    }

    async function likeTweet(tweetId, likeElement) {
        if (!authToken) {
            showAuthModal();
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/tweets/${tweetId}/like`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to like tweet');
            }
            
            const data = await response.json();
            
            // Update the UI
            const likeIcon = likeElement.querySelector('i');
            const likeCount = likeElement.querySelector('span');
            
            if (data.liked) {
                likeIcon.className = 'fas fa-heart';
                likeCount.textContent = parseInt(likeCount.textContent) + 1;
            } else {
                likeIcon.className = 'far fa-heart';
                likeCount.textContent = parseInt(likeCount.textContent) - 1;
            }
        } catch (error) {
            console.error('Error liking tweet:', error);
        }
    }
});
  

