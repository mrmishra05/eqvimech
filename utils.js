import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Combines multiple class names using clsx and tailwind-merge
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/**
 * Format currency in Indian Rupees
 */
export function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(amount);
}

/**
 * Format date in Indian format (DD/MM/YYYY)
 */
export function formatDate(dateString) {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-IN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    }).format(date);
  } catch (error) {
    return '';
  }
}

/**
 * Get initials from a name
 */
export function getInitials(name) {
  if (!name) return '';
  
  return name
    .split(' ')
    .map(part => part.charAt(0).toUpperCase())
    .slice(0, 2)
    .join('');
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text, maxLength) {
  if (!text || text.length <= maxLength) return text;
  
  return `${text.slice(0, maxLength)}...`;
}

/**
 * Calculate percentage
 */
export function calculatePercentage(value, total) {
  if (!total) return 0;
  
  return (value / total) * 100;
}

/**
 * Debounce function
 */
export function debounce(func, wait) {
  let timeout;
  
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

