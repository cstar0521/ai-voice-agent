import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LeadManagement from '../LeadManagement';
import apiClient from '../../services/api';

jest.mock('../../services/api');

const mockLeads = [
  {
    lead_id: 'lead_123',
    phone: '+919876543210',
    language: 'hinglish',
    country: 'US',
    degree: 'masters',
    status: 'qualified',
    eligibility_category: 'public_secured',
    urgency: 'high',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    lead_id: 'lead_456',
    phone: '+919876543211',
    language: 'english',
    country: 'UK',
    degree: 'bachelors',
    status: 'new',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

describe('LeadManagement Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders lead list', async () => {
    jest.spyOn(apiClient, 'getLeads').mockResolvedValue({ leads: mockLeads });

    render(
      <BrowserRouter>
        <LeadManagement />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('lead_123')).toBeInTheDocument();
      expect(screen.getByText('lead_456')).toBeInTheDocument();
      expect(screen.getByText('+919876543210')).toBeInTheDocument();
    });
  });

  test('filters leads by status', async () => {
    jest.spyOn(apiClient, 'getLeads').mockResolvedValue({ leads: mockLeads });

    render(
      <BrowserRouter>
        <LeadManagement />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('lead_123')).toBeInTheDocument();
    });

    const statusSelect = screen.getByLabelText(/status/i);
    fireEvent.mouseDown(statusSelect);
    
    await waitFor(() => {
      const qualifiedOption = screen.getByText('Qualified');
      fireEvent.click(qualifiedOption);
    });

    expect(apiClient.getLeads).toHaveBeenCalledWith({ status: 'qualified' });
  });

  test('displays empty state when no leads', async () => {
    jest.spyOn(apiClient, 'getLeads').mockResolvedValue({ leads: [] });

    render(
      <BrowserRouter>
        <LeadManagement />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No leads found')).toBeInTheDocument();
    });
  });
});
