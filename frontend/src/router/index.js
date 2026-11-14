import { createRouter, createWebHistory } from 'vue-router';
import SeatsView from '@/views/SeatsView.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/seats' },
    { path: '/seats', component: SeatsView },
  ],
});
