import os
import sqlite3
import base64
from functools import wraps

from flask import (
    Flask, render_template, redirect, request,
    url_for, session, flash
)
from werkzeug.security import check_password_hash

app = Flask(__name__)

# Chave de segurança
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "Defina a variável de ambiente FLASK_SECRET_KEY antes de iniciar o app."
    )


# =========================================================
# BANCO DE DADOS E MIGRAÇÃO AUTOMÁTICA
# =========================================================

def conexao():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def valor_ativo(valor):
    return 1 if valor in ("on", "1", "True", "true", "sim") else 0


def preparar_banco():
    """
    Acrescenta os campos específicos de motocicletas.
    Preserva os dados já existentes.
    """

    conn = conexao()

    try:
        colunas_existentes = {
            coluna["name"]
            for coluna in conn.execute(
                "PRAGMA table_info(produto)"
            ).fetchall()
        }

        novas_colunas = {
            "marca": "TEXT",
            "modelo": "TEXT",
            "ano": "TEXT",
            "cilindrada": "TEXT",
            "quilometragem": "TEXT",
            "cor": "TEXT",
            "cambio": "TEXT",
            "combustivel": "TEXT",
            "estado_conservacao": "TEXT",
            "descricao": "TEXT",
            "telefone_whatsapp": "TEXT",
        }

        for nome_coluna, tipo in novas_colunas.items():
            if nome_coluna not in colunas_existentes:
                conn.execute(
                    f"ALTER TABLE produto ADD COLUMN {nome_coluna} {tipo}"
                )

        conn.commit()

    finally:
        conn.close()


def administrador_logado(funcao):

    @wraps(funcao)
    def verificar_acesso(*args, **kwargs):

        if "usuario_id" not in session:
            flash(
                "Faça login para acessar a área administrativa.",
                "warning"
            )
            return redirect(url_for("login"))

        return funcao(*args, **kwargs)

    return verificar_acesso


def dados_moto_do_formulario():

    return {
        "marca": request.form.get("marca", "").strip(),
        "modelo": request.form.get("modelo", "").strip(),
        "ano": request.form.get("ano", "").strip(),
        "cilindrada": request.form.get("cilindrada", "").strip(),
        "quilometragem": request.form.get("quilometragem", "").strip(),
        "cor": request.form.get("cor", "").strip(),
        "cambio": request.form.get("cambio", "").strip(),
        "combustivel": request.form.get("combustivel", "").strip(),
        "estado_conservacao": request.form.get(
            "estado_conservacao", ""
        ).strip(),
        "descricao": request.form.get("descricao", "").strip(),
        "telefone_whatsapp": request.form.get(
            "telefone_whatsapp", ""
        ).strip(),
    }


def imagem_em_base64(arquivo):

    if arquivo and arquivo.filename:
        return base64.b64encode(
            arquivo.read()
        ).decode("utf-8")

    return None


# =========================================================
# LOGIN E LOGOUT
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()
        senha = request.form.get("senha", "")

        conn = conexao()

        try:
            usuario = conn.execute(
                """
                SELECT id, nome, senha, ativo
                FROM usuario
                WHERE nome = ?
                """,
                (nome,)
            ).fetchone()

        finally:
            conn.close()

        if (
            usuario
            and str(usuario["ativo"]).lower() in ("1", "true", "on")
            and check_password_hash(usuario["senha"], senha)
        ):

            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]

            flash(
                "Login realizado com sucesso!",
                "success"
            )

            return redirect(url_for("dashboard"))

        flash(
            "Nome ou senha inválidos, ou usuário inativo.",
            "danger"
        )

    return render_template("admin/login.html")


@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    flash("Você saiu do sistema.", "info")

    return redirect(url_for("login"))


# =========================================================
# INÍCIO PÚBLICO
# =========================================================

@app.route("/")
def index():

    return render_template("inicio.html")


# =========================================================
# CADASTRAR CATEGORIAS
# =========================================================

