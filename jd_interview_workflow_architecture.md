# JD Interview Workflow - Architecture Documentation

## Overview

The JD Interview Workflow is a voice-based AI interview system built on LiveKit that refines auto-generated job description briefs through conversational interviews with recruiters.

---

## 1. High-Level System Architecture

```mermaid
flowchart TB
    subgraph External["External Systems"]
        LK[LiveKit Server]
        OAI[OpenAI API]
        DG[Deepgram API]
    end

    subgraph Entry["Entry Point"]
        WF[workflow.py<br/>Main Entrypoint]
    end

    subgraph Session["Agent Session"]
        AS[AgentSession<br/>STT + LLM + TTS + VAD]
    end

    subgraph Core["Core Components"]
        ORCH[BriefInterviewOrchestrator<br/>Root Agent]
        SC[SharedContext<br/>State Management]
    end

    subgraph Agents["Section Agents"]
        INTRO[IntroAgent]
        COMP[CompanyAgent]
        ROLE[RoleAgent]
        SKILLS[SkillsAgent]
        CAND[CandidateAgent]
        LOG[LogisticsAgent]
        CLOSE[ClosingAgent]
    end

    subgraph Services["Services Layer"]
        BP[BriefParser]
        RC[RoleClassifier]
        QG[QuestionGenerator]
        OG[OutputGenerator]
    end

    subgraph Models["Data Models"]
        PB[ParsedBrief]
        RT[RoleType]
        RBO[RefinedBriefOutput]
    end

    WF --> AS
    AS --> ORCH
    ORCH --> SC
    ORCH --> INTRO

    INTRO --> COMP --> ROLE --> SKILLS --> CAND --> LOG --> CLOSE

    ORCH --> BP
    ORCH --> RC
    ORCH --> QG
    CLOSE --> OG

    BP --> PB
    RC --> RT
    OG --> RBO

    AS <--> LK
    AS <--> OAI
    AS <--> DG

    style ORCH fill:#f9f,stroke:#333,stroke-width:2px
    style SC fill:#bbf,stroke:#333,stroke-width:2px
```

---

## 2. Agent Flow & State Transitions

```mermaid
stateDiagram-v2
    [*] --> Orchestrator: Session Start

    Orchestrator --> IntroAgent: start_interview()

    IntroAgent --> CompanyAgent: complete_intro_section()
    CompanyAgent --> RoleAgent: complete_company_section()
    RoleAgent --> SkillsAgent: complete_role_section()
    SkillsAgent --> CandidateAgent: complete_skills_section()
    CandidateAgent --> LogisticsAgent: complete_candidate_section()
    LogisticsAgent --> ClosingAgent: complete_logistics_section()

    ClosingAgent --> [*]: end_interview()

    note right of IntroAgent
        Each agent can:
        - jump_to_section()
        - return_to_previous_section()
    end note

    state "Navigation Stack" as nav {
        IntroAgent --> CompanyAgent: push to stack
        CompanyAgent --> IntroAgent: pop from stack
    }
```

---

## 3. Detailed Component Architecture

```mermaid
flowchart LR
    subgraph Workflow["workflow.py"]
        EP[entrypoint]
        EP --> |"Configure"| STT_CFG[STT Config<br/>Deepgram Nova-3<br/>+ Whisper Fallback]
        EP --> |"Configure"| LLM_CFG[LLM Config<br/>GPT-4o]
        EP --> |"Configure"| TTS_CFG[TTS Config<br/>GPT-4o-mini-tts<br/>+ Deepgram Fallback]
        EP --> |"Configure"| VAD_CFG[VAD Config<br/>Silero VAD]
    end

    subgraph Orchestrator["BriefInterviewOrchestrator"]
        INIT[Initialize]
        INIT --> PARSE[Parse Brief]
        INIT --> CLASSIFY[Classify Role]
        INIT --> GENQ[Generate Questions]
        INIT --> PREFILL[Pre-fill Data]

        PARSE --> BP_SVC[BriefParser]
        CLASSIFY --> RC_SVC[RoleClassifier]
        GENQ --> QG_SVC[QuestionGenerator]
    end

    subgraph SharedContext["SharedContext"]
        LK_RES[LiveKit Resources<br/>lkapi, job_ctx, room_name]
        BRIEF_DATA[Brief Data<br/>original_brief, role_type]
        Q_TRACK[Question Tracking<br/>questions_to_ask, questions_asked]
        REFINE[Refinements<br/>company, mission, role, skills...]
        GATHER[Gathered Data<br/>job_title, skills, logistics...]
        NAV[Navigation State<br/>agent_stack, current_agent]
    end

    EP --> Orchestrator
    Orchestrator --> SharedContext
```

