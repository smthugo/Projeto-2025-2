import sqlite3
import hashlib
import random
import os
from flask import Flask, request, redirect, url_for, render_template_string

# --- Configuração do Aplicativo ---
app = Flask(__name__)
DB_FILE = 'boletim.db'

# --- Utilitários de Segurança e Geração de Dados ---

def hash_password(password):
    """Gera o hash SHA256 da senha fornecida. Usado para persistência."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_initial_grades():
    """Gera notas aleatórias persistentes (entre 5.0 e 10.0)."""
    return {
        "Português": round(random.uniform(5.0, 10.0), 1),
        "Matemática": round(random.uniform(5.0, 10.0), 1),
        "Ciências": round(random.uniform(5.0, 10.0), 1),
        "História": round(random.uniform(5.0, 10.0), 1),
        "Geografia": round(random.uniform(5.0, 10.0), 1),
        "Inglês": round(random.uniform(5.0, 10.0), 1),
    }

def create_tables(cursor):
    """Cria as tabelas de alunos e notas no banco de dados."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            ra TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            senha_hash TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ra TEXT,
            disciplina TEXT NOT NULL,
            nota REAL NOT NULL,
            FOREIGN KEY (ra) REFERENCES alunos(ra)
        );
    """)

def insert_initial_data(cursor):
    """Insere dados de exemplo se o banco estiver vazio."""
    cursor.execute("SELECT COUNT(*) FROM alunos")
    if cursor.fetchone()[0] == 0:
        print("--- Inicializando dados de exemplo... (RAs numéricos) ---")
        
        initial_students = [
            ("123456", "senha123", "Aluno: 123456"), 
            ("987654", "aluno123", "Aluno: 987654"),
        ]

        for ra, initial_password, name in initial_students:
            hashed_pw = hash_password(initial_password)
            cursor.execute(
                "INSERT INTO alunos (ra, nome, senha_hash) VALUES (?, ?, ?)",
                (ra, name, hashed_pw)
            )

            grades = generate_initial_grades()
            for discipline, grade in grades.items():
                cursor.execute(
                    "INSERT INTO notas (ra, disciplina, nota) VALUES (?, ?, ?)",
                    (ra, discipline, grade)
                )
            print(f"Aluno {name} (RA: {ra}) criado. Senha inicial: {initial_password}")

def init_db():
    """
    Inicializa o banco de dados. Tenta criar tabelas. Se falhar por erro de
    esquema (DatabaseError), apaga o DB e tenta novamente.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        create_tables(cursor)
        insert_initial_data(cursor)
        conn.commit()
    except sqlite3.DatabaseError:
        print(f"Erro de esquema no DB. Apagando e recriando {DB_FILE}...")
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            create_tables(cursor)
            insert_initial_data(cursor)
            conn.commit()
        except sqlite3.Error as e:
            print(f"Erro ao recriar o banco de dados: {e}")
    except sqlite3.Error as e:
        print(f"Erro geral ao inicializar o banco de dados: {e}")
    finally:
        if conn:
            conn.close()

