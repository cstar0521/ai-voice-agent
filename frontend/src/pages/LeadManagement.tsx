import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  CircularProgress,
  Button,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  Phone as PhoneIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import Layout from '../components/Layout';
import apiClient from '../services/api';
import { Lead } from '../types';

const LeadManagement: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [callingLeadId, setCallingLeadId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  const fetchLeads = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (statusFilter !== 'all') params.status = statusFilter;
      if (categoryFilter !== 'all') params.category = categoryFilter;
      if (searchTerm) params.search = searchTerm;

      const data = await apiClient.getLeads(params);
      setLeads(data.leads || data);
    } catch (error) {
      console.error('Failed to fetch leads:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, [statusFilter, categoryFilter]);

  const handleSearch = () => {
    fetchLeads();
  };

  const handleInitiateCall = async (lead: Lead) => {
    setCallingLeadId(lead.lead_id);
    try {
      const response = await apiClient.initiateOutboundCall({
        phone_number: lead.phone,
        preferred_language: lead.language || 'english',
        lead_source: 'existing_lead',
        metadata: {
          lead_id: lead.lead_id,
          name: lead.name,
          country: lead.country,
          degree: lead.degree,
          loan_amount: lead.loan_amount,
        },
      });
      alert(`Call initiated successfully! Call ID: ${response.call_id}`);
      fetchLeads();
    } catch (error: any) {
      console.error('Failed to initiate call:', error);
      alert(`Failed to initiate call: ${error.response?.data?.detail || error.message}`);
    } finally {
      setCallingLeadId(null);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
      new: 'default',
      qualified: 'primary',
      handoff: 'warning',
      callback: 'warning',
      unreachable: 'error',
      converted: 'success',
    };
    return colors[status] || 'default';
  };

  const getCategoryColor = (category?: string) => {
    const colors: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
      public_secured: 'success',
      private_unsecured: 'primary',
      intl_usd: 'primary',
      escalate: 'error',
    };
    return category ? colors[category] || 'default' : 'default';
  };

  if (loading && leads.length === 0) {
    return (
      <Layout>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Layout>
    );
  }

  return (
    <Layout>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            Lead Management
          </Typography>
          <Box display="flex" gap={1}>
            <Button
              variant="contained"
              color="primary"
              onClick={() => navigate('/new-lead')}
            >
              New Lead & Call
            </Button>
            <IconButton onClick={fetchLeads} color="primary">
              <RefreshIcon />
            </IconButton>
          </Box>
        </Box>

        <Paper sx={{ p: 2, mb: 3 }}>
          <Box display="flex" gap={2} flexWrap="wrap">
            <TextField
              label="Search"
              variant="outlined"
              size="small"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              sx={{ minWidth: 200 }}
            />
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="new">New</MenuItem>
                <MenuItem value="qualified">Qualified</MenuItem>
                <MenuItem value="handoff">Handoff</MenuItem>
                <MenuItem value="callback">Callback</MenuItem>
                <MenuItem value="unreachable">Unreachable</MenuItem>
                <MenuItem value="converted">Converted</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Category"
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="public_secured">Public Secured</MenuItem>
                <MenuItem value="private_unsecured">Private Unsecured</MenuItem>
                <MenuItem value="intl_usd">International USD</MenuItem>
                <MenuItem value="escalate">Escalate</MenuItem>
              </Select>
            </FormControl>
            <Button variant="contained" onClick={handleSearch}>
              Search
            </Button>
          </Box>
        </Paper>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Lead ID</TableCell>
                <TableCell>Phone</TableCell>
                <TableCell>Language</TableCell>
                <TableCell>Country</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Urgency</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {leads.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    No leads found
                  </TableCell>
                </TableRow>
              ) : (
                leads.map((lead) => (
                  <TableRow key={lead.lead_id} hover>
                    <TableCell>{lead.lead_id}</TableCell>
                    <TableCell>{lead.phone}</TableCell>
                    <TableCell>{lead.language}</TableCell>
                    <TableCell>{lead.country || '-'}</TableCell>
                    <TableCell>
                      <Chip
                        label={lead.status}
                        size="small"
                        color={getStatusColor(lead.status)}
                      />
                    </TableCell>
                    <TableCell>
                      {lead.eligibility_category ? (
                        <Chip
                          label={lead.eligibility_category}
                          size="small"
                          color={getCategoryColor(lead.eligibility_category)}
                        />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {lead.urgency ? (
                        <Chip
                          label={lead.urgency}
                          size="small"
                          color={
                            lead.urgency === 'high'
                              ? 'error'
                              : lead.urgency === 'medium'
                              ? 'warning'
                              : 'default'
                          }
                        />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {formatDistanceToNow(new Date(lead.created_at), { addSuffix: true })}
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        color="success"
                        onClick={() => handleInitiateCall(lead)}
                        disabled={callingLeadId === lead.lead_id}
                        title="Call Lead"
                      >
                        <PhoneIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => navigate(`/leads/${lead.lead_id}`)}
                        title="View Details"
                      >
                        <ViewIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Layout>
  );
};

export default LeadManagement;
