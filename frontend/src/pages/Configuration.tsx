import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  TextField,
  Button,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Snackbar,
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';
import Layout from '../components/Layout';
import apiClient from '../services/api';
import { VoicePrompt } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const Configuration: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [language, setLanguage] = useState('hinglish');
  const [prompts, setPrompts] = useState<VoicePrompt[]>([]);
  const [flows, setFlows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  useEffect(() => {
    fetchData();
  }, [language]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [promptsData, flowsData] = await Promise.all([
        apiClient.getPrompts(language),
        apiClient.getFlows(),
      ]);
      setPrompts(promptsData.prompts || promptsData || []);
      setFlows(flowsData.flows || flowsData || []);
    } catch (error) {
      console.error('Failed to fetch configuration:', error);
      setSnackbar({ open: true, message: 'Failed to load configuration', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handlePromptChange = (promptId: string, newText: string) => {
    setPrompts((prev) =>
      prev.map((p) => (p.prompt_id === promptId ? { ...p, text: newText } : p))
    );
  };

  const handleSavePrompts = async () => {
    try {
      setSaving(true);
      await apiClient.updatePrompts({ language, prompts });
      setSnackbar({ open: true, message: 'Prompts saved successfully', severity: 'success' });
    } catch (error) {
      console.error('Failed to save prompts:', error);
      setSnackbar({ open: true, message: 'Failed to save prompts', severity: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestPrompt = (promptText: string) => {
    // Simulate TTS testing
    alert(`Testing prompt: "${promptText}"\n\nIn production, this would play the TTS audio.`);
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
        <Typography variant="h4" component="h1" gutterBottom>
          Configuration Management
        </Typography>

        <Paper sx={{ mt: 3 }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label="Voice Prompts" />
            <Tab label="Conversation Flows" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <Box sx={{ mb: 3 }}>
              <FormControl sx={{ minWidth: 200 }}>
                <InputLabel>Language</InputLabel>
                <Select
                  value={language}
                  label="Language"
                  onChange={(e) => setLanguage(e.target.value)}
                >
                  <MenuItem value="hinglish">Hinglish</MenuItem>
                  <MenuItem value="english">English</MenuItem>
                  <MenuItem value="telugu">Telugu</MenuItem>
                </Select>
              </FormControl>
            </Box>

            {prompts.length === 0 ? (
              <Alert severity="info">
                No prompts found for {language}. Create prompts using the backend API.
              </Alert>
            ) : (
              <Grid container spacing={3}>
                {prompts.map((prompt) => (
                  <Grid item xs={12} key={prompt.prompt_id}>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>
                        {prompt.state.replace(/_/g, ' ').toUpperCase()}
                      </Typography>
                      <TextField
                        fullWidth
                        multiline
                        rows={3}
                        value={prompt.text}
                        onChange={(e) => handlePromptChange(prompt.prompt_id, e.target.value)}
                        sx={{ mb: 2 }}
                      />
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => handleTestPrompt(prompt.text)}
                      >
                        Test Prompt
                      </Button>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            )}

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={handleSavePrompts}
                disabled={saving || prompts.length === 0}
              >
                {saving ? 'Saving...' : 'Save Prompts'}
              </Button>
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            {flows.length === 0 ? (
              <Alert severity="info">
                No conversation flows configured. Create flows using the backend API.
              </Alert>
            ) : (
              <Grid container spacing={3}>
                {flows.map((flow, index) => (
                  <Grid item xs={12} key={index}>
                    <Paper sx={{ p: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        {flow.name || `Flow ${index + 1}`}
                      </Typography>
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          States:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {flow.states?.map((state: string, i: number) => (
                            <Box
                              key={i}
                              sx={{
                                px: 2,
                                py: 1,
                                bgcolor: 'primary.light',
                                color: 'white',
                                borderRadius: 1,
                              }}
                            >
                              {state}
                            </Box>
                          ))}
                        </Box>
                      </Box>
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Flow Visualization:
                        </Typography>
                        <Box
                          sx={{
                            p: 2,
                            bgcolor: 'grey.100',
                            borderRadius: 1,
                            fontFamily: 'monospace',
                          }}
                        >
                          {flow.states?.join(' → ') || 'No states defined'}
                        </Box>
                      </Box>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            )}
          </TabPanel>
        </Paper>

        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </Layout>
  );
};

export default Configuration;
