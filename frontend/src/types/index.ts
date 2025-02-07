export enum PropertyStatus {
    SATILIK = "satilik",
    KIRALIK = "kiralik"
}

export enum PropertyCategory {
    KONUT = "konut",
    ARSA = "arsa",
    ISYERI = "isyeri",
    DEVREMULK = "devremulk",
    TURISTIK = "turistik-isletme"
}

export interface ScrapeRequest {
    ilce: string;
    durum: PropertyStatus;
    kategori?: PropertyCategory;
    mahalleler?: string[];
}

export interface LocationData {
    iller: string[];
    ilceler: { [key: string]: string[] };  // il -> ilçeler
    mahalleler: { [key: string]: string[] };  // ilçe -> mahalleler
}

export interface CategoryData {
    categories: PropertyCategory[];
    status_types: PropertyStatus[];
}

export interface Property {
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
    raw_data?: any;
}

export interface PaginatedResponse {
    items: Property[];
    total: number;
    page: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
} 