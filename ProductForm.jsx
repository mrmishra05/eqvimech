import React, { useState } from 'react';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { X } from 'lucide-react';

const ProductForm = ({
  product,
  families,
  tags,
  onChange,
  isEditing,
  isNew
}) => {
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
  
  // Handle tag selection
  const handleTagToggle = (tagId) => {
    const currentTags = product.tags || [];
    const tag = tags.find(t => t.id === tagId);
    
    if (!tag) return;
    
    // Check if tag is already selected
    const isSelected = currentTags.some(t => t.id === tagId);
    
    if (isSelected) {
      // Remove tag
      onChange('tags', currentTags.filter(t => t.id !== tagId));
    } else {
      // Add tag
      onChange('tags', [...currentTags, tag]);
    }
  };
  
  // Check if a tag is selected
  const isTagSelected = (tagId) => {
    return (product.tags || []).some(t => t.id === tagId);
  };
  
  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <div>
        <h3 className="text-lg font-medium mb-4">Basic Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Product Name */}
          <div className="space-y-2">
            <Label htmlFor="name" className="required">Product Name</Label>
            <Input
              id="name"
              name="name"
              value={product.name || ''}
              onChange={handleInputChange}
              disabled={!isEditing}
              placeholder="Enter product name"
            />
          </div>
          
          {/* SKU */}
          <div className="space-y-2">
            <Label htmlFor="sku" className="required">SKU</Label>
            <Input
              id="sku"
              name="sku"
              value={product.sku || ''}
              onChange={handleInputChange}
              disabled={!isEditing}
              placeholder="Enter SKU"
            />
          </div>
        </div>
        
        {/* Description */}
        <div className="space-y-2 mt-4">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            name="description"
            value={product.description || ''}
            onChange={handleInputChange}
            disabled={!isEditing}
            placeholder="Enter product description"
            rows={3}
          />
        </div>
        
        {/* Family */}
        <div className="space-y-2 mt-4">
          <Label htmlFor="family_id" className="required">Product Family</Label>
          <Select
            value={product.family_id?.toString() || ''}
            onValueChange={(value) => handleSelectChange('family_id', parseInt(value))}
            disabled={!isEditing}
          >
            <SelectTrigger id="family_id">
              <SelectValue placeholder="Select a family" />
            </SelectTrigger>
            <SelectContent>
              {families.map((family) => (
                <SelectItem key={family.id} value={family.id.toString()}>
                  {family.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      
      {/* Pricing and Lead Time */}
      <div>
        <h3 className="text-lg font-medium mb-4">Pricing and Lead Time</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Price */}
          <div className="space-y-2">
            <Label htmlFor="price" className="required">Price (₹)</Label>
            <Input
              id="price"
              name="price"
              type="number"
              min="0"
              step="0.01"
              value={product.price || ''}
              onChange={handleNumberChange}
              disabled={!isEditing}
            />
          </div>
          
          {/* Cost */}
          <div className="space-y-2">
            <Label htmlFor="cost">Cost (₹)</Label>
            <Input
              id="cost"
              name="cost"
              type="number"
              min="0"
              step="0.01"
              value={product.cost || ''}
              onChange={handleNumberChange}
              disabled={!isEditing}
            />
          </div>
          
          {/* Lead Time */}
          <div className="space-y-2">
            <Label htmlFor="lead_time_days">Lead Time (Days)</Label>
            <Input
              id="lead_time_days"
              name="lead_time_days"
              type="number"
              min="1"
              value={product.lead_time_days || ''}
              onChange={handleNumberChange}
              disabled={!isEditing}
            />
          </div>
        </div>
      </div>
      
      {/* Tags */}
      <div>
        <h3 className="text-lg font-medium mb-4">Product Tags</h3>
        
        {/* Selected Tags */}
        <div className="mb-4">
          <Label>Selected Tags</Label>
          <div className="flex flex-wrap gap-2 mt-2">
            {(product.tags || []).length === 0 ? (
              <div className="text-gray-500 text-sm">No tags selected</div>
            ) : (
              product.tags.map(tag => (
                <Badge 
                  key={tag.id} 
                  className={`bg-${tag.color}-100 text-${tag.color}-800 flex items-center`}
                >
                  {tag.name}
                  {isEditing && (
                    <button
                      type="button"
                      className="ml-1 text-gray-500 hover:text-gray-700"
                      onClick={() => handleTagToggle(tag.id)}
                    >
                      <X className="h-3 w-3" />
                    </button>
                  )}
                </Badge>
              ))
            )}
          </div>
        </div>
        
        {/* Available Tags */}
        {isEditing && (
          <div>
            <Label>Available Tags</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {tags.map(tag => (
                <Badge 
                  key={tag.id} 
                  className={`
                    ${isTagSelected(tag.id) 
                      ? `bg-${tag.color}-100 text-${tag.color}-800` 
                      : 'bg-gray-100 text-gray-800'}
                    cursor-pointer hover:bg-${tag.color}-200
                  `}
                  onClick={() => handleTagToggle(tag.id)}
                >
                  {tag.name}
                </Badge>
              ))}
            </div>
          </div>
        )}
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

export default ProductForm;

