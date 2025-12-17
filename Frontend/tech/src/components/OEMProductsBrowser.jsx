/**
 * OEM Products Browser Component
 * Displays 693 products from database with advanced filtering
 */
import React, { useState, useEffect } from 'react';
import {
  getOEMProducts,
  getManufacturers,
  getCategories,
  searchOEMProducts,
} from '../services/oemApi';

const OEMProductsBrowser = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  
  // Filters
  const [manufacturer, setManufacturer] = useState('');
  const [category, setCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [voltage, setVoltage] = useState('');
  const [conductorMaterial, setConductorMaterial] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  
  // Filter options
  const [manufacturers, setManufacturers] = useState({});
  const [categories, setCategories] = useState({});

  // Load filter options
  useEffect(() => {
    Promise.all([getManufacturers(), getCategories()])
      .then(([mfgData, catData]) => {
        setManufacturers(mfgData.manufacturers);
        setCategories(catData.categories);
      })
      .catch((err) => console.error('Failed to load filters:', err));
  }, []);

  // Load products
  useEffect(() => {
    loadProducts();
  }, [page, pageSize, manufacturer, category, voltage, conductorMaterial, minPrice, maxPrice]);

  const loadProducts = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      
      if (manufacturer) params.manufacturer = manufacturer;
      if (category) params.category = category;
      if (searchQuery) params.search = searchQuery;
      if (voltage) params.voltage = voltage;
      if (conductorMaterial) params.conductor_material = conductorMaterial;
      if (minPrice) params.min_price = parseFloat(minPrice);
      if (maxPrice) params.max_price = parseFloat(maxPrice);
      
      const data = await getOEMProducts(params);
      
      setProducts(data.products);
      setTotal(data.total);
      setTotalPages(data.total_pages);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1); // Reset to first page
    loadProducts();
  };

  const handleClearFilters = () => {
    setManufacturer('');
    setCategory('');
    setSearchQuery('');
    setVoltage('');
    setConductorMaterial('');
    setMinPrice('');
    setMaxPrice('');
    setPage(1);
  };

  return (
    <div className="oem-products-browser p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">OEM Products Catalog</h1>
        <p className="text-gray-600">
          Browse {total.toLocaleString()} products from Havells, Polycab, KEI, Finolex & RR Kabel
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Filters</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium mb-1">Search</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Product name..."
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>

          {/* Manufacturer */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Manufacturer
            </label>
            <select
              value={manufacturer}
              onChange={(e) => setManufacturer(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="">All Manufacturers</option>
              {Object.entries(manufacturers).map(([name, count]) => (
                <option key={name} value={name}>
                  {name} ({count})
                </option>
              ))}
            </select>
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-medium mb-1">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="">All Categories</option>
              {Object.entries(categories).map(([name, count]) => (
                <option key={name} value={name}>
                  {name} ({count})
                </option>
              ))}
            </select>
          </div>

          {/* Voltage */}
          <div>
            <label className="block text-sm font-medium mb-1">Voltage</label>
            <input
              type="text"
              value={voltage}
              onChange={(e) => setVoltage(e.target.value)}
              placeholder="e.g., 1.1 kV"
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>

          {/* Conductor Material */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Conductor Material
            </label>
            <input
              type="text"
              value={conductorMaterial}
              onChange={(e) => setConductorMaterial(e.target.value)}
              placeholder="e.g., Copper"
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>

          {/* Min Price */}
          <div>
            <label className="block text-sm font-medium mb-1">Min Price (₹)</label>
            <input
              type="number"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
              placeholder="0"
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>

          {/* Max Price */}
          <div>
            <label className="block text-sm font-medium mb-1">Max Price (₹)</label>
            <input
              type="number"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              placeholder="10000"
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>

          {/* Buttons */}
          <div className="flex items-end gap-2">
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Apply
            </button>
            <button
              onClick={handleClearFilters}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading products...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Products Grid */}
      {!loading && !error && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
            {products.map((product) => (
              <div
                key={product.product_id}
                className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow"
              >
                {/* Product Header */}
                <div className="mb-3">
                  <h3 className="font-semibold text-lg mb-1 line-clamp-2">
                    {product.product_name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {product.manufacturer} • {product.model_number}
                  </p>
                </div>

                {/* Category Badge */}
                <div className="mb-3">
                  <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                    {product.category}
                  </span>
                </div>

                {/* Specifications */}
                <div className="mb-3 text-sm">
                  {product.voltage_rating && (
                    <div className="flex justify-between py-1">
                      <span className="text-gray-600">Voltage:</span>
                      <span className="font-medium">{product.voltage_rating}</span>
                    </div>
                  )}
                  {product.conductor_material && (
                    <div className="flex justify-between py-1">
                      <span className="text-gray-600">Conductor:</span>
                      <span className="font-medium">{product.conductor_material}</span>
                    </div>
                  )}
                  {product.conductor_size && (
                    <div className="flex justify-between py-1">
                      <span className="text-gray-600">Size:</span>
                      <span className="font-medium">{product.conductor_size}</span>
                    </div>
                  )}
                </div>

                {/* Price */}
                <div className="flex justify-between items-center pt-3 border-t">
                  <div>
                    <p className="text-xs text-gray-500">Price/Meter</p>
                    <p className="text-xl font-bold text-green-600">
                      ₹{product.unit_price.toFixed(2)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">Stock</p>
                    <p className="text-sm font-medium">{product.stock_quantity}</p>
                  </div>
                </div>

                {/* Delivery */}
                <div className="mt-2 text-xs text-gray-500">
                  Delivery: {product.delivery_days} days
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600">
              Showing {(page - 1) * pageSize + 1} to{' '}
              {Math.min(page * pageSize, total)} of {total.toLocaleString()} products
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>

              <span className="px-3 py-1">
                Page {page} of {totalPages}
              </span>

              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>

              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setPage(1);
                }}
                className="ml-4 px-3 py-1 border rounded"
              >
                <option value="25">25 per page</option>
                <option value="50">50 per page</option>
                <option value="100">100 per page</option>
              </select>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default OEMProductsBrowser;
