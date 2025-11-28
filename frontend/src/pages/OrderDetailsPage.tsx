import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchOrder } from '../api/client';
import { ArrowLeft, MapPin, Package, Truck, Calendar, User, Info } from 'lucide-react';

export function OrderDetailsPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const orderId = parseInt(id || '0', 10);

    const { data: order, isLoading, error } = useQuery({
        queryKey: ['order', orderId],
        queryFn: () => fetchOrder(orderId),
        enabled: !!orderId,
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gray-50">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (error || !order) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Order not found</h2>
                <button
                    onClick={() => navigate('/orders')}
                    className="flex items-center text-blue-600 hover:text-blue-800"
                >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Orders
                </button>
            </div>
        );
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'Pending': return 'bg-yellow-100 text-yellow-800';
            case 'Assigned': return 'bg-blue-100 text-blue-800';
            case 'In Transit': return 'bg-purple-100 text-purple-800';
            case 'Completed': return 'bg-green-100 text-green-800';
            case 'Cancelled': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="space-y-1">
                        <div className="flex items-center space-x-4 text-sm text-gray-500 mb-2">
                            <button onClick={() => navigate('/orders')} className="hover:text-gray-900">Dashboard</button>
                            <span>/</span>
                            <button onClick={() => navigate('/orders')} className="hover:text-gray-900">Orders</button>
                            <span>/</span>
                            <span className="text-gray-900 font-medium">#{order.email_id}</span>
                        </div>
                        <h1 className="text-3xl font-bold text-gray-900">Order Details: #{order.email_id}</h1>
                    </div>
                    <div className="flex space-x-3">
                        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium flex items-center">
                            <Truck className="w-4 h-4 mr-2" />
                            Assign to Truck
                        </button>
                    </div>
                </div>

                {/* Order Summary Card */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Order Summary</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                            <p className="text-sm text-gray-500 mb-1">Reference Number</p>
                            <p className="font-medium text-gray-900">#{order.email_id}</p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500 mb-1">Status</p>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                                {order.status}
                            </span>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500 mb-1">Order Creation</p>
                            <p className="font-medium text-gray-900">{new Date(order.loading_date).toLocaleDateString()}</p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left Column - Location & Cargo */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Location Details */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                            <h2 className="text-lg font-semibold text-gray-900 mb-6">Location Details</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                {/* Loading Point */}
                                <div className="space-y-4">
                                    <div className="flex items-center space-x-3">
                                        <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
                                            <MapPin className="w-5 h-5" />
                                        </div>
                                        <h3 className="font-medium text-gray-900">Loading Point</h3>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-500 mb-1">Address</p>
                                        <p className="text-gray-900">{order.loading_address}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-500 mb-1">Date & Time</p>
                                        <div className="flex items-center text-gray-900">
                                            <Calendar className="w-4 h-4 mr-2 text-gray-400" />
                                            {new Date(order.loading_date).toLocaleString()}
                                        </div>
                                    </div>
                                </div>

                                {/* Unloading Point */}
                                <div className="space-y-4">
                                    <div className="flex items-center space-x-3">
                                        <div className="p-2 bg-green-50 rounded-lg text-green-600">
                                            <MapPin className="w-5 h-5" />
                                        </div>
                                        <h3 className="font-medium text-gray-900">Unloading Point</h3>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-500 mb-1">Address</p>
                                        <p className="text-gray-900">{order.unloading_address}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-500 mb-1">Date & Time</p>
                                        <div className="flex items-center text-gray-900">
                                            <Calendar className="w-4 h-4 mr-2 text-gray-400" />
                                            {new Date(order.unloading_date).toLocaleString()}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Cargo & Vehicle Requirements */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                            <h2 className="text-lg font-semibold text-gray-900 mb-6">Cargo & Vehicle Requirements</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <p className="text-sm text-gray-500 mb-1">Cargo Description</p>
                                    <div className="flex items-center text-gray-900">
                                        <Package className="w-4 h-4 mr-2 text-gray-400" />
                                        General Cargo
                                    </div>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500 mb-1">Weight</p>
                                    <p className="font-medium text-gray-900">-- kg</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500 mb-1">Required Vehicle</p>
                                    <div className="flex items-center text-gray-900">
                                        <Truck className="w-4 h-4 mr-2 text-gray-400" />
                                        Standard Truck
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right Column - System Info */}
                    <div className="space-y-6">
                        {/* Map Placeholder */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-64 flex items-center justify-center bg-gray-50">
                            <div className="text-center text-gray-500">
                                <MapPin className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                <p>Map View</p>
                            </div>
                        </div>

                        {/* Source & System Info */}
                        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">Source & System Info</h2>
                            <div className="space-y-4">
                                <div>
                                    <p className="text-sm text-gray-500 mb-1">Customer</p>
                                    <div className="flex items-center text-gray-900">
                                        <User className="w-4 h-4 mr-2 text-gray-400" />
                                        {order.customer || 'Unknown'}
                                    </div>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-500 mb-1">System ID</p>
                                    <div className="flex items-center text-gray-900 font-mono text-sm">
                                        <Info className="w-4 h-4 mr-2 text-gray-400" />
                                        {order.id}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
