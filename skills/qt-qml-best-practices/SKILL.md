---
name: qt-qml-best-practices
description: "Trigger: Qt, QML, Qt Quick, best practices, scalability, performance, tooling. Apply official Qt Quick best practices to QML development."
license: Apache-2.0
metadata:
  author: "antigravity"
  version: "1.4"
---

# Qt/QML Best Practices, Scalability, Performance & Tooling

## Activation Contract

Use this skill whenever generating, reviewing, or refactoring QML and Qt code. This ensures the code adheres to official Qt guidelines for maintainability, performance, type safety, conventions, and UI scalability.

## Hard Rules

- **Use Built-in Controls:** Prefer Qt Quick Controls over custom UI elements. Do not customize native styles directly; base customizations on cross-platform styles (Basic, Fusion, Material, Universal).
- **Separate UI from Logic:** QML is for the UI. Complex calculations and data processing belong in C++. Expose C++ data to QML via `QQmlApplicationEngine::setInitialProperties` or singletons.
- **Type Safety:** Always use exact types (e.g., `property string name`, `property int size`). Never use `var` unless strictly necessary.
- **Declarative Bindings:** Prefer declarative bindings (`color: "red"`) over imperative assignments (`Component.onCompleted: color = "red"`).
- **Interaction Signals:** Prefer explicit interaction signals (e.g., `onMoved`) over state-change signals (e.g., `onValueChanged`). Use explicit parameter names in arrow functions (`onClicked: event => { ... }`).
- **State in Models:** Never store state in a UI delegate. State must be stored in the underlying model to prevent loss when delegates are recycled.
- **Translatable Strings:** Wrap all user-facing strings in `qsTr()`.
- **Layouts and Anchors:** When using Qt Quick Layouts, apply anchors or dimensions to the layout itself, but use `Layout.*` attached properties on its immediate children. **Do NOT use bindings to `x`, `y`, `width`, or `height` for items inside a layout** to avoid binding loops and performance drops.
- **Scalable UIs (Resolution & High DPI):** Do not specify explicit pixel sizes for visual items when expecting dynamic scaling. Provide multi-resolution image variants (`@2x`, `@3x`, `@4x`) or scalable SVG/font-based icons. Let `ApplicationWindow` and Layouts automatically calculate sizes.
- **Scalable UIs (Orientation & Responsive):** Change layout flows dynamically based on aspect ratio (e.g. `flow: width > height ? GridLayout.LeftToRight : GridLayout.TopToBottom`). Use `StateGroup` or states to change layout configurations on rotation, do NOT use `Loader` to switch orientations due to performance overhead.
- **On-Demand & Platform Loading:** Use `Loader` for delaying the creation of heavy or conditionally visible components. Use `QQmlFileSelector` (`+android`, `+ios`) to load alternative resources or QML files depending on the platform.
- **QML Declaration Order:** Strictly order elements within a QML object: `id` -> `property` declarations -> `signal` declarations -> `function` declarations -> object properties -> child objects. Separate each section with an empty line.
- **Unqualified Access & Required Properties:** Always reference properties of parent components by their `id` explicitly. Use `required property` to make data dependencies explicit from the outside.
- **Grouped Properties:** Use group notation (`anchors { left: parent.left; top: parent.top }`) instead of dot notation.
- **Tooling First:** Use `qmllint` to verify syntactic validity and catch anti-patterns before manual reviews. Use `qmlformat` to automatically enforce the QML Coding Conventions. Use the **QML Profiler** or GammaRay *before* guessing where performance bottlenecks are.

### Performance & JavaScript Execution
- **Non-blocking Event Loop:** Never spin a manual event loop (e.g., `QEventLoop` or `processEvents()`) in C++ code invoked from QML. Keep frame processing under 16ms to maintain 60 FPS.
- **Property Resolution:** Cache common property bases in local variables when accessed multiple times in a loop or function (e.g., `var rectColor = rect.color`). Do not repeatedly resolve deeply nested properties.
- **Avoid Binding Accumulators:** Do not use bound QML properties as intermediate accumulators in loops. Accumulate in a local `var` and assign the final result to the property once.
- **Sequence Modifications:** Do not modify sequence types (e.g., C++ arrays/lists exposed to QML) element-by-element. Create a local copy (`let data = [...mySequence]`), modify the copy, and assign the full array back to the property.

## Decision Gates

| Need | Action |
|------|--------|
| Verifying syntax and finding anti-patterns | Run `qmllint` |
| Formatting code automatically | Run `qmlformat` |
| Finding performance issues | Run the QML Profiler or GammaRay |
| Reacting to user changes on a control | Use `onMoved` or similar interaction signals, avoid `onValueChanged` |
| Arranging items dynamically | Use Qt Quick Layouts and avoid manual `x/y/width/height` bindings |
| Passing data down to child components | Use `required property` to force explicit data injection |
| Handling different screen orientations | Use `State` changes or layout bindings, avoid `Loader` |
| Doing math in a loop | Store the result in a local JS `var` first, then assign to the property |
| Updating an array element | Copy the array, modify the copy, reassign the array |

## Execution Steps

1. Run `qmllint` on the files to catch obvious anti-patterns automatically.
2. Structure QML object attributes in the exact required order (`id` first, etc.) or use `qmlformat`.
3. Convert unqualified property accesses to explicitly use their parent `id` and enforce `required property` when appropriate.
4. Replace imperative assignments with declarative bindings.
5. Verify that Qt Quick Layout children use `Layout.*` properties instead of `anchors`, `width`, or `height`.
6. Refactor any loops that mutate sequence types directly or use QML properties as intermediate accumulators.

## Output Contract

Return refactored or generated QML/C++ code. Explain the applied principles concisely, emphasizing if tooling (`qmllint`, `qmlformat`) was utilized or recommended.

## References

- [Qt Quick Best Practices](https://doc.qt.io/qt-6/qtquick-bestpractices.html)
- [QML Coding Conventions](https://doc.qt.io/qt-6/qml-codingconventions.html)
- [Qt Quick Scalability](https://doc.qt.io/qt-6/scalability.html)
- [Qt Quick Performance](https://doc.qt.io/qt-6/qtquick-performance.html)
- [Qt Quick Tools and Utilities](https://doc.qt.io/qt-6/qtquick-tools-and-utilities.html)