---

## 4. Agent Inheritance & Tools

```mermaid
classDiagram
    class Agent {
        <<LiveKit>>
        +instructions: str
        +chat_ctx: ChatContext
        +session: AgentSession
        +on_enter()
    }

    class BaseBriefInterviewAgent {
        +orchestrator: BriefInterviewOrchestrator
        +shared: SharedContext
        +_get_agent(section: str)
        +jump_to_section(section, mode)
        +return_to_previous_section()
        +get_brief_section(section)
        +get_section_info(section)
        +add_refinement(section, type, content)
        +update_gathered_data(field, value)
        +add_to_list(list_name, items)
        +get_context_summary()
        +check_navigation_stack()
    }

    class IntroAgent {
        +on_enter()
        +complete_intro_section()
    }

    class CompanyAgent {
        +on_enter()
        +complete_company_section()
    }

    class RoleAgent {
        +on_enter()
        +complete_role_section()
    }

    class SkillsAgent {
        +on_enter()
        +prioritize_skill(skill, priority)
        +complete_skills_section()
    }

    class CandidateAgent {
        +on_enter()
        +complete_candidate_section()
    }

    class LogisticsAgent {
        +on_enter()
        +complete_logistics_section()
    }

    class ClosingAgent {
        +on_enter()
        +end_interview()
    }

    Agent <|-- BaseBriefInterviewAgent
    BaseBriefInterviewAgent <|-- IntroAgent
    BaseBriefInterviewAgent <|-- CompanyAgent
    BaseBriefInterviewAgent <|-- RoleAgent
    BaseBriefInterviewAgent <|-- SkillsAgent
    BaseBriefInterviewAgent <|-- CandidateAgent
    BaseBriefInterviewAgent <|-- LogisticsAgent
    BaseBriefInterviewAgent <|-- ClosingAgent
```

---

## 5. Data Models

```mermaid
classDiagram
    class ParsedBrief {
        +raw_markdown: str
        +job_title: str
        +company_name: str
        +company_overview: ParsedSection
        +mission: ParsedSection
        +who_role_is_for: ParsedSection
        +what_youll_do: ParsedSection
        +key_technical_skills: ParsedSection
        +nice_to_haves: ParsedSection
        +candidate_profile: ParsedSection
        +logistics: ParsedSection
        +red_flags: ParsedSection
        +gaps: List~GapItem~
    }

    class ParsedSection {
        +header: str
        +content: str
        +bullet_points: List~str~
        +completeness_score: float
    }

    class GapItem {
        +section: str
        +description: str
        +priority: int
        +suggested_question: str
    }

    class RoleType {
        <<enumeration>>
        TECHNICAL
        SALES
        MARKETING
        FINANCE
        HEALTHCARE
        OPERATIONS
        HR
        EXECUTIVE
        GENERAL
    }

    class RefinedBriefOutput {
        +generated_at: str
        +role_type: str
        +interview_duration_seconds: int
        +confidence_score: float
        +job_details: JobDetails
        +requirements: Requirements
        +candidate_profile: CandidateProfile
        +logistics: Logistics
        +refinements: List~Refinement~
        +to_dict()
    }

    class JobDetails {
        +job_title: str
        +company_name: str
        +company_overview: str
        +mission: str
    }

    class Requirements {
        +must_have_skills: List~SkillItem~
        +nice_to_have_skills: List~SkillItem~
        +experience_years: Dict
        +education: Dict
        +certifications: Dict
    }

    class Refinement {
        +section: str
        +refinement_type: str
        +content: str
        +timestamp: str
    }

    ParsedBrief "1" --> "*" ParsedSection
    ParsedBrief "1" --> "*" GapItem
    RefinedBriefOutput "1" --> "1" JobDetails
    RefinedBriefOutput "1" --> "1" Requirements
    RefinedBriefOutput "1" --> "*" Refinement
```

