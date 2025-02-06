import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';

const HomePage: React.FC = () => {
  const [searchUrl, setSearchUrl] = useState('');
  
  const { mutate: startScraping, isLoading, isError, error, isSuccess } = useMutation({
    mutationFn: async (url: string) => {
      const response = await axios.post('http://localhost:8000/scrape', null, {
        params: { search_url: url },
      });
      return response.data;
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchUrl) {
      startScraping(searchUrl);
    }
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', mt: 4 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          HepsiEmlak Veri Toplama
        </Typography>
        
        <Typography variant="body1" sx={{ mb: 4 }}>
          HepsiEmlak'tan emlak ilanlarını toplamak için arama sayfası URL'sini girin.
        </Typography>

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="HepsiEmlak Arama URL'si"
            variant="outlined"
            value={searchUrl}
            onChange={(e) => setSearchUrl(e.target.value)}
            placeholder="https://www.hepsiemlak.com/[arama-kriterleri]"
            sx={{ mb: 2 }}
          />

          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            disabled={isLoading || !searchUrl}
            sx={{ mb: 2 }}
          >
            {isLoading ? (
              <>
                <CircularProgress size={24} sx={{ mr: 1 }} color="inherit" />
                Veri Toplanıyor...
              </>
            ) : (
              'Veri Toplamayı Başlat'
            )}
          </Button>
        </form>

        {isSuccess && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Veri toplama işlemi başlatıldı! İlanlar arka planda toplanıyor.
          </Alert>
        )}

        {isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Hata oluştu: {(error as any)?.message || 'Bilinmeyen bir hata oluştu'}
          </Alert>
        )}

        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Nasıl Kullanılır?
          </Typography>
          <Typography variant="body2" component="div">
            <ol>
              <li>HepsiEmlak'ta istediğiniz arama kriterlerini seçin</li>
              <li>Arama sonuçları sayfasının URL'sini kopyalayın</li>
              <li>URL'yi yukarıdaki alana yapıştırın</li>
              <li>"Veri Toplamayı Başlat" butonuna tıklayın</li>
              <li>İlanlar otomatik olarak toplanacak ve kaydedilecektir</li>
              <li>Toplanan ilanları "İlanlar" sayfasından görüntüleyebilirsiniz</li>
            </ol>
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default HomePage; 