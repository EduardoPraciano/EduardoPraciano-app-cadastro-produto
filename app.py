from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///produtos.db'
app.config['SECRET_KEY'] = 'minha_chave_secreta'  # Necessário para usar flash messages
db = SQLAlchemy(app)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)  # Adicionando restrição de unicidade

@app.route('/')
def home():
    produtos = Produto.query.all()
    pdf_path = 'pdfs/arquivo.pdf'
    produtos_no_pdf = read_pdf_products(pdf_path)
    return render_template('index.html', produtos=produtos, produtos_no_pdf=produtos_no_pdf)

@app.route('/add', methods=['POST'])
def add_produto():
    nome = request.form.get('nome').upper()  # Convertendo para maiúsculas
    novo_produto = Produto(nome=nome)
    try:
        db.session.add(novo_produto)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('Produto já cadastrado!', 'error')
    return redirect(url_for('home'))

@app.route('/delete/<int:id>')
def delete_produto(id):
    produto = Produto.query.get_or_404(id)
    pdf_path = 'pdfs/arquivo.pdf'
    
    # Remover produto do banco de dados
    db.session.delete(produto)
    db.session.commit()
    
    # Remover produto do PDF
    products = read_pdf_products(pdf_path)
    if produto.nome in products:
        products.remove(produto.nome)
        write_pdf_products(pdf_path, products)
    
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('home'))

def read_pdf_products(pdf_path):
    if not os.path.exists(pdf_path):
        return []
    reader = PdfReader(pdf_path)
    products = []
    for page in reader.pages:
        text = page.extract_text()
        products.extend(text.split('\n'))
    return [p for p in products if p and p != "Este é um PDF em branco."]

def write_pdf_products(pdf_path, products):
    c = canvas.Canvas(pdf_path, pagesize=letter)
    y = 750
    for product in products:
        c.drawString(100, y, product)
        y -= 20
    c.save()

@app.route('/add_to_pdf/<int:id>')
def add_to_pdf(id):
    produto = Produto.query.get_or_404(id)
    pdf_path = 'pdfs/arquivo.pdf'
    
    # Criar diretório se não existir
    if not os.path.exists('pdfs'):
        os.makedirs('pdfs')
    
    # Ler produtos existentes no PDF
    products = read_pdf_products(pdf_path)
    
    # Adicionar produto ao PDF se não estiver presente
    if produto.nome not in products:
        products.append(produto.nome)
        write_pdf_products(pdf_path, products)
        flash('Produto adicionado ao PDF!', 'success')
    else:
        flash('Produto já está no PDF!', 'info')
    
    return redirect(url_for('home'))

@app.route('/remove_from_pdf/<int:id>')
def remove_from_pdf(id):
    produto = Produto.query.get_or_404(id)
    pdf_path = 'pdfs/arquivo.pdf'
    
    # Ler produtos existentes no PDF
    products = read_pdf_products(pdf_path)
    
    # Remover produto do PDF se estiver presente
    if produto.nome in products:
        products.remove(produto.nome)
        write_pdf_products(pdf_path, products)
        flash('Produto removido do PDF!', 'success')
    else:
        flash('Produto não está no PDF!', 'info')
    
    return redirect(url_for('home'))

@app.route('/open_pdf')
def open_pdf():
    pdf_path = 'pdfs/arquivo.pdf'
    
    # Criar diretório se não existir
    if not os.path.exists('pdfs'):
        os.makedirs('pdfs')
    
    # Criar um PDF em branco se não existir
    if not os.path.exists(pdf_path):
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, "Este é um PDF em branco.")
        c.save()
    
    return send_file(pdf_path, mimetype='application/pdf', as_attachment=False)

@app.route('/delete_pdf')
def delete_pdf():
    pdf_path = 'pdfs/arquivo.pdf'
    try:
        os.remove(pdf_path)
        flash('PDF excluído com sucesso!', 'success')
    except Exception as e:
        flash('Erro ao excluir o PDF!', 'error')
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
