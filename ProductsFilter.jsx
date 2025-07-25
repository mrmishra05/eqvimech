import React, { useState } from 'react';
import { Search, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';

const ProductsFilter = ({ 
  filters, 
  onFilterChange, 
  families, 
  tags 
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
  
  // Apply filters
  const applyFilters = () => {
    onFilterChange(localFilters);
  };
  
  // Reset filters
  const resetFilters = () => {
    const emptyFilters = {
      search: '',
      family_id: '',
      tag_id: ''
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
              placeholder="Name, SKU, description..."
              className="pl-8"
              value={localFilters.search || ''}
              onChange={handleInputChange}
            />
          </div>
        </div>
        
        {/* Family */}
        <div className="space-y-2">
          <Label htmlFor="family_id">Product Family</Label>
          <Select
            value={localFilters.family_id?.toString() || ''}
            onValueChange={(value) => handleSelectChange('family_id', value ? parseInt(value) : '')}
          >
            <SelectTrigger id="family_id">
              <SelectValue placeholder="All families" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All families</SelectItem>
              {families.map((family) => (
                <SelectItem key={family.id} value={family.id.toString()}>
                  {family.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {/* Tag */}
        <div className="space-y-2">
          <Label htmlFor="tag_id">Product Tag</Label>
          <Select
            value={localFilters.tag_id?.toString() || ''}
            onValueChange={(value) => handleSelectChange('tag_id', value ? parseInt(value) : '')}
          >
            <SelectTrigger id="tag_id">
              <SelectValue placeholder="All tags" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All tags</SelectItem>
              {tags.map((tag) => (
                <SelectItem key={tag.id} value={tag.id.toString()}>
                  {tag.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
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

export default ProductsFilter;

