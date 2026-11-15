import { useAuthStore } from '@/stores/auth.js';
import { ApiError } from './errors.js';
import { validateResponse } from './validate.js';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api';

export async function request(path, { method = 'GET', body, schema, auth = true, retried = false } = {}) {
  const authStore = useAuthStore();
  const headers = { Accept: 'application/json' };
  if (body) headers['Content-Type'] = 'application/json';
  if (auth) headers.Authorization = `Bearer ${await authStore.accessToken()}`;

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && auth && !retried) {
    await authStore.refresh();
    return request(path, { method, body, schema, auth, retried: true });
  }

  if (!response.ok) {
    const problem = await response.json().catch(() => ({}));
    throw new ApiError(response.status, problem);
  }

  const payload = await response.json();
  return schema ? validateResponse(schema, payload) : payload;
}
