# main.py
# link do vídeo no youtube: https://youtu.be/XH0-Ofzz9YE?feature=shared
"""
Menu principal do mini-projeto:
1 - Scraper de Notícias (salva em manchetes.json)
2 - Bot Instagram (salva em bio.json) - automático no perfil padrão definido no insta_bot.py
0 - Sair
"""

import subprocess
import sys

def run_scraper():
    subprocess.run([sys.executable, "news_scraper.py"])

def run_instabot():
    subprocess.run([sys.executable, "insta_bot.py"])

def main():
    while True:
        print("\n===== MENU PRINCIPAL =====")
        print("1 - Scraper de Notícias")
        print("2 - Bot2 Instagram (automático no perfil padrão)")
        print("0 - Sair")
        choice = input("Escolha uma opção: ").strip()
        if choice == "1":
            run_scraper()
        elif choice == "2":
            run_instabot()
        elif choice == "0":
            print("Saindo... até logo!")
            break
        else:
            print("Opção inválida, tente novamente.")

if __name__ == "__main__":
    main()