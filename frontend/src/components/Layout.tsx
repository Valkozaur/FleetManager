import { LayoutDashboard, List, Truck } from "lucide-react";
import { Link, useLocation, Outlet } from "react-router-dom";

export function Layout() {
    const location = useLocation();

    const navItems = [
        { name: "Dashboard", href: "/", icon: LayoutDashboard },
        { name: "Orders", href: "/orders", icon: List },
        { name: "Fleet", href: "/fleet", icon: Truck },
    ];

    return (
        <div className="flex min-h-screen bg-gray-50">
            {/* Sidebar */}
            <aside className="w-64 bg-white border-r border-gray-200 hidden md:block">
                <div className="p-6">
                    <div className="flex items-center gap-2 mb-8">
                        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                            <Truck className="w-4 h-4 text-gray-600" />
                        </div>
                        <div>
                            <h1 className="font-bold text-gray-900">TruckLink</h1>
                            <p className="text-xs text-gray-500">Logistics</p>
                        </div>
                    </div>

                    <nav className="space-y-1">
                        {navItems.map((item) => {
                            const isActive = location.pathname === item.href;
                            return (
                                <Link
                                    key={item.name}
                                    to={item.href}
                                    className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive
                                        ? "bg-gray-100 text-gray-900"
                                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                                        }`}
                                >
                                    <item.icon className={`w-5 h-5 ${isActive ? "text-gray-900" : "text-gray-400"}`} />
                                    {item.name}
                                </Link>
                            );
                        })}
                    </nav>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto">
                <div className="p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
