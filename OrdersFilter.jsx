import React, { useState } from 'react';
import { Search, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';

const OrdersFilter = ({ 
  filters, 
  onFilterChange, 
  customers, 
  products, 
  statuses 
}) => {
  const [localFilters, setLocalFilters] = useState(filters);
  
  // Handle input change
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLocalFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Handle select change
  const handleSelectChange = (name, value) => {
    setLocalFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Handle switch change
  const handleSwitchChange = (name, checked) => {
    setLocalFilters(prev => ({
      ...prev,
      [name]: checked
    }));
  };
  
  // Apply filters
  const applyFilters = () => {
    onFilterChange(localFilters);
  };
  
  // Reset filters
  const resetFilters = () => {
    const emptyFilters = {
      status: '',
      customer_id: '',
      product_id: '',
      search: '',
      start_date: '',
      end_date: '',
      is_delayed: null
    };
    setLocalFilters(emptyFilters);
    onFilterChange(emptyFilters);
  };
  
  return (
    <div className="bg-white p-4 rounded-md border shadow-sm">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Search */}
        <div className="space-y-2">
          <Label htmlFor="search">Search</Label>
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-500" />
            <Input
              id="search"
              name="search"
              placeholder="Order number, product, customer..."
              className="pl-8"
              value={localFilters.search || ''}
              onChange={handleInputChange}
            />
          </div>
        </div>
        
        {/* Status */}
        <div className="space-y-2">
          <Label htmlFor="status">Status</Label>
          <Select
            value={localFilters.status || ''}
            onValueChange={(value) => handleSelectChange('status', value)}
          >
            <SelectTrigger id="status">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All statuses</SelectItem>
              {statuses.map((status) => (
                <SelectItem key={status} value={status}>
                  {status}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {/* Customer */}
        <div className="space-y-2">
          <Label htmlFor="customer_id">Customer</Label>
          <Select
            value={localFilters.customer_id?.toString() || ''}
            onValueChange={(value) => handleSelectChange('customer_id', value ? parseInt(value) : '')}
          >
            <SelectTrigger id="customer_id">
              <SelectValue placeholder="All customers" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All customers</SelectItem>
              {customers.map((customer) => (
                <SelectItem key={customer.id} value={customer.id.toString()}>
                  {customer.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {/* Product */}
        <div className="space-y-2">
          <Label htmlFor="product_id">Product</Label>
          <Select
            value={localFilters.product_id?.toString() || ''}
            onValueChange={(value) => handleSelectChange('product_id', value ? parseInt(value) : '')}
          >
            <SelectTrigger id="product_id">
              <SelectValue placeholder="All products" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All products</SelectItem>
              {products.map((product) => (
                <SelectItem key={product.id} value={product.id.toString()}>
                  {product.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {/* Start Date */}
        <div className="space-y-2">
          <Label htmlFor="start_date">Start Date (From)</Label>
          <Input
            id="start_date"
            name="start_date"
            type="date"
            value={localFilters.start_date || ''}
            onChange={handleInputChange}
          />
        </div>
        
        {/* End Date */}
        <div className="space-y-2">
          <Label htmlFor="end_date">Start Date (To)</Label>
          <Input
            id="end_date"
            name="end_date"
            type="date"
            value={localFilters.end_date || ''}
            onChange={handleInputChange}
          />
        </div>
        
        {/* Delayed Orders */}
        <div className="space-y-2 flex items-center">
          <div className="flex items-center space-x-2">
            <Switch
              id="is_delayed"
              checked={localFilters.is_delayed === true}
              onCheckedChange={(checked) => handleSwitchChange('is_delayed', checked ? true : null)}
            />
            <Label htmlFor="is_delayed">Show only delayed orders</Label>
          </div>
        </div>
      </div>
      
      {/* Filter actions */}
      <div className="flex justify-end space-x-2 mt-4">
        <Button
          variant="outline"
          size="sm"
          onClick={resetFilters}
        >
          <X className="w-4 h-4 mr-2" />
          Reset
        </Button>
        <Button
          variant="default"
          size="sm"
          onClick={applyFilters}
        >
          <Search className="w-4 h-4 mr-2" />
          Apply Filters
        </Button>
      </div>
    </div>
  );
};

export default OrdersFilter;

