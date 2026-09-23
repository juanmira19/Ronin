# Gates Makers — revisión 2026-09-23

Referencia revisada: `origin/main`, integrada localmente en `makers/review`.

| Gate | Estado | Evidencia | Para cerrar |
|---|---|---|---|
| Arquitectura atribuible | PASS | `docs/arquitectura.md`; aportes de Andrés Jacobo y Juan Pablo. | Ambos deben explicar ingesta, métricas, LLM y verificación. |
| Uso de IA + evals | PARCIAL | Ejecución local actual: 145 pasan y falla 1 test de onboarding; real continuo 3 PASS/1 FAIL/1 N/A y sintético 5/5. | Corregir onboarding y conseguir partido intermitente real. |
| Jailbreak y safety | PARCIAL | Contrato, guardrails y casos adversariales. | Ejecutarlos automáticamente en CI y con proveedor real controlado. |
| Mantenibilidad | PASS | Módulos pequeños y responsabilidades claras. | Evitar que la demo acumule lógica de dominio. |
| Producto ejecutable | PASS | Web, Apple Health y demo. | Prueba con atleta/entrenador y decisión observable. |
| Git profesional | PARCIAL | Ambos tienen ramas y trabajo integrado; se agregó CI en `makers/review`. | Hacer pasar 146/146 y normalizar ramas a `dev/nombre`. |

El producto no puede declarar validación deportiva mientras el único partido intermitente sea sintético.
