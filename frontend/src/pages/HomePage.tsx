import React from 'react';
import { Box, Typography, Container, Paper } from '@mui/material';
import ScrapeForm from '../components/ScrapeForm';

const HomePage: React.FC = () => {
  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
          <Typography 
            variant="h4" 
            component="h1" 
            gutterBottom 
            align="center"
            sx={{ 
              mb: 4,
              fontWeight: 'bold',
              color: 'primary.main'
            }}
          >
            HepsiEmlak Scraper
          </Typography>

          <Typography 
            variant="body1" 
            align="center" 
            sx={{ mb: 4, color: 'text.secondary' }}
          >
            HepsiEmlak üzerinden emlak ilanlarını toplamak için aşağıdaki formu kullanın.
            İl, ilçe ve kategori seçerek başlayın.
          </Typography>

          <ScrapeForm />
        </Paper>
      </Box>
    </Container>
  );
};

export default HomePage; 