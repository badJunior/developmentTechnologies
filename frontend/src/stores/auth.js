import { defineStore } from 'pinia';
import { ref } from 'vue';
import { request } from '@/api/client.js';

export const useAuthStore = defineStore('auth', () => {
  const access = ref(null);
  const user = ref(null);

  async function login(email, password) {
    const tokens = await request('/v1/auth/token', {
      method: 'POST', body: { email, password }, auth: false,
    });
    access.value = tokens.access_token;
    user.value = email;
  }

  async function accessToken() {
    return access.value;
  }

  async function refresh() {
    throw new Error('Not implemented');
  }

  function logout() {
    access.value = null;
    user.value = null;
  }

  return { user, login, logout, accessToken, refresh };
});
