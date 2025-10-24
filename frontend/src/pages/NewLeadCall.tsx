import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  MenuItem,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import { Phone as PhoneIcon } from '@mui/icons-material';
import Layout from '../components/Layout';
import apiClient from '../services/api';

const NewLeadCall: React.FC = () => {
  const [formData, setFormData] = useState({
    phone: '',
    name: '',
    language: 'english',
    country: '',
    degree: '',
    loan_amount: '',
    offer_letter: '',
    coapplicant_itr: '',
    collateral: '',
    visa_timeline: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError('');
    setSuccess('');
  };

  const handleCreateAndCall = async () => {
    // Validation
    if (!formData.phone || !formData.name) {
      setError('Phone and Name are required fields');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Prepare metadata with all lead information
      const metadata = {
        name: formData.name,
        country: formData.country || undefined,
        degree: formData.degree || undefined,
        loan_amount: formData.loan_amount ? parseFloat(formData.loan_amount) : undefined,
        offer_letter: formData.offer_letter || undefined,
        coapplicant_itr: formData.coapplicant_itr || undefined,
        collateral: formData.collateral || undefined,
        visa_timeline: formData.visa_timeline || undefined,
      };

      // Initiate outbound call with proper backend format
      const callResponse = await apiClient.initiateOutboundCall({
        phone_number: formData.phone,
        preferred_language: formData.language,
        lead_source: 'manual_entry',
        metadata: metadata,
      });

      setSuccess(`Call initiated successfully! Call ID: ${callResponse.call_id}`);
      
      // Reset form
      setFormData({
        phone: '',
        name: '',
        language: 'english',
        country: '',
        degree: '',
        loan_amount: '',
        offer_letter: '',
        coapplicant_itr: '',
        collateral: '',
        visa_timeline: '',
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initiate call');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          New Lead & Initiate Call
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Create a new lead and immediately initiate an outbound call
        </Typography>

        <Paper sx={{ p: 3, mt: 3 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          {success && (
            <Alert severity="success" sx={{ mb: 3 }}>
              {success}
            </Alert>
          )}

          <Typography variant="h6" gutterBottom>
            Basic Information
          </Typography>
          <Divider sx={{ mb: 3 }} />

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                label="Phone Number"
                placeholder="+919876543210"
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                helperText="Include country code (e.g., +91 for India)"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                label="Name"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Language"
                value={formData.language}
                onChange={(e) => handleChange('language', e.target.value)}
              >
                <MenuItem value="english">English</MenuItem>
                <MenuItem value="hinglish">Hinglish</MenuItem>
                <MenuItem value="hindi">Hindi</MenuItem>
                <MenuItem value="telugu">Telugu</MenuItem>
                <MenuItem value="tamil">Tamil</MenuItem>
              </TextField>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Country"
                value={formData.country}
                onChange={(e) => handleChange('country', e.target.value)}
                placeholder="e.g., US, UK, Canada"
              />
            </Grid>
          </Grid>

          <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
            Loan Details
          </Typography>
          <Divider sx={{ mb: 3 }} />

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Degree"
                value={formData.degree}
                onChange={(e) => handleChange('degree', e.target.value)}
              >
                <MenuItem value="">Select Degree</MenuItem>
                <MenuItem value="bachelors">Bachelors</MenuItem>
                <MenuItem value="masters">Masters</MenuItem>
                <MenuItem value="phd">PhD</MenuItem>
              </TextField>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Loan Amount"
                value={formData.loan_amount}
                onChange={(e) => handleChange('loan_amount', e.target.value)}
                placeholder="e.g., 50000"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Offer Letter"
                value={formData.offer_letter}
                onChange={(e) => handleChange('offer_letter', e.target.value)}
              >
                <MenuItem value="">Select</MenuItem>
                <MenuItem value="yes">Yes</MenuItem>
                <MenuItem value="no">No</MenuItem>
              </TextField>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Co-applicant ITR"
                value={formData.coapplicant_itr}
                onChange={(e) => handleChange('coapplicant_itr', e.target.value)}
              >
                <MenuItem value="">Select</MenuItem>
                <MenuItem value="yes">Yes</MenuItem>
                <MenuItem value="no">No</MenuItem>
              </TextField>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Collateral"
                value={formData.collateral}
                onChange={(e) => handleChange('collateral', e.target.value)}
              >
                <MenuItem value="">Select</MenuItem>
                <MenuItem value="yes">Yes</MenuItem>
                <MenuItem value="no">No</MenuItem>
              </TextField>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Visa Timeline"
                value={formData.visa_timeline}
                onChange={(e) => handleChange('visa_timeline', e.target.value)}
                placeholder="e.g., 2 months"
              />
            </Grid>
          </Grid>

          <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              color="primary"
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <PhoneIcon />}
              onClick={handleCreateAndCall}
              disabled={loading}
            >
              {loading ? 'Initiating Call...' : 'Create Lead & Call'}
            </Button>
          </Box>
        </Paper>
      </Box>
    </Layout>
  );
};

export default NewLeadCall;
