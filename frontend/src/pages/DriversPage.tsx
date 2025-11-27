import { useState, useEffect } from "react";
import { Plus, Search, MoreVertical, Truck, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
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

// Types
interface Driver {
    id: string;
    name: string;
    phone: string;
    status: "AVAILABLE" | "ON_ROUTE" | "OFF_DUTY";
    truck_id: string | null;
    assigned_truck_plate: string | null;
}

interface Truck {
    id: string;
    plate_number: string;
    status: string;
}

export default function DriversPage() {
    const [drivers, setDrivers] = useState<Driver[]>([]);
    const [trucks, setTrucks] = useState<Truck[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState("All");

    // Modal states
    const [isAddDriverOpen, setIsAddDriverOpen] = useState(false);
    const [isAssignTruckOpen, setIsAssignTruckOpen] = useState(false);
    const [selectedDriver, setSelectedDriver] = useState<Driver | null>(null);
    const [driverForm, setDriverForm] = useState({ name: "", phone: "", status: "AVAILABLE" });
    const [isEditing, setIsEditing] = useState(false);
    const [selectedTruckId, setSelectedTruckId] = useState<string>("");
    const [driverToDelete, setDriverToDelete] = useState<string | null>(null);

    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

    useEffect(() => {
        fetchDrivers();
        fetchTrucks();
    }, []);

    const fetchDrivers = async () => {
        try {
            const response = await fetch(`${API_URL}/drivers/`);
            if (response.ok) {
                const data = await response.json();
                setDrivers(data);
            }
        } catch (error) {
            console.error("Error fetching drivers:", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchTrucks = async () => {
        try {
            const response = await fetch(`${API_URL}/trucks/`);
            if (response.ok) {
                const data = await response.json();
                setTrucks(data);
            }
        } catch (error) {
            console.error("Error fetching trucks:", error);
        }
    };

    const handleSaveDriver = async () => {
        try {
            const url = isEditing && selectedDriver
                ? `${API_URL}/drivers/${selectedDriver.id}`
                : `${API_URL}/drivers/`;

            const method = isEditing ? "PUT" : "POST";

            const response = await fetch(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(driverForm),
            });

            if (response.ok) {
                setIsAddDriverOpen(false);
                setDriverForm({ name: "", phone: "", status: "AVAILABLE" });
                setIsEditing(false);
                setSelectedDriver(null);
                fetchDrivers();
            }
        } catch (error) {
            console.error("Error saving driver:", error);
        }
    };

    const openAddModal = () => {
        setIsEditing(false);
        setDriverForm({ name: "", phone: "", status: "AVAILABLE" });
        setIsAddDriverOpen(true);
    };

    const openEditModal = (driver: Driver) => {
        setIsEditing(true);
        setSelectedDriver(driver);
        setDriverForm({
            name: driver.name,
            phone: driver.phone,
            status: driver.status as string
        });
        setIsAddDriverOpen(true);
    };

    const handleDeleteClick = (id: string) => {
        setDriverToDelete(id);
    };

    const handleConfirmDelete = async () => {
        if (!driverToDelete) return;
        try {
            const response = await fetch(`${API_URL}/drivers/${driverToDelete}`, {
                method: "DELETE",
            });
            if (response.ok) {
                fetchDrivers();
            }
        } catch (error) {
            console.error("Error deleting driver:", error);
        } finally {
            setDriverToDelete(null);
        }
    };

    const handleAssignTruck = async () => {
        if (!selectedDriver || !selectedTruckId) return;
        try {
            const response = await fetch(`${API_URL}/drivers/${selectedDriver.id}/assign_truck?truck_id=${selectedTruckId}`, {
                method: "POST",
            });
            if (response.ok) {
                setIsAssignTruckOpen(false);
                setSelectedDriver(null);
                setSelectedTruckId("");
                fetchDrivers();
            }
        } catch (error) {
            console.error("Error assigning truck:", error);
        }
    };

    const filteredDrivers = drivers.filter((driver) => {
        const matchesSearch = driver.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            driver.phone.includes(searchQuery);
        const matchesStatus = statusFilter === "All" || driver.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    const getStatusColor = (status: string) => {
        switch (status) {
            case "AVAILABLE": return "bg-green-100 text-green-800";
            case "ON_ROUTE": return "bg-blue-100 text-blue-800";
            case "OFF_DUTY": return "bg-gray-100 text-gray-800";
            default: return "bg-gray-100 text-gray-800";
        }
    };

    return (
        <div className="p-8 space-y-8 bg-gray-50 min-h-screen font-sans">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-gray-900">Driver Management</h1>
                    <p className="text-gray-500 mt-1">View, add, and manage all company drivers.</p>
                </div>
                <Dialog open={isAddDriverOpen} onOpenChange={setIsAddDriverOpen}>
                    <DialogTrigger asChild>
                        <Button className="bg-blue-600 hover:bg-blue-700 text-white" onClick={openAddModal}>
                            <Plus className="mr-2 h-4 w-4" /> Add New Driver
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>{isEditing ? "Edit Driver" : "Add New Driver"}</DialogTitle>
                            <DialogDescription>{isEditing ? "Update driver details." : "Enter the details of the new driver."}</DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="name" className="text-right">Name</Label>
                                <Input
                                    id="name"
                                    value={driverForm.name}
                                    onChange={(e) => setDriverForm({ ...driverForm, name: e.target.value })}
                                    className="col-span-3"
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="phone" className="text-right">Phone</Label>
                                <Input
                                    id="phone"
                                    value={driverForm.phone}
                                    onChange={(e) => setDriverForm({ ...driverForm, phone: e.target.value })}
                                    className="col-span-3"
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button onClick={handleSaveDriver}>{isEditing ? "Update Driver" : "Save Driver"}</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 space-y-4">
                <div className="flex gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-500" />
                        <Input
                            placeholder="Search by driver name, phone..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-8"
                        />
                    </div>
                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Status: All" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="All">Status: All</SelectItem>
                            <SelectItem value="AVAILABLE">Available</SelectItem>
                            <SelectItem value="ON_ROUTE">On Route</SelectItem>
                            <SelectItem value="OFF_DUTY">Off Duty</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div className="rounded-md border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-[50px]"><Checkbox /></TableHead>
                                <TableHead>DRIVER NAME</TableHead>
                                <TableHead>CONTACT PHONE</TableHead>
                                <TableHead>STATUS</TableHead>
                                <TableHead>ASSIGNED TRUCK</TableHead>
                                <TableHead className="text-right">ACTIONS</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loading ? (
                                <TableRow>
                                    <TableCell colSpan={6} className="text-center py-8">Loading drivers...</TableCell>
                                </TableRow>
                            ) : filteredDrivers.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={6} className="text-center py-8">No drivers found.</TableCell>
                                </TableRow>
                            ) : (
                                filteredDrivers.map((driver) => (
                                    <TableRow key={driver.id}>
                                        <TableCell><Checkbox /></TableCell>
                                        <TableCell className="font-medium">{driver.name}</TableCell>
                                        <TableCell>{driver.phone}</TableCell>
                                        <TableCell>
                                            <Badge variant="secondary" className={getStatusColor(driver.status)}>
                                                {driver.status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            {driver.assigned_truck_plate ? (
                                                <div className="flex flex-col">
                                                    <span className="font-medium">{driver.assigned_truck_plate}</span>
                                                    {/* <span className="text-xs text-gray-500">TRK-101</span> */}
                                                </div>
                                            ) : (
                                                <span className="text-gray-400 italic">Unassigned</span>
                                            )}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" className="h-8 w-8 p-0">
                                                        <MoreVertical className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem onClick={() => {
                                                        setSelectedDriver(driver);
                                                        setIsAssignTruckOpen(true);
                                                    }}>
                                                        <Truck className="mr-2 h-4 w-4" /> Assign Truck
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem onClick={() => openEditModal(driver)}>
                                                        <Pencil className="mr-2 h-4 w-4" /> Edit Driver
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem className="text-red-600" onClick={() => handleDeleteClick(driver.id)}>
                                                        Delete Driver
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </div>
            </div>

            {/* Assign Truck Modal */}
            <Dialog open={isAssignTruckOpen} onOpenChange={setIsAssignTruckOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Assign Truck</DialogTitle>
                        <DialogDescription>
                            Assign a truck to {selectedDriver?.name}.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="py-4">
                        <Label htmlFor="truck">Select Truck</Label>
                        <Select value={selectedTruckId} onValueChange={setSelectedTruckId}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select a truck..." />
                            </SelectTrigger>
                            <SelectContent>
                                {trucks.map((truck) => (
                                    <SelectItem key={truck.id} value={truck.id}>
                                        {truck.plate_number} ({truck.status})
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    <DialogFooter>
                        <Button onClick={handleAssignTruck}>Assign Truck</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={!!driverToDelete} onOpenChange={(open) => !open && setDriverToDelete(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This action cannot be undone. This will permanently delete the driver from the system.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={handleConfirmDelete} className="bg-red-600 hover:bg-red-700">
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
