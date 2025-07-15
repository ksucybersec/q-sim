import React, { useState, useRef, useEffect } from 'react';

interface FloatableProps {
    children: React.ReactNode;
    defaultPosition?: { x: number; y: number };
    className?: string;
    style?: React.CSSProperties;
    resetTrigger?: number;
}

export const Floatable: React.FC<FloatableProps> = ({
    children,
    defaultPosition = { x: 20, y: 20 },
    className = '',
    style = {},
    resetTrigger = 0,
}) => {
    const [position, setPosition] = useState(defaultPosition);
    const [isDragging, setIsDragging] = useState(false);
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
    const elementRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (resetTrigger > 0) {
            setPosition(defaultPosition);
        }
    }, [resetTrigger, defaultPosition]);

    const handleMouseDown = (e: React.MouseEvent) => {
        if (!elementRef.current) return;

        setDragOffset({
            x: e.clientX - position.x,
            y: e.clientY - position.y
        });
        setIsDragging(true);
    };

    const handleMouseMove = (e: MouseEvent) => {
        if (!isDragging || !elementRef.current) return;

        const newX = e.clientX - dragOffset.x;
        const newY = e.clientY - dragOffset.y;

        // Get parent container bounds (prioritize parent over window)
        const parent = elementRef.current.offsetParent as HTMLElement;
        const parentRect = parent?.getBoundingClientRect();
        const elementWidth = elementRef.current.offsetWidth;
        const elementHeight = elementRef.current.offsetHeight;
        const elementRect = elementRef.current.getBoundingClientRect();

        const parentX = elementRect.left - parentRect.left + parent.scrollLeft;
        const parentY = elementRect.top - parentRect.top + parent.scrollTop;

        let maxX, maxY, minX, minY;

        if (parent && parentRect) {
            // Use parent bounds
            minX = -parentX;
            minY = -parentY;
            maxX = parent.clientWidth - elementWidth;
            maxY = parent.clientHeight - elementHeight;
        } else {
            // Fallback to window bounds
            minX = 0;
            minY = 0;
            maxX = window.innerWidth - elementWidth;
            maxY = window.innerHeight - elementHeight;
        }

        setPosition({
            x: Math.max(minX, Math.min(newX, maxX)),
            y: Math.max(minY, Math.min(newY, maxY))
        });
    };

    const handleMouseUp = () => {
        setIsDragging(false);
    };

    useEffect(() => {
        if (isDragging) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);

            return () => {
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
            };
        }
    }, [isDragging, dragOffset]);

    return (
        <div
            ref={elementRef}
            className={`absolute z-50 cursor-move select-none ${isDragging ? 'opacity-80' : 'opacity-100'
                } ${className}`}
            style={{
                left: position.x,
                top: position.y,
                ...style
            }}
            onMouseDown={handleMouseDown}
        >
            {children}
        </div>
    );
};