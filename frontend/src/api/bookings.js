import { request } from './client.js';

export function createBooking({ seatId, startsAt, endsAt }) {
  return request('/v1/bookings', {
    method: 'POST',
    body: { seat_id: seatId, starts_at: startsAt, ends_at: endsAt },
    schema: 'Booking',
  });
}