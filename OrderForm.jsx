import React from 'react';
import { format } from 'date-fns';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';

const OrderForm = ({
  order,
  customers,
  products,
  statuses,
  onChange,
  isEditing,
  isNew
}) => {
  // Helper function to format date for input
  const formatDateForInput = (dateString) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return format(date, 'yyyy-MM-dd');
    } catch (error) {
      return '';
    }
  };
  
  // Handle input change
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    onChange(name, value);
  };
  
  // Handle number input change
  const handleNumberChange = (e) => {
    const { name, value } = e.target;
    onChange(name, parseFloat(value) || 0);
  };
  
  // Handle select change
  const handleSelectChange = (name, value) => {
    onChange(name, value);
  };
  
  return (
    <div className="space-y-6">
      {/* Order Number (read-only if not new) */}
      {!isNew && (
        <div className="space-y-2">
          <Label htmlFor="order_number">Order Number</Label>
          <Input
            id="order_number"
            name="order_number"
            value={order.order_number || ''}
            onChange={handleInputChange}
            disabled={!isEditing}
            placeholder="Auto-generated if left blank"
          />
          <p className="text-xs text-gray-500">
            Format: EM-YYYYMMDD-XXX (auto-generated if left blank)
          </p>
        </div>
      )}
      
      {/* Product */}
      <div className="space-y-2">
        <Label htmlFor="product_id" className="required">Product</Label>
        <Select
          value={order.product_id?.toString() || ''}
          onValueChange={(value) => handleSelectChange('product_id', parseInt(value))}
          disabled={!isEditing}
        >
          <SelectTrigger id="product_id">
            <SelectValue placeholder="Select a product" />
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
      
      {/* Customer */}
      <div className="space-y-2">
        <Label htmlFor="customer_id" className="required">Customer</Label>
        <Select
          value={order.customer_id?.toString() || ''}
          onValueChange={(value) => handleSelectChange('customer_id', parseInt(value))}
          disabled={!isEditing}
        >
          <SelectTrigger id="customer_id">
            <SelectValue placeholder="Select a customer" />
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
      
      {/* Dates */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="start_date">Start Date</Label>
          <Input
            id="start_date"
            name="start_date"
            type="date"
            value={formatDateForInput(order.start_date)}
            onChange={handleInputChange}
            disabled={!isEditing}
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="delivery_date" className="required">Delivery Date</Label>
          <Input
            id="delivery_date"
            name="delivery_date"
            type="date"
            value={formatDateForInput(order.delivery_date)}
            onChange={handleInputChange}
            disabled={!isEditing}
          />
        </div>
      </div>
      
      {/* Status */}
      <div className="space-y-2">
        <Label htmlFor="status">Status</Label>
        <Select
          value={order.status || ''}
          onValueChange={(value) => handleSelectChange('status', value)}
          disabled={!isEditing}
        >
          <SelectTrigger id="status">
            <SelectValue placeholder="Select status" />
          </SelectTrigger>
          <SelectContent>
            {statuses.map((status) => (
              <SelectItem key={status} value={status}>
                {status}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      {/* Amount */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="amount" className="required">Total Amount (₹)</Label>
          <Input
            id="amount"
            name="amount"
            type="number"
            min="0"
            step="0.01"
            value={order.amount || ''}
            onChange={handleNumberChange}
            disabled={!isEditing}
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="amount_received">Amount Received (₹)</Label>
          <Input
            id="amount_received"
            name="amount_received"
            type="number"
            min="0"
            step="0.01"
            value={order.amount_received || ''}
            onChange={handleNumberChange}
            disabled={!isEditing}
          />
          {order.amount && order.amount_received !== undefined && (
            <p className="text-xs text-gray-500">
              Due: ₹{(order.amount - order.amount_received).toLocaleString('en-IN')}
            </p>
          )}
        </div>
      </div>
      
      {/* Notes */}
      <div className="space-y-2">
        <Label htmlFor="notes">Notes</Label>
        <Textarea
          id="notes"
          name="notes"
          value={order.notes || ''}
          onChange={handleInputChange}
          disabled={!isEditing}
          rows={4}
        />
      </div>
      
      {/* Required fields note */}
      <p className="text-xs text-gray-500">
        Fields marked with <span className="text-red-500">*</span> are required.
      </p>
      
      <style jsx>{`
        .required:after {
          content: " *";
          color: red;
        }
      `}</style>
    </div>
  );
};

export default OrderForm;

