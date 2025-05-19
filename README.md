# Eco-move_backend

Backend desarrollado en Django y Django REST Framework para la aplicación Eco-move.

## Descripción

Este proyecto proporciona la API REST necesaria para gestionar estaciones de carga, reservas, usuarios, vehículos y otras funcionalidades relacionadas con la aplicación móvil Eco-move, enfocada en facilitar la movilidad eléctrica.

## Run the project locally

### Install all the requirements from the root folder

    pip install -r requirements.txt

## Test Coverage (Cobertura de Tests)

Este proyecto usa [`coverage.py`](https://coverage.readthedocs.io/) para medir la cobertura de código de los tests.

### Requisitos

Asegúrate de tener coverage.py instalado (ver sección anterior para instalar los requisitos del proyecto).
    
    pip install -r requirements.txt

### Cómo usar

Ejecuta estos comandos desde la carpeta raíz del proyecto:
1. Ejecuta los tests con cobertura:

```
coverage run manage.py test
```

2. Muestra un resumen en la terminal:

``` 
coverage report
```

Si deseas ver qué líneas exactas no fueron ejecutadas:

```
coverage report -m
```

3. (Opcional) Genera un informe visual en HTML:
``` 
coverage html
```
Esto generará una carpeta htmlcov/. Abre el archivo htmlcov/index.html en tu navegador para ver el informe visual.

Cómo abrir el informe HTML automáticamente

- En macOS/Linux:

```
coverage html && open htmlcov/index.html
```

- En Windows (PowerShell):
```
coverage html
start htmlcov\index.html
```

#### Archivos excluidos
La configuración del archivo .coveragerc excluye automáticamente archivos que no necesitan cobertura como:
- Archivos de migración (migrations/)
- Archivos de inicialización (__init__.py)
- Archivos administrativos (admin.py, apps.py)
- Archivos de configuración (settings.py, wsgi.py, asgi.py, manage.py)
- Los propios archivos de tests (tests/)
