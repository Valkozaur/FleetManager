import axios from 'axios';

export interface Order {
    id: number;
    email_id: string;
    customer: string;
    loading_address: string;
    unloading_address: string;
    loading_date: string;
    unloading_date: string;
    status: 'Pending' | 'Assigned' | 'In Transit' | 'Completed' | 'Cancelled';
}

const API_URL = import.meta.env.VITE_API_URL || 'https://api.valdanktrading.org';

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true, // Send cookies with cross-origin requests
});

export const fetchOrders = async (): Promise<Order[]> => {
    const response = await apiClient.get<Order[]>('/orders/');
    return response.data;
};

export const fetchOrder = async (id: number): Promise<Order> => {
    const response = await apiClient.get<Order>(`/orders/${id}`);
    return response.data;
};