---

## 6. Services Architecture

```mermaid
flowchart TB
    subgraph BriefParser["BriefParser Service"]
        BP_PARSE[parse<br/>markdown → ParsedBrief]
        BP_TITLE[_extract_job_title]
        BP_COMPANY[_extract_company_name]
        BP_SECTION[_extract_section]
        BP_BULLETS[_extract_bullets]
        BP_GAPS[identify_gaps]
        BP_SKILLS[extract_skills_from_section]

        BP_PARSE --> BP_TITLE
        BP_PARSE --> BP_COMPANY
        BP_PARSE --> BP_SECTION
        BP_SECTION --> BP_BULLETS
        BP_PARSE --> BP_GAPS
    end

    subgraph RoleClassifier["RoleClassifier Service"]
        RC_CLASS[classify<br/>ParsedBrief → RoleType]
        RC_TECH[_check_technical_role]
        RC_SALES[_check_sales_role]
        RC_OTHER[_check_other_roles...]

        RC_CLASS --> RC_TECH
        RC_CLASS --> RC_SALES
        RC_CLASS --> RC_OTHER
    end

    subgraph QuestionGenerator["QuestionGenerator Service"]
        QG_GEN[generate_questions]
        QG_GAPS[_questions_from_gaps]
        QG_ROLE[_role_specific_questions]
        QG_PRIO[_prioritize_questions]

        QG_GEN --> QG_GAPS
        QG_GEN --> QG_ROLE
        QG_GEN --> QG_PRIO
    end

    subgraph OutputGenerator["OutputGenerator Service"]
        OG_BRIEF[generate_enhanced_brief]
        OG_JSON[generate_structured_json]
        OG_SUM[generate_summary]
    end

    INPUT[Raw Markdown Brief] --> BriefParser
    BriefParser --> |ParsedBrief| RoleClassifier
    BriefParser --> |ParsedBrief + Gaps| QuestionGenerator
    RoleClassifier --> |RoleType| QuestionGenerator

    INTERVIEW[Interview Complete] --> OutputGenerator
    OutputGenerator --> |Enhanced Brief| OUTPUT1[Markdown Output]
    OutputGenerator --> |Structured JSON| OUTPUT2[JSON Output]
```

---

## 7. Interview Flow Sequence

```mermaid
sequenceDiagram
    participant R as Recruiter
    participant LK as LiveKit
    participant WF as Workflow
    participant O as Orchestrator
    participant SC as SharedContext
    participant A as Section Agents
    participant S as Services

    R->>LK: Join Room
    LK->>WF: Job Context + Metadata
    WF->>O: Create Orchestrator

    O->>S: BriefParser.parse(markdown)
    S-->>O: ParsedBrief
    O->>S: RoleClassifier.classify()
    S-->>O: RoleType
    O->>S: QuestionGenerator.generate()
    S-->>O: Questions[]

    O->>SC: Initialize SharedContext
    O->>R: "Hi! Ready to start?"

    R->>O: "Yes"
    O->>A: start_interview() → IntroAgent

    loop For Each Section
        A->>R: Ask Questions
        R->>A: Provide Answers
        A->>SC: add_refinement()
        A->>SC: update_gathered_data()
        A->>A: complete_section() → Next Agent
    end

    A->>S: OutputGenerator.generate()
    S-->>A: Enhanced Brief + JSON
    A->>LK: Send Data (interview_complete)
    A->>R: "Your brief is ready!"
    A->>LK: Delete Room
```

---

## 8. Navigation & Jump System

```mermaid
flowchart TB
    subgraph Normal["Normal Flow"]
        I[Intro] --> C[Company] --> R[Role] --> S[Skills] --> CA[Candidate] --> L[Logistics] --> CL[Closing]
    end

    subgraph Jump["Jump Navigation"]
        direction TB
        CURR[Current Agent<br/>e.g., Skills]
        STACK[Agent Stack<br/>push current]
        TARGET[Target Agent<br/>e.g., Company]
        MODE[Jump Mode<br/>review/modify/gather]

        CURR --> |jump_to_section| STACK
        STACK --> TARGET
        TARGET --> MODE
    end

    subgraph Return["Return Navigation"]
        RET_TARGET[Return to Agent]
        RET_STACK[Pop from Stack]
        RET_FLAG[is_returning = true]

        RET_STACK --> RET_TARGET
        RET_TARGET --> RET_FLAG
    end

    Jump --> |return_to_previous_section| Return
```

