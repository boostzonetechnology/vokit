# Code Minimalism & Clean Implementation

## Purpose

Write **complete, production-quality code with the minimum necessary complexity**.

The goal is not to make code artificially short. The goal is to prevent unnecessary, excessive, duplicated, speculative, or dead code.

If a flow genuinely requires 100 lines, write 100 lines.

If the same flow can be implemented correctly in 20 lines, do not write 100 lines.

**Never reduce code by removing required behavior. Reduce code by removing unnecessary behavior and complexity.**

---

# 1. Core Principle

Always prefer:

> **Simple + complete + maintainable**

over:

> **Verbose + over-engineered + unnecessarily abstract**

Before writing code, ask:

1. What is the actual requirement?
2. What is the simplest correct implementation?
3. Which code is actually required for this flow?
4. Am I introducing abstraction that is not currently needed?
5. Am I duplicating logic that already exists?
6. Am I writing code for hypothetical future requirements?
7. Can this be implemented with significantly fewer lines without losing functionality?

Do not optimize for line count alone.

Optimize for:

- correctness
- readability
- maintainability
- reuse where actually needed
- minimal complexity
- minimal duplication
- complete flow coverage

---

# 2. Do Not Over-Engineer

Do not introduce architecture simply because it is possible.

Avoid creating:

- unnecessary interfaces
- unnecessary abstract classes
- unnecessary repositories
- unnecessary factories
- unnecessary managers
- unnecessary wrappers
- unnecessary DTOs
- unnecessary traits
- unnecessary helper classes
- unnecessary configuration layers
- unnecessary service layers
- unnecessary events/listeners
- unnecessary enums
- unnecessary utility classes
- unnecessary design patterns

Use an abstraction when it provides a real benefit.

For example, do not create:

```text
Controller
    ↓
Service
    ↓
Manager
    ↓
Repository
    ↓
Helper
    ↓
Utility
```

for a simple CRUD operation if the project's architecture does not require all of those layers.

Every additional layer must have a reason.

---

# 3. No Hypothetical Code

Do not write code for requirements that do not currently exist.

Do NOT implement things such as:

- "we might need this later"
- "this could support multiple providers in the future"
- "we may add another authentication mechanism later"
- "this allows future extensibility"
- "this might be useful eventually"

unless the current requirement explicitly requires that extensibility.

Implement the current requirement cleanly.

Future requirements can be implemented when they actually exist.

---

# 4. No Dead Code

Never leave unnecessary code behind.

Do not add:

- unused imports
- unused variables
- unused methods
- unused classes
- unused properties
- unreachable branches
- commented-out old implementations
- duplicate implementations
- unused configuration
- unused constants
- unused dependencies

If code is no longer needed because of the implementation, remove it.

Do not preserve old code "just in case".

Version control already preserves history.

---

# 5. No Duplicate Logic

Before implementing new logic, search the codebase.

If equivalent functionality already exists:

- reuse it
- extract it if genuinely reusable
- extend it if appropriate

Do not create another implementation of the same behavior.

For example, avoid:

```text
CustomerService::calculateBalance()
OrderService::calculateBalance()
InvoiceService::calculateBalance()
PaymentService::calculateBalance()
```

if the same business rule should be centralized.

However, do not force unrelated functionality into a shared helper merely to reduce line count.

**Duplication is bad, but artificial abstraction is also bad.**

---

# 6. Keep Files Small

A single source file should generally stay around **300 lines or less**.

300 lines is a guideline, not a hard compiler rule.

If a file becomes substantially larger because it contains multiple responsibilities:

1. Identify the separate responsibilities.
2. Extract meaningful units.
3. Move substantial business logic into appropriate services/classes/modules.
4. Keep the original file focused on its primary responsibility.

For example:

```text
LargeController.php
```

should not become:

```text
LargeController.php
    700 lines
```

Instead, if the logic genuinely represents separate responsibilities:

```text
Controller
    ↓
CustomerService
PaymentService
NotificationService
```

The exact structure depends on the project's existing architecture.

Do NOT split a file into dozens of tiny files simply to satisfy the 300-line guideline.

