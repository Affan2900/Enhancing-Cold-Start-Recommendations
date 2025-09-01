import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Container,
  TextField,
  Button,
  Typography,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Paper,
  Box,
  Grid,
  Chip,
  Alert,
  Tabs,
  Tab
} from '@mui/material';

function App() {
  const [userId, setUserId] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersError, setUsersError] = useState(null);
  const [totalUsers, setTotalUsers] = useState(0);
  const [activeTab, setActiveTab] = useState(0);

  // Fetch available users on component mount
  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setUsersLoading(true);
    setUsersError(null);
    try {
      const response = await axios.get('http://localhost:5001/users');
      setUsers(response.data.users || []);
      setTotalUsers(response.data.total_users || 0);
    } catch (err) {
      setUsersError(err.response?.data?.error || 'Failed to fetch users');
    } finally {
      setUsersLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('http://localhost:5001/recommend', {
        user_id: userId
      });
      setRecommendations(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to get recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleUserClick = (user) => {
    setUserId(user.user_id);
    setActiveTab(0); // Switch to recommendations tab
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Recommendation System
      </Typography>

      <Paper elevation={3}>
        <Tabs value={activeTab} onChange={handleTabChange} centered>
          <Tab label="Get Recommendations" />
          <Tab label={`Available Users (${totalUsers})`} />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {activeTab === 0 && (
            <>
              <Box component="form" onSubmit={handleSubmit} sx={{ mb: 3 }}>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={9}>
                    <TextField
                      fullWidth
                      label="User ID"
                      variant="outlined"
                      value={userId}
                      onChange={(e) => setUserId(e.target.value)}
                      required
                      helperText="Enter a user ID or select from available users"
                    />
                  </Grid>
                  <Grid item xs={3}>
                    <Button
                      type="submit"
                      variant="contained"
                      color="primary"
                      fullWidth
                      disabled={loading || !userId}
                    >
                      {loading ? <CircularProgress size={24} /> : 'Get Recs'}
                    </Button>
                  </Grid>
                </Grid>
              </Box>

              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              {recommendations.length > 0 && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Top Recommendations for User: {userId}
                  </Typography>
                  <List>
                    {recommendations.map((rec, index) => (
                      <ListItem key={index} divider>
                        <ListItemText
                          primary={`Item ID: ${rec.item_idx}`}
                          secondary={`Confidence Score: ${rec.score.toFixed(4)}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
            </>
          )}

          {activeTab === 1 && (
            <>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Available Users ({totalUsers} total)
                </Typography>
                <Button 
                  variant="outlined" 
                  onClick={fetchUsers}
                  disabled={usersLoading}
                >
                  {usersLoading ? <CircularProgress size={20} /> : 'Refresh'}
                </Button>
              </Box>

              {usersError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {usersError}
                </Alert>
              )}

              {usersLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              ) : users.length > 0 ? (
                <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto' }}>
                  <List>
                    {users.map((user, index) => (
                      <ListItem 
                        key={index} 
                        divider
                        button
                        onClick={() => handleUserClick(user)}
                        selected={userId === user.user_id}
                      >
                        <ListItemText
                          primary={user.user_id}
                          secondary={`Internal Index: ${user.internal_index}`}
                        />
                        <Chip 
                          label="Select" 
                          size="small" 
                          color="primary" 
                          variant="outlined"
                        />
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              ) : (
                <Alert severity="info">
                  No users found. Make sure your backend is running and user mappings are loaded.
                </Alert>
              )}

              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Click on any user to select them for recommendations
              </Typography>
            </>
          )}
        </Box>
      </Paper>
    </Container>
  );
}

export default App;