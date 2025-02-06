import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Link,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import axios from 'axios';

interface SearchHistory {
  id: number;
  search_url: string;
  search_params: Record<string, any>;
  results_count: number;
  created_at: string;
}

const SearchHistoryPage: React.FC = () => {
  const { data: searchHistory, isLoading, error } = useQuery<SearchHistory[]>({
    queryKey: ['search-history'],
    queryFn: async () => {
      const response = await axios.get('http://localhost:8000/search-history');
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
        Arama geçmişi yüklenirken bir hata oluştu: {(error as any).message}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Arama Geçmişi
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Tarih</TableCell>
              <TableCell>Arama URL'si</TableCell>
              <TableCell>Sonuç Sayısı</TableCell>
              <TableCell>İşlemler</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {searchHistory?.map((search) => (
              <TableRow key={search.id}>
                <TableCell>
                  {new Date(search.created_at).toLocaleString('tr-TR')}
                </TableCell>
                <TableCell>{search.search_url}</TableCell>
                <TableCell>{search.results_count || 'Bekliyor'}</TableCell>
                <TableCell>
                  <Link
                    component={RouterLink}
                    to="/properties"
                    color="primary"
                    sx={{ mr: 2 }}
                  >
                    Sonuçları Görüntüle
                  </Link>
                  <Link
                    href={search.search_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    color="secondary"
                  >
                    Orijinal Sayfaya Git
                  </Link>
                </TableCell>
              </TableRow>
            ))}
            {(!searchHistory || searchHistory.length === 0) && (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  Henüz arama geçmişi bulunmuyor
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default SearchHistoryPage; 