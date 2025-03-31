import subprocess
import sys
import os

# Caminho para o executável Python
python_path = sys.executable

# Caminho para o módulo streamlit (pode variar dependendo do ambiente)
streamlit_path = os.path.join(os.path.dirname(python_path), 'streamlit')

try:
    # Tenta executar o streamlit com o app.py
    result = subprocess.run(
        [python_path, '-m', 'streamlit', 'run', 'app.py', 
         '--server.port=5000', '--server.headless=true', '--server.address=0.0.0.0'],
        check=True
    )
    print(f"Aplicação finalizada com código: {result.returncode}")
except subprocess.CalledProcessError as e:
    print(f"Erro ao iniciar a aplicação: {e}")
except FileNotFoundError:
    print(f"Streamlit não encontrado no caminho: {streamlit_path}")
    print("Tente instalar o Streamlit com: pip install streamlit")