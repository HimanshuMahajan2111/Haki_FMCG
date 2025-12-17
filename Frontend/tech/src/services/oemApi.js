/**
 * OEM Products API Service - Optimized for 693 database products
 * 
 * Provides access to Havells, Polycab, KEI, Finolex, and RR Kabel products
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD ? '' : 'http://localhost:8000');

const oemApi = axios.create({
  baseURL: `${API_BASE_URL}/api/oem`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Error interceptor
oemApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('OEM API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Get OEM products with pagination and filtering
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number (starts at 1)
 * @param {number} params.page_size - Items per page (max 100)
 * @param {string} params.manufacturer - Filter by manufacturer
 * @param {string} params.category - Filter by category
 * @param {string} params.search - Search in product names
 * @param {string} params.voltage - Filter by voltage rating
 * @param {string} params.conductor_material - Filter by conductor material
 * @param {number} params.min_price - Minimum price filter
 * @param {number} params.max_price - Maximum price filter
 * @returns {Promise<Object>} Product list with pagination
 */
export const getOEMProducts = async (params = {}) => {
  const {
    page = 1,
    page_size = 50,
    manufacturer,
    category,
    search,
    voltage,
    conductor_material,
    min_price,
    max_price,
  } = params;

  const queryParams = new URLSearchParams();
  queryParams.append('page', page);
  queryParams.append('page_size', page_size);
  
  if (manufacturer) queryParams.append('manufacturer', manufacturer);
  if (category) queryParams.append('category', category);
  if (search) queryParams.append('search', search);
  if (voltage) queryParams.append('voltage', voltage);
  if (conductor_material) queryParams.append('conductor_material', conductor_material);
  if (min_price !== undefined) queryParams.append('min_price', min_price);
  if (max_price !== undefined) queryParams.append('max_price', max_price);

  const response = await oemApi.get(`/products?${queryParams.toString()}`);
  return response.data;
};

/**
 * Get a specific product by ID
 * @param {string} productId - Product ID
 * @returns {Promise<Object>} Product details
 */
export const getOEMProductById = async (productId) => {
  const response = await oemApi.get(`/products/${productId}`);
  return response.data;
};

/**
 * Search products by query
 * @param {string} query - Search query (min 2 chars)
 * @param {number} limit - Maximum results (default 20)
 * @returns {Promise<Object>} Search results
 */
export const searchOEMProducts = async (query, limit = 20) => {
  const response = await oemApi.get(`/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  return response.data;
};

/**
 * Get all manufacturers with product counts
 * @returns {Promise<Object>} Manufacturers dictionary
 */
export const getManufacturers = async () => {
  const response = await oemApi.get('/manufacturers');
  return response.data;
};

/**
 * Get all categories with product counts
 * @returns {Promise<Object>} Categories dictionary
 */
export const getCategories = async () => {
  const response = await oemApi.get('/categories');
  return response.data;
};

/**
 * Get product statistics
 * @returns {Promise<Object>} Statistics with counts
 */
export const getStatistics = async () => {
  const response = await oemApi.get('/statistics');
  return response.data;
};

/**
 * Get all voltage ratings with counts
 * @returns {Promise<Object>} Voltage ratings dictionary
 */
export const getVoltageRatings = async () => {
  const response = await oemApi.get('/voltage-ratings');
  return response.data;
};

/**
 * Get all conductor materials with counts
 * @returns {Promise<Object>} Conductor materials dictionary
 */
export const getConductorMaterials = async () => {
  const response = await oemApi.get('/conductor-materials');
  return response.data;
};

/**
 * Hook for manufacturers (for React components)
 */
export const useManufacturers = () => {
  const [manufacturers, setManufacturers] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    getManufacturers()
      .then((data) => {
        const mfgList = Object.entries(data.manufacturers).map(([name, count]) => ({
          name,
          count,
        }));
        setManufacturers(mfgList);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });
  }, []);

  return { manufacturers, loading, error };
};

export default {
  getOEMProducts,
  getOEMProductById,
  searchOEMProducts,
  getManufacturers,
  getCategories,
  getStatistics,
  getVoltageRatings,
  getConductorMaterials,
};
