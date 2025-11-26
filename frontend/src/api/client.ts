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

const API_URL = 'http://localhost:8000'; // Adjust if needed

export const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const fetchOrders = async (): Promise<Order[]> => {
    const response = await apiClient.get<Order[]>('/orders/');
    return response.data;
};
