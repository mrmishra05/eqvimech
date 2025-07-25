import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { dashboardApi } from '../lib/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart
} from 'recharts';
import { TrendingUp, BarChart3, PieChart as PieChartIcon, Calendar } from 'lucide-react';

const DashboardCharts = () => {
  const [salesTrends, setSalesTrends] = useState([]);
  const [statusDistribution, setStatusDistribution] = useState([]);
  const [familyPerformance, setFamilyPerformance] = useState([]);
  const [topCustomers, setTopCustomers] = useState([]);
  const [deliveryPerformance, setDeliveryPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('monthly');

  useEffect(() => {
    loadChartData();
  }, [period]);

  const loadChartData = async () => {
    try {
      setLoading(true);
      
      const [trends, status, family, customers, delivery] = await Promise.all([
        dashboardApi.getSalesTrends({ period }),
        dashboardApi.getOrderStatusDistribution(),
        dashboardApi.getProductFamilyPerformance(),
        dashboardApi.getTopCustomers({ limit: 5 }),
        dashboardApi.getDeliveryPerformance()
      ]);

      setSalesTrends(trends.trends || []);
      setStatusDistribution(status.distribution || []);
      setFamilyPerformance(family.performance || []);
      setTopCustomers(customers.top_customers || []);
      setDeliveryPerformance(delivery.delivery_performance || {});
    } catch (error) {
      console.error('Error loading chart data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Color schemes for charts
  const statusColors = {
    'pending': '#f59e0b',
    'in_production': '#3b82f6',
    'quality_check': '#8b5cf6',
    'completed': '#10b981',
    'delayed': '#ef4444',
    'cancelled': '#6b7280'
  };

  const pieColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6b7280'];

  const deliveryData = deliveryPerformance ? [
    { name: 'On Time', value: deliveryPerformance.on_time, color: '#10b981' },
    { name: 'Late', value: deliveryPerformance.late, color: '#ef4444' },
    { name: 'Early', value: deliveryPerformance.early, color: '#3b82f6' }
  ] : [];

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-gray-200 rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Chart Controls */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Analytics & Trends</h3>
        <div className="flex items-center space-x-4">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="monthly">Monthly</SelectItem>
              <SelectItem value="quarterly">Quarterly</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={loadChartData}>
            <Calendar className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales Trends Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-blue-600" />
              <span>Sales Trends</span>
            </CardTitle>
            <CardDescription>
              Revenue and order count over time ({period})
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={salesTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip 
                  formatter={(value, name) => [
                    name === 'revenue' ? `$${value.toLocaleString()}` : value,
                    name === 'revenue' ? 'Revenue' : 'Orders'
                  ]}
                />
                <Legend />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="revenue"
                  stackId="1"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                  name="Revenue"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="order_count"
                  stroke="#10b981"
                  strokeWidth={3}
                  name="Orders"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Order Status Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <PieChartIcon className="h-5 w-5 text-green-600" />
              <span>Order Status Distribution</span>
            </CardTitle>
            <CardDescription>
              Current status of all orders
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ status, count, percent }) => 
                    `${status}: ${count} (${(percent * 100).toFixed(0)}%)`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {statusDistribution.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={statusColors[entry.status] || pieColors[index % pieColors.length]} 
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Delivery Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Calendar className="h-5 w-5 text-purple-600" />
              <span>Delivery Performance</span>
            </CardTitle>
            <CardDescription>
              On-time delivery analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={deliveryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value, percent }) => 
                    `${name}: ${value} (${(percent * 100).toFixed(0)}%)`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {deliveryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Product Family Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-orange-600" />
              <span>Product Family Performance</span>
            </CardTitle>
            <CardDescription>
              Revenue by product family
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={familyPerformance} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="family_name" type="category" width={100} />
                <Tooltip 
                  formatter={(value) => [`$${value.toLocaleString()}`, 'Revenue']}
                />
                <Bar dataKey="revenue" fill="#f59e0b" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Top Customers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-indigo-600" />
              <span>Top Customers</span>
            </CardTitle>
            <CardDescription>
              Highest revenue customers
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topCustomers}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip 
                  formatter={(value) => [`$${value.toLocaleString()}`, 'Revenue']}
                />
                <Bar dataKey="total_revenue" fill="#6366f1" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DashboardCharts;

