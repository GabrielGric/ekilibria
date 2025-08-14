import { defineConfig,loadEnv } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file from current directory
  const env = loadEnv(mode, '../../../', '')
  
  return {
    plugins: [svelte()],
    define: {
      // Make environment variables available
      'import.meta.env.VITE_ENV': JSON.stringify(env.VITE_ENV || 'development')
    }
  }
})