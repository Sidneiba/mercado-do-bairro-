from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/data/com.termux/files/home/mamao-chat/instance/database.db'
app.secret_key = 'sua_chave_secreta_aqui'
db = SQLAlchemy(app)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    senha = db.Column(db.String(6), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    cep = db.Column(db.String(10), nullable=False)
    lojas_favoritas = db.Column(db.String(200), default="")
    bloqueados = db.Column(db.String(200), default="")

class Lojista(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    senha = db.Column(db.String(6), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    cep = db.Column(db.String(10), nullable=False)
    raio = db.Column(db.Integer, default=5)
    online = db.Column(db.Boolean, default=False)
    formas_pagamento = db.Column(db.String(200), default="Pix, Na Entrega")
    horario = db.Column(db.String(100), default="Seg-Sex: 8h-18h")
    bloqueados = db.Column(db.String(200), default="")

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    unidade = db.Column(db.String(20), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    codigo = db.Column(db.String(10), nullable=False)
    disponivel = db.Column(db.Boolean, default=True)
    preco = db.Column(db.Float, nullable=False)
    lojista_id = db.Column(db.Integer, db.ForeignKey('lojista.id'), nullable=False)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    lojista_id = db.Column(db.Integer, db.ForeignKey('lojista.id'), nullable=False)
    itens = db.Column(db.String(500), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="Aberto")
    data = db.Column(db.String(20), default="29/03/2025")

class Mensagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    lojista_id = db.Column(db.Integer, db.ForeignKey('lojista.id'))
    texto = db.Column(db.String(500), nullable=True)
    audio = db.Column(db.Boolean, default=False)
    remetente = db.Column(db.String(10), nullable=False)

@app.route('/')
def abertura():
    return render_template('abertura.html')

@app.route('/login')
def index():
    return render_template('login.html')

@app.route('/cliente', methods=['GET', 'POST'])
def cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        acao = request.form['acao']
        if acao == 'cadastrar':
            endereco = request.form['endereco']
            telefone = request.form['telefone']
            cep = request.form['cep']
            if Cliente.query.filter_by(nome=nome).first():
                flash('Cliente já cadastrado!')
                return redirect(url_for('index'))
            novo_cliente = Cliente(nome=nome, senha=senha, endereco=endereco, telefone=telefone, cep=cep)
            db.session.add(novo_cliente)
            db.session.commit()
            return redirect(url_for('painel_cliente', cliente_id=novo_cliente.id))
        elif acao == 'entrar':
            cliente = Cliente.query.filter_by(nome=nome, senha=senha).first()
            if cliente:
                session['cliente_id'] = cliente.id
                if 'carrinho' not in session:
                    session['carrinho'] = []
                return redirect(url_for('painel_cliente', cliente_id=cliente.id))
            else:
                flash('Nome ou senha inválidos!')
                return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/lojista', methods=['GET', 'POST'])
def lojista():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        acao = request.form['acao']
        if acao == 'cadastrar':
            endereco = request.form['endereco']
            telefone = request.form['telefone']
            cep = request.form['cep']
            raio = int(request.form['raio'])
            if Lojista.query.filter_by(nome=nome).first():
                flash('Lojista já cadastrado!')
                return redirect(url_for('index'))
            novo_lojista = Lojista(nome=nome, senha=senha, endereco=endereco, telefone=telefone, cep=cep, raio=raio)
            db.session.add(novo_lojista)
            db.session.commit()
            return redirect(url_for('painel_lojista', lojista_id=novo_lojista.id))
        elif acao == 'entrar':
            lojista = Lojista.query.filter_by(nome=nome, senha=senha).first()
            if lojista:
                lojista.online = True
                db.session.commit()
                return redirect(url_for('painel_lojista', lojista_id=lojista.id))
            else:
                flash('Nome ou senha inválidos!')
                return redirect(url_for('index'))
        elif acao == 'entrar_como_cliente':
            lojista = Lojista.query.filter_by(nome=nome, senha=senha).first()
            if lojista:
                cliente = Cliente.query.filter_by(nome=nome).first()
                if not cliente:
                    cliente = Cliente(nome=nome, senha=senha, endereco=lojista.endereco, telefone=lojista.telefone, cep=lojista.cep)
                    db.session.add(cliente)
                    db.session.commit()
                session['cliente_id'] = cliente.id
                if 'carrinho' not in session:
                    session['carrinho'] = []
                return redirect(url_for('painel_cliente', cliente_id=cliente.id))
            else:
                flash('Nome ou senha inválidos!')
                return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/painel_cliente/<int:cliente_id>', methods=['GET', 'POST'])
def painel_cliente(cliente_id):
    cliente = Cliente.query.get(cliente_id)
    if not cliente or 'cliente_id' not in session or session['cliente_id'] != cliente_id:
        return redirect(url_for('index'))
    lojistas = Lojista.query.filter_by(online=True).all()
    favoritos = cliente.lojas_favoritas.split(",") if cliente.lojas_favoritas else []
    for lojista in Lojista.query.filter(Lojista.id.in_(favoritos)).all():
        if lojista not in lojistas:
            lojistas.append(lojista)

    lojista_selecionado_id = session.get('lojista_selecionado', 1)
    if request.method == 'POST' and 'selecionar_lojista' in request.form:
        lojista_selecionado_id = int(request.form['lojista_id'])
        session['lojista_selecionado'] = lojista_selecionado_id
        session.modified = True

    produtos = Produto.query.filter_by(lojista_id=lojista_selecionado_id, disponivel=True).all()

    if 'carrinho' not in session:
        session['carrinho'] = []

    if request.method == 'POST':
        acao = request.form.get('acao')
        produto_id = request.form.get('produto_id')
        if acao == 'adicionar' and produto_id:
            produto = Produto.query.get(int(produto_id))
            session['carrinho'].append({'id': produto.id, 'nome': produto.nome, 'preco': produto.preco, 'lojista_id': lojista_selecionado_id})
            session.modified = True
        elif acao == 'remover' and produto_id:
            for i, item in enumerate(session['carrinho']):
                if item['id'] == int(produto_id) and item['lojista_id'] == lojista_selecionado_id:
                    session['carrinho'].pop(i)
                    session.modified = True
                    break
        elif acao == 'pagar':
            carrinho_itens = [item for item in session['carrinho'] if item['lojista_id'] == lojista_selecionado_id]
            if carrinho_itens:
                total = sum(item['preco'] for item in carrinho_itens)
                itens_texto = ", ".join(f"{item['nome']} (R${item['preco']:.2f})" for item in carrinho_itens)
                pedido = Pedido(cliente_id=cliente_id, lojista_id=lojista_selecionado_id, itens=itens_texto, total=total)
                db.session.add(pedido)
                db.session.commit()
                session['carrinho'] = [item for item in session['carrinho'] if item['lojista_id'] != lojista_selecionado_id]
                session.modified = True
            return redirect(url_for('chat', cliente_id=cliente_id, lojista_id=lojista_selecionado_id))

    carrinho_contagem = {}
    for item in session['carrinho']:
        if item['lojista_id'] == lojista_selecionado_id:
            carrinho_contagem[item['id']] = carrinho_contagem.get(item['id'], 0) + 1

    carrinho_itens = []
    total = 0
    for produto in produtos:
        quantidade = carrinho_contagem.get(produto.id, 0)
        if quantidade > 0:
            subtotal = produto.preco * quantidade
            carrinho_itens.append({'nome': produto.nome, 'quantidade': quantidade, 'preco_unitario': produto.preco, 'subtotal': subtotal})
            total += subtotal

    lojista_selecionado = Lojista.query.get(lojista_selecionado_id)
    return render_template('cliente.html', cliente=cliente, lojistas=lojistas, produtos=produtos, carrinho_itens=carrinho_itens, total=total, lojista_selecionado=lojista_selecionado)

@app.route('/painel_lojista/<int:lojista_id>', methods=['GET', 'POST'])
def painel_lojista(lojista_id):
    lojista = Lojista.query.get(lojista_id)
    if not lojista:
        return redirect(url_for('index'))

    if request.method == 'POST':
        acao = request.form.get('acao')
        if acao == 'abrir_loja':
            lojista.online = True
            db.session.commit()
        elif acao == 'fechar_loja':
            lojista.online = False
            db.session.commit()
        elif acao == 'atualizar_pedido':
            pedido_id = request.form.get('pedido_id')
            novo_status = request.form.get('status')
            pedido = Pedido.query.get(pedido_id)
            if pedido and pedido.lojista_id == lojista_id:
                pedido.status = novo_status
                db.session.commit()
        elif acao == 'adicionar_produto':
            nome = request.form['nome']
            tipo = request.form['tipo']
            unidade = request.form['unidade']
            quantidade = int(request.form['quantidade'])
            codigo = request.form['codigo']
            preco = float(request.form['preco'])
            novo_produto = Produto(nome=nome, tipo=tipo, unidade=unidade, quantidade=quantidade, codigo=codigo, preco=preco, lojista_id=lojista_id)
            db.session.add(novo_produto)
            db.session.commit()

    pedidos_abertos = Pedido.query.filter_by(lojista_id=lojista_id, status="Aberto").all()
    pedidos_fechados = Pedido.query.filter(Pedido.lojista_id == lojista_id, Pedido.status.in_(["Pago", "Entregue", "Cancelado", "Concluído"])).all()
    estoque = Produto.query.filter_by(lojista_id=lojista_id).all()

    return render_template('lojista.html', lojista=lojista, pedidos_abertos=pedidos_abertos, pedidos_fechados=pedidos_fechados, estoque=estoque)

@app.route('/chat/<int:cliente_id>/<int:lojista_id>', methods=['GET', 'POST'])
def chat(cliente_id, lojista_id):
    cliente = Cliente.query.get(cliente_id)
    lojista = Lojista.query.get(lojista_id)
    if not cliente or not lojista:
        return redirect(url_for('index'))
    mensagens = Mensagem.query.filter_by(cliente_id=cliente_id, lojista_id=lojista_id).all()
    if request.method == 'POST':
        texto = request.form.get('texto', '')
        audio = 'audio' in request.form
        remetente = 'cliente' if 'cliente_id' in session and session['cliente_id'] == cliente_id else 'lojista'
        mensagem = Mensagem(cliente_id=cliente_id, lojista_id=lojista_id, texto=texto, audio=audio, remetente=remetente)
        db.session.add(mensagem)
        db.session.commit()
    return render_template('chat.html', cliente=cliente, lojista=lojista, mensagens=mensagens)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Lojista.query.filter_by(nome="Mercado do Bairro (Simulação)").first():
            lojista = Lojista(nome="Mercado do Bairro (Simulação)", senha="123456", endereco="Rua Teste, 123", telefone="11987654321", cep="12345-678", raio=5)
            db.session.add(lojista)
            db.session.commit()
            produtos = [
                Produto(nome="Coca-Cola 2L", tipo="Refrigerante", unidade="2L", quantidade=999, codigo="001", preco=15.0, lojista_id=lojista.id),
                Produto(nome="Pizza", tipo="Congelada", unidade="un", quantidade=999, codigo="002", preco=30.0, lojista_id=lojista.id),
                Produto(nome="Arroz", tipo="Grão", unidade="1kg", quantidade=999, codigo="003", preco=10.0, lojista_id=lojista.id),
                Produto(nome="Feijão", tipo="Grão", unidade="1kg", quantidade=999, codigo="004", preco=12.0, lojista_id=lojista.id),
                Produto(nome="Café", tipo="Arábica", unidade="500g", quantidade=999, codigo="005", preco=20.0, lojista_id=lojista.id),
                Produto(nome="Leite", tipo="Integral", unidade="1L", quantidade=999, codigo="006", preco=5.0, lojista_id=lojista.id),
                Produto(nome="Pão", tipo="Francês", unidade="un", quantidade=999, codigo="007", preco=1.0, lojista_id=lojista.id),
                Produto(nome="Manteiga", tipo="Com Sal", unidade="200g", quantidade=999, codigo="008", preco=8.0, lojista_id=lojista.id),
                Produto(nome="Sabonete", tipo="Neutro", unidade="un", quantidade=999, codigo="009", preco=2.0, lojista_id=lojista.id),
                Produto(nome="Shampoo", tipo="Cabelos Lisos", unidade="300ml", quantidade=999, codigo="010", preco=15.0, lojista_id=lojista.id)
            ]
            db.session.add_all(produtos)
            db.session.commit()
    app.run(debug=True, host='0.0.0.0', port=8080)
