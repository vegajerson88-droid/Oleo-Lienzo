# FastAPI frente a Django REST Framework

> Análisis aplicado al proyecto **Óleo & Lienzo**. No es una comparación
> genérica: cada punto se contrasta con código que está en este repositorio.

---

## Resumen

| Criterio | FastAPI | Django REST Framework | En este proyecto |
|---|---|---|---|
| Lenguaje y base | Python sobre Starlette + Pydantic | Python sobre Django | — |
| Modelo de concurrencia | Asíncrono nativo (ASGI) | Síncrono (WSGI); async parcial desde Django 3.1 | Decisivo |
| Validación | Pydantic v2, con anotaciones de tipo | Serializers propios de DRF | Ventaja FastAPI |
| ORM | Libre (aquí SQLAlchemy 2) | Django ORM, acoplado | Indiferente |
| Documentación | OpenAPI y Swagger automáticos | Requiere drf-spectacular o similar | Ventaja FastAPI |
| Panel de administración | No trae | `django-admin` completo | Ventaja DRF |
| Autenticación | Se implementa (aquí JWT con python-jose) | Incluida, con sesiones y permisos | Ventaja DRF |
| Migraciones | Externas (Alembic) | `makemigrations` integrado | Ventaja DRF |
| Curva de aprendizaje | Suave: son funciones con tipos | Más pronunciada: hay que aprender Django | Ventaja FastAPI |
| Tamaño del proyecto | Ligero | Pesado, con muchas piezas incluidas | Ventaja FastAPI |

---

## 1. Concurrencia: el motivo principal de la elección

Óleo & Lienzo hace cosas que tardan y que no consumen CPU: llamar a Groq,
crear una sesión de pago en Stripe, conectarse a un servidor SMTP.

En **FastAPI**, mientras se espera una de esas respuestas el servidor atiende
a otros usuarios. El endpoint del chatbot es así:

```python
# app/services/chatbot.py
async with httpx.AsyncClient(timeout=settings.groq_timeout_seconds) as cliente:
    respuesta = await cliente.post(f"{settings.groq_base_url}/chat/completions", ...)
```

Groq puede tardar varios segundos. Con el modelo síncrono de DRF, cada una de
esas peticiones bloquea un proceso o un hilo del servidor durante todo ese
tiempo. Con veinte visitantes preguntándole al chatbot a la vez, harían falta
veinte trabajadores. En FastAPI los atiende un único proceso.

DRF admite vistas `async` desde Django 3.1, pero el ORM de Django sigue siendo
mayoritariamente síncrono y hay que envolverlo con `sync_to_async`, lo que
devuelve buena parte del problema.

---

## 2. Validación: Pydantic frente a los serializers

Ambos validan bien. La diferencia está en cuánto código hace falta y en qué
más se obtiene a cambio.

**FastAPI + Pydantic** — el mismo tipo sirve para validar, documentar y
autocompletar en el editor:

```python
# app/schemas/usuario.py
class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=8, max_length=64)
    confirmar_password: str

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if not PASSWORD_RE.match(v):
            raise ValueError(MENSAJE_PASSWORD)
        return v

    @model_validator(mode="after")
    def validar_confirmacion(self) -> "UsuarioCreate":
        if self.password != self.confirmar_password:
            raise ValueError("Las contraseñas no coinciden.")
        return self
```

Eso, sin escribir nada más, genera el 422 con la lista de errores, el esquema
de OpenAPI y el ejemplo que aparece en Swagger.

**DRF** necesita un `Serializer` equivalente y, además, un paquete extra
(`drf-spectacular`) con sus anotaciones para que la documentación refleje lo
mismo.

Un detalle donde Pydantic destacó en este proyecto: separar `PUT` de `PATCH`.
Basta con dos clases —`ObraReplace` con todos los campos obligatorios y
`ObraUpdate` con todos opcionales— y el comportamiento REST correcto sale
solo. En DRF se resuelve con el argumento `partial=True`, que funciona, pero
deja la distinción implícita en la vista en lugar de explícita en el tipo.

---

## 3. Documentación automática

FastAPI genera `/docs` y `/redoc` a partir de las firmas de las funciones. En
este proyecto las 60 operaciones están documentadas sin escribir un solo
archivo aparte: los `summary`, `description` y `responses` viven junto al
código que describen, así que es difícil que se queden desfasados.

