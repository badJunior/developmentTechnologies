import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    nfr01: {
      executor: 'constant-arrival-rate',
      rate: 20,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 20,
      maxVUs: 50,
    },
  },
  thresholds: {
    'http_req_duration{expected_response:true}': ['p(95)<300'],
    'http_req_failed': ['rate<0.01'],
  },
};

const today = new Date().toISOString().slice(0, 10);

export default function () {
  const res = http.get(`${__ENV.BASE_URL}/health`);
  check(res, { 'status is 200': (r) => r.status === 200 });
}
