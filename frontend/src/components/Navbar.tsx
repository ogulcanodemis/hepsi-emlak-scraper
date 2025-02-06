import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
} from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';

const Navbar: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <AppBar position="static" color="primary" elevation={0}>
      <Container maxWidth="lg">
        <Toolbar disableGutters>
          <Typography
            variant="h6"
            component={RouterLink}
            to="/"
            sx={{
              textDecoration: 'none',
              color: 'inherit',
              flexGrow: 1,
              fontWeight: 700,
            }}
          >
            HepsiEmlak Scraper
          </Typography>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              component={RouterLink}
              to="/"
              color="inherit"
              sx={{
                fontWeight: isActive('/') ? 700 : 400,
                textDecoration: isActive('/') ? 'underline' : 'none',
              }}
            >
              Ana Sayfa
            </Button>
            <Button
              component={RouterLink}
              to="/properties"
              color="inherit"
              sx={{
                fontWeight: isActive('/properties') ? 700 : 400,
                textDecoration: isActive('/properties') ? 'underline' : 'none',
              }}
            >
              İlanlar
            </Button>
            <Button
              component={RouterLink}
              to="/search-history"
              color="inherit"
              sx={{
                fontWeight: isActive('/search-history') ? 700 : 400,
                textDecoration: isActive('/search-history') ? 'underline' : 'none',
              }}
            >
              Arama Geçmişi
            </Button>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Navbar; 