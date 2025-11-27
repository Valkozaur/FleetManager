
import { useEffect } from "react";
import { useForm, type SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import type { Truck } from "../pages/FleetPage";

const formSchema = z.object({
    plate_number: z.string().min(1, "License plate is required").max(50),
    trailer_plate_number: z.string().min(1, "Trailer plate is required").max(50),
    capacity_weight: z.coerce.number().gt(0, "Capacity must be greater than 0"),
    status: z.enum(["AVAILABLE", "MAINTENANCE", "OUT_OF_SERVICE", "INACTIVE"]),
});

type FormValues = z.infer<typeof formSchema>;

interface TruckModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    truck: Truck | null;
}

export function TruckModal({ isOpen, onClose, onSuccess, truck }: TruckModalProps) {
    const form = useForm<FormValues>({
        resolver: zodResolver(formSchema) as any,
        defaultValues: {
            plate_number: "",
            trailer_plate_number: "",
            capacity_weight: 0,
            status: "AVAILABLE",
        },
    });

    useEffect(() => {
        if (truck) {
            form.reset({
                plate_number: truck.plate_number,
                trailer_plate_number: truck.trailer_plate_number || "",
                capacity_weight: truck.capacity_weight,
                status: truck.status,
            });
        } else {
            form.reset({
                plate_number: "",
                trailer_plate_number: "",
                capacity_weight: 0,
                status: "AVAILABLE",
            });
        }
    }, [truck, form, isOpen]);

    const onSubmit: SubmitHandler<FormValues> = async (values) => {
        try {
            const baseUrl = (import.meta.env.VITE_API_URL || "http://localhost:8000").trim().replace(/\/$/, "");
            const url = truck
                ? `${baseUrl}/trucks/${truck.id}`
                : `${baseUrl}/trucks/`;

            const method = truck ? "PUT" : "POST";

            const payload = {
                ...values,
            };

            const response = await fetch(url, {
                method,
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to save truck");
            }

            onSuccess();
            onClose();
        } catch (error) {
            console.error("Error saving truck:", error);
            // Ideally show error toast here
            alert(error instanceof Error ? error.message : "An error occurred");
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>{truck ? "Edit Truck" : "Add New Truck"}</DialogTitle>
                </DialogHeader>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit as any)} className="space-y-4">
                        <FormField
                            control={form.control as any}
                            name="plate_number"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>License Plate</FormLabel>
                                    <FormControl>
                                        <Input placeholder="e.g. US-789-XYZ" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control as any}
                            name="trailer_plate_number"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Trailer Plate</FormLabel>
                                    <FormControl>
                                        <Input placeholder="e.g. T-123-456" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control as any}
                            name="capacity_weight"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Capacity (kg)</FormLabel>
                                    <FormControl>
                                        <Input type="number" placeholder="20000" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control as any}
                            name="status"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Status</FormLabel>
                                    <Select onValueChange={field.onChange} defaultValue={field.value as string}>
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select status" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            <SelectItem value="AVAILABLE">Available</SelectItem>
                                            <SelectItem value="MAINTENANCE">Maintenance</SelectItem>
                                            <SelectItem value="OUT_OF_SERVICE">Out of Service</SelectItem>
                                            <SelectItem value="INACTIVE">Inactive</SelectItem>
                                        </SelectContent>
                                    </Select>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <DialogFooter>
                            <Button type="button" variant="outline" onClick={onClose}>
                                Cancel
                            </Button>
                            <Button type="submit">{truck ? "Save Changes" : "Create Truck"}</Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
