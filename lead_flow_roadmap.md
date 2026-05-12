# Product Roadmap: Manual vs AI-Optimized Lead Flow

```mermaid
flowchart LR
  %% =========================
  %% Manual Workflow
  %% =========================
  subgraph M[Current Manual Lead Flow]
    direction LR
    M1([Inbound Call]) --> M2([Voicemail])
    M2 --> M3([Manual Callback])
    M3 --> M4([Scheduling])
  end

  %% =========================
  %% AI-Optimized Workflow
  %% =========================
  subgraph A[AI-Optimized Workflow]
    direction LR
    A1([Inbound Call]) --> A2([AI Intercepts Call])
    A2 --> A3{Check [Software Name]\nAvailability}
    A3 --> A4([Send Calendar Invite])
    A4 --> A5([Send Text Confirmation])
    A5 --> A6([Auto-Sync Lead Data to CRM])
  end

  %% =========================
  %% Contrast Connectors
  %% =========================
  M1 -. comparison .-> A1
  M2 -. delay risk .-> A2
  M3 -. labor intensive .-> A3
  M4 -. manual handoff .-> A6

  %% =========================
  %% Styling
  %% =========================
  classDef manual fill:#F5F5F5,stroke:#9E9E9E,color:#333,stroke-width:1px;
  classDef ai fill:#EAF4FF,stroke:#1E88E5,color:#0D47A1,stroke-width:1px;

  class M1,M2,M3,M4 manual;
  class A1,A2,A3,A4,A5,A6 ai;
```
