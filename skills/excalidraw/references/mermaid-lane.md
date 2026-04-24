# Mermaid Lane

This file covers writing Mermaid that works well with Excalidraw's Mermaid-to-Excalidraw importer. Follow these rules and the import produces a clean, editable diagram. Ignore them and the import produces a mess that takes longer to fix than drawing from scratch.

---

## Workflow

1. The agent writes the Mermaid source to `<filename>.mmd` on disk.
2. The agent tells the user: open https://excalidraw.com, click the Menu icon (top-left hamburger) and choose "Generate...", then select "Mermaid to Excalidraw". On some UI versions the path is Tools - "Mermaid to Excalidraw". Paste the contents of `<filename>.mmd` into the text box and click "Insert".
3. The user saves the result via Menu - Save, or exports it as PNG/SVG from Menu - Export image.

Do not ask the user to edit the `.mmd` file manually unless they request it. The agent owns the Mermaid source; the user owns the resulting diagram.

---

## Per-type Mermaid style

### Flowchart

Use `flowchart TD` for top-to-bottom. Use `flowchart LR` for left-to-right pipelines. Never mix them.

DO:
```
flowchart TD
    A([Start]) --> B[Collect credentials]
    B --> C{Valid?}
    C -- yes --> D[Create session]
    C -- no --> E[Show error]
    D --> F([End])
    E --> B
```

DON'T:
```
flowchart TD
    A --> B
    B --> C
    C --> D
    B --> E
    E --> C
```
The don't example uses single-letter node IDs with no labels and no arrowhead text. The importer renders it, but the diagram conveys nothing. Every node needs a readable label.

### Sequence

Use `sequenceDiagram` with explicit participant declarations at the top. Number messages manually in the label text.

DO:
```
sequenceDiagram
    participant C as Client
    participant G as API Gateway
    participant A as Auth Service
    C->>G: 1. POST /login
    G->>A: 2. validate token
    A-->>G: 3. 200 OK
    G-->>C: 4. 200 + session
```

DON'T:
```
sequenceDiagram
    Client->Gateway: request
    Gateway->Auth: check
    Auth->Gateway: result
    Gateway->Client: response
```
The don't example uses `->` (open arrow, no arrowhead) and omits numbering and participant aliases. The importer maps `->` to an association line, which looks like a mistake.

### Class

Use `classDiagram` with explicit member visibility prefixes.

DO:
```
classDiagram
    class Order {
        +UUID id
        +OrderStatus status
        +addItem() void
        +total() Money
    }
    Order "1" --> "1..*" LineItem : contains
```

DON'T:
```
classDiagram
    class Order~T~ {
        List~T~ items
        process(T item) T
    }
```
Generic type parameters (`Order~T~`) may not render correctly in the importer. Drop generics and use plain type names.

### State

Use `stateDiagram-v2`. Always include `[*]` for initial and terminal states.

DO:
```
stateDiagram-v2
    [*] --> Pending
    Pending --> Processing : submit
    Processing --> Fulfilled : ship
    Processing --> Pending : retry
    Fulfilled --> [*]
```

DON'T:
```
stateDiagram-v2
    state Processing {
        Validating --> Picking
        Picking --> Packing
    }
```
Composite states with deeply nested sub-states often import as overlapping rectangles. Keep state diagrams flat unless the composite boundary is essential.

### ERD

Use `erDiagram` with Crow's foot cardinality notation.

DO:
```
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE_ITEM : contains
    PRODUCT ||--o{ LINE_ITEM : "included in"
```

DON'T:
```
erDiagram
    CUSTOMER {
        uuid id PK
        string email
        string name
    }
    CUSTOMER ||--o{ ORDER : places
```
Attribute blocks inside `erDiagram` curly braces are often misaligned or truncated by the importer. Define attributes separately in a note or keep them in the diagram description rather than inline.

### DFD (via flowchart)

Mermaid has no native DFD type. Model a DFD using `flowchart` with shape overrides:

- External entities: `A[Customer]` (rectangle)
- Processes: `B((1.0\nProcess Order))` (circle with number and name)
- Data stores: `C[/D1 Orders/]` (parallelogram as the closest approximation)

DO:
```
flowchart LR
    Customer[Customer] -->|Order request| P1((1.0\nProcess Order))
    P1 -->|Confirmed order| D1[/D1 Orders/]
    D2[/D2 Products/] -->|Product details| P1
    P1 -->|Order confirmation| Customer
```

DON'T:
```
flowchart LR
    Customer[Customer] -->|Order request| P1{1.0\nProcess Order}
    P1 -->|Valid?| P2{2.0\nCheck Stock}
    P2 -->|Yes| D1[/D1 Orders/]
    P2 -->|No| Customer
```
Decision diamonds (`{}`) are flowchart control-flow, not DFD processes. Using them as process nodes mixes the two notations. All process nodes in a DFD must be circles (`(())`); save diamonds for actual flowchart decisions.

---

## Label hygiene

Keep labels to 2-4 words. The importer wraps long text inside shapes based on fixed width estimates, and the wrapping breaks at unpredictable points.

If a label must be longer, use `\n` to force a break at a natural point: `POST /orders\nwith payload` rather than letting the importer wrap it.

Avoid special characters in labels: `<`, `>`, `&`, `"`. These can break the Mermaid parser or produce escaped HTML entities in the output. Use plain ASCII. If you need to label a type annotation, write `List of Items` rather than `List<Item>`.

---

## Supported features vs. not

The importer supports:

- flowchart (TD and LR)
- sequenceDiagram
- classDiagram (basic members and relationships)
- stateDiagram-v2
- erDiagram

Known gaps:

- Gantt diagrams are not supported. The importer silently fails or produces empty output.
- Custom styling directives (`classDef`, `style`, `linkStyle`) are parsed by Mermaid but ignored by the importer. Apply visual styling after import using Excalidraw's own properties panel.
- Complex class-diagram generics (`Class~T~`, `method(List~T~): T`) may not render or may render incorrectly. Replace with plain type names before importing.
- `%%` comments in Mermaid source sometimes cause parse failures in the importer. Remove comments from the `.mmd` file before pasting.

For the full list of supported Mermaid features in Excalidraw's integration layer, see: https://docs.excalidraw.com/docs/@excalidraw/excalidraw/integration
