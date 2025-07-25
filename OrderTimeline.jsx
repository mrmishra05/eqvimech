import React, { useState } from 'react';
import { format } from 'date-fns';
import { CheckCircle, Circle, AlertTriangle, ChevronRight } from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';

const OrderTimeline = ({ order, statuses, onStatusUpdate }) => {
  const [showStatusDialog, setShowStatusDialog] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('');
  const [statusNotes, setStatusNotes] = useState('');
  
  // Helper function to format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm');
    } catch (error) {
      return 'Invalid date';
    }
  };
  
  // Get current status index
  const getCurrentStatusIndex = () => {
    return statuses.findIndex(status => status === order.status);
  };
  
  // Check if a status is completed
  const isStatusCompleted = (statusIndex) => {
    const currentIndex = getCurrentStatusIndex();
    return statusIndex < currentIndex;
  };
  
  // Check if a status is current
  const isStatusCurrent = (statusIndex) => {
    const currentIndex = getCurrentStatusIndex();
    return statusIndex === currentIndex;
  };
  
  // Handle status update
  const handleStatusUpdate = (status) => {
    setSelectedStatus(status);
    setStatusNotes('');
    setShowStatusDialog(true);
  };
  
  // Confirm status update
  const confirmStatusUpdate = () => {
    onStatusUpdate(selectedStatus, statusNotes);
    setShowStatusDialog(false);
  };
  
  // Get next available status
  const getNextStatus = () => {
    const currentIndex = getCurrentStatusIndex();
    if (currentIndex < statuses.length - 1) {
      return statuses[currentIndex + 1];
    }
    return null;
  };
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Manufacturing Timeline</h3>
        {onStatusUpdate && getNextStatus() && (
          <Button
            variant="default"
            size="sm"
            onClick={() => handleStatusUpdate(getNextStatus())}
          >
            <ChevronRight className="w-4 h-4 mr-2" />
            Update to {getNextStatus()}
          </Button>
        )}
      </div>
      
      {/* Status progress */}
      <div className="relative">
        {/* Progress line */}
        <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200" />
        
        {/* Status items */}
        <div className="space-y-8">
          {statuses.map((status, index) => {
            const isCompleted = isStatusCompleted(index);
            const isCurrent = isStatusCurrent(index);
            
            // Find status history entry
            const historyEntry = order.status_history?.find(h => h.new_status === status);
            
            return (
              <div key={status} className="relative flex items-start">
                {/* Status icon */}
                <div className={`
                  flex items-center justify-center w-10 h-10 rounded-full z-10
                  ${isCompleted ? 'bg-green-100' : isCurrent ? 'bg-blue-100' : 'bg-gray-100'}
                `}>
                  {isCompleted ? (
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  ) : isCurrent ? (
                    <Circle className="w-6 h-6 text-blue-600" />
                  ) : (
                    <Circle className="w-6 h-6 text-gray-400" />
                  )}
                </div>
                
                {/* Status content */}
                <div className="ml-4">
                  <div className="flex items-center">
                    <h4 className={`font-medium ${
                      isCompleted ? 'text-green-600' : isCurrent ? 'text-blue-600' : 'text-gray-500'
                    }`}>
                      {status}
                    </h4>
                    
                    {/* If current status is delayed */}
                    {isCurrent && order.is_delayed && (
                      <span className="ml-2 flex items-center text-red-500 text-sm">
                        <AlertTriangle className="w-4 h-4 mr-1" />
                        Delayed
                      </span>
                    )}
                    
                    {/* Update button */}
                    {onStatusUpdate && isCurrent && getNextStatus() && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="ml-2"
                        onClick={() => handleStatusUpdate(getNextStatus())}
                      >
                        Update to {getNextStatus()}
                      </Button>
                    )}
                  </div>
                  
                  {/* Status timestamp and user */}
                  {historyEntry && (
                    <div className="text-sm text-gray-500">
                      {formatDate(historyEntry.timestamp)}
                      {historyEntry.user_name && (
                        <span> by {historyEntry.user_name}</span>
                      )}
                    </div>
                  )}
                  
                  {/* Status notes */}
                  {historyEntry?.notes && (
                    <div className="mt-1 text-sm text-gray-600">
                      {historyEntry.notes}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Status update dialog */}
      <Dialog open={showStatusDialog} onOpenChange={setShowStatusDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Order Status</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p>
              Are you sure you want to update the status from{' '}
              <strong>{order.status}</strong> to <strong>{selectedStatus}</strong>?
            </p>
            <div className="mt-4 space-y-2">
              <label htmlFor="status_notes" className="text-sm font-medium">
                Notes (optional)
              </label>
              <Textarea
                id="status_notes"
                value={statusNotes}
                onChange={(e) => setStatusNotes(e.target.value)}
                placeholder="Add any notes about this status update"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowStatusDialog(false)}
            >
              Cancel
            </Button>
            <Button
              variant="default"
              onClick={confirmStatusUpdate}
            >
              Update Status
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default OrderTimeline;