A 320-line cohesive class can be better than six artificial 50-line classes.

---

# 7. File Size Is a Signal, Not a Goal

Do not blindly split every file at exactly 300 lines.

Use judgment.

### Good reason to split

A file contains multiple independent responsibilities:

```text
UserController
- authentication
- billing
- reporting
- notifications
- exports
```

These should probably be separated.

### Bad reason to split

A class contains one cohesive operation that naturally requires 310 lines.

Do not create:

```text
ServicePart1
ServicePart2
ServicePart3
```

just to make the original file smaller.

The goal is **cohesion**, not an artificial line-count target.

---

# 8. Complete Flow Is Mandatory

Conciseness must NEVER result in an incomplete implementation.

Before considering a task complete, verify the complete flow.

For example, if implementing an API endpoint:

```text
Request
 ↓
Validation
 ↓
Authorization
 ↓
Business logic
 ↓
Database operation
 ↓
Response
```

Do not remove a required step simply to reduce code.

The following must still be handled when required by the project:

- validation
- authorization
- authentication
- business rules
- database consistency
- transactions
- error handling
- required logging/auditing
- API response formatting
- required events
- required notifications
- edge cases explicitly defined by requirements

**Shorter code is not automatically better code.**

---

# 9. Prefer Existing Framework Features

Before implementing custom logic, check whether the framework already provides the functionality.

Prefer framework-native solutions where appropriate.

Examples:

- framework validation instead of manually validating every field
- framework authorization instead of custom permission checks everywhere
- ORM relationships instead of manually querying related records
- framework queues instead of custom queue implementations
- framework caching instead of unnecessary custom caching layers
- framework events when events are actually required
- framework pagination instead of custom pagination
- framework resources/serializers when the project uses them

Do not reinvent functionality the framework already solves well.

---

# 10. Avoid Excessive Defensive Programming

Handle realistic failure cases.

Do not create enormous amounts of defensive code for impossible or irrelevant scenarios.

Bad:

```text
check A
check B
check C
check D
check E
check F
check G
```

when the framework/database/type system already guarantees most of those conditions.

Good:

- validate external/user-controlled input
- handle realistic failures
- preserve required invariants
- allow the framework to handle framework-level guarantees

Defensive programming should protect the system, not bury the actual business logic.

---

# 11. Avoid Excessive Comments

Comments should explain **why**, not restate **what** the code obviously does.

Bad:

```php
// Get the customer
$customer = Customer::find($id);

// Check if customer exists
if (!$customer) {
    ...
}
```

Good:

```php
// Customer records must not be deleted because invoices reference them historically.
```

Do not add comments merely to make the code appear documented.

---

# 12. Do Not Generate Boilerplate Without Need

Do not automatically generate:

- getters/setters for properties that do not need them
- wrappers around single method calls
- methods that only call another method
- constants used only once when a literal is clearer
- classes containing one trivial function
- interfaces with only one implementation when the architecture does not require them
- empty constructors
- empty methods
- unnecessary type-conversion helpers
- unnecessary response wrappers

Use the language and framework directly where appropriate.

---

# 13. Prefer Guard Clauses

When appropriate, use guard clauses instead of deeply nested conditionals.

Prefer:

```php
if (!$user) {
    return;
}

if (!$user->active) {
    return;
}

process($user);
```

over deeply nested code when the guard-clause version is clearer.

Do not force guard clauses where they make the flow harder to understand.

---

# 14. Avoid Clever Code

Concise does not mean cryptic.

Do not use:

- obscure one-liners
- excessive chaining
- magic behavior
- complicated regular expressions when simple code works
- clever tricks that reduce lines but reduce readability

Prefer code that another developer can understand quickly.

The target is:

> **Minimal code, maximum clarity.**

---

# 15. Search Before Creating

Before creating a new:

- class
- method
- service
- helper
- component
- constant
- configuration
- database query
- validation rule

search the existing codebase.

Check whether equivalent functionality already exists.

Do not create duplicates.

---

# 16. Refactor Only When Useful

