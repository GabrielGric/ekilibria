<script>
  import Router from 'svelte-spa-router';
  import Home from './Home.svelte';
  import Show from './Show.svelte';

  const routes = {
    '/': Home,
    '/show': Show
  };
</script>

<Router {routes} />