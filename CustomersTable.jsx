import React from 'react';
import { ChevronLeft, ChevronRight, ArrowUpDown, Eye } from 'lucide-react';
import { Button } from '../ui/button';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '../ui/table';

const CustomersTable = ({ 
  customers, 
  onViewCustomer, 
  onSort, 
  sorting, 
  pagination, 
  onPageChange 
}) => {
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
                  ID
                  {renderSortIndicator('id')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('name')}
                >
                  Name
                  {renderSortIndicator('name')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('contact_person')}
                >
                  Contact Person
                  {renderSortIndicator('contact_person')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('email')}
                >
                  Email
                  {renderSortIndicator('email')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('phone')}
                >
                  Phone
                  {renderSortIndicator('phone')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('city')}
                >
                  City
                  {renderSortIndicator('city')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('state')}
                >
                  State
                  {renderSortIndicator('state')}
                </button>
              </TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {customers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                  No customers found. Try adjusting your filters.
                </TableCell>
              </TableRow>
            ) : (
              customers.map((customer) => (
                <TableRow key={customer.id}>
                  <TableCell className="font-medium">{customer.id}</TableCell>
                  <TableCell>{customer.name}</TableCell>
                  <TableCell>{customer.contact_person}</TableCell>
                  <TableCell>
                    <a href={`mailto:${customer.email}`} className="text-blue-600 hover:underline">
                      {customer.email}
                    </a>
                  </TableCell>
                  <TableCell>
                    <a href={`tel:${customer.phone}`} className="text-blue-600 hover:underline">
                      {customer.phone}
                    </a>
                  </TableCell>
                  <TableCell>{customer.city}</TableCell>
                  <TableCell>{customer.state}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewCustomer(customer.id)}
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
            Showing {customers.length} of {pagination.totalItems} customers
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

export default CustomersTable;

