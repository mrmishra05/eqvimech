import React from 'react';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';

const CustomerForm = ({
  customer,
  onChange,
  isEditing,
  isNew
}) => {
  // Handle input change
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    onChange(name, value);
  };
  
  return (
    <div className="space-y-6">
      {/* Customer Name */}
      <div className="space-y-2">
        <Label htmlFor="name" className="required">Customer Name</Label>
        <Input
          id="name"
          name="name"
          value={customer.name || ''}
          onChange={handleInputChange}
          disabled={!isEditing}
          placeholder="Enter customer name"
        />
      </div>
      
      {/* Contact Person */}
      <div className="space-y-2">
        <Label htmlFor="contact_person" className="required">Contact Person</Label>
        <Input
          id="contact_person"
          name="contact_person"
          value={customer.contact_person || ''}
          onChange={handleInputChange}
          disabled={!isEditing}
          placeholder="Enter contact person name"
        />
      </div>
      
      {/* Contact Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="email" className="required">Email</Label>
          <Input
            id="email"
            name="email"
            type="email"
            value={customer.email || ''}
            onChange={handleInputChange}
            disabled={!isEditing}
            placeholder="Enter email address"
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="phone" className="required">Phone</Label>
          <Input
            id="phone"
            name="phone"
            value={customer.phone || ''}
            onChange={handleInputChange}
            disabled={!isEditing}
            placeholder="Enter phone number"
          />
        </div>
      </div>
      
      {/* Address */}
      <div className="space-y-2">
        <Label htmlFor="address">Address</Label>
        <Textarea
          id="address"
          name="address"
          value={customer.address || ''}
          onChange={handleInputChange}
          disabled={!isEditing}
          placeholder="Enter street address"
          rows={2}
        />
      </div>
      
      {/* City, State, Pincode */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label htmlFor="city">City</Label>
          <Input
            id="city"
            name="city"
            value={customer.city || ''}
            onChange={handleInputChange}
            disabled={!isEditing}
            placeholder="Enter city"
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="state">State</Label>
          <Input
            id="state"
            name="state"
            value={customer.state || ''}
            onChange={handleInputChange}
            disabled={!isEditing}
            placeholder="Enter state"
          />
        </div>
        
        <div className="space-y-2">
          <Label htmlFor="pincode">Pincode</Label>
          <Input
            id="pincode"
            name="pincode"
            value={customer.pincode || ''}
            onChange={handleInputChange}
            disabled={!isEditing}
            placeholder="Enter pincode"
          />
        </div>
      </div>
      
      {/* GSTIN */}
      <div className="space-y-2">
        <Label htmlFor="gstin">GSTIN</Label>
        <Input
          id="gstin"
          name="gstin"
          value={customer.gstin || ''}
          onChange={handleInputChange}
          disabled={!isEditing}
          placeholder="Enter GSTIN"
        />
        <p className="text-xs text-gray-500">
          Format: 27AABCU9603R1ZX (15 characters)
        </p>
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

export default CustomerForm;

