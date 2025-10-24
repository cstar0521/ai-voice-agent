import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  CircularProgress,
} from '@mui/material';
import {
  Phone as PhoneIcon,
  People as PeopleIcon,
  TrendingUp as TrendingUpIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import Layout from '../components/Layout';
import apiClient from '../services/api';
import { Metrics } from '../types';

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await apiClient.getMetrics();
        setMetrics(data);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, []);

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
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>

        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Calls
                </Typography>
                <Typography variant="h4">{metrics?.total_calls || 0}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  All time
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Active Calls
                </Typography>
                <Typography variant="h4" color="primary">
                  {metrics?.active_calls || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Currently in progress
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Completion Rate
                </Typography>
                <Typography variant="h4" color="success.main">
                  {metrics?.call_completion_rate
                    ? `${(metrics.call_completion_rate * 100).toFixed(1)}%`
                    : '0%'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Target: 80%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Handoff Rate
                </Typography>
                <Typography variant="h4">
                  {metrics?.handoff_rate
                    ? `${(metrics.handoff_rate * 100).toFixed(1)}%`
                    : '0%'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Target: 55%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box display="flex" alignItems="center" mb={2}>
                <PhoneIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Call Monitoring</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                Monitor active calls in real-time, view call status, and manage ongoing conversations.
              </Typography>
              <Button variant="contained" onClick={() => navigate('/calls')}>
                View Calls
              </Button>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box display="flex" alignItems="center" mb={2}>
                <PeopleIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Lead Management</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                View and manage leads, filter by status and category, and track lead progress.
              </Typography>
              <Button variant="contained" onClick={() => navigate('/leads')}>
                View Leads
              </Button>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box display="flex" alignItems="center" mb={2}>
                <TrendingUpIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Analytics</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                View detailed analytics, metrics, and insights about call performance and trends.
              </Typography>
              <Button variant="contained" onClick={() => navigate('/analytics')}>
                View Analytics
              </Button>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box display="flex" alignItems="center" mb={2}>
                <SettingsIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Configuration</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                Manage voice prompts, conversation flows, and system configuration settings.
              </Typography>
              <Button variant="contained" onClick={() => navigate('/config')}>
                Configure
              </Button>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Layout>
  );
};

export default Dashboard;
