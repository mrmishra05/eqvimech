import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
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
  ShoppingCart, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  BarChart3, 
  Calendar, 
  DollarSign,
  TrendingUp,
  Download
} from 'lucide-react';
import DashboardCharts from './DashboardCharts';
import { fetchDashboardKpis, fetchOrders } from '../lib/api';
import { format } from 'date-fns';

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

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [kpis, setKpis] = useState({
    totalOrders: 0,
    completedOrders: 0,
    pendingOrders: 0,
    delayedOrders: 0,
    completionRate: 0,
    onTimeDelivery: 0,
    totalRevenue: 0,
    periodRevenue: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Detail dialog state
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [detailType, setDetailType] = useState(null);
  const [detailTitle, setDetailTitle] = useState('');
  const [detailData, setDetailData] = useState([]);
  
  // Fetch KPI data
  useEffect(() => {
    const loadKpis = async () => {
      setLoading(true);
      try {
        console.log('Fetching dashboard KPIs...');
        const data = await fetchDashboardKpis();
        console.log('Dashboard KPIs data:', data);
        
        // Ensure we have default values if any field is missing
        setKpis({
          totalOrders: data?.totalOrders || 0,
          completedOrders: data?.completedOrders || 0,
          pendingOrders: data?.pendingOrders || 0,
          delayedOrders: data?.delayedOrders || 0,
          completionRate: data?.completionRate || 0,
          onTimeDelivery: data?.onTimeDelivery || 0,
          totalRevenue: data?.totalRevenue || 0,
          periodRevenue: data?.periodRevenue || 0
        });
      } catch (err) {
        console.error('Error loading KPIs:', err);
        setError('Failed to load dashboard data');
        
        // Set default values on error
        setKpis({
          totalOrders: 0,
          completedOrders: 0,
          pendingOrders: 0,
          delayedOrders: 0,
          completionRate: 0,
          onTimeDelivery: 0,
          totalRevenue: 0,
          periodRevenue: 0
        });
      } finally {
        setLoading(false);
      }
    };
    
    loadKpis();
  }, []);
  
  // Handle KPI card click
  const handleKpiClick = async (type) => {
    try {
      setLoading(true);
      console.log('Fetching orders for KPI click:', type);
      let title = '';
      let orders = await fetchOrders();
      console.log('Orders data for KPI click:', orders);
      
      // Default to empty array if orders is undefined
      orders = orders || [];
      
      let filteredOrders = [];
      
      switch (type) {
        case 'total':
          title = 'All Orders';
          filteredOrders = orders;
          break;
        case 'completed':
          title = 'Completed Orders';
          filteredOrders = orders.filter(order => 
            ['verified', 'dispatch'].includes(order.status.toLowerCase())
          );
          break;
        case 'pending':
          title = 'Pending Orders';
          filteredOrders = orders.filter(order => 
            !['verified', 'dispatch'].includes(order.status.toLowerCase())
          );
          break;
        case 'delayed':
          title = 'Delayed Orders';
          filteredOrders = orders.filter(order => {
            const today = new Date();
            const deliveryDate = new Date(order.delivery_date);
            const isCompleted = ['verified', 'dispatch'].includes(order.status.toLowerCase());
            return !isCompleted && today > deliveryDate;
          });
          break;
        default:
          break;
      }
      
      setDetailType(type);
      setDetailTitle(title);
      setDetailData(filteredOrders);
      setIsDetailDialogOpen(true);
    } catch (err) {
      console.error('Error loading detail data:', err);
      setError('Failed to load detail data');
    } finally {
      setLoading(false);
    }
  };
  
  // Format currency
  const formatCurrency = (amount) => {
    return `₹${parseFloat(amount).toLocaleString('en-IN')}`;
  };
  
  // Format percentage
  const formatPercentage = (value) => {
    return `${value}%`;
  };
  
  // Export to CSV
  const exportToCsv = (data, filename) => {
    if (!data || !data.length) return;
    
    // Create headers
    const headers = Object.keys(data[0]).filter(key => 
      !['id', 'product_id', 'customer_id'].includes(key)
    );
    
    // Create CSV content
    const csvContent = [
      headers.join(','),
      ...data.map(row => 
        headers.map(header => {
          let value = row[header] || '';
          // Handle values with commas
          if (typeof value === 'string' && value.includes(',')) {
            value = `"${value}"`;
          }
          return value;
        }).join(',')
      )
    ].join('\\n');
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `${filename}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="text-gray-600">Manufacturing performance overview</p>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">
            <BarChart3 className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <TrendingUp className="h-4 w-4 mr-2" />
            Analytics
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Total Orders */}
            <Card 
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleKpiClick('total')}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Total Orders
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  <div className="mr-4 rounded-full p-2 bg-blue-100">
                    <ShoppingCart className="h-6 w-6 text-blue-700" />
                  </div>
                  <div>
                    <div className="text-3xl font-bold">{kpis.totalOrders}</div>
                    <p className="text-xs text-gray-500">All time orders</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {/* Completed Orders */}
            <Card 
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleKpiClick('completed')}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Completed Orders
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  <div className="mr-4 rounded-full p-2 bg-green-100">
                    <CheckCircle className="h-6 w-6 text-green-700" />
                  </div>
                  <div>
                    <div className="text-3xl font-bold">{kpis.completedOrders}</div>
                    <p className="text-xs text-gray-500">Successfully completed</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {/* Pending Orders */}
            <Card 
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleKpiClick('pending')}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Pending Orders
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  <div className="mr-4 rounded-full p-2 bg-yellow-100">
                    <Clock className="h-6 w-6 text-yellow-700" />
                  </div>
                  <div>
                    <div className="text-3xl font-bold">{kpis.pendingOrders}</div>
                    <p className="text-xs text-gray-500">In progress</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {/* Delayed Orders */}
            <Card 
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleKpiClick('delayed')}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Delayed Orders
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  <div className="mr-4 rounded-full p-2 bg-red-100">
                    <AlertTriangle className="h-6 w-6 text-red-700" />
                  </div>
                  <div>
                    <div className="text-3xl font-bold">{kpis.delayedOrders}</div>
                    <p className="text-xs text-gray-500">Behind schedule</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          
          {/* Performance Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Completion Rate */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Completion Rate
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  <div className="mr-4 rounded-full p-2 bg-emerald-100">
                    <div className="h-6 w-6 flex items-center justify-center text-emerald-700 font-bold">
                      %
                    </div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold">{formatPercentage(kpis.completionRate)}</div>
                    <p className="text-xs text-gray-500">Orders completed</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {/* On-Time Delivery */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">
                  On-Time Delivery
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  <div className="mr-4 rounded-full p-2 bg-blue-100">
                    <Calendar className="h-6 w-6 text-blue-700" />
                  </div>
                  <div>
                    <div className="text-3xl font-bold">{formatPercentage(kpis.onTimeDelivery)}</div>
                    <p className="text-xs text-gray-500">Delivered on time</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {/* Total Revenue */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Total Revenue
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  <div className="mr-4 rounded-full p-2 bg-green-100">
                    <DollarSign className="h-6 w-6 text-green-700" />
                  </div>
                  <div>
                    <div className="text-3xl font-bold">{formatCurrency(kpis.totalRevenue)}</div>
                    <p className="text-xs text-gray-500">All time revenue</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {/* Period Revenue */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Period Revenue
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  <div className="mr-4 rounded-full p-2 bg-purple-100">
                    <TrendingUp className="h-6 w-6 text-purple-700" />
                  </div>
                  <div>
                    <div className="text-3xl font-bold">{formatCurrency(kpis.periodRevenue)}</div>
                    <p className="text-xs text-gray-500">Last 30 days</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        <TabsContent value="analytics">
          <DashboardCharts />
        </TabsContent>
      </Tabs>
      
      {/* Detail Dialog */}
      <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{detailTitle}</DialogTitle>
            <DialogDescription>
              Detailed information about {detailTitle.toLowerCase()}
            </DialogDescription>
          </DialogHeader>
          
          <div className="overflow-x-auto">
            {detailData.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">No data available</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Product</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Start Date</TableHead>
                    <TableHead>Delivery Date</TableHead>
                    <TableHead className="text-right">Amount (₹)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {detailData.map((order) => (
                    <TableRow key={order.id}>
                      <TableCell className="font-medium">{order.id}</TableCell>
                      <TableCell>{order.product_name}</TableCell>
                      <TableCell>{order.customer_name}</TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(order.status)}>
                          {order.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{format(new Date(order.start_date), 'dd/MM/yyyy')}</TableCell>
                      <TableCell>{format(new Date(order.delivery_date), 'dd/MM/yyyy')}</TableCell>
                      <TableCell className="text-right">{formatCurrency(order.amount)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
          
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setIsDetailDialogOpen(false)}
            >
              Close
            </Button>
            <Button 
              onClick={() => exportToCsv(detailData, detailTitle.replace(/\s+/g, '_').toLowerCase())}
              disabled={detailData.length === 0}
            >
              <Download className="mr-2 h-4 w-4" />
              Export to CSV
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      <div className="text-right text-xs text-gray-500">
        Last updated: {format(new Date(), 'h:mm:ss a')}
      </div>
    </div>
  );
};

export default Dashboard;

