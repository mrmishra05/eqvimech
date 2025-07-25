import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { customersApi, ordersApi, handleApiError } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import CustomerForm from '../components/customers/CustomerForm';
import CustomerOrders from '../components/customers/CustomerOrders';
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

const CustomerDetail = ({ isNew = false }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  
  // State
  const [customer, setCustomer] = useState(null);
  const [customerOrders, setCustomerOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(isNew);
  const [activeTab, setActiveTab] = useState('details');
  
  // Fetch customer details
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        if (!isNew) {
          const customerRes = await customersApi.getCustomer(id);
          setCustomer(customerRes.data);
          
          // Fetch customer orders
          fetchCustomerOrders(id);
        } else {
          // Initialize new customer
          setCustomer({
            name: '',
            contact_person: '',
            email: '',
            phone: '',
            address: '',
            city: '',
            state: '',
            pincode: '',
            gstin: ''
          });
        }
      } catch (err) {
        console.error('Failed to fetch customer data:', err);
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
  
  // Fetch customer orders
  const fetchCustomerOrders = async (customerId) => {
    try {
      setOrdersLoading(true);
      
      const response = await ordersApi.getOrders({ customer_id: customerId });
      setCustomerOrders(response.data.orders || []);
    } catch (err) {
      console.error('Failed to fetch customer orders:', err);
      toast({
        title: 'Warning',
        description: 'Failed to load customer orders',
        variant: 'warning'
      });
    } finally {
      setOrdersLoading(false);
    }
  };
  
  // Handle form change
  const handleFormChange = (field, value) => {
    setCustomer(prev => ({
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
      const requiredFields = ['name', 'contact_person', 'email', 'phone'];
      const missingFields = requiredFields.filter(field => !customer[field]);
      
      if (missingFields.length > 0) {
        throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
      }
      
      let savedCustomer;
      
      if (isNew) {
        // Create new customer
        const response = await customersApi.createCustomer(customer);
        savedCustomer = response.data;
        toast({
          title: 'Success',
          description: 'Customer created successfully',
          variant: 'success'
        });
      } else {
        // Update existing customer
        const response = await customersApi.updateCustomer(id, customer);
        savedCustomer = response.data;
        toast({
          title: 'Success',
          description: 'Customer updated successfully',
          variant: 'success'
        });
      }
      
      // If new customer, navigate to the saved customer
      if (isNew) {
        navigate(`/customers/${savedCustomer.id}`);
      } else {
        // Update local state and exit edit mode
        setCustomer(savedCustomer);
        setIsEditing(false);
      }
    } catch (err) {
      console.error('Failed to save customer:', err);
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
    if (!window.confirm('Are you sure you want to delete this customer?')) {
      return;
    }
    
    try {
      setSaving(true);
      setError(null);
      
      await customersApi.deleteCustomer(id);
      
      toast({
        title: 'Success',
        description: 'Customer deleted successfully',
        variant: 'success'
      });
      
      navigate('/customers');
    } catch (err) {
      console.error('Failed to delete customer:', err);
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
  
  // Handle create order for customer
  const handleCreateOrder = () => {
    navigate('/orders/new', { state: { customer_id: id } });
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
            onClick={() => navigate('/customers')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Customers
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              {isNew ? 'New Customer' : customer?.name}
            </h1>
            {!isNew && customer && (
              <p className="text-gray-600">
                {customer.city}, {customer.state}
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
      {customer && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="details">
              <FileEdit className="w-4 h-4 mr-2" />
              Customer Details
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
              <CustomerForm
                customer={customer}
                onChange={handleFormChange}
                isEditing={isEditing || isNew}
                isNew={isNew}
              />
            </div>
          </TabsContent>
          
          {!isNew && (
            <TabsContent value="orders" className="mt-4">
              <div className="bg-white p-6 rounded-md border shadow-sm">
                <CustomerOrders
                  orders={customerOrders}
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

export default CustomerDetail;

