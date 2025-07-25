import React from 'react';
import { format } from 'date-fns';
import { ChevronLeft, ChevronRight, ArrowUpDown, Eye } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '../ui/table';

const OrdersTable = ({ 
  orders, 
  onViewOrder, 
  onSort, 
  sorting, 
  pagination, 
  onPageChange 
}) => {
  // Helper function to format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'dd/MM/yyyy');
    } catch (error) {
      return 'Invalid date';
    }
  };
  
  // Helper function to get status badge color
  const getStatusColor = (status) => {
    switch (status) {
      case 'Raw Material Ordered':
        return 'bg-gray-200 text-gray-800';
      case 'Raw Material Received':
        return 'bg-blue-100 text-blue-800';
      case 'Frame Fabrication':
        return 'bg-purple-100 text-purple-800';
      case 'Outsource Machining':
        return 'bg-indigo-100 text-indigo-800';
      case 'Initial Assembly':
        return 'bg-cyan-100 text-cyan-800';
      case 'Electrical Wiring':
        return 'bg-teal-100 text-teal-800';
      case 'Final Assembly':
        return 'bg-amber-100 text-amber-800';
      case 'Loadcell Calibration':
        return 'bg-yellow-100 text-yellow-800';
      case 'Verified':
        return 'bg-green-100 text-green-800';
      case 'Dispatch':
        return 'bg-emerald-100 text-emerald-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  
  // Helper function to render sort indicator
  const renderSortIndicator = (column) => {
    if (sorting.sort_by !== column) {
      return <ArrowUpDown className="ml-2 h-4 w-4" />;
    }
    
    return sorting.sort_order === 'asc' ? (
      <span className="ml-2">↑</span>
    ) : (
      <span className="ml-2">↓</span>
    );
  };
  
  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('id')}
                >
                  Order ID
                  {renderSortIndicator('id')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('order_number')}
                >
                  Order Number
                  {renderSortIndicator('order_number')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('product_name')}
                >
                  Product
                  {renderSortIndicator('product_name')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('customer_name')}
                >
                  Customer
                  {renderSortIndicator('customer_name')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('start_date')}
                >
                  Start Date
                  {renderSortIndicator('start_date')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('delivery_date')}
                >
                  Delivery Date
                  {renderSortIndicator('delivery_date')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('status')}
                >
                  Status
                  {renderSortIndicator('status')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('amount')}
                >
                  Amount (₹)
                  {renderSortIndicator('amount')}
                </button>
              </TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {orders.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center py-8 text-gray-500">
                  No orders found. Try adjusting your filters.
                </TableCell>
              </TableRow>
            ) : (
              orders.map((order) => (
                <TableRow key={order.id}>
                  <TableCell className="font-medium">{order.id}</TableCell>
                  <TableCell>{order.order_number || 'N/A'}</TableCell>
                  <TableCell>{order.product_name}</TableCell>
                  <TableCell>{order.customer_name}</TableCell>
                  <TableCell>{formatDate(order.start_date)}</TableCell>
                  <TableCell>
                    <div className="flex items-center">
                      {formatDate(order.delivery_date)}
                      {order.is_delayed && (
                        <span className="ml-2 h-2 w-2 rounded-full bg-red-500" title="Delayed" />
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(order.status)}>
                      {order.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {order.amount.toLocaleString('en-IN')}
                    {order.amount_due > 0 && (
                      <div className="text-xs text-gray-500">
                        Due: ₹{order.amount_due.toLocaleString('en-IN')}
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewOrder(order.id)}
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      
      {/* Pagination */}
      {pagination.totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Showing {orders.length} of {pagination.totalItems} orders
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(pagination.currentPage - 1)}
              disabled={pagination.currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <div className="text-sm">
              Page {pagination.currentPage} of {pagination.totalPages}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(pagination.currentPage + 1)}
              disabled={pagination.currentPage === pagination.totalPages}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrdersTable;

