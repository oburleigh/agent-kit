# Diagram Patterns

Each section covers one diagram type. Read only the section that applies to the diagram you are building. Each section is self-contained: it explains when to use the type, what the layout conventions are, and provides a concrete numbered coordinate example.

---

## Architecture

Use an architecture diagram when you need to show how components are deployed or communicate at a system level. Choose it when the audience needs to understand service boundaries, data flows, or ownership - not execution order (that is a sequence diagram) and not control flow (that is a flowchart).

### Picking a template

The `references/templates/` directory holds pre-laid-out `.excalidraw` files. Pick the one whose topology matches the system:

- `microservices-with-gateway.excalidraw`: use when there is a single entry point that fans out to independently deployed services.
- `layered-3-tier.excalidraw`: use for a classic presentation-logic-data stack, or any domain where tiers are owned by separate teams.
- `event-driven.excalidraw`: use when services communicate primarily through a shared event bus or message broker rather than direct calls.

If no template fits, build from scratch following the conventions below.

### Microservices with gateway

The API gateway sits in the horizontal centre of the canvas, roughly 200-300px from the top edge. Services fan out horizontally below it at equal horizontal spacing (100px between adjacent service boxes). Datastores sit directly below their owning service, 100px of vertical gap between the service box's bottom edge and the datastore's top edge.

Arrows from the gateway to services are solid with arrowheads (primary flow). Arrows from services to their datastores are also solid. Return paths are dashed.

Example layout for three services (gateway at x=400, y=100):
1. Gateway box: x=350, y=100, width=200, height=60
2. Service A: x=100, y=300, width=160, height=60
3. Service B: x=350, y=300, width=160, height=60
4. Service C: x=600, y=300, width=160, height=60
5. Datastore A: x=100, y=450, width=160, height=60
6. Datastore B: x=350, y=450, width=160, height=60
7. Datastore C: x=600, y=450, width=160, height=60

### Layered 3-tier

