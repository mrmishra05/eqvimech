import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { 
  ShoppingCart, 
  Plus, 
  Search, 
  Filter, 
  Edit, 
  Trash2, 
  Eye, 
  Calendar, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  RefreshCw,
  ArrowUpDown,
  Download
} from 'lucide-react';
import { format } from 'date-fns';
import { fetchOrders, fetchCustomers, fetchProducts, createOrder, updateOrder, deleteOrder } from '../lib/api';

// Status badge colors
const getStatusColor = (status) => {
  const statusMap = {
    'raw material ordered': 'bg-purple-100 text-purple-800',
    'raw material received': 'bg-blue-100 text-blue-800',
    'frame fabrication': 'bg-yellow-100 text-yellow-800',
    'outsource machining': 'bg-orange-100 text-orange-800',
    'initial assembly': 'bg-indigo-100 text-indigo-800',
    'electrical wiring': 'bg-pink-100 text-pink-800',
    'final assembly': 'bg-emerald-100 text-emerald-800',
    'loadcell calibration': 'bg-cyan-100 text-cyan-800',
    'verified': 'bg-green-100 text-green-800',
    'dispatch': 'bg-teal-100 text-teal-800'
  };
  
  return statusMap[status.toLowerCase()] || 'bg-gray-100 text-gray-800';
};

// Manufacturing stages in order
const manufacturingStages = [
  'Raw Material Ordered',
  'Raw Material Received',
  'Frame Fabrication',
  'Outsource Machining',
  'Initial Assembly',
  'Electrical Wiring',
  'Final Assembly',
  'Loadcell Calibration',
  'Verified',
  'Dispatch'
];

