import { request } from './client.js';

export function fetchSeats(date) {
  return request(`/v1/seats?date=${encodeURIComponent(date)}`, {
    auth: false,
    schema: 'SeatListResponse',
  });
}
