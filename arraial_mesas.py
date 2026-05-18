from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # Permite que o HTML acesse o Python

print("TESTE: O Python começou a ler o arquivo!")
DB_NAME = "arraial.db"

def conectar_banco():
    """
    Estabelece uma conexão com o banco de dados SQLite.
    Configura o row_factory para retornar os dados como dicionários (chave: valor),
    o que facilita a conversão para JSON na hora de enviar para o site.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  
    return conn

def iniciar_banco():
    """
    Cria a tabela 'mesas' se ela ainda não existir no banco de dados.
    Caso a tabela esteja totalmente vazia, insere automaticamente 
    60 mesas iniciais com o status padrão 'livre'.
    """
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mesas (
            id INTEGER PRIMARY KEY,
            status TEXT DEFAULT 'livre',
            nome_cliente TEXT,
            telefone TEXT,
            forma_pagamento TEXT
        )
    ''')
    
    # Verifica se já existem mesas cadastradas
    cursor.execute("SELECT COUNT(*) FROM mesas")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 61):
            cursor.execute("INSERT INTO mesas (id, status) VALUES (?, 'livre')", (i,))
        conn.commit()
    conn.close()

# ROTA 1: Listar todas as mesas
@app.route('/mesas', methods=['GET'])
def listar_mesas():
    """
    Rota acessada via método GET.
    Busca todas as mesas do banco de dados e as retorna em formato JSON.
    O site usará essa rota para saber quais mesas pintar de verde ou vermelho.
    """
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mesas")
    mesas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(mesas)

# ROTA 2: Reservar uma mesa
@app.route('/reservar/<int:mesa_id>', methods=['POST'])
def reservar_mesa(mesa_id):
    """
    Rota acessada via método POST quando o usuário escolhe uma mesa e clica em reservar.
    Recebe os dados do cliente (nome, telefone, forma de pagamento) via JSON.
    Altera o status da mesa para 'pendente_pix' ou 'pendente_dinheiro'.
    Bloqueia a mesa para evitar que duas pessoas escolham a mesma ao mesmo tempo.
    """
    dados = request.json
    nome = dados.get('nome')
    telefone = dados.get('telefone')
    forma_pagto = dados.get('forma_pagamento') 
    
    # Define o status provisório com base na escolha do usuário
    novo_status = "pendente_pix" if forma_pagto == "pix" else "pendente_dinheiro"

    conn = conectar_banco()
    cursor = conn.cursor()
    
    # Verifica na hora se a mesa ainda está livre de verdade no banco
    cursor.execute("SELECT status FROM mesas WHERE id = ?", (mesa_id,))
    mesa = cursor.fetchone()
    
    if mesa and mesa['status'] == 'livre':
        cursor.execute('''
            UPDATE mesas 
            SET status = ?, nome_cliente = ?, telefone = ?, forma_pagamento = ?
            WHERE id = ?
        ''', (novo_status, nome, telefone, forma_pagto, mesa_id))
        conn.commit()
        conn.close()
        return jsonify({"sucesso": True, "status": novo_status})
    
    conn.close()
    return jsonify({"sucesso": False, "mensagem": "Mesa já ocupada ou reservada!"}), 400

# ROTA 3: Confirmar Pagamento (Para o Administrador)
@app.route('/admin/confirmar/<int:mesa_id>', methods=['POST'])
def confirmar_pagamento(mesa_id):
    """
    Rota exclusiva do Administrador/Coordenador.
    Muda o status da mesa permanentemente para 'ocupada' assim que o pagamento 
    em dinheiro ou pix for validado manualmente.
    """
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("UPDATE mesas SET status = 'ocupada' WHERE id = ?", (mesa_id,))
    conn.commit()
    conn.close()
    return jsonify({"sucesso": True})

# ROTA 4: Liberar/Cancelar Mesa (Para o Administrador)
@app.route('/admin/liberar/<int:mesa_id>', methods=['POST'])
def liberar_mesa(mesa_id):
    """
    Rota exclusiva do Administrador/Coordenador.
    Limpa os dados do cliente e devolve o status da mesa para 'livre'.
    Útil caso alguém desista ou não apareça para pagar em dinheiro.
    """
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("UPDATE mesas SET status = 'livre', nome_cliente = NULL, telefone = NULL, forma_pagamento = NULL WHERE id = ?", (mesa_id,))
    conn.commit()
    conn.close()
    return jsonify({"sucesso": True})

# ==========================================================
# AS LINHAS ABAIXO ESTAVAM FALTANDO NO SEU ARQUIVO:
# ==========================================================
if __name__ == '__main__':
    iniciar_banco()  # Cria o arquivo arraial.db com as 60 mesas
    print("Servidor rodando com sucesso!")
    app.run(debug=True)  # Mantém o servidor ligado ouvindo o HTML