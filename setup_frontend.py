import os
from pathlib import Path

def create_file(path, content):
    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Создан: {path}")

# 1. Настройки Vite (перенаправление /api)
create_file("frontend/vite.config.js", """
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

const apiProxy = {
  '/api': {
    target: process.env.API_PROXY_TARGET ?? 'http://localhost:8080',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\\/api/, ''),
  },
};

export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: { port: 5173, proxy: apiProxy },
});
""")

# 2. Настройки Vitest
create_file("frontend/vitest.config.js", """
import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config.js';

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      include: ['tests/unit/**/*.test.js'],
    },
  }),
);
""")

# 3. Скрипт генерации схем из OpenAPI
create_file("frontend/scripts/generate-schemas.js", """
import { readFileSync, writeFileSync } from 'node:fs';
import yaml from 'js-yaml';

const spec = yaml.load(readFileSync('../docs/api/openapi.yaml', 'utf8'));
const schemas = JSON.parse(
  JSON.stringify(spec.components.schemas).replaceAll(
    '#/components/schemas/', '#/definitions/',
  ),
);

const EXTENSIBLE_ENUMS = ['SeatKind', 'BookingStatus'];
for (const name of EXTENSIBLE_ENUMS) {
  if (schemas[name]) delete schemas[name].enum;
}

writeFileSync(
  'src/api/schemas.js',
  `// ПОРОЖДЕННЫЙ ФАЙЛ. Не править руками.\\n` +
  `export const schemas = ${JSON.stringify({ definitions: schemas, ...schemas }, null, 2)};\\n`,
);
""")

# 4. API клиент
create_file("frontend/src/api/client.js", """
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
""")

# 5. Валидация
create_file("frontend/src/api/validate.js", """
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { ContractError } from './errors.js';
import { schemas } from './schemas.js';

const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);

export function validateResponse(schemaName, payload) {
  const schema = schemas[schemaName];
  if (!schema) throw new Error(`Схема ${schemaName} отсутствует`);
  const validate = ajv.compile({ ...schema, definitions: schemas.definitions });
  if (!validate(payload)) throw new ContractError(schemaName, validate.errors);
  return payload;
}
""")

# 6. Ошибки
create_file("frontend/src/api/errors.js", """
export class ApiError extends Error {
  constructor(status, problem) {
    super(problem.title ?? `HTTP ${status}`);
    this.status = status;
    this.type = problem.type;
    this.requestId = problem.request_id;
  }
  get userMessage() { return this.title ?? 'Что-то пошло не так'; }
}

export class ContractError extends Error {
  constructor(schemaName, violations) {
    super(`Response does not match schema ${schemaName}`);
    this.schemaName = schemaName;
  }
  get userMessage() { return 'Сервер прислал данные в неожиданном виде.'; }
}
""")

# 7. Хранилище авторизации
create_file("frontend/src/stores/auth.js", """
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
""")

# 8. API для мест
create_file("frontend/src/api/seats.js", """
import { request } from './client.js';

export function fetchSeats(date) {
  return request(`/v1/seats?date=${encodeURIComponent(date)}`, {
    auth: false,
    schema: 'SeatListResponse',
  });
}
""")

# 9. Простое представление
create_file("frontend/src/views/SeatsView.vue", """
<script setup>
import { ref, onMounted } from 'vue';
import { fetchSeats } from '@/api/seats.js';

const seats = ref([]);
const error = ref(null);

onMounted(async () => {
  try {
    const response = await fetchSeats('2026-12-01');
    seats.value = response.items;
  } catch (e) {
    error.value = e;
  }
});
</script>

<template>
  <main>
    <h1>Свободные места</h1>
    <p v-if="error">{{ error.userMessage }}</p>
    <ul v-else>
      <li v-for="seat in seats" :key="seat.id">{{ seat.code }}</li>
    </ul>
  </main>
</template>
""")

# 10. Роутер
create_file("frontend/src/router/index.js", """
import { createRouter, createWebHistory } from 'vue-router';
import SeatsView from '@/views/SeatsView.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/seats' },
    { path: '/seats', component: SeatsView },
  ],
});
""")

# 11. main.js и App.vue
create_file("frontend/src/main.js", """
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import { router } from './router/index.js';

createApp(App).use(createPinia()).use(router).mount('#app');
""")

create_file("frontend/src/App.vue", """
<script setup>
import { RouterView } from 'vue-router';
</script>

<template>
  <RouterView />
</template>
""")

print("\n✅ Файлы клиентской части созданы!")
print("Теперь выполните:")
print("cd frontend && npm run dev")