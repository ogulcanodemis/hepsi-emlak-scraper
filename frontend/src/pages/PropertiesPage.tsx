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
  Container,
  Pagination,
} from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { PropertyCategory } from '../types';

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
  category?: string;
  province?: string;
  district?: string;
  neighborhood?: string;
  status?: string;
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

interface PropertyType {
  type: string;
  count: number;
}

interface PropertyTypesResponse {
  property_types: PropertyType[];
}

const CATEGORY_MAPPING = {
  'konut': 'konut',
  'arsa': 'arsa',
  'isyeri': 'is-yeri',  // URL'deki format ile eşleştiriyoruz
  'devremulk': 'devremulk',
  'turistik': 'turistik-isletme'
};

const CATEGORY_LABELS = {
  'konut': 'Konut',
  'arsa': 'Arsa',
  'isyeri': 'İş Yeri',
  'devremulk': 'Devremülk',
  'turistik': 'Turistik Tesis'
};

// Durum seçenekleri için sabit
const STATUS_LABELS = {
  'satilik': 'Satılık',
  'kiralik': 'Kiralık'
};

// İlçe listesi için sabit
const DISTRICTS = [
  'Adalar', 'Arnavutköy', 'Ataşehir', 'Avcılar', 'Bağcılar', 'Bahçelievler',
  'Bakırköy', 'Başakşehir', 'Bayrampaşa', 'Beşiktaş', 'Beykoz', 'Beylikdüzü',
  'Beyoğlu', 'Büyükçekmece', 'Çatalca', 'Çekmeköy', 'Esenler', 'Esenyurt',
  'Eyüpsultan', 'Fatih', 'Gaziosmanpaşa', 'Güngören', 'Kadıköy', 'Kağıthane',
  'Kartal', 'Küçükçekmece', 'Maltepe', 'Pendik', 'Sancaktepe', 'Sarıyer',
  'Silivri', 'Sultanbeyli', 'Sultangazi', 'Şile', 'Şişli', 'Tuzla', 'Ümraniye',
  'Üsküdar', 'Zeytinburnu'
];

const PropertiesPage: React.FC = () => {
  const location = useLocation();
  const [filters, setFilters] = useState<FilterParams>(() => {
    // URL'den parametreleri al
    const params = new URLSearchParams(location.search);
    const pathParts = location.pathname.split('/');
    
    // URL path'inden ilçe ve durum bilgisini çıkar
    // Örnek: /beykoz-satilik -> district: beykoz, status: satilik
    let district = '';
    let status = '';
    if (pathParts.length > 1) {
      const locationPart = pathParts[1];
      const parts = locationPart.split('-');
      if (parts.length === 2) {
        district = parts[0];
        status = parts[1];
      }
    }

    return {
      localKw: params.get('local_kw') || '',
      minPrice: params.get('min_price') ? Number(params.get('min_price')) : undefined,
      maxPrice: params.get('max_price') ? Number(params.get('max_price')) : undefined,
      location: params.get('location') || '',
      category: params.get('category') || '',
      province: params.get('province') || '',
      district: district || '',
      neighborhood: params.get('neighborhood') || '',
      status: status || ''
    };
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

  // Debug query to check property types
  const { data: propertyTypes } = useQuery<PropertyTypesResponse>({
    queryKey: ['propertyTypes'],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/debug/property-types');
      console.log('Property Types:', response.data);
      return response.data;
    }
  });

  const { data: response, isLoading, error } = useQuery<PaginatedResponse>({
    queryKey: ['properties', page, filters],
    queryFn: async () => {
      console.log('Requesting with filters:', filters);
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
          neighborhood: filters.neighborhood,
          status: filters.status
        },
      });
      console.log('Response:', response.data);
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
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Arama"
              value={filters.localKw || ''}
              onChange={handleFilterChange('localKw')}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Kategori</InputLabel>
              <Select
                value={filters.category || ''}
                onChange={(e) => {
                  console.log('Selected category:', e.target.value);
                  setFilters(prev => ({ ...prev, category: e.target.value }));
                }}
                label="Kategori"
              >
                <MenuItem value="">Tümü</MenuItem>
                {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                  <MenuItem key={value} value={value}>
                    {label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Durum</InputLabel>
              <Select
                value={filters.status || ''}
                onChange={(e) => {
                  console.log('Selected status:', e.target.value);
                  setFilters(prev => ({ ...prev, status: e.target.value }));
                }}
                label="Durum"
              >
                <MenuItem value="">Tümü</MenuItem>
                {Object.entries(STATUS_LABELS).map(([value, label]) => (
                  <MenuItem key={value} value={value}>
                    {label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>İlçe</InputLabel>
              <Select
                value={filters.district || ''}
                onChange={(e) => {
                  console.log('Selected district:', e.target.value);
                  setFilters(prev => ({ ...prev, district: e.target.value }));
                }}
                label="İlçe"
              >
                <MenuItem value="">Tümü</MenuItem>
                {DISTRICTS.map((district) => (
                  <MenuItem key={district} value={district.toLowerCase()}>
                    {district}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {/* Property type debug info */}
        {propertyTypes && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Mevcut kategoriler: {propertyTypes.property_types.map((t: PropertyType) => `${t.type} (${t.count})`).join(', ')}
            </Typography>
          </Box>
        )}

        {isLoading ? (
          <Typography>Yükleniyor...</Typography>
        ) : (
          <>
            <Grid container spacing={3}>
              {response?.items.map((property: Property) => (
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

            {response && (
              <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
                <Pagination
                  count={response.total_pages}
                  page={page}
                  onChange={(_, value) => setPage(value)}
                  color="primary"
                />
              </Box>
            )}
          </>
        )}
      </Box>
    </Container>
  );
};

export default PropertiesPage; 