```python
@router.patch(
    "/{pedido_id}/estado",
    response_model=PedidoOut,
    summary="Cambiar el estado de un pedido",
    description="... Confirmar genera automáticamente la venta ...",
    responses={**RESPUESTA_404, **RESPUESTA_422},
)
```

En DRF la documentación es un añadido que hay que instalar y mantener.

---

## 4. Dónde gana Django REST Framework

Sería deshonesto presentar solo las ventajas de la opción elegida.

**Panel de administración.** `django-admin` habría dado gratis un CRUD
completo de las 15 tablas. En este proyecto ese panel se programó a mano
—`UsuariosManager`, `ObrasManager`, `VentasManager`…— con el trabajo de
frontend que eso implica. Para un proyecto puramente interno, DRF habría
ahorrado semanas.

**Autenticación y permisos.** Django trae usuarios, grupos, permisos, hashing
y recuperación de contraseña listos. Aquí hubo que construir: `security.py`
(bcrypt y JWT), `dependencies/auth.py` (dependencias de rol y permiso), la
tabla `permisos` y el flujo de recuperación con su token de un solo uso. Es
más código y, por tanto, más superficie donde equivocarse.

**Migraciones.** `makemigrations` y `migrate` no tienen equivalente incluido
en FastAPI. Este proyecto usa `Base.metadata.create_all` para desarrollo y un
script SQL versionado para producción; un sistema mayor necesitaría Alembic.

**Madurez del ecosistema.** Django lleva más de quince años y casi cualquier
problema tiene una solución documentada.

---

## 5. Por qué FastAPI para este proyecto

1. **El frontend ya es React.** No hace falta el sistema de plantillas ni el
   panel de Django: el backend solo tiene que servir JSON. Django habría
   aportado mucha maquinaria que quedaría sin usar.
2. **Hay tres integraciones externas lentas** (Groq, Stripe, SMTP). El modelo
   asíncrono no es un lujo, es lo que evita que el servidor se bloquee.
3. **La documentación automática es parte de la entrega.** Swagger es una de
   las evidencias exigidas, y aquí sale del propio código.
4. **El proyecto es mediano.** Quince tablas y sesenta endpoints no justifican
   el peso de Django si su mayor ventaja —el panel de administración— no se
   va a usar.
5. **Validación en un solo sitio.** Las mismas reglas del formulario de React
   se declaran en Pydantic y el backend las impone, sin poder saltárselas.

---

## 6. Cómo se vería el mismo endpoint en cada uno

**FastAPI** (`app/routers/productos.py`):

```python
@router.get("", response_model=Page[ObraOut], summary="Listar obras del catálogo")
async def listar_obras(
    artista: str | None = Query(default=None, max_length=80),
    disponible: bool | None = Query(default=None),
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
):
    items, total = await obra_crud.list_obras(db, ...)
    return Page(items=items, total=total, page=pagination.page,
                page_size=pagination.page_size)
```

**Django REST Framework**, equivalente:

```python
class ObraFilter(django_filters.FilterSet):
    artista = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Obra
        fields = ["artista", "disponible"]


class ObraViewSet(viewsets.ModelViewSet):
    queryset = Obra.objects.all()
    serializer_class = ObraSerializer
    filterset_class = ObraFilter
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
```

El `ViewSet` de DRF es más corto porque asume más cosas: da por hecho el CRUD
completo y hay que restringirlo. La versión de FastAPI es más explícita: se ve
en la propia firma qué parámetros acepta, de qué tipo y con qué validación.

Para un CRUD estándar, DRF escribe menos. En cuanto aparece lógica que no es
CRUD —como `PATCH /pedidos/{id}/estado`, que valida una transición y genera
una venta— la ventaja se invierte: en FastAPI es una función normal, mientras
que en DRF hay que salirse del `ViewSet` con un `@action`.

---

## Conclusión

Para **Óleo & Lienzo**, FastAPI fue la elección correcta: el frontend en React
no necesita nada de lo que Django aporta de más, las integraciones externas se
benefician del modelo asíncrono y la documentación automática es parte de lo
que hay que entregar.

Django REST Framework habría sido mejor opción en un escenario distinto: una
aplicación con plantillas servidas por el propio backend, con un equipo
administrativo que necesite un panel desde el primer día, o con un modelo de
datos que cambie a menudo y donde las migraciones integradas ahorren más
tiempo del que cuesta el peso del framework.

No hay un ganador absoluto: hay una herramienta que encaja mejor con esta
arquitectura concreta.
