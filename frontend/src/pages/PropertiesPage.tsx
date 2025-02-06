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
  Select,
  MenuItem,
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
  localKw?: string;
  category?: string;  // Konut, Arsa, İşyeri
  province?: string;  // İl
  district?: string;  // İlçe
  neighborhood?: string;  // Mahalle
}

interface PaginatedResponse {
  items: Property[];
  total: number;
  page: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

interface LocationData {
  provinces: string[];
  districts: string[];
  neighborhoods: string[];
}

interface CategoryData {
  categories: string[];
}

const PropertiesPage: React.FC = () => {
  const [filters, setFilters] = useState<FilterParams>({
    localKw: '',
    minPrice: undefined,
    maxPrice: undefined,
    location: '',
    category: '',
    province: '',
    district: '',
    neighborhood: ''
  });
  const [page, setPage] = useState(1);
  const limit = 12;

  // Konum ve kategori verilerini çek
  const { data: locationData } = useQuery<LocationData>({
    queryKey: ['locations'],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/locations');
      return response.data;
    }
  });

  const { data: categoryData } = useQuery<CategoryData>({
    queryKey: ['categories'],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/categories');
      return response.data;
    }
  });

  const { data: response, isLoading, error } = useQuery<PaginatedResponse>({
    queryKey: ['properties', page, filters],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/properties', {
        params: {
          skip: (page - 1) * limit,
          limit,
          local_kw: filters.localKw,
          min_price: filters.minPrice,
          max_price: filters.maxPrice,
          location: filters.location,
          category: filters.category,
          province: filters.province,
          district: filters.district,
          neighborhood: filters.neighborhood
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
            {/* Kategori seçimi */}
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Kategori</InputLabel>
                <Select
                  value={filters.category || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                  label="Kategori"
                >
                  <MenuItem value="">Tümü</MenuItem>
                  {categoryData?.categories.map((category) => (
                    <MenuItem key={category} value={category}>
                      {category === 'konut' ? 'Konut' : 
                       category === 'arsa' ? 'Arsa' : 
                       category === 'isyeri' ? 'İşyeri' : category}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* İl seçimi */}
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>İl</InputLabel>
                <Select
                  value={filters.province || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, province: e.target.value }))}
                  label="İl"
                >
                  <MenuItem value="">Tümü</MenuItem>
                  {locationData?.provinces.map((province) => (
                    <MenuItem key={province} value={province}>
                      {province}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* İlçe seçimi */}
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>İlçe</InputLabel>
                <Select
                  value={filters.district || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, district: e.target.value }))}
                  label="İlçe"
                >
                  <MenuItem value="">Tümü</MenuItem>
                  {locationData?.districts.map((district) => (
                    <MenuItem key={district} value={district}>
                      {district}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Mahalle seçimi */}
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Mahalle</InputLabel>
                <Select
                  value={filters.neighborhood || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, neighborhood: e.target.value }))}
                  label="Mahalle"
                >
                  <MenuItem value="">Tümü</MenuItem>
                  {locationData?.neighborhoods.map((neighborhood) => (
                    <MenuItem key={neighborhood} value={neighborhood}>
                      {neighborhood}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Mevcut filtreler */}
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

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  onClick={() => setFilters({
                    localKw: '',
                    minPrice: undefined,
                    maxPrice: undefined,
                    location: '',
                    category: '',
                    province: '',
                    district: '',
                    neighborhood: ''
                  })}
                >
                  Filtreleri Temizle
                </Button>
                <Button type="submit" variant="contained" color="primary">
                  Filtrele
                </Button>
              </Box>
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
        {response?.items?.map((property: Property) => (
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
      {!isLoading && response && (
        <Box sx={{ mt: 2, mb: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Toplam {response.total} ilan içinden {((page - 1) * limit) + 1} - {Math.min(page * limit, response.total)} arası gösteriliyor
          </Typography>
        </Box>
      )}

      {/* Pagination */}
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center', gap: 2 }}>
        <Button
          variant="outlined"
          disabled={!response?.has_previous || isLoading}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Önceki Sayfa
        </Button>
        <Button
          variant="outlined"
          disabled={!response?.has_next || isLoading}
          onClick={() => setPage((p) => p + 1)}
        >
          Sonraki Sayfa
        </Button>
      </Box>
    </Box>
  );
};

export default PropertiesPage; 