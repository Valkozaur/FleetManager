import { Badge } from "@/components/ui/badge";

interface StatusBadgeProps {
    status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
    let variant: "default" | "secondary" | "destructive" | "outline" = "default";
    let className = "";

    switch (status) {
        case "Pending":
            variant = "secondary";
            className = "bg-gray-200 text-gray-800 hover:bg-gray-300";
            break;
        case "Assigned":
            variant = "outline";
            className = "border-blue-500 text-blue-500";
            break;
        case "In Transit":
            variant = "default";
            className = "bg-yellow-100 text-yellow-800 hover:bg-yellow-200 border-yellow-200";
            break;
        case "Completed":
            variant = "default";
            className = "bg-green-100 text-green-800 hover:bg-green-200 border-green-200";
            break;
        case "Cancelled":
            variant = "destructive";
            break;
        default:
            variant = "default";
    }

    return (
        <Badge variant={variant} className={className}>
            {status}
        </Badge>
    );
}
