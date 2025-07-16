import { sendClickEvent } from '@/helpers/userEvents/userEvents';
import { UserEventType } from '@/helpers/userEvents/userEvents.enums';
import { UserEventData } from '@/helpers/userEvents/userEvents.interface';
import { merge } from 'lodash';
import React, { cloneElement } from 'react';

interface ClickEventButtonProps {
    children: React.ReactElement;
    eventType?: UserEventType
    elementType?: string;
    elementDescription?: string;
    extraInfo?: Partial<UserEventData>;
}

export const ClickEventButton: React.FC<ClickEventButtonProps> = ({ children, eventType, elementType, elementDescription, extraInfo }) => {
    const props = children.props as any;
    const handleClick = (e: React.MouseEvent) => {

        let eventData: Partial<UserEventData> = {
            event_type: eventType || UserEventType.CLICK,
            element_type: elementType,
            element_description: elementDescription,
            click_coordinates: { x: e.nativeEvent.offsetX, y: e.nativeEvent.offsetY }
        }

        if (extraInfo) {
            eventData = merge(eventData, extraInfo)
        }

        sendClickEvent(eventData)

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