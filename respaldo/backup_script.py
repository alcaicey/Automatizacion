import os
import shutil

# --- Configuración ---
CODE_EXTENSIONS = ['.py', '.js', '.html', '.css', '.mjs', '.yml', '.json', '.ini', '.md', '.svg']
SOURCE_ROOT = '.'
DOCS_FOLDER = 'src/docs'
DEST_DIR = 'respaldo'
# Excluir directorios que no son parte del código fuente
EXCLUDE_DIRS = ['venv', '__pycache__', 'node_modules', '.git', '.idea', '.vscode', 'respaldo', 'logs_bolsa']
# Añadir explícitamente algunos archivos importantes de la raíz
ROOT_FILES_TO_COPY = ['Dockerfile', 'requirements.txt', 'requirementsTest.txt']

def create_backup():
    """Encuentra todos los archivos de código/documentación y los copia a la carpeta de respaldo sin estructura de carpetas."""
    if os.path.exists(DEST_DIR):
        print(f"El directorio '{DEST_DIR}' ya existe. Limpiándolo...")
        shutil.rmtree(DEST_DIR)
    os.makedirs(DEST_DIR)
    print(f"Directorio '{DEST_DIR}' creado.")

    copied_files_count = 0
    copied_filenames = set()

    # 1. Copiar todos los archivos de código del proyecto
    for root, dirs, files in os.walk(SOURCE_ROOT, topdown=True):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            source_path = os.path.join(root, file)
            if any(file.endswith(ext) for ext in CODE_EXTENSIONS) or file in ROOT_FILES_TO_COPY:
                dest_path = os.path.join(DEST_DIR, file)
                
                if file in copied_filenames:
                    print(f"Advertencia: Nombre de archivo duplicado, se omitirá la copia de '{source_path}'")
                    continue
                
                try:
                    shutil.copy2(source_path, dest_path)
                    copied_files_count += 1
                    copied_filenames.add(file)
                except Exception as e:
                    print(f"Error al copiar {source_path}: {e}")

    # 2. Copiar todos los archivos de la carpeta de documentación
    if os.path.isdir(DOCS_FOLDER):
        for file in os.listdir(DOCS_FOLDER):
            source_path = os.path.join(DOCS_FOLDER, file)
            if os.path.isfile(source_path):
                dest_path = os.path.join(DEST_DIR, file)
                
                if file in copied_filenames:
                    print(f"Advertencia: Nombre de archivo duplicado de la carpeta docs, se omitirá la copia de '{source_path}'")
                    continue

                try:
                    shutil.copy2(source_path, dest_path)
                    copied_files_count += 1
                    copied_filenames.add(file)
                except Exception as e:
                    print(f"Error al copiar {source_path}: {e}")

    print(f"\nRespaldo completado. Se copiaron {copied_files_count} archivos a la carpeta '{DEST_DIR}'.")

if __name__ == "__main__":
    create_backup() 