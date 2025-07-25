import React from 'react';
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

const ProductsTable = ({ 
  products, 
  onViewProduct, 
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
  
  // Helper function to render tags
  const renderTags = (tags) => {
    if (!tags || tags.length === 0) return null;
    
    return (
      <div className="flex flex-wrap gap-1">
        {tags.map(tag => (
          <Badge 
            key={tag.id} 
            className={`bg-${tag.color}-100 text-${tag.color}-800 text-xs`}
          >
            {tag.name}
          </Badge>
        ))}
      </div>
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
                  onClick={() => onSort('sku')}
                >
                  SKU
                  {renderSortIndicator('sku')}
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
                  onClick={() => onSort('family_name')}
                >
                  Family
                  {renderSortIndicator('family_name')}
                </button>
              </TableHead>
              <TableHead>Tags</TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('price')}
                >
                  Price (₹)
                  {renderSortIndicator('price')}
                </button>
              </TableHead>
              <TableHead>
                <button 
                  className="flex items-center text-left font-medium"
                  onClick={() => onSort('lead_time_days')}
                >
                  Lead Time
                  {renderSortIndicator('lead_time_days')}
                </button>
              </TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {products.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                  No products found. Try adjusting your filters.
                </TableCell>
              </TableRow>
            ) : (
              products.map((product) => (
                <TableRow key={product.id}>
                  <TableCell className="font-medium">{product.sku}</TableCell>
                  <TableCell>{product.name}</TableCell>
                  <TableCell>{product.family_name}</TableCell>
                  <TableCell>{renderTags(product.tags)}</TableCell>
                  <TableCell>{product.price.toLocaleString('en-IN')}</TableCell>
                  <TableCell>{product.lead_time_days} days</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewProduct(product.id)}
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
            Showing {products.length} of {pagination.totalItems} products
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

export default ProductsTable;

