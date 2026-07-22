"""
Orquestra e executa as etapas em sequência
1. bronze_ingest.py
2. silver_transform.py
3. gold_build.py

Cada etapa só começa quando a anterior termina.
"""

import subprocess
import sys

def run_step(script_name):
    print(f"\n==============================")
    print(f" INICIANDO: {script_name}")
    print(f"==============================\n")

    result = subprocess.run([sys.executable, script_name])

    if result.returncode != 0:
        print(f"\n ERRO ao executar {script_name}. Pipeline interrompido.")
        sys.exit(result.returncode)

    print(f"\n FINALIZADO: {script_name}\n")


if __name__ == "__main__":
    print("\n======================================")
    print("      PIPELINE      ")
    print("  Bronze → Silver → Gold )")
    print("======================================\n")

    run_step("bronze_ingest.py")
    run_step("silver_transform.py")
    run_step("gold_build.py")

    print("\n======================================")
    print("   PIPELINE CONCLUÍDO COM SUCESSO!")
    print("======================================\n")
