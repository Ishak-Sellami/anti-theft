import React from 'react';
import { Battery, BatteryCharging, BatteryLow, BatteryWarning } from 'lucide-react';
import { clsx } from 'clsx';

interface BatteryIndicatorProps {
  level?: number;
  isCharging?: boolean;
  className?: string;
}

export const BatteryIndicator: React.FC<BatteryIndicatorProps> = ({
  level,
  isCharging = false,
  className,
}) => {
  if (level === undefined || level === null) {
    return <span className="text-xs text-slate-500 font-mono">--%</span>;
  }

  const getIcon = () => {
    if (isCharging) return <BatteryCharging size={16} className="text-emerald-400" />;
    if (level <= 10) return <BatteryWarning size={16} className="text-red-400 animate-pulse" />;
    if (level <= 20) return <BatteryLow size={16} className="text-amber-400" />;
    return <Battery size={16} className="text-emerald-400" />;
  };

  const getColor = () => {
    if (isCharging) return 'text-emerald-400';
    if (level <= 10) return 'text-red-400 font-bold';
    if (level <= 20) return 'text-amber-400';
    return 'text-slate-300';
  };

  return (
    <div className={clsx('inline-flex items-center gap-1.5 font-mono text-xs', className)}>
      {getIcon()}
      <span className={getColor()}>{level}%</span>
      {isCharging && <span className="text-[10px] text-emerald-500 font-semibold">(AC)</span>}
    </div>
  );
};
