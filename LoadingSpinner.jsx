import React from 'react';

const LoadingSpinner = ({ size = 'default' }) => {
  // Size classes
  const sizeClasses = {
    small: 'w-4 h-4 border-2',
    default: 'w-8 h-8 border-4',
    large: 'w-12 h-12 border-4'
  };
  
  return (
    <div className="flex justify-center items-center">
      <div
        className={`${sizeClasses[size]} rounded-full border-t-orange-600 border-orange-200 animate-spin`}
      />
    </div>
  );
};

export default LoadingSpinner;

