import React, { useState } from 'react';
import { IndianRupee, Plus } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';
import { Progress } from '../ui/progress';

const OrderPayment = ({ order, onPaymentUpdate }) => {
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');
  
  // Calculate payment progress
  const totalAmount = order.amount || 0;
  const amountReceived = order.amount_received || 0;
  const amountDue = totalAmount - amountReceived;
  const paymentProgress = totalAmount > 0 ? (amountReceived / totalAmount) * 100 : 0;
  
  // Handle payment update
  const handlePaymentUpdate = () => {
    const amount = parseFloat(paymentAmount) || 0;
    if (amount <= 0) {
      alert('Please enter a valid payment amount');
      return;
    }
    
    const newAmountReceived = amountReceived + amount;
    if (newAmountReceived > totalAmount) {
      alert('Payment amount exceeds the total order amount');
      return;
    }
    
    onPaymentUpdate(newAmountReceived);
    setShowPaymentDialog(false);
    setPaymentAmount('');
  };
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Payment Information</h3>
        {onPaymentUpdate && amountDue > 0 && (
          <Button
            variant="default"
            size="sm"
            onClick={() => setShowPaymentDialog(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            Record Payment
          </Button>
        )}
      </div>
      
      {/* Payment summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-50 p-4 rounded-md">
          <div className="text-sm text-gray-500">Total Amount</div>
          <div className="text-2xl font-semibold flex items-center">
            <IndianRupee className="w-5 h-5 mr-1" />
            {totalAmount.toLocaleString('en-IN')}
          </div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-md">
          <div className="text-sm text-gray-500">Amount Received</div>
          <div className="text-2xl font-semibold flex items-center text-green-600">
            <IndianRupee className="w-5 h-5 mr-1" />
            {amountReceived.toLocaleString('en-IN')}
          </div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-md">
          <div className="text-sm text-gray-500">Amount Due</div>
          <div className="text-2xl font-semibold flex items-center text-red-600">
            <IndianRupee className="w-5 h-5 mr-1" />
            {amountDue.toLocaleString('en-IN')}
          </div>
        </div>
      </div>
      
      {/* Payment progress */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Payment Progress</span>
          <span>{paymentProgress.toFixed(0)}%</span>
        </div>
        <Progress value={paymentProgress} className="h-2" />
      </div>
      
      {/* Payment history */}
      <div className="space-y-2">
        <h4 className="font-medium">Payment History</h4>
        {order.payment_history?.length > 0 ? (
          <div className="border rounded-md overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recorded By
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {order.payment_history.map((payment, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(payment.timestamp).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ₹{payment.amount.toLocaleString('en-IN')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {payment.user_name || 'Unknown'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-sm text-gray-500 py-4">
            No payment history available.
            {amountReceived > 0 && ' Initial payment was recorded during order creation.'}
          </div>
        )}
      </div>
      
      {/* Record payment dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Payment</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-500">Total Amount</div>
                  <div className="text-lg font-semibold">₹{totalAmount.toLocaleString('en-IN')}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Amount Due</div>
                  <div className="text-lg font-semibold text-red-600">₹{amountDue.toLocaleString('en-IN')}</div>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="payment_amount" className="required">Payment Amount (₹)</Label>
                <Input
                  id="payment_amount"
                  type="number"
                  min="0"
                  step="0.01"
                  max={amountDue}
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  placeholder="Enter payment amount"
                />
                {parseFloat(paymentAmount) > amountDue && (
                  <p className="text-xs text-red-500">
                    Payment amount exceeds the due amount
                  </p>
                )}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowPaymentDialog(false)}
            >
              Cancel
            </Button>
            <Button
              variant="default"
              onClick={handlePaymentUpdate}
              disabled={!paymentAmount || parseFloat(paymentAmount) <= 0 || parseFloat(paymentAmount) > amountDue}
            >
              Record Payment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default OrderPayment;

