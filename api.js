const API_BASE_URL = '/api';

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include', // Include cookies for session management
    ...options,
  };

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new ApiError(errorData.error || 'Request failed', response.status);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Network error', 0);
  }
}

// Authentication API
export const authApi = {
  login: (credentials) => apiRequest('/auth/login', {
    method: 'POST',
    body: credentials,
  }),
  
  logout: () => apiRequest('/auth/logout', {
    method: 'POST',
  }),
  
  getCurrentUser: () => apiRequest('/auth/me'),
  
  register: (userData) => apiRequest('/auth/register', {
    method: 'POST',
    body: userData,
  }),
  
  getUsers: () => apiRequest('/auth/users'),
  
  updateUser: (userId, userData) => apiRequest(`/auth/users/${userId}`, {
    method: 'PUT',
    body: userData,
  }),
};

// Orders API
export const ordersApi = {
  getOrders: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/orders${queryString ? `?${queryString}` : ''}`);
  },
  
  getOrder: (id) => apiRequest(`/orders/${id}`),
  
  createOrder: (orderData) => apiRequest('/orders', {
    method: 'POST',
    body: orderData,
  }),
  
  updateOrder: (id, orderData) => apiRequest(`/orders/${id}`, {
    method: 'PUT',
    body: orderData,
  }),
  
  deleteOrder: (id) => apiRequest(`/orders/${id}`, {
    method: 'DELETE',
  }),
  
  getOrderStats: () => apiRequest('/orders/stats'),
};

// Customers API
export const customersApi = {
  getCustomers: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/customers${queryString ? `?${queryString}` : ''}`);
  },
  
  getCustomer: (id) => apiRequest(`/customers/${id}`),
  
  createCustomer: (customerData) => apiRequest('/customers', {
    method: 'POST',
    body: customerData,
  }),
  
  updateCustomer: (id, customerData) => apiRequest(`/customers/${id}`, {
    method: 'PUT',
    body: customerData,
  }),
  
  deleteCustomer: (id) => apiRequest(`/customers/${id}`, {
    method: 'DELETE',
  }),
  
  getCustomerOrders: (id) => apiRequest(`/customers/${id}/orders`),
};

// Products API
export const productsApi = {
  getProducts: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/products${queryString ? `?${queryString}` : ''}`);
  },
  
  getProduct: (id) => apiRequest(`/products/${id}`),
  
  createProduct: (productData) => apiRequest('/products', {
    method: 'POST',
    body: productData,
  }),
  
  updateProduct: (id, productData) => apiRequest(`/products/${id}`, {
    method: 'PUT',
    body: productData,
  }),
  
  deleteProduct: (id) => apiRequest(`/products/${id}`, {
    method: 'DELETE',
  }),
  
  getProductFamilies: () => apiRequest('/product-families'),
  
  createProductFamily: (familyData) => apiRequest('/product-families', {
    method: 'POST',
    body: familyData,
  }),
};

// Dashboard API
export const dashboardApi = {
  getKpis: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/dashboard/kpis${queryString ? `?${queryString}` : ''}`);
  },
  
  getSalesTrends: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/dashboard/sales-trends${queryString ? `?${queryString}` : ''}`);
  },
  
  getOrderStatusDistribution: () => apiRequest('/dashboard/order-status-distribution'),
  
  getProductFamilyPerformance: () => apiRequest('/dashboard/product-family-performance'),
  
  getTopCustomers: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/dashboard/top-customers${queryString ? `?${queryString}` : ''}`);
  },
  
  getDeliveryPerformance: () => apiRequest('/dashboard/delivery-performance'),
};

// Simplified wrapper functions for components
export async function fetchOrders() {
  try {
    return await ordersApi.getOrders();
  } catch (error) {
    console.error('Error fetching orders:', error);
    throw error;
  }
}

export async function fetchCustomers() {
  try {
    return await customersApi.getCustomers();
  } catch (error) {
    console.error('Error fetching customers:', error);
    throw error;
  }
}

export async function fetchProducts() {
  try {
    return await productsApi.getProducts();
  } catch (error) {
    console.error('Error fetching products:', error);
    throw error;
  }
}

export async function createOrder(orderData) {
  try {
    return await ordersApi.createOrder(orderData);
  } catch (error) {
    console.error('Error creating order:', error);
    throw error;
  }
}

export async function updateOrder(id, orderData) {
  try {
    return await ordersApi.updateOrder(id, orderData);
  } catch (error) {
    console.error('Error updating order:', error);
    throw error;
  }
}

export async function deleteOrder(id) {
  try {
    return await ordersApi.deleteOrder(id);
  } catch (error) {
    console.error('Error deleting order:', error);
    throw error;
  }
}

export async function createCustomer(customerData) {
  try {
    return await customersApi.createCustomer(customerData);
  } catch (error) {
    console.error('Error creating customer:', error);
    throw error;
  }
}

export async function updateCustomer(id, customerData) {
  try {
    return await customersApi.updateCustomer(id, customerData);
  } catch (error) {
    console.error('Error updating customer:', error);
    throw error;
  }
}

export async function deleteCustomer(id) {
  try {
    return await customersApi.deleteCustomer(id);
  } catch (error) {
    console.error('Error deleting customer:', error);
    throw error;
  }
}

export async function createProduct(productData) {
  try {
    return await productsApi.createProduct(productData);
  } catch (error) {
    console.error('Error creating product:', error);
    throw error;
  }
}

export async function updateProduct(id, productData) {
  try {
    return await productsApi.updateProduct(id, productData);
  } catch (error) {
    console.error('Error updating product:', error);
    throw error;
  }
}

export async function deleteProduct(id) {
  try {
    return await productsApi.deleteProduct(id);
  } catch (error) {
    console.error('Error deleting product:', error);
    throw error;
  }
}

export async function fetchDashboardKpis() {
  try {
    return await dashboardApi.getKpis();
  } catch (error) {
    console.error('Error fetching dashboard KPIs:', error);
    throw error;
  }
}

export { ApiError };