Stack tiers vertically. Presentation at the top, logic in the middle, data at the bottom. Each tier gets a frame (transparent fill, dashed border) that spans the full width of its content. Use consistent semantic colour per tier: green (#2f9e44 / #b2f2bb) for presentation, blue (#1971c2 / #a5d8ff) for logic, purple (#6741d9 / #d0bfff) for data. Arrows always point downward for requests and upward for responses; no arrows should skip a tier.

### Event-driven

The event bus (or message broker) occupies the horizontal centre of the diagram. Event producers sit on the left side, 200px from the bus. Event consumers sit on the right side, 200px from the bus. Datastores belonging to each consumer sit behind the consumer (further right), 100px gap. Arrows from producers to the bus are solid; arrows from the bus to consumers are dashed (asynchronous delivery). Datastores connect to their consumer with a solid arrow.

### Grouping with frames

Use Excalidraw's frame element to show swimlanes, bounded contexts, or deployment boundaries. The frame gets a transparent fill and a dashed stroke at 2px width. The frame label sits in the top-left corner of the frame at 16px. Do not fill frames with a solid colour - it washes out the semantic colours of the elements inside.

---

## Sequence

Use a sequence diagram when you need to show the temporal order of messages between participants. It answers "what calls what, in what order?" Architecture diagrams show structure; sequence diagrams show behaviour.

### Layout conventions

Participant boxes sit in a horizontal row at the top of the canvas. The first participant is at x=100. Each subsequent participant is 200px further right. For a three-participant diagram the positions are x=100, x=300, x=500. Participant box height is 50px; width adjusts to the label but starts at 120px.

Dashed lifelines descend from the bottom centre of each participant box. Set the lifeline stroke to #868e96 (grey), strokeStyle dashed, strokeWidth 1. Lifelines extend to 50px below the last message in the diagram.

Activation rectangles (thin boxes on the lifeline showing when a component is actively processing) are 10-14px wide, centred on the lifeline, with a white fill and a 1px solid border in the participant's colour. They start at the message that initiates the operation and end at the return message.

### Message conventions

Synchronous call: solid arrow, standard arrowhead, label above the arrow line.
Asynchronous message: dashed arrow, standard arrowhead, label above the arrow line.
Return message: dashed arrow, grey stroke (#868e96), arrowhead pointing back to the caller, label is the return value or status code.

Messages are numbered sequentially from 1 at the top. The number sits to the left of the label text, separated by a period and a space: "1. POST /orders". Number in the label text, not as a separate element.

Messages flow left to right for requests. Returns flow right to left. Never show a request flowing right-to-left - swap the caller and callee instead.

### Fragment frames

Use alt/opt/loop fragments to group related messages. Draw a rectangle around the grouped messages with a transparent fill and a solid 1px border in #868e96. The fragment type label ("alt", "opt", "loop") sits in the top-left corner of the rectangle at 14px, distinguished from message labels by being lowercase and styled at 14px italic where the renderer supports it.

### Concrete example

Three-participant sequence diagram (Client, API Gateway, Auth Service):

1. Client box at x=100, y=50, width=120, height=50
2. API Gateway box at x=300, y=50, width=160, height=50
3. Auth Service box at x=500, y=50, width=160, height=50
4. Client lifeline: x=160 (centre of Client box), y=100, descending
5. API Gateway lifeline: x=380, y=100, descending
6. Auth Service lifeline: x=580, y=100, descending
7. Message 1 (solid arrow, left-to-right): y=150, "1. POST /login"
8. Message 2 (solid arrow, left-to-right): y=200, "2. validate token"
9. Message 3 (dashed grey arrow, right-to-left): y=250, "3. 200 OK"
10. Message 4 (dashed grey arrow, right-to-left): y=300, "4. 200 + session"

---

## Flowchart

Use a flowchart when you need to trace execution through a process: what happens next, what decision is made, where the process terminates. Flowcharts show control flow. They are not for showing system topology (use architecture) or message sequences (use sequence).

### ANSI symbols

Follow ANSI flowchart conventions:

- Rectangle: process step. Something is done.
- Diamond: decision. A question is asked with two or more answers.
- Ellipse (or rounded rectangle with extreme rounding): terminal. The process starts or ends here.
- Parallelogram: input/output. Optional; use when data entering or leaving is worth calling out.

### Direction

Default orientation is top-to-bottom. Every step is below its predecessor. Use left-to-right only for pipeline-style flows where the reader naturally reads left to right (CI/CD stages, data transformation chains). Never mix orientations in one diagram - it forces the reader to track two reading directions simultaneously.

### Decision diamonds

Every diamond has exactly two outgoing arrows labelled "yes" and "no". Place the "yes" label on the downward arrow (continuing the happy path) and "no" on the sideways arrow (branching to an exception or alternative). If a decision has more than two outcomes, model it as multiple sequential diamonds, each handling one condition.

When several decision diamonds appear in sequence along the happy path, top-align them. Their top edges share the same y-coordinate. This alignment makes the happy path visually obvious as a straight vertical line.

### Concrete example

A three-step login flow (top-to-bottom, canvas starting at y=50):

1. Ellipse "Start" at x=300, y=50, width=120, height=50
2. Rectangle "Collect credentials" at x=300, y=150, width=160, height=60
3. Diamond "Credentials valid?" at x=300, y=260, width=140, height=80
4. Arrow from 3 downward labelled "yes" to step 5
5. Rectangle "Create session" at x=300, y=390, width=160, height=60
6. Ellipse "End" at x=300, y=500, width=120, height=50
7. Arrow from diamond sideways (right) labelled "no" to:
8. Rectangle "Show error" at x=520, y=260, width=120, height=60
9. Arrow from "Show error" looping back up to "Collect credentials"

---

## Class

Use a class diagram when you need to show the structure of a domain model, a set of interfaces, or object relationships. Class diagrams are appropriate for communicating API contracts and inheritance hierarchies. They are not suited for runtime behaviour - use a sequence diagram for that.

### Compartment boxes

Each class is a rectangle divided into three horizontal compartments:

- Top compartment: class name, centred, at 20px bold.
- Middle compartment: attributes, left-aligned at 16px. Each attribute is prefixed with a visibility symbol: `+` for public, `-` for private, `#` for protected. Format is `+ attributeName: Type`.
- Bottom compartment: methods, left-aligned at 16px. Same visibility prefix. Format is `+ methodName(param: Type): ReturnType`.

If a class has no attributes or no methods, leave that compartment empty rather than omitting it. The consistent three-compartment shape makes the class type instantly recognisable.

### Relationship lines

Inheritance (is-a): solid line with an empty triangle arrowhead at the parent end.
Composition (owns): solid line with a filled diamond at the owner end. The owned object cannot exist without the owner.
Aggregation (has): solid line with an empty diamond at the container end. The contained object can exist independently.
Association (uses): plain solid line with a standard arrowhead. Labelled with the role name on each end.
Dependency (depends-on): dashed line with a standard arrowhead.

Multiplicity labels (1, *, 0..1, 1..*) sit at each end of association and composition lines, 10px from the line endpoint.

### Concrete example

Two-class diagram (Order and LineItem):

1. Order box at x=100, y=100, width=200, height=120
   - Top: "Order"
   - Middle: "- id: UUID", "+ status: OrderStatus"
   - Bottom: "+ addItem(): void", "+ total(): Money"
2. LineItem box at x=400, y=100, width=200, height=100
   - Top: "LineItem"
   - Middle: "- productId: UUID", "- quantity: int"
   - Bottom: "+ price(): Money"
3. Composition line from Order to LineItem, filled diamond at Order end, "1" near Order, "1..*" near LineItem.

---

## State

Use a state diagram when you need to show the lifecycle of an object or a system: what states exist, what events trigger transitions, and what the terminal states are. State diagrams are the right tool for modelling order statuses, user session states, document workflows, and protocol handshakes.

### Node conventions

Initial state: filled black circle, 20px diameter, no label. There is exactly one initial state per diagram.

Terminal state: a filled black circle (20px) ringed by a larger unfilled circle (30px). There can be more than one terminal state.

Regular state: rounded rectangle, 120 x 50px minimum, labelled with the state name at 20px centred.

### Transition labels

Every arrow between states carries a label. The label format is `event [guard] / action`:

- `event` is the trigger (required).
- `[guard]` is an optional condition in square brackets.
- `/ action` is the optional action performed on the transition.

Label sits above the arrow line, centred at the midpoint, with 20px perpendicular clearance.

### Composite states

When several inner states share a common trigger that takes them all to the same outer state (for example, any state inside "Processing" transitions to "Failed" on an error), draw a frame around the inner states to represent the composite state. The frame uses the same style as architecture frames: transparent fill, dashed 2px border, label in the top-left corner.

### Concrete example

Order lifecycle (four states):

1. Initial circle at x=200, y=50
2. State "Pending" at x=150, y=100, width=120, height=50
3. State "Processing" at x=150, y=220, width=120, height=50
4. State "Fulfilled" at x=150, y=340, width=120, height=50
5. Terminal circle at x=200, y=430
6. Arrow from initial to Pending, no label.
7. Arrow from Pending to Processing, label "submit"
8. Arrow from Processing to Fulfilled, label "ship"
9. Arrow from Fulfilled to terminal, no label.
10. Arrow from Processing back to Pending, label "retry [attempts < 3]"

---

## ERD (Gane-Sarson default)

Use an entity-relationship diagram when you need to show the data model: what entities exist, what attributes they have, and how entities relate. ERDs communicate database schema design, API resource models, and domain data structures. Use Gane-Sarson notation unless the team has a stated preference for another notation.

### Entity conventions

Each entity is a rectangle labelled with the entity name in the top compartment (20px, centred, bold). Attributes list below the entity name inside the same rectangle, left-aligned at 16px. Mark the primary key attribute with `PK` to the right of the attribute name. Mark foreign key attributes with `FK`.

For entities with many attributes, split the attribute list into a separate connected ellipse (the original ER notation) only when the entity box would exceed 200px in height. In practice, list attributes inside the box for all entities under eight attributes.

### Relationships

Draw a solid line between related entities. Label the line at its midpoint with the relationship verb ("places", "contains", "belongs to"). Use crow's foot notation at each end of the line to show cardinality:

- Exactly one: a single vertical tick.
- Zero or one: a circle plus a tick.
- One or more: a crow's foot plus a tick.
- Zero or more: a crow's foot plus a circle.

Place multiplicity labels (1, 0..1, 1..*, 0..*) 15px from each entity's edge along the line.

### Layout for ERDs

Lay entities out in a horizontal row first. If relationships produce too many crossing lines, shift related entities closer together and move less-related ones to the periphery. Keep all entity boxes on the 50px grid. Leave 150px horizontal gap between adjacent entity boxes so relationship lines and their multiplicity labels have room.

When a diagram has more than six entities, split it into two related diagrams: one showing the core domain entities and their relationships, one showing the supporting entities (lookup tables, audit tables, configuration). Reference the two diagrams from a shared frame.

### Concrete example

Three-entity model (Customer, Order, Product):

1. Customer box at x=100, y=200, width=160, height=100
   - "id: UUID PK", "email: string", "name: string"
2. Order box at x=400, y=200, width=160, height=100
   - "id: UUID PK", "customerId: UUID FK", "createdAt: datetime"
3. Product box at x=700, y=200, width=160, height=100
   - "id: UUID PK", "name: string", "price: Money"
4. Line from Customer to Order, "places", crow's foot at Order (0..*), tick at Customer (1).
5. Line from Order to Product via a junction entity "OrderLine" at x=550, y=350:
   - OrderLine box: "orderId FK", "productId FK", "quantity: int"
   - Line from Order to OrderLine: tick at Order (1), crow's foot at OrderLine (1..*)
   - Line from OrderLine to Product: tick at Product (1), crow's foot at OrderLine (0..*)

---

## DFD (Yourdon-Coad)

Use a data flow diagram when you need to show what data moves through a system and where it is transformed or stored. DFDs are well suited to regulatory compliance diagrams (GDPR data flows), ETL pipelines, and high-level system analysis where the focus is on data movement rather than component ownership. Yourdon-Coad is the default notation for this skill.

### Element conventions

External entity: rectangle at the edges of the diagram. Represents a person, organisation, or system outside the scope of the model. Labelled with the entity name.

Process: circle in the middle zone of the diagram. Numbered (1.0, 2.0, 2.1 for decomposed sub-processes) with a name label below the number inside the circle. In Gane-Sarson notation, processes are rounded rectangles split horizontally with the number in the top half.

Data store: open-ended rectangle - a rectangle with no left and right sides, drawn as two horizontal parallel lines. Labelled with "D1 Orders" format: a D-prefix number followed by the store name.

### Data flow arrows

Every arrow is labelled with the name of the data being transferred. "Customer data" is acceptable; "data" alone is not. Arrow labels must answer "what data?" not just "flow exists."

Use a solid line with a standard arrowhead for all data flows in a DFD. Do not use dashed or dotted lines - style variation is not part of the Yourdon-Coad vocabulary.

External entities connect only to processes, never directly to data stores. Data stores connect only to processes, never directly to external entities. If the business domain seems to require an external entity writing directly to a data store, model it as: external entity - arrow to - a process (even a trivial "Receive X" process) - arrow to - the data store.

### DFD levels

Context-level (level 0): a single process bubble representing the entire system, surrounded by external entities, with data flows between them. This is the starting point. Draw it first to confirm the system boundary before decomposing.

Level 1: the context-level process explodes into the major sub-processes, typically 4-8 bubbles. Data stores appear at level 1 for the first time. Each sub-process is numbered 1.0, 2.0, 3.0 and so on.

Level 2: each level-1 process can be decomposed again. Sub-process numbering follows the parent: 1.1, 1.2, 2.1, 2.2. In practice, stop at level 2 for most diagrams. Deeper decomposition is a sign the diagram needs to be split by domain.

### Concrete example

Order submission DFD (context-level, one process):

1. External entity "Customer" at x=50, y=200, width=120, height=50
2. Process "1.0 Process Order" (circle) at x=350, y=200, diameter=100
3. Data store "D1 Orders" at x=600, y=200 (two horizontal lines, width=140)
4. Data store "D2 Products" at x=600, y=100 (two horizontal lines, width=140)
5. Arrow from Customer to process 1.0, label "Order request"
6. Arrow from process 1.0 to D1 Orders, label "Confirmed order"
7. Arrow from D2 Products to process 1.0, label "Product details"
8. Arrow from process 1.0 to Customer, label "Order confirmation"

This is a context-level (level 0) DFD. To produce level 1, replace process 1.0 with four sub-processes: "1.1 Validate order", "1.2 Check inventory", "1.3 Charge payment", "1.4 Confirm order".
