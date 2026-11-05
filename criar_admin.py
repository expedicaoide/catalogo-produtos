
import sqlite3
from getpass import getpass
from werkzeug.security import generate_password_hash


def criar_admin():
    nome = input("Digite o nome do administrador: ").strip()

    if not nome:
        print("O nome não pode ficar vazio.")
        return

    senha = getpass("Digite a senha do administrador: ")
    confirmar = getpass("Confirme a senha: ")

    if len(senha) < 8:
        print("A senha precisa ter pelo menos 8 caracteres.")
        return

    if senha != confirmar:
        print("As senhas não coincidem.")
        return

    conn = sqlite3.connect("database.db")

    try:
        existente = conn.execute(
            "SELECT id FROM usuario WHERE nome = ?",
            (nome,)
        ).fetchone()

        if existente:
            print("Já existe um usuário com esse nome.")
            return

        senha_hash = generate_password_hash(senha)

        conn.execute(
            "INSERT INTO usuario (nome, senha, ativo) VALUES (?, ?, ?)",
            (nome, senha_hash, 1)
        )

        conn.commit()
        print("Administrador criado com sucesso!")

    except sqlite3.Error as erro:
        print(f"Erro ao criar administrador: {erro}")

    finally:
        conn.close()


if __name__ == "__main__":
    criar_admin()
