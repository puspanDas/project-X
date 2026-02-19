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

// --- AI Endpoints ---

export async function analyzeNumber(traceData) {
  const res = await API.post('/api/ai/analyze', { trace_data: traceData });
  return res.data;
}

export async function aiChat(message, history = []) {
  const res = await API.post('/api/ai/chat', { message, history });
  return res.data;
}

export default API;
