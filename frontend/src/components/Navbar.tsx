import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Minhas ingestões", href: "/ingestions" },
  { label: "Alertas", href: "/alerts" },
  { label: "Minha Conta", href: "/account" },
];

const Navbar = () => {
  const location = useLocation();

  return (
    <header className="border-b border-border">
      <div className="container flex h-14 items-center gap-8">
        <Link to="/" className="text-lg font-bold text-foreground">
          Satus
        </Link>
        <nav className="flex items-center gap-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              to={item.href}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground",
                location.pathname === item.href &&
                  "bg-secondary text-foreground font-medium"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
};

export default Navbar;
