import React, { useState, useEffect } from 'react';
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
  Button,
  CircularProgress,
} from '@mui/material';
import { Refresh as RefreshIcon, PhoneDisabled as HangupIcon } from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import Layout from '../components/Layout';
import apiClient from '../services/api';
import { Call } from '../types';

const CallMonitoring: React.FC = () => {
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchCalls = async () => {
    try {
      const data = await apiClient.getCalls({ limit: 50 });
      setCalls(data.calls || data);
    } catch (error) {
      console.error('Failed to fetch calls:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchCalls, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const handleHangup = async (callId: string) => {
    try {
      await apiClient.hangupCall(callId);
      fetchCalls();
    } catch (error) {
      console.error('Failed to hangup call:', error);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
      initiated: 'default',
      connected: 'primary',
      in_progress: 'primary',
      completed: 'success',
      failed: 'error',
      no_answer: 'warning',
    };
    return colors[status] || 'default';
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
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

  return (
    <Layout>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            Call Monitoring
          </Typography>
          <Box>
            <Button
              variant={autoRefresh ? 'contained' : 'outlined'}
              onClick={() => setAutoRefresh(!autoRefresh)}
              sx={{ mr: 1 }}
            >
              {autoRefresh ? 'Auto-Refresh ON' : 'Auto-Refresh OFF'}
            </Button>
            <IconButton onClick={fetchCalls} color="primary">
              <RefreshIcon />
            </IconButton>
          </Box>
        </Box>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Call ID</TableCell>
                <TableCell>Direction</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Start Time</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Language</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {calls.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No calls found
                  </TableCell>
                </TableRow>
              ) : (
                calls.map((call) => (
                  <TableRow key={call.call_id}>
                    <TableCell>{call.call_id}</TableCell>
                    <TableCell>
                      <Chip
                        label={call.direction}
                        size="small"
                        color={call.direction === 'inbound' ? 'primary' : 'secondary'}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={call.status}
                        size="small"
                        color={getStatusColor(call.status)}
                      />
                    </TableCell>
                    <TableCell>
                      {call.start_time
                        ? formatDistanceToNow(new Date(call.start_time), { addSuffix: true })
                        : '-'}
                    </TableCell>
                    <TableCell>{formatDuration(call.duration)}</TableCell>
                    <TableCell>-</TableCell>
                    <TableCell>
                      {call.status === 'in_progress' && (
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleHangup(call.call_id)}
                        >
                          <HangupIcon />
                        </IconButton>
                      )}
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

export default CallMonitoring;
