import React from 'react';

const Logo = ({ size = 'default' }) => {
  // Size variants
  const sizes = {
    small: {
      container: 'h-8',
      em: 'text-xl',
      text: 'text-xs'
    },
    default: {
      container: 'h-10',
      em: 'text-2xl',
      text: 'text-sm'
    },
    large: {
      container: 'h-12',
      em: 'text-3xl',
      text: 'text-base'
    }
  };
  
  const sizeClass = sizes[size] || sizes.default;
  
  return (
    <div className="flex items-center">
      <div className={`flex items-center ${sizeClass.container}`}>
        {/* EM Logo */}
        <div className="flex items-center">
          <span className={`font-bold ${sizeClass.em} text-orange-600`}>E</span>
          <span className={`font-bold ${sizeClass.em} text-orange-600 -ml-1`}>M</span>
        </div>
        
        {/* Company Name */}
        <div className="ml-1 flex flex-col justify-center">
          <span className={`font-semibold uppercase leading-none ${sizeClass.text} text-gray-800`}>
            EQVIMECH
          </span>
          <span className={`text-xs text-gray-600 leading-none`}>
            Private Limited
          </span>
        </div>
      </div>
    </div>
  );
};

export default Logo;