@app.route("/cadastrar_categorias", methods=["GET", "POST"])
@administrador_logado
def cadastrarCategoria():

    if request.method == "POST":

        nome = request.form.get(
            "nome_categoria", ""
        ).strip()

        descricao = request.form.get(
            "descricao", ""
        ).strip()

        ativo = valor_ativo(
            request.form.get("ativo")
        )

        imagem_base64 = imagem_em_base64(
            request.files.get("imagem")
        )

        if not nome or not descricao:

            flash(
                "Preencha o nome e a descrição da categoria.",
                "warning"
            )

        else:

            conn = conexao()

            try:

                conn.execute(
                    """
                    INSERT INTO categoria
                        (nome, descricao, ativo, imagem)
                    VALUES (?, ?, ?, ?)
                    """,
                    (nome, descricao, ativo, imagem_base64)
                )

                conn.commit()

                flash(
                    "Categoria cadastrada com sucesso!",
                    "success"
                )

                return redirect(
                    url_for("listarCategoria")
                )

            finally:
                conn.close()

    return render_template(
        "admin/cadastrar_categoria.html"
    )


# =========================================================
# LISTAGEM DE CATEGORIAS
# =========================================================

@app.route("/listar_categorias")
@administrador_logado
def listarCategoria():

    por_pagina = 10

    try:
        pagina = max(
            1,
            int(request.args.get("pagina", 1))
        )

    except (TypeError, ValueError):
        pagina = 1

    conn = conexao()

    try:

        total_categorias = conn.execute(
            "SELECT COUNT(*) FROM categoria"
        ).fetchone()[0]

        total_paginas = max(
            1,
            (total_categorias + por_pagina - 1) // por_pagina
        )

        pagina = min(pagina, total_paginas)

        offset = (pagina - 1) * por_pagina

        categorias = conn.execute(
            """
            SELECT *
            FROM categoria
            ORDER BY id
            LIMIT ? OFFSET ?
            """,
            (por_pagina, offset)
        ).fetchall()

    finally:
        conn.close()

    return render_template(
        "admin/listar_categoria.html",
        categorias=categorias,
        pagina=pagina,
        total_paginas=total_paginas,
        total_categorias=total_categorias
    )


# =========================================================
# EDITAR CATEGORIA
# =========================================================

@app.route("/editar_categoria/<int:id>", methods=["GET", "POST"])
@administrador_logado
def editarCategoria(id):

    conn = conexao()

    try:

        categoria = conn.execute(
            "SELECT * FROM categoria WHERE id = ?",
            (id,)
        ).fetchone()

        if categoria is None:

            flash(
                "Categoria não encontrada.",
                "warning"
            )

            return redirect(
                url_for("listarCategoria")
            )

        if request.method == "POST":

            nome = request.form.get(
                "nome_categoria", ""
            ).strip()

            descricao = request.form.get(
                "descricao", ""
            ).strip()

            ativo = valor_ativo(
                request.form.get("ativo")
            )

            imagem_base64 = categoria["imagem"]

            nova_imagem = imagem_em_base64(
                request.files.get("imagem")
            )

            if nova_imagem:
                imagem_base64 = nova_imagem

            if not nome or not descricao:

                flash(
                    "Preencha o nome e a descrição da categoria.",
                    "warning"
                )

            else:

                conn.execute(
                    """
                    UPDATE categoria
                    SET nome = ?, descricao = ?, ativo = ?, imagem = ?
                    WHERE id = ?
                    """,
                    (
                        nome,
                        descricao,
                        ativo,
                        imagem_base64,
                        id
                    )
                )

                conn.commit()

                flash(
                    "Categoria atualizada com sucesso!",
                    "success"
                )

                return redirect(
                    url_for("listarCategoria")
                )

        return render_template(
            "admin/editar_categoria.html",
            categoria=categoria
        )

    finally:
        conn.close()


# =========================================================
# EXCLUIR CATEGORIA
# =========================================================

