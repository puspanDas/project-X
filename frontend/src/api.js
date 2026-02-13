import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000',
});

export async function traceNumber(number) {
  const res = await API.get('/api/trace', { params: { number } });
  return res.data;
}

export async function reportNumber(data) {
  const res = await API.post('/api/report', data);
  return res.data;
}

export async function getHistory() {
  const res = await API.get('/api/recent');
  return res.data;
}

export default API;
