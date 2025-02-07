import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
    Box,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Button,
    CircularProgress,
    Alert,
    Chip,
    OutlinedInput,
    SelectChangeEvent,
    FormHelperText,
} from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
    PropertyStatus,
    PropertyCategory,
    ScrapeRequest,
    LocationData,
} from '../types';

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
    PaperProps: {
        style: {
            maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
            width: 250,
        },
    },
};

const ISTANBUL_DISTRICTS = [
    'Adalar', 'Arnavutköy', 'Ataşehir', 'Avcılar', 'Bağcılar', 'Bahçelievler',
    'Bakırköy', 'Başakşehir', 'Bayrampaşa', 'Beşiktaş', 'Beykoz', 'Beylikdüzü',
    'Beyoğlu', 'Büyükçekmece', 'Çatalca', 'Çekmeköy', 'Esenler', 'Esenyurt',
    'Eyüpsultan', 'Fatih', 'Gaziosmanpaşa', 'Güngören', 'Kadıköy', 'Kağıthane',
    'Kartal', 'Küçükçekmece', 'Maltepe', 'Pendik', 'Sancaktepe', 'Sarıyer',
    'Silivri', 'Sultanbeyli', 'Sultangazi', 'Şile', 'Şişli', 'Tuzla', 'Ümraniye',
    'Üsküdar', 'Zeytinburnu'
];

const STATUS_TYPES = [
    { value: PropertyStatus.SATILIK, label: 'Satılık' },
    { value: PropertyStatus.KIRALIK, label: 'Kiralık' }
];

const CATEGORIES = [
    { value: PropertyCategory.KONUT, label: 'Konut' },
    { value: PropertyCategory.ARSA, label: 'Arsa' },
    { value: PropertyCategory.ISYERI, label: 'İş Yeri' },
    { value: PropertyCategory.DEVREMULK, label: 'Devremülk' },
    { value: PropertyCategory.TURISTIK, label: 'Turistik İşletme' }
];

const ScrapeForm: React.FC = () => {
    const navigate = useNavigate();
    
    // State
    const [selectedIlce, setSelectedIlce] = useState<string>('');
    const [selectedMahalleler, setSelectedMahalleler] = useState<string[]>([]);
    const [selectedDurum, setSelectedDurum] = useState<PropertyStatus>(PropertyStatus.SATILIK);
    const [selectedKategori, setSelectedKategori] = useState<PropertyCategory>(PropertyCategory.KONUT);

    // Form validation state
    const [errors, setErrors] = useState<{
        ilce?: string;
        durum?: string;
        kategori?: string;
    }>({});

    // Location data query
    const { data: locationData, isLoading: isLocationLoading } = useQuery<LocationData>({
        queryKey: ['locations', 'İstanbul'],
        queryFn: async () => {
            const response = await axios.get(`http://localhost:8000/locations/İstanbul`);
            return response.data;
        }
    });

    // Mutations with success handling
    const scrapeMutation = useMutation({
        mutationFn: async (data: ScrapeRequest) => {
            const response = await axios.post('http://localhost:8000/scrape', data);
            return response.data;
        },
        onSuccess: (data) => {
            // 3 saniye sonra search history sayfasına yönlendir
            setTimeout(() => {
                navigate('/search-history');
            }, 3000);
        }
    });

    // Handlers
    const handleIlceChange = (event: SelectChangeEvent) => {
        setSelectedIlce(event.target.value);
        setSelectedMahalleler([]);
    };

    const handleMahalleChange = (event: SelectChangeEvent<string[]>) => {
        const value = event.target.value;
        setSelectedMahalleler(typeof value === 'string' ? value.split(',') : value);
    };

    // Validation
    const validateForm = (): boolean => {
        const newErrors: typeof errors = {};

        if (!selectedIlce) {
            newErrors.ilce = 'İlçe seçimi zorunludur';
        }
        if (!selectedDurum) {
            newErrors.durum = 'Durum seçimi zorunludur';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    // Submit handler with validation
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }
        
        const request: ScrapeRequest = {
            ilce: selectedIlce,
            durum: selectedDurum,
            kategori: selectedKategori,
            mahalleler: selectedMahalleler.length > 0 ? selectedMahalleler : undefined
        };

        await scrapeMutation.mutateAsync(request);
    };

    return (
        <Box component="form" onSubmit={handleSubmit} sx={{ '& > *': { m: 1 } }}>
            {/* İlçe Seçimi */}
            <FormControl fullWidth error={!!errors.ilce}>
                <InputLabel>İlçe</InputLabel>
                <Select
                    value={selectedIlce}
                    onChange={handleIlceChange}
                    label="İlçe"
                >
                    {ISTANBUL_DISTRICTS.map((ilce) => (
                        <MenuItem key={ilce} value={ilce}>
                            {ilce}
                        </MenuItem>
                    ))}
                </Select>
                {errors.ilce && <FormHelperText>{errors.ilce}</FormHelperText>}
            </FormControl>

            {/* Mahalle Seçimi */}
            <FormControl fullWidth disabled={!selectedIlce}>
                <InputLabel>Mahalleler</InputLabel>
                <Select
                    multiple
                    value={selectedMahalleler}
                    onChange={handleMahalleChange}
                    input={<OutlinedInput label="Mahalleler" />}
                    renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {selected.map((value) => (
                                <Chip key={value} label={value} />
                            ))}
                        </Box>
                    )}
                    MenuProps={MenuProps}
                >
                    {locationData?.mahalleler[selectedIlce]?.map((mahalle) => (
                        <MenuItem key={mahalle} value={mahalle}>
                            {mahalle}
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>

            {/* Durum Seçimi */}
            <FormControl fullWidth>
                <InputLabel>Durum</InputLabel>
                <Select
                    value={selectedDurum}
                    onChange={(e) => setSelectedDurum(e.target.value as PropertyStatus)}
                    label="Durum"
                >
                    {STATUS_TYPES.map(({ value, label }) => (
                        <MenuItem key={value} value={value}>
                            {label}
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>

            {/* Kategori Seçimi */}
            <FormControl fullWidth>
                <InputLabel>Kategori</InputLabel>
                <Select
                    value={selectedKategori}
                    onChange={(e) => setSelectedKategori(e.target.value as PropertyCategory)}
                    label="Kategori"
                >
                    {CATEGORIES.map(({ value, label }) => (
                        <MenuItem key={value} value={value}>
                            {label}
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>

            {/* Submit Button with Loading State */}
            <Button
                type="submit"
                variant="contained"
                fullWidth
                disabled={!selectedIlce || scrapeMutation.isLoading}
                sx={{ mt: 3 }}
            >
                {scrapeMutation.isLoading ? (
                    <CircularProgress size={24} color="inherit" />
                ) : (
                    'Scraping Başlat'
                )}
            </Button>

            {/* Error Message with Auto Dismiss */}
            {scrapeMutation.isError && (
                <Alert 
                    severity="error"
                    onClose={() => scrapeMutation.reset()}
                    sx={{ mt: 2 }}
                >
                    {(scrapeMutation.error as any)?.message || 'Bir hata oluştu'}
                </Alert>
            )}

            {/* Success Message with Redirect Info */}
            {scrapeMutation.isSuccess && (
                <Alert severity="success" sx={{ mt: 2 }}>
                    Scraping başarıyla başlatıldı! Search History sayfasına yönlendiriliyorsunuz...
                </Alert>
            )}
        </Box>
    );
};

export default ScrapeForm; 