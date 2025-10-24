import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  Button,
  CircularProgress,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { ArrowBack as BackIcon, Edit as EditIcon, Phone as PhoneIcon, PhoneForwarded as CallIcon } from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import Layout from '../components/Layout';
import apiClient from '../services/api';
import { Lead, Call } from '../types';

const LeadDetail: React.FC = () => {
  const { leadId } = useParams<{ leadId: string }>();
  const navigate = useNavigate();
  const [lead, setLead] = useState<Lead | null>(null);
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [calling, setCalling] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editedStatus, setEditedStatus] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      if (!leadId) return;
      try {
        const [leadData, callsData] = await Promise.all([
          apiClient.getLead(leadId),
          apiClient.getCalls({ lead_id: leadId }),
        ]);
        setLead(leadData);
        setCalls(callsData.calls || callsData);
        setEditedStatus(leadData.status);
      } catch (error) {
        console.error('Failed to fetch lead details:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [leadId]);

  const handleUpdateStatus = async () => {
    if (!leadId) return;
    try {
      await apiClient.updateLead(leadId, { status: editedStatus });
      setLead((prev) => (prev ? { ...prev, status: editedStatus } : null));
      setEditDialogOpen(false);
    } catch (error) {
      console.error('Failed to update lead:', error);
    }
  };

  const handleInitiateCall = async () => {
    if (!lead) return;
    setCalling(true);
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
      // Refresh calls list
      const callsData = await apiClient.getCalls({ lead_id: leadId });
      setCalls(callsData.calls || callsData);
    } catch (error: any) {
      console.error('Failed to initiate call:', error);
      alert(`Failed to initiate call: ${error.response?.data?.detail || error.message}`);
    } finally {
      setCalling(false);
    }
  };

  const handleHandoff = async () => {
    if (!leadId) return;
    try {
      await apiClient.triggerHandoff(leadId);
      alert('Handoff triggered successfully');
    } catch (error) {
      console.error('Failed to trigger handoff:', error);
    }
  };

  if (loading) {
    return (
      <Layout>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Layout>
    );
  }

  if (!lead) {
    return (
      <Layout>
        <Typography>Lead not found</Typography>
      </Layout>
    );
  }

  return (
    <Layout>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box display="flex" alignItems="center" gap={2}>
            <Button startIcon={<BackIcon />} onClick={() => navigate('/leads')}>
              Back
            </Button>
            <Typography variant="h4" component="h1">
              Lead Details
            </Typography>
          </Box>
          <Box>
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={() => setEditDialogOpen(true)}
              sx={{ mr: 1 }}
            >
              Edit Status
            </Button>
            <Button
              variant="contained"
              color="success"
              startIcon={<CallIcon />}
              onClick={handleInitiateCall}
              disabled={calling}
              sx={{ mr: 1 }}
            >
              {calling ? 'Calling...' : 'Call Lead'}
            </Button>
            <Button variant="contained" startIcon={<PhoneIcon />} onClick={handleHandoff}>
              Trigger Handoff
            </Button>
          </Box>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Basic Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box display="flex" flexDirection="column" gap={1.5}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Lead ID
                  </Typography>
                  <Typography>{lead.lead_id}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Phone
                  </Typography>
                  <Typography>{lead.phone}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Name
                  </Typography>
                  <Typography>{lead.name || '-'}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Language
                  </Typography>
                  <Typography>{lead.language}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Status
                  </Typography>
                  <Chip label={lead.status} size="small" color="primary" />
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Created
                  </Typography>
                  <Typography>
                    {formatDistanceToNow(new Date(lead.created_at), { addSuffix: true })}
                  </Typography>
                </Box>
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Eligibility Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box display="flex" flexDirection="column" gap={1.5}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Country
                  </Typography>
                  <Typography>{lead.country || '-'}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Degree
                  </Typography>
                  <Typography>{lead.degree || '-'}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Loan Amount
                  </Typography>
                  <Typography>{lead.loan_amount ? `₹${lead.loan_amount}` : '-'}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Collateral
                  </Typography>
                  <Typography>{lead.collateral || '-'}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Co-applicant ITR
                  </Typography>
                  <Typography>{lead.coapplicant_itr || '-'}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Category
                  </Typography>
                  {lead.eligibility_category ? (
                    <Chip label={lead.eligibility_category} size="small" color="success" />
                  ) : (
                    <Typography>-</Typography>
                  )}
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Urgency
                  </Typography>
                  {lead.urgency ? (
                    <Chip label={lead.urgency} size="small" />
                  ) : (
                    <Typography>-</Typography>
                  )}
                </Box>
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Call History
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Call ID</TableCell>
                      <TableCell>Direction</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Start Time</TableCell>
                      <TableCell>Duration</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {calls.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} align="center">
                          No calls found
                        </TableCell>
                      </TableRow>
                    ) : (
                      calls.map((call) => (
                        <TableRow key={call.call_id}>
                          <TableCell>{call.call_id}</TableCell>
                          <TableCell>
                            <Chip label={call.direction} size="small" />
                          </TableCell>
                          <TableCell>
                            <Chip label={call.status} size="small" />
                          </TableCell>
                          <TableCell>
                            {call.start_time
                              ? formatDistanceToNow(new Date(call.start_time), {
                                addSuffix: true,
                              })
                              : '-'}
                          </TableCell>
                          <TableCell>
                            {call.duration ? `${Math.floor(call.duration / 60)}m ${call.duration % 60}s` : '-'}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        </Grid>

        <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)}>
          <DialogTitle>Edit Lead Status</DialogTitle>
          <DialogContent>
            <TextField
              select
              fullWidth
              label="Status"
              value={editedStatus}
              onChange={(e) => setEditedStatus(e.target.value)}
              sx={{ mt: 2, minWidth: 300 }}
            >
              <option value="new">New</option>
              <option value="qualified">Qualified</option>
              <option value="handoff">Handoff</option>
              <option value="callback">Callback</option>
              <option value="unreachable">Unreachable</option>
              <option value="converted">Converted</option>
            </TextField>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdateStatus} variant="contained">
              Save
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Layout>
  );
};

export default LeadDetail;
