import { writable } from 'svelte/store';

export const userSession = writable({ user_email: null, login_method: null });
