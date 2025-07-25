import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { productsApi, ordersApi, handleApiError } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import ProductForm from '../components/products/ProductForm';
import ProductOrders from '../components/products/ProductOrders';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useToast } from '../components/ui/use-toast';
import { 
  ArrowLeft, 
  Save, 
  Trash2, 
  FileEdit,
  ShoppingCart
} from 'lucide-react';

const ProductDetail = ({ isNew = false }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  
  // State
  const [product, setProduct] = useState(null);
  const [productOrders, setProductOrders] = useState([]);
  const [families, setFamilies] = useState([]);
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(isNew);
  const [activeTab, setActiveTab] = useState('details');
  
  // Fetch product details
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch families and tags
        const [familiesRes, tagsRes] = await Promise.all([
          productsApi.getProductFamilies(),
          productsApi.getProductTags()
        ]);
        
        setFamilies(familiesRes.data || []);
        setTags(tagsRes.data || []);
        
        if (!isNew) {
          const productRes = await productsApi.getProduct(id);
          setProduct(productRes.data);
          
          // Fetch product orders
          fetchProductOrders(id);
        } else {
          // Initialize new product
          setProduct({
            name: '',
            description: '',
            sku: '',
            family_id: '',
            price: 0,
            cost: 0,
            lead_time_days: 30,
            tags: []
          });
        }
      } catch (err) {
        console.error('Failed to fetch product data:', err);
        setError(handleApiError(err));
        toast({
          title: 'Error',
          description: handleApiError(err),
          variant: 'destructive'
        });
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [id, isNew, toast]);
  
  // Fetch product orders
  const fetchProductOrders = async (productId) => {
    try {
      setOrdersLoading(true);
      
      const response = await ordersApi.getOrders({ product_id: productId });
      setProductOrders(response.data.orders || []);
    } catch (err) {
      console.error('Failed to fetch product orders:', err);
      toast({
        title: 'Warning',
        description: 'Failed to load product orders',
        variant: 'warning'
      });
    } finally {
      setOrdersLoading(false);
    }
  };
  
  // Handle form change
  const handleFormChange = (field, value) => {
    setProduct(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  // Handle save
  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      
      // Validate required fields
      const requiredFields = ['name', 'sku', 'family_id', 'price'];
      const missingFields = requiredFields.filter(field => !product[field]);
      
      if (missingFields.length > 0) {
        throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
      }
      
      let savedProduct;
      
      if (isNew) {
        // Create new product
        const response = await productsApi.createProduct(product);
        savedProduct = response.data;
        toast({
          title: 'Success',
          description: 'Product created successfully',
          variant: 'success'
        });
      } else {
        // Update existing product
        const response = await productsApi.updateProduct(id, product);
        savedProduct = response.data;
        toast({
          title: 'Success',
          description: 'Product updated successfully',
          variant: 'success'
        });
      }
      
      // If new product, navigate to the saved product
      if (isNew) {
        navigate(`/products/${savedProduct.id}`);
      } else {
        // Update local state and exit edit mode
        setProduct(savedProduct);
        setIsEditing(false);
      }
    } catch (err) {
      console.error('Failed to save product:', err);
      setError(handleApiError(err));
      toast({
        title: 'Error',
        description: handleApiError(err),
        variant: 'destructive'
      });
    } finally {
      setSaving(false);
    }
  };
  
  // Handle delete
  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this product?')) {
      return;
    }
    
    try {
      setSaving(true);
      setError(null);
      
      await productsApi.deleteProduct(id);
      
      toast({
        title: 'Success',
        description: 'Product deleted successfully',
        variant: 'success'
      });
      
      navigate('/products');
    } catch (err) {
      console.error('Failed to delete product:', err);
      setError(handleApiError(err));
      toast({
        title: 'Error',
        description: handleApiError(err),
        variant: 'destructive'
      });
    } finally {
      setSaving(false);
    }
  };
  
  // Handle create order for this product
  const handleCreateOrder = () => {
    navigate('/orders/new', { state: { product_id: id } });
  };
  
  // Check permissions
  const canEdit = user?.role === 'admin';
  
  // If loading
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/products')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Products
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              {isNew ? 'New Product' : product?.name}
            </h1>
            {!isNew && product && (
              <p className="text-gray-600">
                {product.sku} - {product.family_name}
              </p>
            )}
          </div>
        </div>
        <div className="flex space-x-2">
          {!isNew && !isEditing && canEdit && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(true)}
            >
              <FileEdit className="w-4 h-4 mr-2" />
              Edit
            </Button>
          )}
          
          {(isNew || isEditing) && (
            <Button
              variant="default"
              size="sm"
              onClick={handleSave}
              disabled={saving}
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Saving...' : 'Save'}
            </Button>
          )}
          
          {!isNew && !isEditing && canEdit && (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleDelete}
              disabled={saving}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          )}
          
          {!isNew && !isEditing && (
            <Button
              variant="default"
              size="sm"
              onClick={handleCreateOrder}
            >
              <ShoppingCart className="w-4 h-4 mr-2" />
              New Order
            </Button>
          )}
        </div>
      </div>
      
      {/* Error display */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}
      
      {/* Content */}
      {product && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="details">
              <FileEdit className="w-4 h-4 mr-2" />
              Product Details
            </TabsTrigger>
            {!isNew && (
              <TabsTrigger value="orders">
                <ShoppingCart className="w-4 h-4 mr-2" />
                Orders
              </TabsTrigger>
            )}
          </TabsList>
          
          <TabsContent value="details" className="mt-4">
            <div className="bg-white p-6 rounded-md border shadow-sm">
              <ProductForm
                product={product}
                families={families}
                tags={tags}
                onChange={handleFormChange}
                isEditing={isEditing || isNew}
                isNew={isNew}
              />
            </div>
          </TabsContent>
          
          {!isNew && (
            <TabsContent value="orders" className="mt-4">
              <div className="bg-white p-6 rounded-md border shadow-sm">
                <ProductOrders
                  orders={productOrders}
                  loading={ordersLoading}
                  onCreateOrder={handleCreateOrder}
                />
              </div>
            </TabsContent>
          )}
        </Tabs>
      )}
    </div>
  );
};

export default ProductDetail;

