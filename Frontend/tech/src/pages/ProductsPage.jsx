/**
 * OEM Products Page - Browse 693 products from database
 */
import React, { useState, useEffect } from 'react';
import { Package, Search, Filter, Download, RefreshCw, Plus } from 'lucide-react';
import {
  getOEMProducts,
  getManufacturers,
  getCategories,
  getStatistics,
  searchOEMProducts,
} from '../services/oemApi';
import AddProductModal from '../components/AddProductModal';

const ProductsPage = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  
  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  
  // Filters
  const [manufacturer, setManufacturer] = useState('');
  const [category, setCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(true);
  
  // Add Product Modal
  const [showAddModal, setShowAddModal] = useState(false);
  
  // Filter options
  const [manufacturers, setManufacturers] = useState({});
  const [categories, setCategories] = useState({});

  useEffect(() => {
    loadStats();
    loadFilterOptions();
    loadProducts(); // Load products on mount
  }, []);

  // Removed auto-reload on dependency changes - only use manual refresh or search button

  const loadStats = async () => {
    try {
      const data = await getStatistics();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const loadFilterOptions = async () => {
    try {
      const [mfgData, catData] = await Promise.all([
        getManufacturers(),
        getCategories(),
      ]);
      setManufacturers(mfgData.manufacturers);
      setCategories(catData.categories);
    } catch (err) {
      console.error('Failed to load filters:', err);
    }
  };

  const loadProducts = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      
      if (manufacturer) params.manufacturer = manufacturer;
      if (category) params.category = category;
      if (searchQuery) params.search = searchQuery;
      
      const data = await getOEMProducts(params);
      
      // Only update if data actually changed to prevent infinite loops
      if (JSON.stringify(data.products) !== JSON.stringify(products)) {
        setProducts(data.products);
        setTotal(data.total);
        setTotalPages(data.total_pages);
      }
    } catch (err) {
      console.error('Failed to load products:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    setTimeout(() => loadProducts(), 100);
  };

  const handlePageChange = (newPage) => {
    setPage(newPage);
    setTimeout(() => loadProducts(), 100);
  };

  const handlePageSizeChange = (newSize) => {
    setPageSize(newSize);
    setPage(1);
    setTimeout(() => loadProducts(), 100);
  };

  const handleClear = () => {
    setManufacturer('');
    setCategory('');
    setSearchQuery('');
    setPage(1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-800 to-dark-900">
      {/* Header */}
      <div className="bg-dark-900/50 backdrop-blur-xl border-b border-dark-700/50 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">OEM Products Catalog</h1>
            <p className="text-gray-400">
              Browse {total?.toLocaleString() || '693'} products from 5 manufacturers
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              <Plus size={16} />
              Add Product
            </button>
            <button
              onClick={loadProducts}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
            >
              <RefreshCw size={16} />
              Refresh
            </button>
          </div>
        </div>

        {/* Statistics Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-dark-800/50 backdrop-blur p-4 rounded-lg border border-dark-700/50">
              <div className="text-gray-400 text-sm mb-1">Total Products</div>
              <div className="text-2xl font-bold text-white">
                {stats.total_products}
              </div>
            </div>
            {Object.entries(stats.manufacturers).slice(0, 4).map(([mfg, count]) => (
              <div key={mfg} className="bg-dark-800/50 backdrop-blur p-4 rounded-lg border border-dark-700/50">
                <div className="text-gray-400 text-sm mb-1">{mfg}</div>
                <div className="text-2xl font-bold text-primary-400">{count}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="p-6">
        {/* Filters */}
        <div className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 mb-6">
          <div
            className="flex items-center justify-between p-4 cursor-pointer"
            onClick={() => setShowFilters(!showFilters)}
          >
            <div className="flex items-center gap-2">
              <Filter size={20} className="text-primary-400" />
              <h2 className="text-lg font-semibold text-white">Filters</h2>
            </div>
            <span className="text-gray-400">{showFilters ? '▼' : '▶'}</span>
          </div>

          {showFilters && (
            <div className="p-4 pt-0 border-t border-dark-700/50">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Search */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Search
                  </label>
                  <div className="relative">
                    <Search
                      size={16}
                      className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                    />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                      placeholder="Product name..."
                      className="w-full pl-10 pr-3 py-2 bg-dark-700/50 border border-dark-600 rounded-lg text-white placeholder-gray-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Manufacturer */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Manufacturer
                  </label>
                  <select
                    value={manufacturer}
                    onChange={(e) => {
                      setManufacturer(e.target.value);
                      setPage(1);
                    }}
                    className="w-full px-3 py-2 bg-dark-700/50 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
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
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => {
                      setCategory(e.target.value);
                      setPage(1);
                    }}
                    className="w-full px-3 py-2 bg-dark-700/50 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">All Categories</option>
                    {Object.entries(categories).map(([name, count]) => (
                      <option key={name} value={name}>
                        {name} ({count})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Buttons */}
                <div className="flex items-end gap-2">
                  <button
                    onClick={handleSearch}
                    className="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
                  >
                    Apply
                  </button>
                  <button
                    onClick={handleClear}
                    className="flex-1 px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors"
                  >
                    Clear
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Loading */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
            <p className="mt-4 text-gray-400">Loading products...</p>
          </div>
        )}

        {/* Products Grid */}
        {!loading && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
              {products.map((product) => (
                <div
                  key={product.product_id}
                  className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-5 hover:border-primary-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary-500/10"
                >
                  {/* Header */}
                  <div className="mb-4">
                    <h3 className="font-semibold text-lg text-white mb-2 line-clamp-2">
                      {product.product_name}
                    </h3>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-gray-400">{product.manufacturer}</span>
                      <span className="text-gray-600">•</span>
                      <span className="text-gray-500 text-xs">{product.model_number}</span>
                    </div>
                  </div>

                  {/* Category */}
                  <div className="mb-4">
                    <span className="inline-block px-3 py-1 text-xs bg-primary-500/20 text-primary-300 rounded-full border border-primary-500/30">
                      {product.category}
                    </span>
                  </div>

                  {/* Specs */}
                  <div className="space-y-2 mb-4 text-sm">
                    {product.voltage_rating && (
                      <div className="flex justify-between">
                        <span className="text-gray-400">Voltage:</span>
                        <span className="text-white font-medium">{product.voltage_rating}</span>
                      </div>
                    )}
                    {product.conductor_material && (
                      <div className="flex justify-between">
                        <span className="text-gray-400">Conductor:</span>
                        <span className="text-white font-medium">{product.conductor_material}</span>
                      </div>
                    )}
                    {product.conductor_size && (
                      <div className="flex justify-between">
                        <span className="text-gray-400">Size:</span>
                        <span className="text-white font-medium">{product.conductor_size}</span>
                      </div>
                    )}
                  </div>

                  {/* Footer */}
                  <div className="flex justify-between items-center pt-4 border-t border-dark-700/50">
                    <div>
                      <p className="text-xs text-gray-500">Price/Meter</p>
                      <p className="text-xl font-bold text-green-400">
                        ₹{product.unit_price.toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">Stock</p>
                      <p className="text-sm font-medium text-white">{product.stock_quantity}</p>
                    </div>
                  </div>

                  <div className="mt-2 text-xs text-gray-500">
                    Delivery: {product.delivery_days} days
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-4">
              <div className="text-sm text-gray-400">
                Showing {(page - 1) * pageSize + 1} to{' '}
                {Math.min(page * pageSize, total)} of {total.toLocaleString()} products
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => handlePageChange(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>

                <span className="text-white">
                  Page {page} of {totalPages}
                </span>

                <button
                  onClick={() => handlePageChange(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>

                <select
                  value={pageSize}
                  onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                  className="ml-2 px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500"
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

      {/* Add Product Modal */}
      <AddProductModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={(newProduct) => {
          console.log('Product added:', newProduct);
          // Reload products to show the new one
          loadProducts();
          loadStats();
        }}
      />
    </div>
  );
};

export default ProductsPage;
