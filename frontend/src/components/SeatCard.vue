<script setup>
defineProps({
  seat: { type: Object, required: true },
});
defineEmits(['book']);
</script>

<template>
  <div class="seat-card" :class="{ 'is-busy': !seat.is_available }">
    <div class="seat-header">
      <h3>{{ seat.code }}</h3>
      <span v-if="seat.is_available" class="badge free">Свободно</span>
      <span v-else class="badge busy">Занято</span>
    </div>
    
    <div class="seat-details">
      <p>Тип: <strong>{{ seat.kind === 'desk' ? 'Стол' : 'Переговорная' }}</strong></p>
      <p>Вместимость: <strong>{{ seat.capacity }} чел.</strong></p>
    </div>

    <button 
      v-if="seat.is_available" 
      class="book-btn"
      @click="$emit('book', seat)"
    >
      Забронировать
    </button>
  </div>
</template>

<style scoped>
.seat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e0e0e0;
  display: inline-block;
  vertical-align: top;
  width: 220px;
  margin: 10px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.seat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.seat-card.is-busy {
  opacity: 0.7;
  background: #fafafa;
}

.seat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 1px solid #eee;
  padding-bottom: 12px;
}

.seat-header h3 {
  margin: 0;
  color: #2c3e50;
}

.badge {
  font-size: 0.8rem;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: bold;
}

.badge.free {
  background-color: #e8f8f5;
  color: #27ae60;
}

.badge.busy {
  background-color: #fdedec;
  color: #e74c3c;
}

.seat-details p {
  margin: 8px 0;
  color: #555;
  font-size: 0.95rem;
}

.book-btn {
  width: 100%;
  margin-top: 16px;
}
</style>