---

## 9. Folder Structure

```
agents/jd_interview_workflow/
├── __init__.py
├── workflow.py              # Main entry point, AgentSession config
├── orchestrator.py          # BriefInterviewOrchestrator root agent
├── shared_context.py        # SharedContext state management
│
├── agents/                  # Section-specific agents
│   ├── __init__.py
│   ├── base_agent.py        # BaseBriefInterviewAgent with common tools
│   ├── intro_agent.py       # Introduction & greeting
│   ├── company_agent.py     # Company & mission clarification
│   ├── role_agent.py        # Role responsibilities
│   ├── skills_agent.py      # Technical skills prioritization
│   ├── candidate_agent.py   # Ideal candidate profile
│   ├── logistics_agent.py   # Location, salary, timeline
│   └── closing_agent.py     # Summary & output generation
│
├── models/                  # Data models & schemas
│   ├── __init__.py
│   ├── brief_schema.py      # ParsedBrief, ParsedSection, GapItem
│   ├── role_types.py        # RoleType enum
│   └── output_schema.py     # RefinedBriefOutput, Refinement, etc.
│
├── prompts/                 # Agent prompts & instructions
│   ├── __init__.py
│   ├── about_interviewer.py # Interviewer persona
│   ├── base_instructions.py # Common instructions
│   ├── intro_prompt.py
│   ├── company_prompt.py
│   ├── role_prompt.py
│   ├── skills_prompt.py
│   ├── candidate_prompt.py
│   ├── logistics_prompt.py
│   └── closing_prompt.py
│
├── services/                # Business logic services
│   ├── __init__.py
│   ├── brief_parser.py      # Parse markdown → ParsedBrief
│   ├── role_classifier.py   # Classify role type
│   ├── question_generator.py# Generate interview questions
│   └── output_generator.py  # Generate final outputs
│
└── test_runner.py           # Testing utilities
```

---

## 10. Key Design Patterns

### Pattern 1: Agent Handoff
Each section agent returns the next agent from its completion tool, enabling seamless transitions.

### Pattern 2: Shared Context
All agents share a single `SharedContext` instance for state management, avoiding prop-drilling.

### Pattern 3: Navigation Stack
Agents can jump to any section and return using a stack-based navigation system.

### Pattern 4: Tool-Based Actions
All agent actions (data updates, navigation, section completion) are exposed as `@function_tool()` for LLM control.

### Pattern 5: Service Layer
Business logic (parsing, classification, question generation, output generation) is decoupled into services.

---

## 11. Technology Stack

| Component | Technology |
|-----------|------------|
| Voice Framework | LiveKit Agents SDK |
| Speech-to-Text | Deepgram Nova-3 (primary), OpenAI Whisper (fallback) |
| LLM | OpenAI GPT-4o |
| Text-to-Speech | OpenAI GPT-4o-mini-tts (primary), Deepgram Aura (fallback) |
| Voice Activity Detection | Silero VAD |
| Noise Cancellation | LiveKit BVC |

---

## 12. Output Flow

```mermaid
flowchart LR
    subgraph Input
        BRIEF[Raw Markdown Brief]
        INTERVIEW[Interview Refinements]
    end

    subgraph Processing
        OG[OutputGenerator]
        MERGE[Merge Original + Refinements]
    end

    subgraph Output
        MD[Enhanced Markdown Brief]
        JSON[Structured JSON]
        SUM[Summary Stats]
    end

    subgraph Delivery
        LK_DATA[LiveKit Data Channel<br/>topic: interview-output]
        FRONTEND[Frontend Application]
    end

    BRIEF --> OG
    INTERVIEW --> OG
    OG --> MERGE
    MERGE --> MD
    MERGE --> JSON
    MERGE --> SUM

    MD --> LK_DATA
    JSON --> LK_DATA
    SUM --> LK_DATA
    LK_DATA --> FRONTEND
```
