import React from 'react';
import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  onClick,
  hoverable = false,
}) => {
  return (
    <div
      onClick={onClick}
      className={clsx(
        'bg-surface border border-slate-800 rounded-xl p-5 shadow-lg',
        hoverable && 'hover:border-slate-700 transition-all cursor-pointer hover:shadow-xl',
        className
      )}
    >
      {children}
    </div>
  );
};
