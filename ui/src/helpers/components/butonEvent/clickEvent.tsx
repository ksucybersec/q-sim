import { sendClickEvent } from '@/helpers/userEvents/userEvents';
import { UserEventType } from '@/helpers/userEvents/userEvents.enums';
import React, { useState, useRef, useEffect, cloneElement } from 'react';

interface ClickEventButtonProps {
    children: React.ReactElement;
    eventType?: UserEventType
    elementType?: string;
    elementDescription?: string;
}

export const ClickEventButton: React.FC<ClickEventButtonProps> = ({ children, eventType, elementType, elementDescription }) => {
    const props = children.props as any;
    const handleClick = (e: React.MouseEvent) => {

        sendClickEvent({
            event_type: eventType || UserEventType.CLICK,
            element_type: elementType,
            element_description: elementDescription,
            click_coordinates: { x: e.nativeEvent.offsetX, y: e.nativeEvent.offsetY }
        })

        if (props.onClick) {
            return props.onClick(e);
        }
    };

    const clonedChild = cloneElement(children, {
        onClick: handleClick,
    } as any);

    return (
        <span>
            {clonedChild}
        </span>
    );
}