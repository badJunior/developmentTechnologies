<script setup>
import { ref, onMounted } from 'vue';
import { fetchSeats } from '@/api/seats.js';
import SeatCard from '@/components/SeatCard.vue';
import BookingForm from '@/components/BookingForm.vue';

const seats = ref([]);
const error = ref(null);
const isLoading = ref(true);
const selectedSeat = ref(null);
const selectedDate = ref('2026-12-01');

async function loadSeats() {
  isLoading.value = true;
  error.value = null;
  try {
    seats.value = await fetchSeats(selectedDate.value);
  } catch (e) {
    error.value = e;
  } finally {
    isLoading.value = false;
  }
}

function onBook(seat) {
  selectedSeat.value = seat;
}

function onCreated() {
  selectedSeat.value = null;
  loadSeats();
}

onMounted(loadSeats);
</script>

<template>
  <main>
    <h1>Свободные места</h1>
    
    <div class="date-picker">
      <label>Выберите дату: </label>
      <input v-model="selectedDate" type="date" @change="loadSeats" />
    </div>

    <div v-if="isLoading" class="state-msg">Загрузка...</div>
    <div v-else-if="error" class="state-msg error">{{ error.userMessage }}</div>
    <div v-else-if="seats.length === 0" class="state-msg">На эту дату свободных мест нет.</div>
    
    <div v-else class="seats-grid">
      <SeatCard 
        v-for="seat in seats" 
        :key="seat.id" 
        :seat="seat" 
        @book="onBook" 
      />
    </div>

    <BookingForm 
      v-if="selectedSeat" 
      :seat="selectedSeat" 
      :date="selectedDate"
      @created="onCreated"
      @cancelled="selectedSeat = null"
    />
  </main>
</template>

<style scoped>
.date-picker {
  margin-bottom: 24px;
  font-size: 1.1rem;
}
.date-picker input {
  padding: 8px;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 6px;
}
.state-msg {
  font-size: 1.2rem;
  color: #555;
  text-align: center;
  margin-top: 40px;
}
.state-msg.error {
  color: #e74c3c;
}
.seats-grid {
  display: flex;
  flex-wrap: wrap;
  margin: -10px;
}
</style>