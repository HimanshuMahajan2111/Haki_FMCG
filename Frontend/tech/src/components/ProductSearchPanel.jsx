 
import React, { useState } from 'react';
import { useProductSearch } from '../hooks/useRFPApi';
import { Search, Filter, X, ShoppingCart, Info } from 'lucide-react';

export default function ProductSearchPanel() {
  const [searchParams, setSearchParams] = useState({
    query: '',
    category: '',
    min_price: '',
    max_price: '',
    in_stock: true,
    limit: 20
  });

  const [activeSearch, setActiveSearch] = useState(null);
  const { products, isLoading, error } = useProductSearch(activeSearch);

  const handleSearch = (e) => {
    e.preventDefault();
    // Only search if there's a query or filters
    if (searchParams.query || searchParams.category || searchParams.min_price || searchParams.max_price) {
      const params = {
        ...searchParams,
        min_price: searchParams.min_price ? parseFloat(searchParams.min_price) : undefined,
        max_price: searchParams.max_price ? parseFloat(searchParams.max_price) : undefined
      };
      setActiveSearch(params);
    }
  };

  const handleClearFilters = () => {
    const clearedParams = {
      query: '',
      category: '',
      min_price: '',
      max_price: '',
      in_stock: true,
      limit: 20
    };
    setSearchParams(clearedParams);
    setActiveSearch(null);
  };

  const handleInputChange = (key, value) => {
    setSearchParams(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Product Search</h1>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="bg-white rounded-lg shadow-sm p-6 mb-6">
        {/* Main Search Bar */}
        <div className="flex gap-2 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search products by name, code, or description..."
              value={searchParams.query}
              onChange={(e) => handleInputChange('query', e.target.value)}
              className="w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={searchParams.category}
              onChange={(e) => handleInputChange('category', e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              <option value="cables">Cables</option>
              <option value="wires">Wires</option>
              <option value="switches">Switches</option>
              <option value="lighting">Lighting</option>
              <option value="accessories">Accessories</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Min Price (₹)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              value={searchParams.min_price}
              onChange={(e) => handleInputChange('min_price', e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Price (₹)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              placeholder="10000.00"
              value={searchParams.max_price}
              onChange={(e) => handleInputChange('max_price', e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Results per page
            </label>
            <select
              value={searchParams.limit}
              onChange={(e) => handleInputChange('limit', parseInt(e.target.value))}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </div>
        </div>

        {/* Stock Filter */}
        <div className="mt-4 flex items-center gap-2">
          <input
            type="checkbox"
            id="in_stock"
            checked={searchParams.in_stock}
            onChange={(e) => handleInputChange('in_stock', e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
          />
          <label htmlFor="in_stock" className="text-sm text-gray-700">
            Show only products in stock
          </label>
        </div>

        {/* Clear Filters */}
        {activeSearch && (
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={handleClearFilters}
              className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
            >
              <X className="w-4 h-4" />
              Clear all filters
            </button>
          </div>
        )}
      </form>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">Error: {error.message}</p>
        </div>
      )}

      {/* Results */}
      {!activeSearch && !isLoading && (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Enter search criteria to find products</p>
        </div>
      )}

      {activeSearch && !isLoading && products.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <p className="text-gray-500">No products found matching your criteria</p>
        </div>
      )}

      {products.length > 0 && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <p className="text-sm text-gray-600">
              Found <span className="font-semibold">{products.length}</span> products
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Product Card Component
function ProductCard({ product }) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
      <div className="p-4">
        {/* Product Header */}
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-semibold text-lg line-clamp-2">{product.name}</h3>
          {product.in_stock ? (
            <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
              In Stock
            </span>
          ) : (
            <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">
              Out of Stock
            </span>
          )}
        </div>

        {/* Product Code */}
        {product.code && (
          <p className="text-sm text-gray-600 mb-2">Code: {product.code}</p>
        )}

        {/* Category */}
        {product.category && (
          <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded mb-3">
            {product.category}
          </span>
        )}

        {/* Price */}
        <div className="mb-3">
          <span className="text-2xl font-bold text-blue-600">
            ₹{product.price?.toLocaleString() || 'N/A'}
          </span>
          {product.unit && (
            <span className="text-sm text-gray-600 ml-1">per {product.unit}</span>
          )}
        </div>

        {/* Description */}
        {product.description && (
          <p className="text-sm text-gray-600 line-clamp-2 mb-3">
            {product.description}
          </p>
        )}

        {/* Stock Quantity */}
        {product.stock_quantity !== undefined && (
          <p className="text-sm text-gray-600 mb-3">
            Available: <span className="font-medium">{product.stock_quantity}</span> units
          </p>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium">
            <ShoppingCart className="w-4 h-4" />
            Add to RFP
          </button>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
            title="View Details"
          >
            <Info className="w-4 h-4" />
          </button>
        </div>

        {/* Expandable Details */}
        {showDetails && (
          <div className="mt-4 pt-4 border-t">
            <h4 className="font-medium text-sm mb-2">Specifications</h4>
            {product.specifications ? (
              <pre className="text-xs text-gray-600 whitespace-pre-wrap bg-gray-50 p-2 rounded">
                {JSON.stringify(product.specifications, null, 2)}
              </pre>
            ) : (
              <p className="text-xs text-gray-500">No specifications available</p>
            )}

            {product.manufacturer && (
              <div className="mt-2">
                <span className="text-xs text-gray-600">Manufacturer: </span>
                <span className="text-xs font-medium">{product.manufacturer}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
