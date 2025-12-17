/**
 * Add Product Modal Component
 * Allows adding new products to the database
 */
import React, { useState } from 'react';
import { X, Save, AlertCircle } from 'lucide-react';

const AddProductModal = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    manufacturer: '',
    product_name: '',
    model_number: '',
    category: '',
    sub_category: '',
    voltage_rating: '',
    conductor_material: '',
    conductor_size: '',
    insulation_type: '',
    list_price: '',
    unit: 'meter',
    stock_quantity: '',
    delivery_days: '7',
    description: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleChange = (e) => {
    e.stopPropagation();
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Validate required fields
      if (!formData.manufacturer || !formData.product_name) {
        setError('Please fill in all required fields (Manufacturer and Product Name)');
        setLoading(false);
        return;
      }

      // Prepare data for API (convert to backend schema)
      const productData = {
        manufacturer: formData.manufacturer,
        product_code: formData.model_number || `${formData.manufacturer}-${Date.now()}`, // Use model_number as product_code
        product_name: formData.product_name,
        model_number: formData.model_number,
        category: formData.category,
        subcategory: formData.sub_category,
        list_price: parseFloat(formData.list_price) || 0,
        voltage_rating: formData.voltage_rating || '',
        conductor_material: formData.conductor_material || '',
        conductor_size: formData.conductor_size || '',
        insulation_type: formData.insulation_type || '',
        unit: formData.unit,
        stock_quantity: parseInt(formData.stock_quantity) || 0,
        delivery_days: parseInt(formData.delivery_days) || 7,
        description: formData.description || '',
      };

      const response = await fetch('http://localhost:8000/api/products/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(productData),
      });

      let errorData;
      try {
        errorData = await response.json();
      } catch (parseError) {
        errorData = { detail: 'Server returned invalid response' };
      }

      if (!response.ok) {
        let errorMessage = 'Failed to add product';
        
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' 
            ? errorData.detail 
            : JSON.stringify(errorData.detail);
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else {
          errorMessage = `Failed to add product (Status: ${response.status})`;
        }
        
        setError(errorMessage);
        setLoading(false);
        return;
      }

      setSuccess(true);
      
      // Call success callback
      if (onSuccess) {
        onSuccess(errorData);
      }

      // Reset form and close after 1.5 seconds
      setTimeout(() => {
        resetForm();
        onClose();
      }, 1500);

    } catch (err) {
      console.error('Error adding product:', err);
      let errorMessage = 'An unexpected error occurred';
      
      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      } else if (err && typeof err === 'object') {
        errorMessage = JSON.stringify(err);
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      manufacturer: '',
      product_name: '',
      model_number: '',
      category: '',
      sub_category: '',
      voltage_rating: '',
      conductor_material: '',
      conductor_size: '',
      insulation_type: '',
      list_price: '',
      unit: 'meter',
      stock_quantity: '',
      delivery_days: '7',
      description: '',
    });
    setError(null);
    setSuccess(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" onClick={(e) => e.stopPropagation()}>
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-white z-10">
          <h2 className="text-2xl font-bold text-gray-900">Add New Product</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} onReset={(e) => e.preventDefault()} className="p-6">
          {/* Success Message */}
          {success && (
            <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg flex items-center gap-2">
              <Save size={20} />
              <span>Product added successfully!</span>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg flex items-center gap-2">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {/* Basic Information */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Basic Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Manufacturer <span className="text-red-500">*</span>
                </label>
                <select
                  name="manufacturer"
                  value={formData.manufacturer}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Manufacturer</option>
                  <option value="Havells">Havells</option>
                  <option value="Polycab">Polycab</option>
                  <option value="KEI">KEI</option>
                  <option value="Finolex">Finolex</option>
                  <option value="RR Kabel">RR Kabel</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Product Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="product_name"
                  value={formData.product_name}
                  onChange={handleChange}
                  required
                  placeholder="e.g., HRFR Cable 1.5 sq mm"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model Number
                </label>
                <input
                  type="text"
                  name="model_number"
                  value={formData.model_number}
                  onChange={handleChange}
                  placeholder="e.g., HAV-HRFR-1.5"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category <span className="text-red-500">*</span>
                </label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Category</option>
                  <option value="Cables">Cables</option>
                  <option value="Wires">Wires</option>
                  <option value="Switches">Switches</option>
                  <option value="Lighting">Lighting</option>
                  <option value="Fans">Fans</option>
                  <option value="Switchgear">Switchgear</option>
                  <option value="Motors">Motors</option>
                  <option value="Appliances">Appliances</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sub Category
                </label>
                <input
                  type="text"
                  name="sub_category"
                  value={formData.sub_category}
                  onChange={handleChange}
                  placeholder="e.g., House Wires, Industrial Cables"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Technical Specifications */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Technical Specifications</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Voltage Rating
                </label>
                <input
                  type="text"
                  name="voltage_rating"
                  value={formData.voltage_rating}
                  onChange={handleChange}
                  placeholder="e.g., 1100V, 440V"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Conductor Material
                </label>
                <select
                  name="conductor_material"
                  value={formData.conductor_material}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Material</option>
                  <option value="Copper">Copper</option>
                  <option value="Aluminum">Aluminum</option>
                  <option value="Tinned Copper">Tinned Copper</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Conductor Size
                </label>
                <input
                  type="text"
                  name="conductor_size"
                  value={formData.conductor_size}
                  onChange={handleChange}
                  placeholder="e.g., 1.5 sq mm, 2.5 sq mm"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Insulation Type
                </label>
                <input
                  type="text"
                  name="insulation_type"
                  value={formData.insulation_type}
                  onChange={handleChange}
                  placeholder="e.g., PVC, XLPE, FR"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Pricing & Inventory */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Pricing & Inventory</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  List Price (₹) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="list_price"
                  value={formData.list_price}
                  onChange={handleChange}
                  required
                  step="0.01"
                  min="0"
                  placeholder="e.g., 125.50"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Unit
                </label>
                <select
                  name="unit"
                  value={formData.unit}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="meter">Meter</option>
                  <option value="piece">Piece</option>
                  <option value="box">Box</option>
                  <option value="roll">Roll</option>
                  <option value="set">Set</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stock Quantity
                </label>
                <input
                  type="number"
                  name="stock_quantity"
                  value={formData.stock_quantity}
                  onChange={handleChange}
                  min="0"
                  placeholder="e.g., 1000"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Delivery Days
                </label>
                <input
                  type="number"
                  name="delivery_days"
                  value={formData.delivery_days}
                  onChange={handleChange}
                  min="1"
                  placeholder="e.g., 7"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Description */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="3"
              placeholder="Enter product description..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={() => {
                resetForm();
                onClose();
              }}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || success}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Adding...
                </>
              ) : success ? (
                <>
                  <Save size={16} />
                  Added!
                </>
              ) : (
                <>
                  <Save size={16} />
                  Add Product
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddProductModal;