Do not perform large unrelated refactors while implementing a feature.

If existing code works and is outside the task:

- do not rewrite it unnecessarily
- do not rename unrelated classes
- do not restructure unrelated modules
- do not "clean up" the entire project

Only refactor existing code when:

1. the current task requires it, or
2. the existing structure directly prevents a clean implementation.

Keep changes focused.

---

# 17. Minimize Change Surface

For every task, prefer the smallest set of files and changes required to correctly implement the requirement.

Before finishing, ask:

> "Did I modify anything that was not necessary for this task?"

If yes, revert/remove unnecessary changes unless they are required for correctness.

Avoid:

```text
Task requires 3 files
Changed 18 unrelated files
```

Unrelated modifications increase regression risk.

---

# 18. Do Not Repeat Code Just To Be Explicit

Avoid unnecessary repetition.

Instead of repeatedly writing the same logic:

```php
if ($status === 'active') {
    ...
}

if ($status === 'active') {
    ...
}

if ($status === 'active') {
    ...
}
```

consider whether the logic can be expressed once.

But do not extract every repeated 2-line expression into a helper.

Extraction should create meaningful reuse.

---

# 19. Use Appropriate Abstraction Levels

Use the project's established architecture.

For a business-heavy operation, a service may be appropriate:

```text
Controller
    ↓
Service
    ↓
Repository/ORM
```

But do not automatically create:

```text
Controller
    ↓
Service
    ↓
Manager
    ↓
Coordinator
    ↓
Repository
    ↓
Adapter
    ↓
Helper
```

unless the project genuinely requires those boundaries.

Every abstraction should answer:

> "What problem does this abstraction solve?"

If there is no clear answer, do not create it.

---

# 20. Do Not Optimize Only For Fewer Lines

The objective is NOT:

```text
100 lines → 20 lines
```

at any cost.

The objective is:

```text
500 unnecessary lines → 150 necessary lines
```

while keeping all required behavior.

A 150-line implementation is better than a 30-line implementation that:

- skips validation
- ignores authorization
- hides errors
- duplicates database operations
- breaks edge cases
- violates project architecture
- makes the code unreadable

---

# 21. Before Writing Code

For every task, first determine:

### Required behavior

What exactly must happen?

### Existing behavior

What already exists?

### Reusable code

What can be reused?

### Required changes

What is the minimum change needed?

### File structure

Which existing file should contain the change?

### New files

Are new files genuinely necessary?

Only after answering these should implementation begin.

---

# 22. Before Finishing

Perform a cleanup pass.

Check:

- [ ] No unused imports
- [ ] No unused variables
- [ ] No dead methods
- [ ] No commented-out code
- [ ] No duplicate logic
- [ ] No unnecessary abstractions
- [ ] No unnecessary files
- [ ] No unnecessary dependencies
- [ ] No speculative functionality
- [ ] No unrelated refactoring
- [ ] No excessive comments
- [ ] No unnecessary nesting
- [ ] No unnecessarily long methods
- [ ] Files remain reasonably sized
- [ ] Required validation exists
- [ ] Required authorization exists
- [ ] Required business rules are preserved
- [ ] Error handling is preserved where required
- [ ] Complete flow works end-to-end

---

# 23. Code Review Question

Before presenting the implementation, ask yourself:

> **"If another experienced developer reviewed this code, could they reasonably ask why any of this code exists?"**

If the answer is yes, investigate whether that code can be removed or simplified.

For every significant abstraction, there should be a concrete reason.

For every significant block of code, there should be a requirement or architectural reason.

---

# 24. Golden Rule

Always follow this priority:

```text
Correctness
    ↓
Completeness
    ↓
Maintainability
    ↓
Readability
    ↓
Simplicity
    ↓
Minimum necessary code
```

Never sacrifice an earlier item merely to achieve a later one.

The final implementation should be:

> **The simplest complete solution that fits the existing architecture.**

Not the shortest possible solution.

Not the most abstract solution.

Not the most configurable solution.

Not the most "future-proof" solution.

Just the **simplest complete and maintainable solution required by the actual task**.