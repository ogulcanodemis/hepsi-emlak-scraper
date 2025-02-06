import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  OutlinedInput,
  InputAdornment,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Link } from 'react-router-dom';
import axios from 'axios';

interface Property {
  id: number;
  url: string;
  title?: string;
  price?: number;
  location?: string;
  description?: string;
  created_at?: string;
  features: string[];
  images: string[];
  seller_info: {
    name?: string;
    company?: string;
    phone?: string;
    membership_status?: string;
    profile_url?: string;
  };
  raw_data?: any;  // Backend'den gelen ham veriyi saklamak için
}

interface FilterParams {
  minPrice?: number;
  maxPrice?: number;
  location?: string;
  localKw?: string;  // Arama için keyword eklendi
}

const PropertiesPage: React.FC = () => {
  const [filters, setFilters] = useState<FilterParams>({
    localKw: '',
    minPrice: undefined,
    maxPrice: undefined,
    location: ''
  });
  const [page, setPage] = useState(1);
  const limit = 12;

  const { data: properties, isLoading, error } = useQuery<Property[]>({
    queryKey: ['properties', page, filters],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/properties', {
        params: {
          skip: (page - 1) * limit,
          limit,
          local_kw: filters.localKw,  // Keyword parametresi eklendi
          min_price: filters.minPrice,
          max_price: filters.maxPrice,
          location: filters.location,
        },
      });
      return response.data;
    },
  });

  const handleFilterChange = (field: keyof FilterParams) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.value;
    setFilters((prev) => ({
      ...prev,
      [field]: value === '' ? undefined : field.includes('rice') ? Number(value) : value,
    }));
    setPage(1); // Reset to first page when filters change
  };

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // The query will automatically refresh due to the queryKey including filters
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        Veriler yüklenirken bir hata oluştu: {(error as any).message}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Emlak İlanları
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 4, p: 2 }}>
        <form onSubmit={handleFilterSubmit}>
          <Grid container spacing={2} alignItems="flex-end">
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Arama"
                variant="outlined"
                value={filters.localKw || ''}
                onChange={handleFilterChange('localKw')}
                placeholder="İlan başlığında ara..."
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth variant="outlined">
                <InputLabel htmlFor="min-price">Minimum Fiyat</InputLabel>
                <OutlinedInput
                  id="min-price"
                  type="number"
                  value={filters.minPrice || ''}
                  onChange={handleFilterChange('minPrice')}
                  endAdornment={<InputAdornment position="end">TL</InputAdornment>}
                  label="Minimum Fiyat"
                />
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth variant="outlined">
                <InputLabel htmlFor="max-price">Maksimum Fiyat</InputLabel>
                <OutlinedInput
                  id="max-price"
                  type="number"
                  value={filters.maxPrice || ''}
                  onChange={handleFilterChange('maxPrice')}
                  endAdornment={<InputAdornment position="end">TL</InputAdornment>}
                  label="Maksimum Fiyat"
                />
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Konum"
                variant="outlined"
                value={filters.location || ''}
                onChange={handleFilterChange('location')}
                placeholder="Konum ara..."
              />
            </Grid>
          </Grid>
        </form>
      </Card>

      {/* Loading State */}
      {isLoading && (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      )}

      {/* Property Grid */}
      <Grid container spacing={3}>
        {properties?.map((property: Property) => (
          <Grid item xs={12} sm={6} md={4} key={property.id}>
            <Card
              component={Link}
              to={`/properties/${property.id}`}
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                textDecoration: 'none',
                color: 'inherit',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  transition: 'transform 0.2s ease-in-out',
                },
              }}
            >
              <CardMedia
                component="img"
                height="200"
                image={property.images[0] || '/placeholder-house.jpg'}
                alt={property.title || ''}
              />
              <CardContent>
                <Typography gutterBottom variant="h6" component="div" noWrap>
                  {property.title || ''}
                </Typography>
                <Typography variant="h6" color="primary" gutterBottom>
                  {property.price?.toLocaleString('tr-TR') || ''} TL
                </Typography>
                <Typography variant="body2" color="text.secondary" noWrap>
                  {property.location || ''}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  {property.features.slice(0, 3).map((feature, index) => (
                    <Typography
                      key={index}
                      variant="body2"
                      color="text.secondary"
                      component="span"
                      sx={{ mr: 1 }}
                    >
                      • {feature}
                    </Typography>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Pagination Info */}
      {!isLoading && properties && (
        <Box sx={{ mt: 2, mb: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Gösterilen: {((page - 1) * limit) + 1} - {((page - 1) * limit) + properties.length}
          </Typography>
        </Box>
      )}

      {/* Pagination */}
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center', gap: 2 }}>
        <Button
          variant="outlined"
          disabled={page === 1 || isLoading}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Önceki Sayfa
        </Button>
        <Button
          variant="outlined"
          disabled={!properties || properties.length < limit || isLoading}
          onClick={() => setPage((p) => p + 1)}
        >
          Sonraki Sayfa
        </Button>
      </Box>
    </Box>
  );
};

export default PropertiesPage; 