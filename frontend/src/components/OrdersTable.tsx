import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { type Order } from "@/api/client";
import { StatusBadge } from "./StatusBadge";
import { Eye, Truck, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { format } from "date-fns";
import { useNavigate } from "react-router-dom";

interface OrdersTableProps {
    orders: Order[];
}

export function OrdersTable({ orders }: OrdersTableProps) {
    const navigate = useNavigate();

    return (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            <Table>
                <TableHeader className="bg-gray-50/50">
                    <TableRow>
                        <TableHead className="w-[50px]"></TableHead>
                        <TableHead className="font-semibold text-gray-600">ORDER ID</TableHead>
                        <TableHead className="font-semibold text-gray-600">CUSTOMER</TableHead>
                        <TableHead className="font-semibold text-gray-600">FROM</TableHead>
                        <TableHead className="font-semibold text-gray-600">TO</TableHead>
                        <TableHead className="font-semibold text-gray-600">DATE</TableHead>
                        <TableHead className="font-semibold text-gray-600">STATUS</TableHead>
                        <TableHead className="font-semibold text-gray-600 text-right">ACTIONS</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {orders.map((order) => (
                        <TableRow
                            key={order.id}
                            className="hover:bg-gray-50/50 cursor-pointer"
                            onClick={() => navigate(`/orders/${order.id}`)}
                        >
                            <TableCell onClick={(e) => e.stopPropagation()}>
                                <input type="checkbox" className="rounded border-gray-300" />
                            </TableCell>
                            <TableCell className="font-medium">#{order.id}</TableCell>
                            <TableCell>
                                <div className="font-medium text-gray-900">{order.customer || "Unknown"}</div>
                            </TableCell>
                            <TableCell className="text-gray-600">{order.loading_address}</TableCell>
                            <TableCell className="text-gray-600">{order.unloading_address}</TableCell>
                            <TableCell className="text-gray-600">
                                {order.loading_date ? format(new Date(order.loading_date), "yyyy-MM-dd") : "-"}
                            </TableCell>
                            <TableCell>
                                <StatusBadge status={order.status} />
                            </TableCell>
                            <TableCell className="text-right">
                                <div className="flex items-center justify-end gap-2">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 text-gray-500 hover:text-gray-900"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            navigate(`/orders/${order.id}`);
                                        }}
                                    >
                                        <Eye className="h-4 w-4" />
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 text-gray-500 hover:text-gray-900"
                                        onClick={(e) => e.stopPropagation()}
                                    >
                                        <Truck className="h-4 w-4" />
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 text-gray-500 hover:text-gray-900"
                                        onClick={(e) => e.stopPropagation()}
                                    >
                                        <Pencil className="h-4 w-4" />
                                    </Button>
                                </div>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}
