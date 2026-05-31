import { cn } from "@/lib/utils";

interface StepIndicatorProps {
  totalSteps: number;
  currentStep: number;
}

const StepIndicator = ({ totalSteps, currentStep }: StepIndicatorProps) => {
  return (
    <div className="flex items-center justify-center gap-2 py-6">
      {Array.from({ length: totalSteps }, (_, i) => (
        <div
          key={i}
          className={cn(
            "h-3 w-3 rounded-full transition-colors",
            i < currentStep
              ? "bg-foreground"
              : i === currentStep
              ? "bg-muted-foreground"
              : "bg-border"
          )}
        />
      ))}
    </div>
  );
};

export default StepIndicator;
