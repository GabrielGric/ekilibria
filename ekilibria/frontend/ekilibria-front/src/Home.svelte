<style>
  .container {
    text-align: center;
    margin-top: 50px;
  }

  h1 {
    font-size: 2.5em;
    margin-bottom: 20px;
  }

  p {
    font-size: 1.2em;
    margin-bottom: 30px;
  }

  button {
    border: none;
    padding: 10px 20px;
    font-size: 1em;
    cursor: pointer;
    margin: 10px;
    border-radius: 5px;
  }

  button:hover {
    background-color: #005A9E;
  }

  button:focus {
      outline: none;
      box-shadow: 0 0 0 3px rgba(0, 120, 212, 0.5);
  }

  button:active {
      background-color: #004578;
  }
</style>

<script>
  import Icon from 'svelte-awesome/components/Icon.svelte';
  import { google, windows } from 'svelte-awesome/icons';
  import { userSession } from './lib/userSession.js';

  // Button functions
  async function googleLogin() {
    console.log('Google login button clicked');
    const response = await fetch('/auth/google');
    if (response.ok) {
        const data = await response.json();
        userSession.set({
          user_email: data.user_email,
          login_method: 'google' 
        });
        // redirect to next page
        window.location.href = '/#/show';

    }
  }

  async function microsoftLogin() {
    console.log('Microsoft login button clicked');
    const response = await fetch('/auth/microsoft');
    if (response.ok) {
        const data = await response.json();
        userSession.set({
          user_email: data.user_email, 
          login_method: 'microsoft' 
        });
        // redirect to next page
        window.location.href = '/#/show';
    }
  }
</script>

<div class="container">
    <h1>Welcome to Ekilibria</h1>
    <button on:click={microsoftLogin} id="microsoft-login" class="microsoft-login">
        <Icon data={windows} style="color: #0078D4; padding-right:5px" />Log in with Microsoft
    </button>
    <button on:click={googleLogin} id="google-login" class="google-login">
      <Icon data={google} style="padding-right:5px" />Log in with Google
    </button>
</div>
