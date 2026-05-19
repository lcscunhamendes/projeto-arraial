from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

DB_NAME = "arraial.db"
SENHA_ADMIN = "arraial2026"  # Pode trocar para a senha que quiser

# Pasta atual onde estão os arquivos HTML
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def conectar_banco():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  
    return conn

def iniciar_banco():
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
    cursor.execute("SELECT COUNT(*) FROM mesas")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 61):
            cursor.execute("INSERT INTO mesas (id, status) VALUES (?, 'livre')", (i,))
        conn.commit()
    conn.close()

# --- ROTAS PARA SERVIR O FRONT-END (HTML, CSS, IMAGENS) ---
@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory(BASE_DIR, 'admin.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(BASE_DIR, filename)
# ----------------------------------------------------------

@app.route('/mesas', methods=['GET'])
def listar_mesas():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mesas")
    mesas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(mesas)

@app.route('/reservar/<int:mesa_id>', methods=['POST'])
def reservar_mesa(mesa_id):
    dados = request.json
    nome = dados.get('nome')
    telefone = dados.get('telefone')
    forma_pagto = dados.get('forma_pagamento') 
    
    conn = conectar_banco()
    cursor = conn.cursor()
    
    cursor.execute("SELECT status FROM mesas WHERE id = ?", (mesa_id,))
    mesa = cursor.fetchone()
    
    if not mesa or mesa['status'] != 'livre':
        conn.close()
        return jsonify({"sucesso": False, "mensagem": "Mesa já ocupada ou reservada!"}), 400

    if forma_pagto == "dinheiro":
        cursor.execute('''
            UPDATE mesas SET status = 'pendente_dinheiro', nome_cliente = ?, telefone = ?, forma_pagamento = ? WHERE id = ?
        ''', (nome, telefone, forma_pagto, mesa_id))
        conn.commit()
        conn.close()
        return jsonify({"sucesso": True, "status": "pendente_dinheiro", "metodo": "dinheiro"})

    elif forma_pagto == "pix":
        cursor.execute('''
            UPDATE mesas SET status = 'pendente_pix', nome_cliente = ?, telefone = ?, forma_pagamento = ? WHERE id = ?
        ''', (nome, telefone, forma_pagto, mesa_id))
        conn.commit()
        conn.close()
        return jsonify({"sucesso": True, "status": "pendente_pix", "metodo": "pix"})

@app.route('/admin/confirmar/<int:mesa_id>', methods=['POST'])
def confirmar_pagamento(mesa_id):
    dados = request.json
    if not dados or dados.get('senha') != SENHA_ADMIN:
        return jsonify({"sucesso": False, "mensagem": "Senha Incorreta!"}), 403

    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("UPDATE mesas SET status = 'ocupada' WHERE id = ?", (mesa_id,))
    conn.commit()
    conn.close()
    return jsonify({"sucesso": True})

@app.route('/admin/liberar/<int:mesa_id>', methods=['POST'])
def liberar_mesa(mesa_id):
    dados = request.json
    if not dados or dados.get('senha') != SENHA_ADMIN:
        return jsonify({"sucesso": False, "mensagem": "Senha Incorreta!"}), 403

    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("UPDATE mesas SET status = 'livre', nome_cliente = NULL, telefone = NULL, forma_pagamento = NULL WHERE id = ?", (mesa_id,))
    conn.commit()
    conn.close()
    return jsonify({"sucesso": True})

if __name__ == '__main__':
    iniciar_banco()
    print("Servidor rodando com sucesso!")
    app.run(debug=True)