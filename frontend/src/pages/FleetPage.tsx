import { useState, useEffect } from "react";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Plus, Search, MoreVertical, Filter } from "lucide-react";
import { TruckModal } from "../components/TruckModal";
import { fetchTrucks as fetchTrucksApi, deleteTruck as deleteTruckApi, type Truck, type TruckStatus } from "../api/client";

const STATUS_COLORS: Record<TruckStatus, string> = {
    AVAILABLE: "bg-green-500",
    MAINTENANCE: "bg-yellow-500",
    OUT_OF_SERVICE: "bg-red-500",
    INACTIVE: "bg-gray-500",
};

const STATUS_LABELS: Record<TruckStatus, string> = {
    AVAILABLE: "Available",
    MAINTENANCE: "Maintenance",
    OUT_OF_SERVICE: "Out of Service",
    INACTIVE: "Inactive",
};

export default function FleetPage() {
    const [trucks, setTrucks] = useState<Truck[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState<string>("all");
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingTruck, setEditingTruck] = useState<Truck | null>(null);

    const fetchTrucks = async () => {
        try {
            setLoading(true);
            const data = await fetchTrucksApi();
            setTrucks(data);
        } catch (error) {
            console.error("Error fetching trucks:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTrucks();
    }, []);

    const [truckToDelete, setTruckToDelete] = useState<string | null>(null);

    const confirmDelete = (id: string) => {
        setTruckToDelete(id);
    };

    const handleDelete = async () => {
        if (!truckToDelete) return;
        try {
            await deleteTruckApi(truckToDelete);
            fetchTrucks();
        } catch (error) {
            console.error("Error deleting truck:", error);
        } finally {
            setTruckToDelete(null);
        }
    };

    const handleEdit = (truck: Truck) => {
        setEditingTruck(truck);
        setIsModalOpen(true);
    };

    const handleCreate = () => {
        setEditingTruck(null);
        setIsModalOpen(true);
    };

    const filteredTrucks = trucks.filter((truck) => {
        const matchesSearch =
            truck.plate_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (truck.assigned_driver &&
                truck.assigned_driver.toLowerCase().includes(searchQuery.toLowerCase()));
        const matchesStatus = statusFilter === "all" || truck.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    return (
        <div className="p-8 space-y-8 bg-gray-50 min-h-screen">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-gray-900">Fleet Management</h1>
                    <p className="text-gray-500 mt-2">
                        View, filter, and manage all trucks in your fleet at a glance.
                    </p>
                </div>
                <Button onClick={handleCreate} className="bg-blue-600 hover:bg-blue-700 text-white">
                    <Plus className="mr-2 h-4 w-4" /> Add New Truck
                </Button>
            </div>

            <div className="flex items-center gap-4">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                        placeholder="Search by license plate or driver name..."
                        className="pl-10 bg-white"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[180px] bg-white">
                        <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Statuses</SelectItem>
                        {Object.entries(STATUS_LABELS).map(([key, label]) => (
                            <SelectItem key={key} value={key}>
                                {label}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>


                <Button variant="outline" size="icon" className="bg-white">
                    <Filter className="h-4 w-4" />
                </Button>
            </div>

            <div className="bg-white rounded-lg border shadow-sm">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-12">
                                <Checkbox />
                            </TableHead>
                            <TableHead>LICENSE PLATE</TableHead>
                            <TableHead>TRAILER PLATE</TableHead>
                            <TableHead>CAPACITY</TableHead>
                            <TableHead>STATUS</TableHead>
                            <TableHead>CURRENT LOCATION</TableHead>
                            <TableHead>ASSIGNED DRIVER</TableHead>
                            <TableHead className="text-right">ACTIONS</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {loading ? (
                            <TableRow>
                                <TableCell colSpan={8} className="text-center py-8">
                                    Loading trucks...
                                </TableCell>
                            </TableRow>
                        ) : filteredTrucks.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                                    No trucks found.
                                </TableCell>
                            </TableRow>
                        ) : (
                            filteredTrucks.map((truck) => (
                                <TableRow key={truck.id}>
                                    <TableCell>
                                        <Checkbox />
                                    </TableCell>
                                    <TableCell className="font-medium">{truck.plate_number}</TableCell>
                                    <TableCell>{truck.trailer_plate_number || "-"}</TableCell>
                                    <TableCell>{truck.capacity_weight.toLocaleString()} kg</TableCell>
                                    <TableCell>
                                        <div className="flex items-center gap-2">
                                            <div className={`h-2 w-2 rounded-full ${STATUS_COLORS[truck.status]}`} />
                                            <span>{STATUS_LABELS[truck.status]}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-gray-500">{truck.current_location || "-"}</TableCell>
                                    <TableCell className="text-gray-500">{truck.assigned_driver || "-"}</TableCell>
                                    <TableCell className="text-right">
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="icon">
                                                    <MoreVertical className="h-4 w-4" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                <DropdownMenuItem onClick={() => handleEdit(truck)}>
                                                    Edit
                                                </DropdownMenuItem>
                                                <DropdownMenuItem
                                                    className="text-red-600 focus:text-red-600"
                                                    onClick={() => confirmDelete(truck.id)}
                                                >
                                                    Delete
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
                <div className="p-4 border-t flex items-center justify-between text-sm text-gray-500">
                    <span>Showing {filteredTrucks.length} of {trucks.length}</span>
                    <div className="flex gap-2">
                        <Button variant="outline" size="sm" disabled>Previous</Button>
                        <Button variant="outline" size="sm" disabled>Next</Button>
                    </div>
                </div>
            </div>

            <TruckModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSuccess={fetchTrucks}
                truck={editingTruck}
            />

            <AlertDialog open={!!truckToDelete} onOpenChange={(open: boolean) => !open && setTruckToDelete(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This action cannot be undone. This will permanently delete the truck from your fleet.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={handleDelete} className="bg-red-600 hover:bg-red-700">
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
