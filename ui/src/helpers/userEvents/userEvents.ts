import { debounce, uniqueId } from "lodash";
import simulationState from "../utils/simulationState";
import { UserEventData } from "./userEvents.interface";
import { UserEventType } from "./userEvents.enums";
import api from "@/services/api";

const sessionID = uniqueId(Date.now().toString());

export function getBaseEvent(event_type: UserEventType): UserEventData {
    return {
        user_id: simulationState.getUserName() as string,
        session_id: sessionID,
        event_type: event_type,
        timestamp: Date.now(),
        world_id: simulationState.getWorldId() as string,
        simulation_id: simulationState.getSimulationID() as string
    }
}

export function sendLoginEvent() {
    const event = getBaseEvent(UserEventType.LOGIN)

    api.sendUserEvent(event)
}

export function sendLogoutEvent() {
    const event = getBaseEvent(UserEventType.LOGOUT)

    api.sendUserEvent(event)
}

export function sendClickEvent(clickData: Partial<UserEventData>) {
    let event = getBaseEvent(UserEventType.CLICK)

    event = {...event, ...clickData}
    api.sendUserEvent(event)
}

export function sendClickComponentEvent(component: string){
    const event = getBaseEvent(UserEventType.COMPONENT_SELECT)
    event.component_id = component

    api.sendUserEvent(event)
}

export function sendComponentDragEvent(nodeID:string, oldXY: string, newXY: string) {
    const event = getBaseEvent(UserEventType.COMPONENT_DRAG)
    event.component_id = nodeID
    event.parameter_name = 'location'
    event.old_value = oldXY
    event.new_value = newXY

    api.sendUserEvent(event)
}

export const sendComponentDragEventDebounced = debounce(sendComponentDragEvent, 2000)

export function sendComponentConnectedEvent(from: string, to: string) {
    const event = getBaseEvent(UserEventType.COMPONENT_CONNECT)
    event.connection_from = from
    event.connection_to = to

    api.sendUserEvent(event)
}

export function sendComponentDisconnectedEvent(from: string, to: string) {
    const event = getBaseEvent(UserEventType.COMPONENT_DISCONNECT)
    event.connection_from = from
    event.connection_to = to
    api.sendUserEvent(event)
}

export function sendAIAgentMessageSentEvent(message: string, conversation_id: string) {
    const event = getBaseEvent(UserEventType.AI_AGENT_MESSAGE)
    event.agent_message = message
    event.conversation_id = conversation_id

    api.sendUserEvent(event)
}

export function sendAiAgentResponseReceivedEvent(response: string, conversation_id: string) {
    const event = getBaseEvent(UserEventType.AI_AGENT_RESPONSE)
    event.agent_response = response
    event.conversation_id = conversation_id

    api.sendUserEvent(event)
}


export function sendParameterChangedEvent(parameterName: string, oldValue: string, newValue: any) {
    const event = getBaseEvent(UserEventType.PARAMETER_CHANGE)
    event.parameter_name = parameterName
    event.old_value = oldValue
    event.new_value = newValue

    api.sendUserEvent(event)
}