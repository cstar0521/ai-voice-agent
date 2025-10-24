import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../Dashboard';
import apiClient from '../../services/api';

jest.mock('../../services/api');

const mockMetrics = {
  total_calls: 100,
  active_calls: 5,
  call_completion_rate: 0.85,
  handoff_rate: 0.55,
  avg_qualification_time: 180,
  sentiment_distribution: {
    positive: 60,
    neutral: 30,
    negative: 10,
  },
  language_usage: {
    hinglish: 50,
    english: 30,
    telugu: 20,
  },
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders dashboard with metrics', async () => {
    jest.spyOn(apiClient, 'getMetrics').mockResolvedValue(mockMetrics);

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('85.0%')).toBeInTheDocument();
      expect(screen.getByText('55.0%')).toBeInTheDocument();
    });
  });

  test('displays navigation cards', async () => {
    jest.spyOn(apiClient, 'getMetrics').mockResolvedValue(mockMetrics);

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Call Monitoring')).toBeInTheDocument();
      expect(screen.getByText('Lead Management')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
      expect(screen.getByText('Configuration')).toBeInTheDocument();
    });
  });

  test('handles API error gracefully', async () => {
    jest.spyOn(apiClient, 'getMetrics').mockRejectedValue(new Error('API Error'));

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });
});
