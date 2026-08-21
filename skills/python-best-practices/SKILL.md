---
name: python-best-practices
description: "Trigger: python best practices, buenas practicas python, clean code python, python architecture, python performance, asyncio, python typing. Applies Python best practices for clean code, architecture, performance, concurrency, typing, and pythonic patterns."
license: Apache-2.0
metadata:
  author: "antigravity"
  version: "1.0"
---

## Activation Contract

Activate this skill when generating, reviewing, or refactoring Python code, especially when the user requests best practices, clean code, architecture patterns (SOLID, Clean Architecture), performance optimizations, concurrency (asyncio, multiprocessing), or strict typing.

## Hard Rules

- **Clean Code & Style:** Always use type hints. Use descriptive variable/function names. Prefer early returns over deep nesting. Configure Ruff as the linter/formatter.
- **Design & Architecture:** Use `typing.Protocol` for structural subtyping and `abc.ABC` for nominal subtyping. Prefer composition over inheritance. Follow Clean Architecture (Domain, Use Cases, Infrastructure, Entrypoint). Output Ports (e.g., Repositories) belong in the Use Cases layer.
- **Performance:** Use `set` for $O(1)$ lookups, `collections.deque` for fast left appends/pops. Use generators over lists for large datasets. Use `functools.cache` or `lru_cache` for memoization. Use `@dataclass(slots=True)` for heavily instantiated classes (Python 3.10+). Always measure with `timeit` or `cProfile` before optimizing.
- **Concurrency:** Use `asyncio` (with `TaskGroup` in 3.11+) for modern I/O-bound tasks, or `concurrent.futures.ThreadPoolExecutor` for synchronous I/O. Use `concurrent.futures.ProcessPoolExecutor` for CPU-bound tasks. Never block the event loop in async code.
- **Advanced Typing:** Use `Literal` for strict values, `TypedDict` for raw dicts, and the modern Type Parameter Syntax (PEP 695, e.g., `def func[T](val: T) -> T:`) for generics instead of `TypeVar`. Use the `|` operator for unions (Python 3.10+). Ensure code passes `mypy --strict`.
- **Pythonic Way:** Use `@contextmanager` for custom context managers. Use unpacking (`*`). Use the Walrus Operator (`:=`) to assign and evaluate. Use `for...else` when applicable.

## Decision Gates

| Need | Action |
|------|--------|
| Small I/O-bound tasks | Use `asyncio` and `asyncio.TaskGroup` |
| Heavy CPU computations | Use `concurrent.futures.ProcessPoolExecutor` |
| Large data processing | Use generators instead of lists |
| External API/JSON typing | Use `TypedDict` |
| Abstract behaviors/interfaces | Use `typing.Protocol` |

## Execution Steps

1. Analyze the Python code or request against the Hard Rules and Decision Gates.
2. Ensure all types are explicitly annotated and use modern syntax (`|` instead of `Union`).
3. Refactor logic to use early returns, descriptive names, and appropriate native data structures.
4. If applicable, structure the code following Clean Architecture principles.
5. Review the final code against the guidelines in `references/python-guidelines.md`.

## Output Contract

Return:
- The generated or refactored Python code.
- A brief explanation of the specific best practices applied.
- Links to relevant sections in the `references/python-guidelines.md` file if further context is needed.

## References

- `references/python-guidelines.md` — Detailed explanations and code examples for all the best practices covered in this skill.
