<script setup>
import { ref } from 'vue';
import { createBooking } from '@/api/bookings.js';

const props = defineProps({
  seat: { type: Object, required: true },
  date: { type: String, required: true },
});
const emit = defineEmits(['created', 'cancelled']);

const startsAt = ref('09:00');
const endsAt = ref('12:00');
const isSubmitting = ref(false);
const error = ref(null);

async function submit() {
  if (isSubmitting.value) return;
  isSubmitting.value = true;
  error.value = null;

  try {
    const starts = new Date(`${props.date}T${startsAt.value}`).toISOString();
    const ends = new Date(`${props.date}T${endsAt.value}`).toISOString();
    
    await createBooking({ seatId: props.seat.id, startsAt: starts, endsAt: ends });
    emit('created');
  } catch (e) {
    error.value = e;
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <div class="modal-overlay">
    <div class="booking-form">
      <h4>Бронирование: {{ seat.code }}</h4>
      
      <div class="form-group">
        <label>Начало</label>
        <input v-model="startsAt" type="time" />
      </div>
      
      <div class="form-group">
        <label>Окончание</label>
        <input v-model="endsAt" type="time" />
      </div>
      
      <p v-if="error" class="error">{{ error.userMessage }}</p>
      
      <div class="actions">
        <button class="confirm-btn" :disabled="isSubmitting" @click="submit">
          {{ isSubmitting ? 'Отправка...' : 'Подтвердить' }}
        </button>
        <button class="cancel-btn" @click="$emit('cancelled')">Отмена</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
}

.booking-form {
  background: white;
  padding: 30px;
  border-radius: 12px;
  width: 320px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}

.booking-form h4 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #2c3e50;
  text-align: center;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: bold;
  color: #555;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  box-sizing: border-box;
}

.error {
  color: #e74c3c;
  font-size: 0.9rem;
  margin-bottom: 16px;
  text-align: center;
}

.actions {
  display: flex;
  gap: 10px;
}

.actions button {
  flex: 1;
}

.cancel-btn {
  background-color: #95a5a6;
}
.cancel-btn:hover {
  background-color: #7f8c8d;
}
</style>