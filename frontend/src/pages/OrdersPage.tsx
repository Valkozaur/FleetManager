import { useQuery } from "@tanstack/react-query";
import { fetchOrders } from "@/api/client";
import { Layout } from "@/components/Layout";
import { OrdersTable } from "@/components/OrdersTable";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

export function OrdersPage() {
    const { data: orders, isLoading, error } = useQuery({
        queryKey: ["orders"],
        queryFn: fetchOrders,
    });

    return (
        <Layout>
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-gray-900">Orders Management</h1>
                </div>

                {/* Filters */}
                <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm space-y-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                            placeholder="Search by Order ID, Customer Name..."
                            className="pl-10 bg-gray-50 border-gray-200"
                        />
                    </div>
                    <div className="flex flex-wrap gap-4">
                        <Select>
                            <SelectTrigger className="w-[180px] bg-gray-50 border-gray-200">
                                <SelectValue placeholder="Status" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Statuses</SelectItem>
                                <SelectItem value="pending">Pending</SelectItem>
                                <SelectItem value="assigned">Assigned</SelectItem>
                                <SelectItem value="in-transit">In Transit</SelectItem>
                                <SelectItem value="completed">Completed</SelectItem>
                            </SelectContent>
                        </Select>
                        <Select>
                            <SelectTrigger className="w-[180px] bg-gray-50 border-gray-200">
                                <SelectValue placeholder="Loading Address" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Locations</SelectItem>
                            </SelectContent>
                        </Select>
                        <Select>
                            <SelectTrigger className="w-[180px] bg-gray-50 border-gray-200">
                                <SelectValue placeholder="Unloading Address" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Locations</SelectItem>
                            </SelectContent>
                        </Select>
                        <Button variant="outline" className="bg-gray-50 border-gray-200 text-gray-700">
                            Date Range
                        </Button>
                    </div>
                </div>

                {/* Content */}
                {isLoading ? (
                    <div className="text-center py-10">Loading orders...</div>
                ) : error ? (
                    <div className="text-center py-10 text-red-500">Error loading orders</div>
                ) : (
                    <>
                        <OrdersTable orders={orders || []} />
                        <div className="flex items-center justify-between">
                            <div className="text-sm text-gray-500">
                                Showing <span className="font-medium">{orders?.length || 0}</span> orders
                            </div>
                            <div className="flex gap-2">
                                {/* Pagination placeholder */}
                                <Button variant="outline" disabled>Previous</Button>
                                <Button variant="outline" disabled>Next</Button>
                            </div>
                        </div>
                    </>
                )}

                <div className="fixed bottom-8 left-8">
                    <Button className="bg-gray-900 text-white hover:bg-gray-800 h-12 px-6 rounded-lg shadow-lg">
                        Create New Order
                    </Button>
                </div>
            </div>
        </Layout>
    );
}
