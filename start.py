from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


BASE_DIR = Path(__file__).resolve().parent
API_HOST = "127.0.0.1"
API_PORT_START = 8000
API_PORT_LIMIT = 8100
FRONTEND_DIR = BASE_DIR / "Front-end"
VITE_ENTRY = FRONTEND_DIR / "node_modules" / "vite" / "bin" / "vite.js"
API_STARTUP_TIMEOUT = 60


def escolher_porta_api() -> int:
    for porta in range(API_PORT_START, API_PORT_LIMIT):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sonda:
            try:
                sonda.bind((API_HOST, porta))
            except OSError:
                continue
            return porta
    raise OSError(
        f"Nenhuma porta disponível entre {API_PORT_START} e {API_PORT_LIMIT - 1}."
    )


def aguardar_servico(
    processo: subprocess.Popen[bytes],
    url: str,
    nome: str,
) -> None:
    prazo = time.monotonic() + API_STARTUP_TIMEOUT
    while time.monotonic() < prazo:
        codigo_saida = processo.poll()
        if codigo_saida is not None:
            raise RuntimeError(
                f"{nome} encerrou durante a inicialização (código {codigo_saida})."
            )

        try:
            with urlopen(url, timeout=1) as resposta:
                if resposta.status == 200:
                    return
        except URLError:
            time.sleep(0.5)

    raise TimeoutError(
        f"{nome} não ficou disponível em {url} dentro de "
        f"{API_STARTUP_TIMEOUT} segundos."
    )


def encerrar_processos(
    processos: list[tuple[str, subprocess.Popen[bytes]]],
) -> None:
    for _, processo in reversed(processos):
        if processo.poll() is None:
            processo.terminate()

    for nome, processo in reversed(processos):
        if processo.poll() is None:
            try:
                processo.wait(timeout=5)
            except subprocess.TimeoutExpired:
                processo.kill()
                processo.wait()


def main() -> None:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js não encontrado. Instale Node.js para iniciar a interface.")
    if not VITE_ENTRY.is_file():
        raise RuntimeError(
            "Dependências do front-end não encontradas. Execute "
            "'npm install' na pasta Front-end antes de iniciar o programa."
        )

    api_port = escolher_porta_api()
    api_url = f"http://{API_HOST}:{api_port}"
    processos: list[tuple[str, subprocess.Popen[bytes]]] = []
    try:
        print("Iniciando a API...", flush=True)
        api = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "api.main:app",
                "--host",
                API_HOST,
                "--port",
                str(api_port),
            ],
            cwd=BASE_DIR,
        )
        processos.append(("API", api))
        aguardar_servico(api, f"{api_url}/health", "API")

        print("Iniciando a interface...", flush=True)
        frontend_env = os.environ.copy()
        frontend_env["VITE_API_URL"] = api_url
        interface = subprocess.Popen(
            [
                node,
                str(VITE_ENTRY),
                "--host",
                "127.0.0.1",
                "--port",
                "5173",
                "--strictPort",
            ],
            cwd=FRONTEND_DIR,
            env=frontend_env,
        )
        processos.append(("Interface", interface))
        aguardar_servico(interface, "http://127.0.0.1:5173", "Interface")

        print("CreditRisk AI iniciado.", flush=True)
        print("Interface: http://127.0.0.1:5173", flush=True)
        print(f"Documentação da API: {api_url}/docs", flush=True)

        while True:
            for nome, processo in processos:
                codigo_saida = processo.poll()
                if codigo_saida is not None:
                    raise RuntimeError(
                        f"{nome} encerrou inesperadamente (código {codigo_saida})."
                    )
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nEncerrando o CreditRisk AI...", flush=True)
    finally:
        encerrar_processos(processos)


if __name__ == "__main__":
    main()
