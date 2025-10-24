import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(username: string, password: string) {
    const response = await this.client.post('/auth/login', { email: username, password });
    return response.data;
  }

  async logout() {
    localStorage.removeItem('auth_token');
  }

  // Call endpoints
  async getCalls(params?: any) {
    const response = await this.client.get('/calls', { params });
    return response.data;
  }

  async getCall(callId: string) {
    const response = await this.client.get(`/calls/${callId}`);
    return response.data;
  }

  async initiateOutboundCall(data: any) {
    const response = await this.client.post('/calls/outbound', data);
    return response.data;
  }

  async hangupCall(callId: string) {
    const response = await this.client.post(`/calls/${callId}/hangup`);
    return response.data;
  }

  // Lead endpoints
  async getLeads(params?: any) {
    const response = await this.client.get('/leads', { params });
    return response.data;
  }

  async getLead(leadId: string) {
    const response = await this.client.get(`/leads/${leadId}`);
    return response.data;
  }

  async updateLead(leadId: string, data: any) {
    const response = await this.client.put(`/leads/${leadId}`, data);
    return response.data;
  }

  async triggerHandoff(leadId: string) {
    const response = await this.client.post(`/leads/${leadId}/handoff`);
    return response.data;
  }

  // Configuration endpoints
  async getPrompts(language?: string) {
    const response = await this.client.get('/config/prompts', { params: { language } });
    return response.data;
  }

  async updatePrompts(data: any) {
    const response = await this.client.put('/config/prompts', data);
    return response.data;
  }

  async getFlows() {
    const response = await this.client.get('/config/flows');
    return response.data;
  }

  // Analytics endpoints
  async getMetrics() {
    const response = await this.client.get('/analytics/metrics');
    return response.data;
  }

  async getCallAnalytics(params?: any) {
    const response = await this.client.get('/analytics/calls', { params });
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;
