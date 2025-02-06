import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Container,
  Grid,
  Typography,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Card,
  CardMedia,
} from '@mui/material';
import {
  LocationOn,
  Euro,
  Home,
  ArrowBack,
  ArrowForward,
} from '@mui/icons-material';
import axios from 'axios';

interface PropertyDetail {
  id: number;
  title: string;
  price: number;
  location: string;
  description: string;
  features: string[];
  images: string[];
  details: {
    room_count?: string;
    size?: string;
    floor?: string;
    building_age?: string;
    heating_type?: string;
    bathroom_count?: string;
    balcony?: string;
    furnished?: string;
    property_type?: string;
  };
  seller_info: {
    name?: string;
    company?: string;
    phone?: string;
    membership_status?: string;
    profile_url?: string;
  };
  raw_data?: {
    danısman_adi?: string;
    ilan_no?: string;
    telefon_numaralari?: string[];
    emlak_ofisi?: string;
  };
}

const PropertyDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  const { data: property, isLoading, error } = useQuery<PropertyDetail>({
    queryKey: ['property', id],
    queryFn: async () => {
      const response = await axios.get(`http://localhost:8000/properties/${id}`);
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" my={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        İlan detayları yüklenirken bir hata oluştu: {(error as any).message}
      </Alert>
    );
  }

  if (!property) {
    return (
      <Alert severity="warning" sx={{ mt: 2 }}>
        İlan bulunamadı
      </Alert>
    );
  }

  const handlePrevImage = () => {
    setCurrentImageIndex((prev) =>
      prev === 0 ? property.images.length - 1 : prev - 1
    );
  };

  const handleNextImage = () => {
    setCurrentImageIndex((prev) =>
      prev === property.images.length - 1 ? 0 : prev + 1
    );
  };

  return (
    <Container maxWidth="lg">
      <Grid container spacing={4}>
        {/* Image Gallery */}
        <Grid item xs={12}>
          <Paper sx={{ position: 'relative', height: 400, overflow: 'hidden' }}>
            {property?.images && property.images.length > 0 ? (
              <>
                <CardMedia
                  component="img"
                  height="400"
                  image={property.images[currentImageIndex]}
                  alt={`Property image ${currentImageIndex + 1}`}
                  sx={{ objectFit: 'cover' }}
                />
                {property.images.length > 1 && (
                  <>
                    <IconButton
                      sx={{
                        position: 'absolute',
                        left: 8,
                        top: '50%',
                        transform: 'translateY(-50%)',
                        bgcolor: 'rgba(255, 255, 255, 0.8)',
                      }}
                      onClick={handlePrevImage}
                    >
                      <ArrowBack />
                    </IconButton>
                    <IconButton
                      sx={{
                        position: 'absolute',
                        right: 8,
                        top: '50%',
                        transform: 'translateY(-50%)',
                        bgcolor: 'rgba(255, 255, 255, 0.8)',
                      }}
                      onClick={handleNextImage}
                    >
                      <ArrowForward />
                    </IconButton>
                  </>
                )}
              </>
            ) : (
              <Box
                display="flex"
                alignItems="center"
                justifyContent="center"
                height="100%"
              >
                <Typography variant="body1" color="text.secondary">
                  Görsel bulunamadı
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Property Details */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
              {property?.title}
            </Typography>

            <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
              <Chip
                icon={<Euro />}
                label={`${property?.price?.toLocaleString('tr-TR')} TL`}
                color="primary"
              />
              <Chip icon={<LocationOn />} label={property?.location} />
              {property?.details?.room_count && (
                <Chip icon={<Home />} label={property.details.room_count} />
              )}
            </Box>

            <Typography variant="h6" gutterBottom>
              Açıklama
            </Typography>
            <Typography variant="body1" paragraph>
              {property?.description}
            </Typography>

            <Typography variant="h6" gutterBottom>
              Özellikler
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
              {property?.features?.map((feature, index) => (
                <Chip key={index} label={feature} variant="outlined" />
              ))}
            </Box>

            <Typography variant="h6" gutterBottom>
              Detaylar
            </Typography>
            <Grid container spacing={2}>
              {property?.details && Object.entries(property.details)
                .filter(([_, value]) => value) // Sadece değeri olan özellikleri göster
                .map(([key, value]) => (
                  <Grid item xs={12} sm={6} key={key}>
                    <Typography variant="body2" color="text.secondary">
                      {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                    </Typography>
                    <Typography variant="body1">{value}</Typography>
                  </Grid>
                ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Seller Info */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              İlan Sahibi
            </Typography>
            {property?.seller_info?.name && (
              <Typography variant="body1" gutterBottom>
                {property.seller_info.name}
              </Typography>
            )}
            {property?.seller_info?.company && (
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {property.seller_info.company}
              </Typography>
            )}
            {property?.seller_info?.phone && (
              <Typography variant="body1" sx={{ mt: 2 }}>
                Tel: {property.seller_info.phone}
              </Typography>
            )}
            {property?.raw_data?.danısman_adi && (
              <Typography variant="body1" sx={{ mt: 2 }}>
                Danışman: {property.raw_data.danısman_adi}
              </Typography>
            )}
            {property?.raw_data?.ilan_no && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {property.raw_data.ilan_no}
              </Typography>
            )}
            {property?.raw_data?.telefon_numaralari && property.raw_data.telefon_numaralari.length > 0 && (
              <>
                <Typography variant="body1" sx={{ mt: 2 }}>
                  İletişim:
                </Typography>
                {property.raw_data.telefon_numaralari.map((phone: string, index: number) => (
                  <Typography key={index} variant="body2" sx={{ mt: 0.5 }}>
                    {phone}
                  </Typography>
                ))}
              </>
            )}
            {property?.raw_data?.emlak_ofisi && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                {property.raw_data.emlak_ofisi}
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default PropertyDetailPage; 