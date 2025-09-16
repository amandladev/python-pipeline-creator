# Pipeline Creator CLI

Un CLI para crear y gestionar pipelines de CI/CD en AWS de forma rápida y sencilla.

## 🚀 Instalación

```bash
# Instalación en modo desarrollo
pip install -e .

# O instalación desde PyPI (próximamente)
pip install pipeline-creator
```

## 📋 Comandos disponibles

### `pipeline init`
Inicializa la configuración del pipeline en tu repositorio.

```bash
pipeline init
```

### `pipeline generate`
Genera los archivos de infraestructura usando AWS CDK.

```bash
pipeline generate
```

### `pipeline deploy`
Ejecuta el despliegue con CDK.

```bash
pipeline deploy
```

### `pipeline status`
Muestra el estado actual del pipeline.

```bash
pipeline status
```

### `pipeline logs`
Muestra los logs del último despliegue.

```bash
pipeline logs
```

## 🛠️ Prerequisitos

- Python 3.8+
- AWS CLI configurado (`aws configure`)
- Node.js (para AWS CDK)

## 📁 Estructura de archivos

Después de ejecutar `pipeline init`, se creará:

```
.pipeline/
  config.json    # Configuración del pipeline
```

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=pipeline_creator
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request