def ensure_user_data(ra, password):
    """
    1. Verifica se o aluno existe no DB. Se não, cadastra (Universal Login).
    2. Verifica se o aluno tem notas. Se não, gera notas aleatórias.
    3. Retorna o nome formatado do aluno.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    student_name = None
    hashed_pw = hash_password(password)
    ra_key = ra.strip()

    cursor.execute("SELECT nome FROM alunos WHERE ra = ?", (ra_key,))
    result = cursor.fetchone()

    if result:
        student_name = result[0]
    else:
        student_name = f"Aluno: {ra_key}" 
        
        cursor.execute(
            "INSERT INTO alunos (ra, nome, senha_hash) VALUES (?, ?, ?)",
            (ra_key, student_name, hashed_pw)
        )
        conn.commit()
        print(f"Novo aluno ({ra_key}) cadastrado automaticamente.")

    cursor.execute("SELECT COUNT(*) FROM notas WHERE ra = ?", (ra_key,))
    if cursor.fetchone()[0] == 0:
        grades = generate_initial_grades()
        for discipline, grade in grades.items():
            cursor.execute(
                "INSERT INTO notas (ra, disciplina, nota) VALUES (?, ?, ?)",
                (ra_key, discipline, grade)
            )
        conn.commit()
        print(f"Notas aleatórias geradas e salvas para o RA: {ra_key}")

    conn.close()
    return student_name

with app.app_context():
    init_db()

# --- Templates HTML e CSS (Embutidos para um Único Arquivo) ---

# CSS Moderno com tema Branco/Azul/Vermelho (Visual Acadêmico)
CSS_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');
    
    :root {
        --cor-primaria: #004D99; /* Azul Institucional */
        --cor-secundaria: #333333; 
        --cor-fundo: #FFFFFF; /* Fundo do Card (Quadro Branco) */
        --cor-fundo-externo: #F9F9F9; /* Cinza extremamente discreto */
        --cor-texto: #212529;
        --cor-sucesso: #28A745; 
        --cor-erro: #DC3545; 
        --sombra-card: 0 8px 20px rgba(0, 0, 0, 0.08); 
    }

    body {
        font-family: 'Inter', sans-serif;
        background-color: var(--cor-fundo-externo); /* Cinza discreto */
        color: var(--cor-texto);
        margin: 0;
        padding: 0;
        display: flex;
        justify-content: center;
        align-items: center; /* AGORA CENTRALIZA VERTICALMENTE */
        min-height: 100vh;
        box-sizing: border-box;
    }

    /* Novo Cabeçalho Fixo do Portal */
    .portal-header {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: var(--cor-primaria);
        color: white;
        text-align: center;
        padding: 15px 0;
        font-weight: 700;
        font-size: 1.5em;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        z-index: 1000;
    }

    .container {
        width: 90%;
        /* max-width removido para ser definido no HTML e permitir largura diferente para login e boletim */
        padding: 0; 
        box-sizing: border-box;
        margin-top: 80px; /* Garante que o conteúdo fique abaixo do header fixo */
        margin-bottom: 20px; /* Espaço para respiro */
    }

    .card {
        background-color: var(--cor-fundo);
        padding: 40px;
        border-radius: 16px; 
        box-shadow: var(--sombra-card);
        text-align: center;
        border: 1px solid #E9ECEF; 
        transition: box-shadow 0.3s ease;
    }
    
    .card:hover {
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.12);
    }
    
    /* Título H2 do Login */
    h2.login-title {
        color: var(--cor-secundaria); 
        font-weight: 700;
        margin-bottom: 25px;
        font-size: 1.8em;
        border-bottom: 2px solid #E9ECEF;
        padding-bottom: 15px;
    }

    h1 {
        display: none; 
    }
    
    label {
        display: block;
        text-align: left;
        font-weight: 600;
        margin-top: 15px;
        margin-bottom: 5px;
        color: var(--cor-secundaria);
    }

    /* Formulários e Botões */
    input[type="text"], input[type="password"] {
        width: 100%;
        padding: 14px;
        margin: 5px 0 20px 0;
        border: 1px solid #ced4da;
        border-radius: 8px;
        box-sizing: border-box;
        font-size: 1em;
        transition: border-color 0.3s, box-shadow 0.3s;
    }

    input[type="text"]:focus, input[type="password"]:focus {
        border-color: var(--cor-primaria);
        outline: none;
        box-shadow: 0 0 0 4px rgba(0, 77, 153, 0.2); 
    }

    button {
        background-color: var(--cor-primaria);
        color: white;
        padding: 15px 25px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-size: 1.1em;
        font-weight: 700;
        transition: background-color 0.3s, transform 0.1s;
        width: 100%;
        margin-top: 20px;
    }

    button:hover {
        background-color: #003366;
    }
    
    .error-message {
        color: var(--cor-erro);
        margin-top: 15px;
        font-weight: 600;
    }
    
    /* Resultados - Específico (Boletim) */
    .header-results {
        background: linear-gradient(135deg, var(--cor-primaria), #007BFF); 
        color: white;
        padding: 30px 40px;
        border-radius: 16px 16px 0 0;
        margin-bottom: 0;
        text-align: left;
        box-shadow: var(--sombra-card);
    }

    .header-results h2 {
        margin: 0;
        font-size: 1.9em;
        font-weight: 700;
    }

    .header-results p {
        margin-top: 8px;
        font-size: 1.1em;
        opacity: 0.9;
        font-weight: 400;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        text-align: left;
        background-color: var(--cor-fundo);
        border-radius: 0 0 16px 16px;
        overflow: hidden;
    }

    th, td {
        padding: 18px 40px;
        border-bottom: 1px solid #e9ecef;
    }

    th {
        background-color: #f8f9fa;
        color: var(--cor-secundaria);
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.9em;
    }
    
    tr:last-child td {
        border-bottom: none;
    }
    
    /* Cores das Notas */
    .nota-destaque {
        font-weight: 700;
        font-size: 1.1em;
    }

    .nota-aprovado {
        color: var(--cor-sucesso); 
    }

    .nota-reprovado {
        color: var(--cor-erro); 
    }
    
    .nota-media {
        background-color: rgba(255, 255, 255, 0.2);
        color: white;
        font-size: 1.2em;
        font-weight: 800;
        padding: 3px 10px;
        border-radius: 6px;
        display: inline-block;
    }
    
    .back-link {
        display: inline-block;
        margin-top: 30px;
        color: var(--cor-primaria);
        text-decoration: none;
        font-weight: 600;
        padding: 10px 20px;
        border: 2px solid var(--cor-primaria);
        border-radius: 8px;
        transition: background-color 0.3s, color 0.3s;
    }
    
    .back-link:hover {
        background-color: var(--cor-primaria);
        color: white;
    }
</style>
"""

