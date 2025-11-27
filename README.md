# Sistema de Procesamiento de PDFs - Despliegue con Docker

## Estructura del Proyecto
- app.py: Punto de entrada principal de la aplicación Flask
- src/: Código fuente organizado en módulos (config, database, routes, services)
- templates/: Plantillas HTML
- static/: Recursos estáticos (CSS, JS, imágenes)
- uploads/: Directorio para almacenar archivos subidos
- docker-compose.yml: Configuración para despliegue con Docker Compose
- Dockerfile: Instrucciones para construir la imagen Docker
- nginx.conf: Configuración del servidor web Nginx

## Requisitos Previos

- Docker Engine
- Docker Compose

## Instrucciones de Despliegue

### 1. Configuración de Variables de Entorno

Antes de iniciar el despliegue, debes crear un archivo `.env` con tus variables de entorno:

```bash
cp .env.example .env
```

Luego edita el archivo `.env` con tus propias credenciales:

```env
# API Keys
OPENAI_API_KEY=tu_openai_api_key_aqui

# Google Drive (OAuth de usuario)
GOOGLE_DRIVE_FOLDER_ID=tu_id_de_carpeta_google_drive
GOOGLE_CLIENT_ID=tu_google_client_id_aqui
GOOGLE_CLIENT_SECRET=tu_google_client_secret_aqui

# File Upload
MAX_FILE_SIZE=52428800

# Development
DEBUG=False
FLASK_ENV=production

# MySQL Database (usuarios)
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=sgdea_user
MYSQL_PASSWORD=tu_contrasena_segura
MYSQL_DATABASE=sgdea_users
```

### 2. Preparar el token de Google OAuth

Si ya tienes un token de Google OAuth válido, asegúrate de copiarlo a `src/token.json` antes de construir la imagen.

### 3. Iniciar los servicios con Docker Compose

```bash
docker-compose up -d
```

Esto iniciará tres servicios:
- MySQL para la base de datos
- Aplicación Flask
- Nginx como proxy inverso

### 4. Verificar el despliegue

- Aplicación web: http://localhost
- Endpoint de salud: http://localhost/health
- API Info: http://localhost/api/info

### 5. Comandos útiles

- Ver logs: `docker-compose logs -f`
- Detener servicios: `docker-compose down`
- Reconstruir imagen: `docker-compose build`
- Ver estado de servicios: `docker-compose ps`

## Consideraciones de Seguridad

1. **Variables de entorno**: No incluyas credenciales en el código fuente
2. **Contraseñas**: Usa contraseñas fuertes para la base de datos
3. **HTTPS**: En producción, configura certificados SSL para HTTPS
4. **Token OAuth**: El token de Google OAuth se monta como volumen para persistencia

## Escalabilidad

El contenedor de la aplicación Flask usa Gunicorn con 4 workers, lo que permite manejar múltiples solicitudes concurrentes. Puedes ajustar el número de workers editando el comando CMD en el Dockerfile.

## Solución de Problemas

### Problemas comunes:

1. **Error de conexión a base de datos**: Asegúrate de que el servicio MySQL esté corriendo
2. **Error 500 al subir archivos**: Verifica que el tamaño del archivo no exceda MAX_FILE_SIZE
3. **Problemas con Google Drive**: Verifica que las credenciales OAuth sean correctas y que tengas un token válido

### Verificar logs:

```bash
# Ver logs de todos los servicios
docker-compose logs

# Ver logs de un servicio específico
docker-compose logs web
docker-compose logs db
docker-compose logs nginx
```

## Personalización

### Cambiar puertos

Si necesitas usar puertos diferentes, edita el archivo `docker-compose.yml`:

```yaml
ports:
  - "8080:80"    # Cambiar puerto de Nginx
  - "3307:3306"  # Cambiar puerto de MySQL
```

### Ajustar recursos

Puedes limitar el uso de CPU y memoria en el `docker-compose.yml`:

```yaml
web:
  # ... otras configuraciones
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
```

¡Tu aplicación está lista para ser desplegada con Docker!