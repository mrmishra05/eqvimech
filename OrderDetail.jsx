import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ordersApi, customersApi, productsApi, handleApiError } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import OrderForm from '../components/orders/OrderForm';
import OrderTimeline from '../components/orders/OrderTimeline';
import OrderPayment from '../components/orders/OrderPayment';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useToast } from '../components/ui/use-toast';
import { 
  ArrowLeft, 
  Save, 
  Trash2, 
  Clock, 
  IndianRupee, 
  FileEdit,
  CheckCircle
} from 'lucide-react';

const OrderDetail = ({ isNew = false }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  
  // State
  const [order, setOrder] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(isNew);
  const [activeTab, setActiveTab] = useState('details');
  
  // Fetch order details
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch customers, products, and statuses
        const [customersRes, productsRes, statusesRes] = await Promise.all([
          customersApi.getCustomers(),
          productsApi.getProducts(),
          ordersApi.getOrderStatuses()
        ]);
        
        setCustomers(customersRes.data.customers || []);
        setProducts(productsRes.data.products || []);
        setStatuses(statusesRes.data || []);
        
        // If not a new order, fetch order details
        if (!isNew) {
          const orderRes = await ordersApi.getOrder(id);
          setOrder(orderRes.data);
        } else {
          // Initialize new order
          setOrder({
            product_id: '',
            customer_id: '',
            start_date: new Date().toISOString().split('T')[0],
            delivery_date: '',
            status: 'Raw Material Ordered',
            amount: 0,
            amount_received: 0,
            notes: ''
          });
        }
      } catch (err) {
        console.error('Failed to fetch data:', err);
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
  
  // Handle form change
  const handleFormChange = (field, value) => {
    setOrder(prev => ({
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
      const requiredFields = ['product_id', 'customer_id', 'delivery_date', 'amount'];
      const missingFields = requiredFields.filter(field => !order[field]);
      
      if (missingFields.length > 0) {
        throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
      }
      
      let savedOrder;
      
      if (isNew) {
        // Create new order
        const response = await ordersApi.createOrder(order);
        savedOrder = response.data;
        toast({
          title: 'Success',
          description: 'Order created successfully',
          variant: 'success'
        });
      } else {
        // Update existing order
        const response = await ordersApi.updateOrder(id, order);
        savedOrder = response.data;
        toast({
          title: 'Success',
          description: 'Order updated successfully',
          variant: 'success'
        });
      }
      
      // If new order, navigate to the saved order
      if (isNew) {
        navigate(`/orders/${savedOrder.id}`);
      } else {
        // Update local state and exit edit mode
        setOrder(savedOrder);
        setIsEditing(false);
      }
    } catch (err) {
      console.error('Failed to save order:', err);
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
    if (!window.confirm('Are you sure you want to delete this order?')) {
      return;
    }
    
    try {
      setSaving(true);
      setError(null);
      
      await ordersApi.deleteOrder(id);
      
      toast({
        title: 'Success',
        description: 'Order deleted successfully',
        variant: 'success'
      });
      
      navigate('/orders');
    } catch (err) {
      console.error('Failed to delete order:', err);
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
  
  // Handle status update
  const handleStatusUpdate = async (newStatus, notes = '') => {
    try {
      setSaving(true);
      setError(null);
      
      const updatedOrder = {
        ...order,
        status: newStatus,
        status_notes: notes
      };
      
      const response = await ordersApi.updateOrder(id, updatedOrder);
      
      setOrder(response.data);
      
      toast({
        title: 'Success',
        description: `Order status updated to ${newStatus}`,
        variant: 'success'
      });
    } catch (err) {
      console.error('Failed to update status:', err);
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
  
  // Handle payment update
  const handlePaymentUpdate = async (amountReceived) => {
    try {
      setSaving(true);
      setError(null);
      
      const updatedOrder = {
        ...order,
        amount_received: amountReceived
      };
      
      const response = await ordersApi.updateOrder(id, updatedOrder);
      
      setOrder(response.data);
      
      toast({
        title: 'Success',
        description: 'Payment information updated',
        variant: 'success'
      });
    } catch (err) {
      console.error('Failed to update payment:', err);
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
  
  // Check permissions
  const canEdit = user?.role === 'admin';
  const canUpdateStatus = user?.role === 'admin' || user?.role === 'operator';
  const canUpdatePayment = user?.role === 'admin' || user?.role === 'accountant';
  
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
            onClick={() => navigate('/orders')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Orders
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              {isNew ? 'New Order' : `Order ${order?.order_number || `#${id}`}`}
            </h1>
            {!isNew && order && (
              <p className="text-gray-600">
                {order.product_name} for {order.customer_name}
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
      {order && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="details">
              <FileEdit className="w-4 h-4 mr-2" />
              Order Details
            </TabsTrigger>
            {!isNew && (
              <>
                <TabsTrigger value="timeline">
                  <Clock className="w-4 h-4 mr-2" />
                  Manufacturing Timeline
                </TabsTrigger>
                <TabsTrigger value="payment">
                  <IndianRupee className="w-4 h-4 mr-2" />
                  Payment
                </TabsTrigger>
              </>
            )}
          </TabsList>
          
          <TabsContent value="details" className="mt-4">
            <div className="bg-white p-6 rounded-md border shadow-sm">
              <OrderForm
                order={order}
                customers={customers}
                products={products}
                statuses={statuses}
                onChange={handleFormChange}
                isEditing={isEditing || isNew}
                isNew={isNew}
              />
            </div>
          </TabsContent>
          
          {!isNew && (
            <>
              <TabsContent value="timeline" className="mt-4">
                <div className="bg-white p-6 rounded-md border shadow-sm">
                  <OrderTimeline
                    order={order}
                    statuses={statuses}
                    onStatusUpdate={canUpdateStatus ? handleStatusUpdate : null}
                  />
                </div>
              </TabsContent>
              
              <TabsContent value="payment" className="mt-4">
                <div className="bg-white p-6 rounded-md border shadow-sm">
                  <OrderPayment
                    order={order}
                    onPaymentUpdate={canUpdatePayment ? handlePaymentUpdate : null}
                  />
                </div>
              </TabsContent>
            </>
          )}
        </Tabs>
      )}
    </div>
  );
};

export default OrderDetail;

