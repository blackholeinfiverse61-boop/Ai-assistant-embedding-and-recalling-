# Database Schema Diagrams

This document provides visual representations of the database schema used in the AI Assistant system.

## Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ SUMMARIES : creates
    USERS ||--o{ TASKS : requests
    USERS ||--o{ RESPONSES : receives
    USERS ||--o{ FEEDBACK : provides
    
    SUMMARIES ||--o{ TASKS : generates
    TASKS ||--o{ RESPONSES : triggers
    SUMMARIES ||--o{ FEEDBACK : receives
    TASKS ||--o{ FEEDBACK : receives
    RESPONSES ||--o{ FEEDBACK : receives
    
    SUMMARIES ||--o{ EMBEDDINGS : has
    TASKS ||--o{ EMBEDDINGS : has
    RESPONSES ||--o{ EMBEDDINGS : has
    
    METRICS }|--|| ENDPOINTS : tracks
    
    USERS {
        string user_id PK
        string name
        string email
        string preferences
        datetime created_at
    }
    
    SUMMARIES {
        string summary_id PK
        string user_id FK
        string message_text
        string summary_text
        float confidence_score
        datetime timestamp
    }
    
    TASKS {
        string task_id PK
        string summary_id FK
        string user_id FK
        string task_text
        string priority
        float confidence_score
        datetime timestamp
    }
    
    RESPONSES {
        string response_id PK
        string task_id FK
        string user_id FK
        string response_text
        string tone
        string status
        float confidence_score
        datetime timestamp
    }
    
    FEEDBACK {
        int id PK
        string summary_id FK
        string task_id FK
        string response_id FK
        int score
        string comment
        datetime timestamp
    }
    
    EMBEDDINGS {
        int id PK
        string item_type
        string item_id
        string vector_blob
        datetime timestamp
    }
    
    METRICS {
        int id PK
        string endpoint
        int status_code
        float latency_ms
        datetime timestamp
    }
    
    ENDPOINTS {
        string endpoint PK
        string description
        string method
    }
```

## Pipeline Flow Diagram

```mermaid
graph TD
    A[User Message] --> B[Message Ingestion]
    B --> C[Summarization Engine]
    C --> D[Summary Storage]
    D --> E[Task Generation Engine]
    E --> F[Task Storage]
    F --> G[Response Generation Engine]
    G --> H[Response Storage]
    H --> I[User Interface]
    I --> J[User Feedback Collection]
    J --> K[Feedback Storage]
    
    D --> L[Embedding Service]
    F --> L
    H --> L
    
    L --> M[Similarity Search]
    M --> N[Context Retrieval]
    
    K --> O[RL Agent]
    O --> P[Behavior Adjustment]
    P --> C
    P --> E
    P --> G
    
    subgraph "Core Pipeline"
        B
        C
        D
        E
        F
        G
        H
        I
        J
        K
    end
    
    subgraph "Chandresh's EmbedCore & Recall"
        L
        M
        N
    end
    
    subgraph "Learning & Adaptation"
        O
        P
    end
    
    style A fill:#e1f5fe
    style I fill:#e8f5e8
    style J fill:#fff3e0
    style K fill:#ffebee
    style L fill:#f3e5f5
    style M fill:#f3e5f5
    style N fill:#f3e5f5
    style O fill:#ffe0b2
    style P fill:#ffe0b2
```

## API Endpoint Relationships

```mermaid
graph TD
    A[Pipeline API] --> B[Summarization Endpoint]
    A --> C[Task Processing Endpoint]
    A --> D[Feedback Endpoint]
    A --> E[Configuration Endpoint]
    A --> F[Metrics Endpoint]
    
    G[Chandresh API] --> H[Similarity Search Endpoint]
    G --> I[Embedding Storage Endpoint]
    G --> J[Embedding Stats Endpoint]
    G --> K[Reindex Endpoint]
    
    B --> L[Database]
    C --> L
    D --> L
    H --> L
    I --> L
    K --> L
    
    L --> M[Embeddings Table]
    L --> N[Summaries Table]
    L --> O[Tasks Table]
    L --> P[Responses Table]
    L --> Q[Feedback Table]
    L --> R[Metrics Table]
    
    subgraph "API Services"
        A
        G
    end
    
    subgraph "Database Tables"
        L
        M
        N
        O
        P
        Q
        R
    end
    
    style A fill:#bbdefb
    style G fill:#bbdefb
    style L fill:#c8e6c9
```

## Data Flow Through System

```mermaid
sequenceDiagram
    participant U as User
    participant API as Pipeline API
    participant DB as Database
    participant EMB as Embedding Service
    participant RL as RL Agent
    
    U->>API: Submit message
    API->>API: Summarize message
    API->>DB: Store summary
    DB-->>API: Confirmation
    API->>EMB: Store summary embedding
    EMB-->>API: Confirmation
    
    API->>API: Generate tasks
    API->>DB: Store tasks
    DB-->>API: Confirmation
    API->>EMB: Store task embedding
    EMB-->>API: Confirmation
    
    API->>API: Generate response
    API->>DB: Store response
    DB-->>API: Confirmation
    API->>EMB: Store response embedding
    EMB-->>API: Confirmation
    
    U->>API: Provide feedback
    API->>DB: Store feedback
    DB-->>API: Confirmation
    API->>RL: Send feedback data
    RL->>RL: Adjust models
    RL-->>API: Updated parameters
    API->>API: Apply adjustments
```

## Component Interaction Map

```mermaid
graph LR
    A[User Interface] --> B[API Gateway]
    B --> C[Summarization Service]
    B --> D[Task Engine]
    B --> E[Response Generator]
    B --> F[Feedback Collector]
    
    C --> G[Database]
    D --> G
    E --> G
    F --> G
    
    C --> H[Embedding Service]
    D --> H
    E --> H
    
    H --> G
    
    F --> I[RL Learning Agent]
    I --> J[Model Updates]
    J --> C
    J --> D
    J --> E
    
    subgraph "Frontend"
        A
    end
    
    subgraph "API Layer"
        B
    end
    
    subgraph "Core Services"
        C
        D
        E
        F
    end
    
    subgraph "Storage & Search"
        G
        H
    end
    
    subgraph "Learning & Adaptation"
        I
        J
    end
    
    style A fill:#e3f2fd
    style B fill:#bbdefb
    style C fill:#e8f5e8
    style D fill:#e8f5e8
    style E fill:#e8f5e8
    style F fill:#fff3e0
    style G fill:#c8e6c9
    style H fill:#f3e5f5
    style I fill:#ffe0b2
    style J fill:#ffe0b2
```