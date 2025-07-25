import React from 'react';

const DashboardKpiCard = ({ 
  title, 
  value, 
  icon, 
  description, 
  color = 'bg-white', 
  onClick 
}) => {
  return (
    <div 
      className={`${color} rounded-lg shadow-sm p-6 transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:shadow-md transform hover:-translate-y-1' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
          <div className="mt-2 flex items-baseline">
            <p className="text-3xl font-semibold text-gray-900">{value}</p>
          </div>
          <p className="mt-1 text-sm text-gray-500">{description}</p>
        </div>
        <div className="p-3 rounded-full bg-opacity-10">
          {icon}
        </div>
      </div>
    </div>
  );
};

export default DashboardKpiCard;