const Orders = () => {
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Order detail state
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  
  // New order state
  const [isNewDialogOpen, setIsNewDialogOpen] = useState(false);
  const [newOrder, setNewOrder] = useState({
    product_id: '',
    customer_id: '',
    start_date: format(new Date(), 'yyyy-MM-dd'),
    delivery_date: format(new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
    status: 'Raw Material Ordered',
    amount: '',
    amount_received: '0',
    notes: ''
  });
  
  // Edit order state
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editOrder, setEditOrder] = useState(null);
  
  // Delete confirmation state
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [orderToDelete, setOrderToDelete] = useState(null);
  
  // Filter state
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    customer: '',
    dateRange: ''
  });
  
  // Sorting state
  const [sortConfig, setSortConfig] = useState({
    key: 'id',
    direction: 'asc'
  });

  // Fetch data on component mount
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        console.log('Fetching orders data...');
        const ordersData = await fetchOrders();
        console.log('Orders data:', ordersData);
        
        console.log('Fetching customers data...');
        const customersData = await fetchCustomers();
        console.log('Customers data:', customersData);
        
        console.log('Fetching products data...');
        const productsData = await fetchProducts();
        console.log('Products data:', productsData);
        
        setOrders(ordersData || []);
        setFilteredOrders(ordersData || []);
        setCustomers(customersData || []);
        setProducts(productsData || []);
      } catch (err) {
        console.error('Error loading data:', err);
        setError('Failed to load data. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, []);
  
  // Apply filters and sorting
  useEffect(() => {
    let result = [...orders];
    
    // Apply search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(order => 
        order.id.toString().includes(searchLower) ||
        order.product_name.toLowerCase().includes(searchLower) ||
        order.customer_name.toLowerCase().includes(searchLower) ||
        order.status.toLowerCase().includes(searchLower)
      );
    }
    
    // Apply status filter
    if (filters.status) {
      result = result.filter(order => 
        order.status.toLowerCase() === filters.status.toLowerCase()
      );
    }
    
    // Apply customer filter
    if (filters.customer) {
      result = result.filter(order => 
        order.customer_id.toString() === filters.customer
      );
    }
    
    // Apply date range filter
    if (filters.dateRange) {
      const today = new Date();
      let startDate;
      
      switch (filters.dateRange) {
        case 'today':
          startDate = new Date(today.setHours(0, 0, 0, 0));
          result = result.filter(order => new Date(order.start_date) >= startDate);
          break;
        case 'week':
          startDate = new Date(today.setDate(today.getDate() - 7));
          result = result.filter(order => new Date(order.start_date) >= startDate);
          break;
        case 'month':
          startDate = new Date(today.setMonth(today.getMonth() - 1));
          result = result.filter(order => new Date(order.start_date) >= startDate);
          break;
        case 'quarter':
          startDate = new Date(today.setMonth(today.getMonth() - 3));
          result = result.filter(order => new Date(order.start_date) >= startDate);
          break;
        default:
          break;
      }
    }
    
    // Apply sorting
    if (sortConfig.key) {
      result.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    
    setFilteredOrders(result);
  }, [orders, filters, sortConfig]);
  
  // Handle sorting
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };
  
  // Handle filter changes
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };
  
  // Reset filters
  const resetFilters = () => {
    setFilters({
      search: '',
      status: '',
      customer: '',
      dateRange: ''
    });
  };
  
  // Handle view order
  const handleViewOrder = (order) => {
    setSelectedOrder(order);
    setIsViewDialogOpen(true);
  };
  
  // Handle new order
  const handleNewOrder = async () => {
    try {
      const response = await createOrder(newOrder);
      setOrders(prev => [...prev, response]);
      setIsNewDialogOpen(false);
      setNewOrder({
        product_id: '',
        customer_id: '',
        start_date: format(new Date(), 'yyyy-MM-dd'),
        delivery_date: format(new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
        status: 'Raw Material Ordered',
        amount: '',
        amount_received: '0',
        notes: ''
      });
    } catch (err) {
      console.error('Error creating order:', err);
      setError('Failed to create order. Please try again.');
    }
  };
  
  // Handle edit order
  const handleEditOrder = (order) => {
    setEditOrder({...order});
    setIsEditDialogOpen(true);
  };
  
  // Handle update order
  const handleUpdateOrder = async () => {
    try {
      const response = await updateOrder(editOrder.id, editOrder);
      setOrders(prev => prev.map(order => 
        order.id === editOrder.id ? response : order
      ));
      setIsEditDialogOpen(false);
    } catch (err) {
      console.error('Error updating order:', err);
      setError('Failed to update order. Please try again.');
    }
  };
  
  // Handle delete confirmation
  const handleDeleteConfirmation = (order) => {
    setOrderToDelete(order);
    setIsDeleteDialogOpen(true);
  };
  
  // Handle delete order
  const handleDeleteOrder = async () => {
    try {
      await deleteOrder(orderToDelete.id);
      setOrders(prev => prev.filter(order => order.id !== orderToDelete.id));
      setIsDeleteDialogOpen(false);
    } catch (err) {
      console.error('Error deleting order:', err);
      setError('Failed to delete order. Please try again.');
    }
  };
  
  // Calculate due amount
  const calculateDueAmount = (order) => {
    const amount = parseFloat(order.amount) || 0;
    const received = parseFloat(order.amount_received) || 0;
    return (amount - received).toFixed(2);
  };
  
  // Format currency
  const formatCurrency = (amount) => {
    return `₹${parseFloat(amount).toLocaleString('en-IN')}`;
  };
  
  // Check if order is delayed
  const isDelayed = (order) => {
    const today = new Date();
    const deliveryDate = new Date(order.delivery_date);
    const isCompleted = ['Verified', 'Dispatch'].includes(order.status);
    
    return !isCompleted && today > deliveryDate;
  };

  // Get product family
  const getProductFamily = (productId) => {
    const product = products.find(p => p.id === productId);
    return product ? product.family : 'Unknown';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Orders Management</h2>
          <p className="text-gray-600">Manage manufacturing orders and track progress</p>
        </div>
        
        {/* New Order Button - Only visible to admin and operator roles */}
        {(user?.role === 'admin' || user?.role === 'operator') && (
          <Button 
            onClick={() => setIsNewDialogOpen(true)}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="mr-2 h-4 w-4" />
            New Order
          </Button>
        )}
      </div>
      
      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Filter className="h-5 w-5" />
            <span>Filters</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="search">Search</Label>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                <Input
                  id="search"
                  placeholder="Search orders..."
                  className="pl-8"
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="status">Status</Label>
              <Select 
                value={filters.status} 
                onValueChange={(value) => handleFilterChange('status', value)}
              >
                <SelectTrigger id="status">
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Statuses</SelectItem>
                  {manufacturingStages.map((stage) => (
                    <SelectItem key={stage} value={stage}>{stage}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="customer">Customer</Label>
              <Select 
                value={filters.customer} 
                onValueChange={(value) => handleFilterChange('customer', value)}
              >
                <SelectTrigger id="customer">
                  <SelectValue placeholder="All Customers" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Customers</SelectItem>
                  {customers.map((customer) => (
                    <SelectItem key={customer.id} value={customer.id.toString()}>
                      {customer.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label htmlFor="dateRange">Date Range</Label>
              <Select 
                value={filters.dateRange} 
                onValueChange={(value) => handleFilterChange('dateRange', value)}
              >
                <SelectTrigger id="dateRange">
                  <SelectValue placeholder="All Time" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Time</SelectItem>
                  <SelectItem value="today">Today</SelectItem>
                  <SelectItem value="week">Last 7 Days</SelectItem>
                  <SelectItem value="month">Last 30 Days</SelectItem>
                  <SelectItem value="quarter">Last 90 Days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="flex justify-end mt-4">
            <Button 
              variant="outline" 
              onClick={resetFilters}
              className="flex items-center"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Reset Filters
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Orders Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ShoppingCart className="h-5 w-5" />
              <span>Orders</span>
            </div>
            <Badge variant="outline" className="ml-2">
              {filteredOrders.length} orders
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700 mx-auto"></div>
              <p className="mt-2 text-gray-600">Loading orders...</p>
            </div>
          ) : error ? (
            <div className="text-center py-8 text-red-600">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p>{error}</p>
            </div>
          ) : filteredOrders.length === 0 ? (
            <div className="text-center py-8">
              <ShoppingCart className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Orders Found</h3>
              <p className="text-gray-600">Try adjusting your filters or create a new order.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px] cursor-pointer" onClick={() => handleSort('id')}>
                      <div className="flex items-center">
                        ID
                        <ArrowUpDown className="ml-1 h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('product_name')}>
                      <div className="flex items-center">
                        Product
                        <ArrowUpDown className="ml-1 h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('customer_name')}>
                      <div className="flex items-center">
                        Customer
                        <ArrowUpDown className="ml-1 h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('status')}>
                      <div className="flex items-center">
                        Status
                        <ArrowUpDown className="ml-1 h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('start_date')}>
                      <div className="flex items-center">
                        Start Date
                        <ArrowUpDown className="ml-1 h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('delivery_date')}>
                      <div className="flex items-center">
                        Delivery Date
                        <ArrowUpDown className="ml-1 h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead className="text-right cursor-pointer" onClick={() => handleSort('amount')}>
                      <div className="flex items-center justify-end">
                        Amount
                        <ArrowUpDown className="ml-1 h-4 w-4" />
                      </div>
                    </TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredOrders.map((order) => (
                    <TableRow 
                      key={order.id}
                      className={isDelayed(order) ? 'bg-red-50' : ''}
                    >
                      <TableCell className="font-medium">{order.id}</TableCell>
                      <TableCell>{order.product_name}</TableCell>
                      <TableCell>{order.customer_name}</TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(order.status)}>
                          {order.status}
                        </Badge>
                        {isDelayed(order) && (
                          <Badge variant="destructive" className="ml-2">
                            Delayed
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>{format(new Date(order.start_date), 'dd/MM/yyyy')}</TableCell>
                      <TableCell>{format(new Date(order.delivery_date), 'dd/MM/yyyy')}</TableCell>
                      <TableCell className="text-right">{formatCurrency(order.amount)}</TableCell>
                      <TableCell>
                        <div className="flex justify-end space-x-2">
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => handleViewOrder(order)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          
                          {/* Edit button - Only visible to admin and operator roles */}
                          {(user?.role === 'admin' || user?.role === 'operator') && (
                            <Button 
                              variant="ghost" 
                              size="icon"
                              onClick={() => handleEditOrder(order)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          )}
                          
                          {/* Delete button - Only visible to admin role */}
                          {user?.role === 'admin' && (
                            <Button 
                              variant="ghost" 
                              size="icon"
                              onClick={() => handleDeleteConfirmation(order)}
                            >
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* View Order Dialog */}
      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Order Details</DialogTitle>
            <DialogDescription>
              Complete information about order #{selectedOrder?.id}
            </DialogDescription>
          </DialogHeader>
          
          {selectedOrder && (
            <Tabs defaultValue="details">
              <TabsList className="grid grid-cols-3">
                <TabsTrigger value="details">Order Details</TabsTrigger>
                <TabsTrigger value="status">Status & Timeline</TabsTrigger>
                <TabsTrigger value="payment">Payment Information</TabsTrigger>
              </TabsList>
              
              <TabsContent value="details" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Order ID</Label>
                    <div className="font-medium">{selectedOrder.id}</div>
                  </div>
                  <div>
                    <Label>Product</Label>
                    <div className="font-medium">{selectedOrder.product_name}</div>
                  </div>
                  <div>
                    <Label>Product Family</Label>
                    <div className="font-medium">{getProductFamily(selectedOrder.product_id)}</div>
                  </div>
                  <div>
                    <Label>Customer</Label>
                    <div className="font-medium">{selectedOrder.customer_name}</div>
                  </div>
                  <div>
                    <Label>Start Date</Label>
                    <div className="font-medium">
                      {format(new Date(selectedOrder.start_date), 'dd/MM/yyyy')}
                    </div>
                  </div>
                  <div>
                    <Label>Delivery Date</Label>
                    <div className="font-medium">
                      {format(new Date(selectedOrder.delivery_date), 'dd/MM/yyyy')}
                      {isDelayed(selectedOrder) && (
                        <Badge variant="destructive" className="ml-2">Delayed</Badge>
                      )}
                    </div>
                  </div>
                  <div className="col-span-2">
                    <Label>Notes</Label>
                    <div className="font-medium">{selectedOrder.notes || 'No notes available'}</div>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="status" className="space-y-4">
                <div>
                  <Label>Current Status</Label>
                  <div className="mt-1">
                    <Badge className={getStatusColor(selectedOrder.status)}>
                      {selectedOrder.status}
                    </Badge>
                  </div>
                </div>
                
                <div className="mt-4">
                  <Label>Manufacturing Timeline</Label>
                  <div className="mt-2 space-y-2">
                    {manufacturingStages.map((stage, index) => {
                      const stageIndex = manufacturingStages.findIndex(
                        s => s.toLowerCase() === selectedOrder.status.toLowerCase()
                      );
                      const isCompleted = index <= stageIndex;
                      const isCurrent = index === stageIndex;
                      
                      return (
                        <div 
                          key={stage}
                          className={`flex items-center p-2 rounded-md ${
                            isCurrent ? 'bg-blue-50 border border-blue-200' : 
                            isCompleted ? 'bg-green-50' : 'bg-gray-50'
                          }`}
                        >
                          {isCompleted ? (
                            <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                          ) : (
                            <Clock className="h-5 w-5 text-gray-400 mr-2" />
                          )}
                          <span className={isCurrent ? 'font-medium' : ''}>{stage}</span>
                          {isCurrent && (
                            <Badge className="ml-auto">Current</Badge>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="payment" className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Total Amount</Label>
                    <div className="font-medium text-lg">{formatCurrency(selectedOrder.amount)}</div>
                  </div>
                  <div>
                    <Label>Amount Received</Label>
                    <div className="font-medium text-lg text-green-600">
                      {formatCurrency(selectedOrder.amount_received)}
                    </div>
                  </div>
                  <div>
                    <Label>Amount Due</Label>
                    <div className="font-medium text-lg text-red-600">
                      {formatCurrency(calculateDueAmount(selectedOrder))}
                    </div>
                  </div>
                </div>
                
                <div className="mt-4">
                  <Label>Payment Status</Label>
                  <div className="mt-1">
                    {parseFloat(selectedOrder.amount) <= parseFloat(selectedOrder.amount_received) ? (
                      <Badge className="bg-green-100 text-green-800">Fully Paid</Badge>
                    ) : parseFloat(selectedOrder.amount_received) > 0 ? (
                      <Badge className="bg-yellow-100 text-yellow-800">Partially Paid</Badge>
                    ) : (
                      <Badge className="bg-red-100 text-red-800">Payment Pending</Badge>
                    )}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsViewDialogOpen(false)}>
              Close
            </Button>
            {(user?.role === 'admin' || user?.role === 'operator') && (
              <Button onClick={() => {
                setIsViewDialogOpen(false);
                handleEditOrder(selectedOrder);
              }}>
                <Edit className="mr-2 h-4 w-4" />
                Edit Order
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* New Order Dialog */}
      <Dialog open={isNewDialogOpen} onOpenChange={setIsNewDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Order</DialogTitle>
            <DialogDescription>
              Enter the details for the new manufacturing order.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="product">Product</Label>
                <Select 
                  value={newOrder.product_id.toString()} 
                  onValueChange={(value) => setNewOrder({...newOrder, product_id: parseInt(value)})}
                >
                  <SelectTrigger id="product">
                    <SelectValue placeholder="Select Product" />
                  </SelectTrigger>
                  <SelectContent>
                    {products.map((product) => (
                      <SelectItem key={product.id} value={product.id.toString()}>
                        {product.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label htmlFor="customer">Customer</Label>
                <Select 
                  value={newOrder.customer_id.toString()} 
                  onValueChange={(value) => setNewOrder({...newOrder, customer_id: parseInt(value)})}
                >
                  <SelectTrigger id="customer">
                    <SelectValue placeholder="Select Customer" />
                  </SelectTrigger>
                  <SelectContent>
                    {customers.map((customer) => (
                      <SelectItem key={customer.id} value={customer.id.toString()}>
                        {customer.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="start_date">Start Date</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={newOrder.start_date}
                  onChange={(e) => setNewOrder({...newOrder, start_date: e.target.value})}
                />
              </div>
              
              <div>
                <Label htmlFor="delivery_date">Delivery Date</Label>
                <Input
                  id="delivery_date"
                  type="date"
                  value={newOrder.delivery_date}
                  onChange={(e) => setNewOrder({...newOrder, delivery_date: e.target.value})}
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="status">Initial Status</Label>
              <Select 
                value={newOrder.status} 
                onValueChange={(value) => setNewOrder({...newOrder, status: value})}
              >
                <SelectTrigger id="status">
                  <SelectValue placeholder="Select Status" />
                </SelectTrigger>
                <SelectContent>
                  {manufacturingStages.map((stage) => (
                    <SelectItem key={stage} value={stage}>{stage}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="amount">Total Amount (₹)</Label>
                <Input
                  id="amount"
                  type="number"
                  placeholder="0.00"
                  value={newOrder.amount}
                  onChange={(e) => setNewOrder({...newOrder, amount: e.target.value})}
                />
              </div>
              
              <div>
                <Label htmlFor="amount_received">Amount Received (₹)</Label>
                <Input
                  id="amount_received"
                  type="number"
                  placeholder="0.00"
                  value={newOrder.amount_received}
                  onChange={(e) => setNewOrder({...newOrder, amount_received: e.target.value})}
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="notes">Notes</Label>
              <Input
                id="notes"
                placeholder="Additional notes about this order"
                value={newOrder.notes}
                onChange={(e) => setNewOrder({...newOrder, notes: e.target.value})}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsNewDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleNewOrder}>
              <Plus className="mr-2 h-4 w-4" />
              Create Order
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Edit Order Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Order #{editOrder?.id}</DialogTitle>
            <DialogDescription>
              Update the details for this manufacturing order.
            </DialogDescription>
          </DialogHeader>
          
          {editOrder && (
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="edit_product">Product</Label>
                  <Select 
                    value={editOrder.product_id.toString()} 
                    onValueChange={(value) => setEditOrder({...editOrder, product_id: parseInt(value)})}
                  >
                    <SelectTrigger id="edit_product">
                      <SelectValue placeholder="Select Product" />
                    </SelectTrigger>
                    <SelectContent>
                      {products.map((product) => (
                        <SelectItem key={product.id} value={product.id.toString()}>
                          {product.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label htmlFor="edit_customer">Customer</Label>
                  <Select 
                    value={editOrder.customer_id.toString()} 
                    onValueChange={(value) => setEditOrder({...editOrder, customer_id: parseInt(value)})}
                  >
                    <SelectTrigger id="edit_customer">
                      <SelectValue placeholder="Select Customer" />
                    </SelectTrigger>
                    <SelectContent>
                      {customers.map((customer) => (
                        <SelectItem key={customer.id} value={customer.id.toString()}>
                          {customer.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="edit_start_date">Start Date</Label>
                  <Input
                    id="edit_start_date"
                    type="date"
                    value={format(new Date(editOrder.start_date), 'yyyy-MM-dd')}
                    onChange={(e) => setEditOrder({...editOrder, start_date: e.target.value})}
                  />
                </div>
                
                <div>
                  <Label htmlFor="edit_delivery_date">Delivery Date</Label>
                  <Input
                    id="edit_delivery_date"
                    type="date"
                    value={format(new Date(editOrder.delivery_date), 'yyyy-MM-dd')}
                    onChange={(e) => setEditOrder({...editOrder, delivery_date: e.target.value})}
                  />
                </div>
              </div>
              
              <div>
                <Label htmlFor="edit_status">Status</Label>
                <Select 
                  value={editOrder.status} 
                  onValueChange={(value) => setEditOrder({...editOrder, status: value})}
                >
                  <SelectTrigger id="edit_status">
                    <SelectValue placeholder="Select Status" />
                  </SelectTrigger>
                  <SelectContent>
                    {manufacturingStages.map((stage) => (
                      <SelectItem key={stage} value={stage}>{stage}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="edit_amount">Total Amount (₹)</Label>
                  <Input
                    id="edit_amount"
                    type="number"
                    placeholder="0.00"
                    value={editOrder.amount}
                    onChange={(e) => setEditOrder({...editOrder, amount: e.target.value})}
                  />
                </div>
                
                <div>
                  <Label htmlFor="edit_amount_received">Amount Received (₹)</Label>
                  <Input
                    id="edit_amount_received"
                    type="number"
                    placeholder="0.00"
                    value={editOrder.amount_received}
                    onChange={(e) => setEditOrder({...editOrder, amount_received: e.target.value})}
                  />
                </div>
              </div>
              
              <div>
                <Label htmlFor="edit_notes">Notes</Label>
                <Input
                  id="edit_notes"
                  placeholder="Additional notes about this order"
                  value={editOrder.notes}
                  onChange={(e) => setEditOrder({...editOrder, notes: e.target.value})}
                />
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateOrder}>
              <CheckCircle className="mr-2 h-4 w-4" />
              Update Order
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Deletion</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete order #{orderToDelete?.id}? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          
          {orderToDelete && (
            <div className="py-4">
              <div className="flex items-center space-x-2 mb-4">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <p className="font-medium">Order details:</p>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="font-medium">Product:</span> {orderToDelete.product_name}
                </div>
                <div>
                  <span className="font-medium">Customer:</span> {orderToDelete.customer_name}
                </div>
                <div>
                  <span className="font-medium">Status:</span> {orderToDelete.status}
                </div>
                <div>
                  <span className="font-medium">Amount:</span> {formatCurrency(orderToDelete.amount)}
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteOrder}>
              <Trash2 className="mr-2 h-4 w-4" />
              Delete Order
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Orders;

