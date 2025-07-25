import React, { useState } from 'react';
import { Search, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';

const CustomersFilter = ({ filters, onFilterChange }) => {
  const [localFilters, setLocalFilters] = useState(filters);
  
  // Handle input change
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLocalFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Apply filters
  const applyFilters = () => {
    onFilterChange(localFilters);
  };
  
  // Reset filters
  const resetFilters = () => {
    const emptyFilters = {
      search: '',
      city: '',
      state: ''
    };
    setLocalFilters(emptyFilters);
    onFilterChange(emptyFilters);
  };
  
  return (
    <div className="bg-white p-4 rounded-md border shadow-sm">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Search */}
        <div className="space-y-2">
          <Label htmlFor="search">Search</Label>
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-500" />
            <Input
              id="search"
              name="search"
              placeholder="Name, contact person, email..."
              className="pl-8"
              value={localFilters.search || ''}
              onChange={handleInputChange}
            />
          </div>
        </div>
        
        {/* City */}
        <div className="space-y-2">
          <Label htmlFor="city">City</Label>
          <Input
            id="city"
            name="city"
            placeholder="Filter by city"
            value={localFilters.city || ''}
            onChange={handleInputChange}
          />
        </div>
        
        {/* State */}
        <div className="space-y-2">
          <Label htmlFor="state">State</Label>
          <Input
            id="state"
            name="state"
            placeholder="Filter by state"
            value={localFilters.state || ''}
            onChange={handleInputChange}
          />
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

export default CustomersFilter;