@app.route("/excluir_categoria/<int:id>", methods=["POST"])
@administrador_logado
def excluirCategoria(id):

    conn = conexao()

    try:

        categoria = conn.execute(
            "SELECT id FROM categoria WHERE id = ?",
            (id,)
        ).fetchone()

        if categoria is None:

            flash(
                "Categoria não encontrada.",
                "warning"
            )

            return redirect(
                url_for("listarCategoria")
            )

        quantidade = conn.execute(
            """
            SELECT COUNT(*)
            FROM produto
            WHERE id_categoria = ?
            """,
            (id,)
        ).fetchone()[0]

        if quantidade:

            flash(
                "Não é possível excluir esta categoria porque existem "
                "motocicletas vinculadas a ela. Altere a categoria ou "
                "exclua os anúncios vinculados primeiro.",
                "warning"
            )

            return redirect(
                url_for("listarCategoria")
            )

        conn.execute(
            "DELETE FROM categoria WHERE id = ?",
            (id,)
        )

        conn.commit()

        flash(
            "Categoria excluída com sucesso!",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        url_for("listarCategoria")
    )


# =========================================================
# LISTAGEM ADMINISTRATIVA DE MOTOCICLETAS
# =========================================================

@app.route("/listar_produtos")
@administrador_logado
def listarProdutos():

    por_pagina = 10

    busca = request.args.get(
        "busca", ""
    ).strip()

    categoria_selecionada = request.args.get(
        "categoria", ""
    ).strip()

    status_selecionado = request.args.get(
        "status", ""
    ).strip()

    try:
        pagina = max(
            1,
            int(request.args.get("pagina", 1))
        )

    except (TypeError, ValueError):
        pagina = 1

    conn = conexao()

    try:

        categorias = conn.execute(
            """
            SELECT id, nome
            FROM categoria
            ORDER BY nome
            """
        ).fetchall()

        condicoes = []
        parametros = []

        if busca:

            condicoes.append(
                """
                (
                    produto.nome LIKE ?
                    OR produto.marca LIKE ?
                    OR produto.modelo LIKE ?
                )
                """
            )

            termo = f"%{busca}%"

            parametros.extend([
                termo,
                termo,
                termo
            ])

        if categoria_selecionada:

            try:

                condicoes.append(
                    "produto.id_categoria = ?"
                )

                parametros.append(
                    int(categoria_selecionada)
                )

            except ValueError:
                categoria_selecionada = ""

        if status_selecionado == "ativo":

            condicoes.append(
                "produto.ativo = 1"
            )

        elif status_selecionado == "inativo":

            condicoes.append(
                "(produto.ativo = 0 OR produto.ativo IS NULL)"
            )

        where_sql = ""

        if condicoes:

            where_sql = (
                "WHERE " + " AND ".join(condicoes)
            )

        total_produtos = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM produto
            {where_sql}
            """,
            parametros
        ).fetchone()[0]

        total_paginas = max(
            1,
            (total_produtos + por_pagina - 1) // por_pagina
        )

        pagina = min(pagina, total_paginas)

        offset = (pagina - 1) * por_pagina

        produtos = conn.execute(
            f"""
            SELECT
                produto.*,
                categoria.nome AS nome_categoria
            FROM produto

            LEFT JOIN categoria
                ON produto.id_categoria = categoria.id

            {where_sql}

            ORDER BY produto.nome

            LIMIT ? OFFSET ?
            """,
            parametros + [
                por_pagina,
                offset
            ]
        ).fetchall()

    finally:
        conn.close()

    return render_template(
        "admin/listar_produtos.html",
        produtos=produtos,
        pagina=pagina,
        total_paginas=total_paginas,
        total_produtos=total_produtos,
        categorias=categorias,
        busca=busca,
        categoria_selecionada=categoria_selecionada,
        status_selecionado=status_selecionado
    )


# =========================================================
# CATÁLOGO PÚBLICO - CATEGORIAS
# =========================================================

@app.route("/catalogo")
def catalogoPublico():

    conn = conexao()

    try:

        categorias = conn.execute(
            """
            SELECT id, nome, descricao, imagem
            FROM categoria

            WHERE (
                ativo = 1
                OR LOWER(CAST(ativo AS TEXT)) IN ('true', 'on')
            )

            ORDER BY nome
            """
        ).fetchall()

    finally:
        conn.close()

    return render_template(
        "categorias_publicas.html",
        categorias=categorias
    )


# =========================================================
# CATÁLOGO PÚBLICO - MOTOCICLETAS DA CATEGORIA
# =========================================================

@app.route("/catalogo/categoria/<int:categoria_id>")
def produtosDaCategoria(categoria_id):

    conn = conexao()

    try:

        categoria = conn.execute(
            """
            SELECT id, nome, descricao, imagem
            FROM categoria

            WHERE id = ?

            AND (
                ativo = 1
                OR LOWER(CAST(ativo AS TEXT)) IN ('true', 'on')
            )
            """,
            (categoria_id,)
        ).fetchone()

        if categoria is None:

            flash(
                "Categoria não encontrada ou inativa.",
                "warning"
            )

            return redirect(
                url_for("catalogoPublico")
            )

        produtos = conn.execute(
            """
            SELECT *
            FROM produto

            WHERE id_categoria = ?

            AND (
                ativo = 1
                OR LOWER(CAST(ativo AS TEXT)) IN ('true', 'on')
            )

            ORDER BY nome
            """,
            (categoria_id,)
        ).fetchall()

    finally:
        conn.close()

    return render_template(
        "catalogo.html",
        produtos=produtos,
        categoria=categoria
    )


# =========================================================
# CADASTRAR MOTOCICLETA
# =========================================================

@app.route("/cadastrar_produtos", methods=["GET", "POST"])
@administrador_logado
def cadastrarProduto():

    conn = conexao()

    try:

        categorias = conn.execute(
            """
            SELECT *
            FROM categoria
            ORDER BY nome
            """
        ).fetchall()

        if request.method == "POST":

            nome = request.form.get(
                "nome", ""
            ).strip()

            preco = request.form.get(
                "preco", ""
            ).strip()

            ativo = valor_ativo(
                request.form.get("ativo")
            )

            id_categoria = (
                request.form.get("id_categoria") or None
            )

            imagem_base64 = imagem_em_base64(
                request.files.get("imagem")
            )

            moto = dados_moto_do_formulario()

            if not nome or not preco:

                flash(
                    "Preencha o nome/modelo e o preço da motocicleta.",
                    "warning"
                )

            else:

                try:

                    preco_numero = float(
                        preco.replace("R$", "")
                        .replace(".", "")
                        .replace(",", ".")
                        .strip()
                    )

                    conn.execute(
                        """
                        INSERT INTO produto (
                            nome,
                            preco,
                            ativo,
                            imagem,
                            id_categoria,
                            marca,
                            modelo,
                            ano,
                            cilindrada,
                            quilometragem,
                            cor,
                            cambio,
                            combustivel,
                            estado_conservacao,
                            descricao,
                            telefone_whatsapp
                        )

                        VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?
                        )
                        """,
                        (
                            nome,
                            preco_numero,
                            ativo,
                            imagem_base64,
                            id_categoria,
                            moto["marca"],
                            moto["modelo"],
                            moto["ano"],
                            moto["cilindrada"],
                            moto["quilometragem"],
                            moto["cor"],
                            moto["cambio"],
                            moto["combustivel"],
                            moto["estado_conservacao"],
                            moto["descricao"],
                            moto["telefone_whatsapp"]
                        )
                    )

                    conn.commit()

                    flash(
                        "Motocicleta cadastrada com sucesso!",
                        "success"
                    )

                    return redirect(
                        url_for("listarProdutos")
                    )

                except ValueError:

                    flash(
                        "Informe um preço válido.",
                        "danger"
                    )

        return render_template(
            "admin/cadastrar_produto.html",
            categorias=categorias
        )

    finally:
        conn.close()


# =========================================================
# EDITAR MOTOCICLETA
# =========================================================

@app.route("/editarproduto/<int:id>", methods=["GET", "POST"])
@administrador_logado
def editarProduto(id):

    conn = conexao()

    try:

        produto = conn.execute(
            """
            SELECT *
            FROM produto
            WHERE id = ?
            """,
            (id,)
        ).fetchone()

        if produto is None:

            flash(
                "Motocicleta não encontrada.",
                "warning"
            )

            return redirect(
                url_for("listarProdutos")
            )

        categorias = conn.execute(
            """
            SELECT *
            FROM categoria
            ORDER BY nome
            """
        ).fetchall()

        if request.method == "POST":

            nome = request.form.get(
                "nome", ""
            ).strip()

            preco = request.form.get(
                "preco", ""
            ).strip()

            ativo = valor_ativo(
                request.form.get("ativo")
            )

            id_categoria = (
                request.form.get("id_categoria") or None
            )

            moto = dados_moto_do_formulario()

            if not nome or not preco:

                flash(
                    "Preencha o nome/modelo e o preço da motocicleta.",
                    "warning"
                )

            else:

                try:

                    preco_numero = float(
                        preco.replace("R$", "")
                        .replace(".", "")
                        .replace(",", ".")
                        .strip()
                    )

                    imagem_base64 = produto["imagem"]

                    nova_imagem = imagem_em_base64(
                        request.files.get("imagem")
                    )

                    if nova_imagem:
                        imagem_base64 = nova_imagem

                    conn.execute(
                        """
                        UPDATE produto

                        SET
                            nome = ?,
                            preco = ?,
                            ativo = ?,
                            imagem = ?,
                            id_categoria = ?,
                            marca = ?,
                            modelo = ?,
                            ano = ?,
                            cilindrada = ?,
                            quilometragem = ?,
                            cor = ?,
                            cambio = ?,
                            combustivel = ?,
                            estado_conservacao = ?,
                            descricao = ?,
                            telefone_whatsapp = ?

                        WHERE id = ?
                        """,
                        (
                            nome,
                            preco_numero,
                            ativo,
                            imagem_base64,
                            id_categoria,
                            moto["marca"],
                            moto["modelo"],
                            moto["ano"],
                            moto["cilindrada"],
                            moto["quilometragem"],
                            moto["cor"],
                            moto["cambio"],
                            moto["combustivel"],
                            moto["estado_conservacao"],
                            moto["descricao"],
                            moto["telefone_whatsapp"],
                            id
                        )
                    )

                    conn.commit()

                    flash(
                        "Motocicleta atualizada com sucesso!",
                        "success"
                    )

                    return redirect(
                        url_for("listarProdutos")
                    )

                except ValueError:

                    flash(
                        "Informe um preço válido.",
                        "danger"
                    )

        return render_template(
            "admin/editar_produto.html",
            produto=produto,
            categorias=categorias
        )

    finally:
        conn.close()


# =========================================================
# EXCLUIR MOTOCICLETA
# =========================================================

@app.route("/excluirproduto/<int:id>", methods=["POST"])
@administrador_logado
def excluirProduto(id):

    conn = conexao()

    try:

        conn.execute(
            """
            DELETE FROM produto
            WHERE id = ?
            """,
            (id,)
        )

        conn.commit()

        flash(
            "Anúncio da motocicleta excluído.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        url_for("listarProdutos")
    )


# =========================================================
# DASHBOARD ADMINISTRATIVO
# =========================================================

@app.route("/dashboard")
@administrador_logado
def dashboard():

    return render_template(
        "admin/dashboard.html"
    )


# =========================================================
# EXECUTAR A APLICAÇÃO
# =========================================================

if __name__ == "__main__":

    preparar_banco()

    app.run(
        debug=True,
        port=5005
    )