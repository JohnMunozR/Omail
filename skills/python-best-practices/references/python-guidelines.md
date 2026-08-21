# Guía Definitiva de Buenas Prácticas en Python

## 1. Clean Code y Estilo (Legibilidad)
*   **Tipado Estático (Type Hints):** Usa siempre anotaciones de tipos. Esto documenta el código y permite usar herramientas como `mypy`.
    ```python
    from collections.abc import Callable
    def procesar(datos: list[dict[str, int]], funcion: Callable[[int], int]) -> list[int]:
        return [funcion(d["valor"]) for d in datos]
    ```
*   **Nombres Descriptivos:** Evita `x`, `y`, `data`. Usa nombres que revelen intención.
*   **Retornos Tempranos (Early Returns):** Evita el anidamiento profundo. Valida al principio y retorna rápido.
*   **Herramientas Modernas:** Configura un linter y formateador desde el día uno (ej. **Ruff**).

## 2. Diseño y Arquitectura (SOLID)
*   **Inversión de Dependencias (Protocol):** Usa `typing.Protocol` para "Duck Typing" estático o `abc.ABC` para tipado nominal y chequeos en tiempo de ejecución.
    ```python
    from typing import Protocol
    class Notificador(Protocol):
        def enviar(self, mensaje: str) -> None: ...
    ```
*   **Composición sobre Herencia:** Inyecta comportamientos en lugar de heredar de múltiples clases.
*   **Clean Architecture:**
    *   `domain/`: Entidades y dataclasses (Dominio central).
    *   `use_cases/`: Lógica de negocio y Puertos de Salida (Output Ports como interfaces de Repositorios).
    *   `infrastructure/`: Adaptadores, BD, APIs.
    *   `main.py`: Composition Root.

## 3. Rendimiento (Performance)
*   **Estructuras Nativas:** Usa `set` para búsquedas $O(1)$. Usa `collections.deque` para insertar/eliminar al principio.
*   **Generadores:** Usa evaluación perezosa para grandes volúmenes de datos `(x * x for x in range(1000000))`.
*   **Caché:** Usa `functools.cache` o `lru_cache`.
*   **__slots__:** Usa el decorador `@dataclass(slots=True)` en clases instanciadas miles de veces para ahorrar memoria automáticamente (Python 3.10+).
*   **Profiling:** Mide siempre antes de optimizar (`timeit`, `cProfile`).

## 4. Concurrencia y Asincronía
*   **I/O-Bound:** Usa `asyncio` (nunca bloquees el Event Loop con `time.sleep` o `requests`). Usa `asyncio.TaskGroup` (Python 3.11+) para gestionar múltiples tareas concurrentes de forma segura. Para I/O síncrono (ej. `requests`), usa `concurrent.futures.ThreadPoolExecutor`.
*   **CPU-Bound:** Usa `concurrent.futures.ProcessPoolExecutor` para evitar el GIL en cálculos pesados.

## 5. Tipado Avanzado
*   `Literal`: Para restringir valores exactos (`Literal["tarjeta", "paypal"]`).
*   `TypedDict`: Para tipar diccionarios crudos (APIs, JSON). Usa `NotRequired` para campos opcionales.
*   `TypeVar` (Generics): Usa la nueva sintaxis de parámetros de tipo (PEP 695) en Python 3.12+ (ej. `def func[T](val: T) -> T:`) en lugar de instanciar `TypeVar` manualmente.
*   **Sintaxis Moderna (3.10+):** Usa `|` en lugar de `Union` o `Optional` (ej. `str | None`).
*   **mypy --strict:** Usa validación estricta en CI/CD.

## 6. El "Pythonic Way"
*   **Context Managers Propios:** Usa `@contextmanager` de `contextlib` en lugar de clases pesadas con `__enter__`/`__exit__`.
*   **Desempaquetado Avanzado (Unpacking):** `nombre, *datos_extra, estado = registro`.
*   **Walrus Operator (`:=`):** Asigna y evalúa en la misma línea para evitar repetición (ej. `if (n := len(texto)) > 5:`).
*   **for...else:** Úsalo para ejecutar código solo si el bucle terminó de forma natural sin un `break`.