# Template HTML da Página de Login
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Boletim Escolar</title>
""" + CSS_STYLE + """
</head>
<body>
    <!-- Novo Cabeçalho Fixo -->
    <div class="portal-header">
        PORTAL DE CONSULTA
    </div>

    <!-- O max-width: 500px garante que o quadro de login não fique muito largo, mantendo o visual centralizado -->
    <div class="container" style="max-width: 500px;"> 
        <div class="card">
            <!-- Título do quadro de login -->
            <h2 class="login-title">Faça seu Login</h2>
            
            <form method="POST">
                <label for="ra">RA (Registro Acadêmico):</label>
                <input type="text" id="ra" name="ra" placeholder="Apenas números, ex: 123456" pattern="[0-9]+" required>
                
                <label for="password">Senha:</label>
                <input type="password" id="password" name="password" placeholder="Qualquer senha" required>
                
                <button type="submit">Acessar Boletim</button>
            </form>
            
            {% if error %}
                <p class="error-message">{{ error }}</p>
            {% endif %}
            
        </div>
    </div>
</body>
</html>
"""

# Template HTML da Página de Resultados (Boletim)
RESULTS_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Boletim de Notas</title>
""" + CSS_STYLE + """
</head>
<body>
    <div class="container" style="max-width: 900px;">
        <!-- O header-results usa um gradiente sutil -->
        <div class="header-results" style="text-align: left;">
            <p style="font-size: 1em; margin-bottom: 5px;">BOLETIM ACADÊMICO - 2025</p>
            <!-- student_name já vem formatado como "Aluno: [RA]" -->
            <h2>{{ student_name }}</h2> 
            <p>RA: {{ ra }} | Média Geral: <span class="nota-media">{{ avg_grade|round(2) }}</span></p>
        </div>
        
        <div class="card" style="padding: 0; text-align: left; border-radius: 0 0 16px 16px; border-top: none;">
            <table>
                <thead>
                    <tr>
                        <th>Disciplina</th>
                        <th>Nota Final</th>
                        <th>Situação</th>
                    </tr>
                </thead>
                <tbody>
                    {% for grade in grades %}
                    <tr>
                        <td>{{ grade.disciplina }}</td>
                        <!-- Aprovado se a nota for >= 7.0 -->
                        <td class="nota-destaque {{ 'nota-aprovado' if grade.nota >= 7.0 else 'nota-reprovado' }}">{{ grade.nota|round(1) }}</td>
                        <td class="{{ 'nota-aprovado' if grade.nota >= 7.0 else 'nota-reprovado' }}">{{ 'APROVADO' if grade.nota >= 7.0 else 'REPROVADO' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <a href="/" class="back-link">← Sair do Portal</a>
    </div>
</body>
</html>
"""


# --- Rotas do Flask ---

@app.route('/', methods=['GET', 'POST'])
def login():
    """Lida com a lógica de login (agora universal, apenas números) e garante o cadastro no DB."""
    error = None
    if request.method == 'POST':
        ra = request.form['ra'].strip()
        password = request.form['password']
        
        if not ra or not password:
             error = 'Preencha todos os campos.'
        # Nova validação: RA deve conter APENAS números
        elif not ra.isdigit():
            error = 'O Registro Acadêmico (RA) deve conter APENAS números.'
        else:
            try:
                # Chama a função que verifica/cria o aluno e garante as notas
                student_name = ensure_user_data(ra, password)
                if student_name:
                    # Login bem-sucedido
                    return redirect(url_for('results', ra=ra))
                else:
                    error = 'Ocorreu um erro ao processar o seu RA.'
            except sqlite3.Error as e:
                print(f"Erro de DB no login/cadastro: {e}")
                error = 'Ocorreu um erro interno no banco de dados.'
            except Exception as e:
                print(f"Erro geral: {e}")
                error = 'Ocorreu um erro interno.'

    # Renderiza o template de login com a mensagem de erro, se houver
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/results')
def results():
    """Exibe o boletim escolar do aluno logado."""
    ra = request.args.get('ra')

    if not ra:
        return redirect(url_for('login'))
        
    ra_key = ra.strip()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    student_name = f"Aluno: {ra_key}"
    grades = []
    total_grade = 0
    
    try:
        # 1. Busca o nome do aluno
        cursor.execute("SELECT nome FROM alunos WHERE ra = ?", (ra_key,))
        result = cursor.fetchone()
        if result:
            student_name = result[0]
        
        # 2. Busca todas as notas do aluno 
        cursor.execute("SELECT disciplina, nota FROM notas WHERE ra = ?", (ra_key,))
        grade_results = cursor.fetchall()
        
        for disciplina, nota in grade_results:
            grades.append({'disciplina': disciplina, 'nota': nota})
            total_grade += nota
            
        avg_grade = total_grade / len(grades) if grades else 0
        
    except sqlite3.Error as e:
        print(f"Erro de DB na busca de resultados: {e}")
        return redirect(url_for('login'))
    finally:
        conn.close()

    # Renderiza o template de resultados
    return render_template_string(
        RESULTS_HTML, 
        ra=ra_key, 
        student_name=student_name, 
        grades=grades, 
        avg_grade=avg_grade
    )

if __name__ == '__main__':
    app.run(debug=True)