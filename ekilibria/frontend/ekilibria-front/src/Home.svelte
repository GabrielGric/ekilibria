<script>
  import Icon from 'svelte-awesome/components/Icon.svelte';
  import { google, windows } from 'svelte-awesome/icons';
  import { userSession } from './lib/userSession.js';
  import { fade,draw } from 'svelte/transition'
  import { onMount } from 'svelte';
  import { msalInstance } from '../auth.js';
  import { Circle2 } from 'svelte-loading-spinners';

  let loading = false;
  let animate = false
  let loginInProgress = false;

  // Button functions

  async function googleLogin() {
    userSession.set({
        user_email: "hola",
        login_method: 'google'
      });
    window.location.href = '/auth/google';
  }

  async function microsoftLogin() {
    // Loading spinner and hide buttons
    loading = true;
    const loginButtons = document.getElementById('login-buttons');
    if (loginButtons) {
      loginButtons.style.display = 'none';
    }

    // Check if login is already in progress
    if (loginInProgress) return;
    loginInProgress = true;
    try {
      // Initialize MSAL instance and login
      await msalInstance.initialize();
      const response = await msalInstance.loginPopup({
        prompt: "select_account",
        scopes: [
          "User.Read",
          "Mail.Read",
          "Calendars.Read",
          "Calendars.ReadBasic",
          "Files.Read",
          "MailboxSettings.Read"
        ]
      });

      userSession.set({
        user_email: response.account.username,
        login_method: 'microsoft',
      });

      // Send data to the server
      const serverResponse = await fetch('/auth/microsoft', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_email: response.account.username,
          login_method: 'microsoft',
          token: response.accessToken,
          expires_on: response.expiresOn
        })
      });
      
      // Check if the server response is ok
      if(serverResponse.ok) {
        const data = await serverResponse.json();
        userSession.set({
          user_email: data.user_email,
          login_method: 'microsoft'
        });
        // redirect to next page
        window.location.href = '/#/show';
      } else {
        console.error("Failed to authenticate with the server");
      }

    } catch (error) {
      console.error(error);
    } finally {
      loginInProgress = false;
    }

    // Hide loading spinner and show buttons
    loading = false;
    if (loginButtons) {
      loginButtons.style.display = 'block';
      loading = false;
    }
  }

  // On mount, animate the buttons
  onMount(() => {
    animate = true;
    const loginButtons = document.getElementById('login-buttons');
    if (loginButtons) {
      loginButtons.style.display = 'block';
    }
  });
</script>

<div class="container">
  {#if animate}
    <h1 in:fade={{ duration: 500 }}>Ekilibria</h1>
    <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
      <circle
        cx="40"
        cy="40"
        r="36"
        stroke="#F19143"
        stroke-width="6"
        fill="#fff"
        in:draw={{ duration: 900 }}
      />
      <path
        d="M20 60 Q40 20 60 60"
        stroke="#F19143"
        stroke-width="5"
        fill="none"
        in:draw={{ duration: 1200 }}
      />
      <circle
        cx="40"
        cy="40"
        r="8"
        fill="#F19143"
        in:draw={{ duration: 700 }}
      />
      <text
        x="40"
        y="75"
        text-anchor="middle"
        font-size="16"
        fill="#F19143"
        font-family="Arial"
        font-weight="bold"
        opacity="0"
        in:fade={{ duration: 600, delay: 1200 }}
      >EKI</text>
    </svg>
    <p in:fade={{ duration: 500 }}>Please log in to continue</p>
  {/if}
  {#if loading}
      <div id="loading" style="display: flex; justify-content: center; align-items: center; width: 100%; height: 100vh;">
          <Circle2 size="200" colorOuter="#2E4052" colorCenter="#2E4052" colorInner="#2E4052" />
      </div>
  {/if}
  <div id="login-buttons" style="display: none;">
    <button on:click={microsoftLogin} id="microsoft-login" class="microsoft-login">
        <Icon data={windows} style="color: #0078D4; padding-right:5px" />Log in with Microsoft
    </button>
    <button on:click={googleLogin} id="google-login" class="google-login">
      <Icon data={google} style="padding-right:5px" />Log in with Google
    </button>
  </div>
</div>
