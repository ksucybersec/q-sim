import { debounce, omit, uniqueId } from "lodash";
import simulationState from "../utils/simulationState";
import { UserEventData } from "./userEvents.interface";
import { UserEventType } from "./userEvents.enums";
import api from "@/services/api";
import { ChatRequestI } from "@/components/ai-agents/message.interface";

const sessionID = uniqueId(Date.now().toString());

export function getBaseEvent(event_type: UserEventType): UserEventData {
    return {
        user_id: simulationState.getUserName() as string,
        session_id: sessionID,
        event_type: event_type,
        timestamp: Date.now(),
        world_id: simulationState.getWorldId() as string,
        simulation_id: simulationState.getSimulationID() as string,
        page_url: location.toString()
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

export function sendAIAgentMessageSentEvent(chatRequest:ChatRequestI) {
    const event = getBaseEvent(UserEventType.AI_AGENT_MESSAGE)
    event.agent_message = chatRequest.user_query
    event.conversation_id = chatRequest.conversation_id
    event.agent_id  = chatRequest.agent_id
    event.task_id  = chatRequest.task_id

    event.ai_message_extra_data = omit(chatRequest, ['agent_id', 'task_id', 'conversation_id', 'user_query'])

    api.sendUserEvent(event)
}

export function sendAiAgentResponseReceivedEvent(response: Object, chatRequest:ChatRequestI) {
    const event = getBaseEvent(UserEventType.AI_AGENT_RESPONSE)
    event.agent_response = response
    event.agent_message = chatRequest.user_query
    event.conversation_id = chatRequest.conversation_id
    event.agent_id  = chatRequest.agent_id
    event.task_id  = chatRequest.task_id

    event.ai_message_extra_data = omit(chatRequest, ['agent_id', 'task_id', 'conversation_id', 'user_query'])

    api.sendUserEvent(event)
}


export function sendParameterChangedEvent(parameterName: string, oldValue: string, newValue: any) {
    const event = getBaseEvent(UserEventType.PARAMETER_CHANGE)
    event.parameter_name = parameterName
    event.old_value = oldValue
    event.new_value = newValue

    api.sendUserEvent(event)
}

export function sendLabCompletedEvent(labId: string) {
    const event = getBaseEvent(UserEventType.LAB_COMPLETE)
    event.lab_id = labId

    api.sendUserEvent(event)
}

export function sendLabProgressEvent(labId: string, stepCompleted: string | null, progress: number) {
    const event = getBaseEvent(UserEventType.LAB_STEP_COMPLETE)
    event.lab_id = labId
    event.lab_progress = progress
    event.lab_step = stepCompleted

    api.sendUserEvent(event)
}