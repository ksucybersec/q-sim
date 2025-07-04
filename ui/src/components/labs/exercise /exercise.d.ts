export interface ExerciseI {
    id: string
    title: string
    description: string
    difficulty: string
    estimatedTime: string
    category: string
    steps: string[]
    requirements: ExerciseRequirements
    tips: string[]
    coding?: CodingExercise
}

export interface ExerciseRequirements {
    nodes: SimulationNodeType[]
    connections: SimulationNodeType[][]
    simulation: boolean
    entanglement?: boolean
    messages?: number
}

export interface CodingExercise {
   enabled: boolean
   language: string
   scaffold: CodeScaffold
   aiPrompts: string[]
   validation: ValidationRules
}

export interface CodeScaffold {
   code: string
   sections: CodeFunctionSection[]
   imports: string[]
   classStructure: ClassStructure
}

export interface CodeFunctionSection {
   id: string
   name: string
   // startLine: number
   // endLine: number
   type: 'readonly' | 'editable' | 'todo' | 'comment'
   // collapsed?: boolean
   functionName: string
   description?: string
}

export interface ClassStructure {
   className: string
   readonlyMethods: string[]
   editableMethods: string[]
   systemMethods: string[] // Hidden from students
}

export interface ValidationRules {
   maxQubits: number
   allowedOperations: string[]
   blockedOperations: string[]
   timeLimit: number
}