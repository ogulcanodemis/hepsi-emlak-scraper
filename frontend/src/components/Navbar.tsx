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

  const linkStyle = {
    color: 'white',
    textDecoration: 'none',
    marginLeft: 2,
  };

  const activeLinkStyle = {
    ...linkStyle,
    fontWeight: 'bold',
    borderBottom: '2px solid white',
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
              sx={isActive('/') ? activeLinkStyle : linkStyle}
            >
              ANA SAYFA
            </Button>
            <Button
              component={RouterLink}
              to="/properties"
              color="inherit"
              sx={isActive('/properties') ? activeLinkStyle : linkStyle}
            >
              İLANLAR
            </Button>
            <Button
              component={RouterLink}
              to="/search-history"
              color="inherit"
              sx={isActive('/search-history') ? activeLinkStyle : linkStyle}
            >
              ARAMA GEÇMİŞİ
            </Button>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Navbar; 