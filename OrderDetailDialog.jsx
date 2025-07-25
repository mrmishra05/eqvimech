import React from 'react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { Eye, Download, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import LoadingSpinner from '../ui/LoadingSpinner';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter 
} from '../ui/dialog';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '../ui/table';

const OrderDetailDialog = ({ 
  title, 
  orders, 
  loading, 
  isOpen, 
  onClose,
  onExport
}) => {
  const navigate = useNavigate();
  
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
  
  // Handle view order
  const handleViewOrder = (orderId) => {
    navigate(`/orders/${orderId}`);
    onClose();
  };
  
  // Calculate total amount
  const totalAmount = orders.reduce((sum, order) => sum + order.amount, 0);
  
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <LoadingSpinner />
          </div>
        ) : orders.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No orders found.
          </div>
        ) : (
          <>
            <div className="py-4">
              <div className="flex justify-between items-center mb-4">
                <div className="text-sm text-gray-500">
                  Showing {orders.length} orders
                </div>
                <div className="text-sm font-medium">
                  Total Amount: ₹{totalAmount.toLocaleString('en-IN')}
                </div>
              </div>
              
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Order #</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Start Date</TableHead>
                      <TableHead>Delivery Date</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Amount (₹)</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.map((order) => (
                      <TableRow key={order.id}>
                        <TableCell className="font-medium">{order.order_number || `#${order.id}`}</TableCell>
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
                        <TableCell>{order.amount.toLocaleString('en-IN')}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewOrder(order.id)}
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            View
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
            
            <DialogFooter>
              <Button
                variant="outline"
                size="sm"
                onClick={onClose}
              >
                <X className="w-4 h-4 mr-2" />
                Close
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={onExport}
              >
                <Download className="w-4 h-4 mr-2" />
                Export CSV
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default OrderDetailDialog;

