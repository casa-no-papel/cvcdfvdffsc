import customtkinter as ctk
from tkinter import messagebox
import firebase_admin
from firebase_admin import credentials, auth, firestore

# ==========================================
# 0. CONFIGURAÇÃO DO DESIGN MODERNO
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

try:
    cred = credentials.Certificate("chave.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    messagebox.showerror("Erro de Conexão", f"Verifique o arquivo chave.json.\nErro: {e}")
    exit()

dict_clientes = {} 

# ==========================================
# 2. FUNÇÕES DO SISTEMA (ABAS 1 e 2)
# ==========================================
def cadastrar_cliente():
    nome = entry_nome.get()
    email = entry_email.get()
    senha = entry_senha.get()
    imovel = entry_imovel_cadastro.get()
    protocolo = entry_protocolo.get()
    
    if not nome or not email or not senha:
        messagebox.showwarning("Aviso", "Nome, E-mail e Senha são obrigatórios!")
        return

    try:
        btn_cadastrar.configure(text="Cadastrando...", state="disabled")
        app.update()

        novo_user = auth.create_user(email=email, password=senha)
        uid = novo_user.uid
        
        dados = {
            "nome": nome,
            "statusGeral": "Iniciando Processo",
            "imovel": imovel,
            "protocolos": protocolo,
            "feito": [],
            "falta": ["Entregar documentação inicial"],
            "etapas": [
                {"nome": "Contrato(s)", "status": "atual"},
                {"nome": "Documentação Pessoal", "status": "pendente"},
                {"nome": "Documentação do Imóvel", "status": "pendente"},
                {"nome": "Em trânsito no cartório", "status": "pendente"},
                {"nome": "Entrega da Escritura", "status": "pendente"}
            ]
        }
        db.collection("clientes").document(uid).set(dados)
        messagebox.showinfo("Sucesso", f"Cliente {nome} cadastrado com sucesso!")
        
        entry_nome.delete(0, 'end')
        entry_email.delete(0, 'end')
        entry_senha.delete(0, 'end')
        entry_imovel_cadastro.delete(0, 'end')
        entry_protocolo.delete(0, 'end')
        
        carregar_clientes() 
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao cadastrar: {e}")
    finally:
        btn_cadastrar.configure(text="CADASTRAR NOVO CLIENTE", state="normal")

def carregar_clientes():
    try:
        docs = db.collection("clientes").stream()
        lista_clientes = []
        global dict_clientes
        dict_clientes.clear()
        
        for doc in docs:
            dados = doc.to_dict()
            nome = dados.get("nome", "Sem Nome")
            uid = doc.id
            lista_clientes.append(nome)
            dict_clientes[nome] = uid
            
        if lista_clientes:
            combo_clientes.configure(values=lista_clientes)
            combo_clientes.set(lista_clientes[0])
            combo_clientes_adv.configure(values=lista_clientes)
            combo_clientes_adv.set(lista_clientes[0])
            atualizar_combo_etapas_aba2() # Atualiza as etapas da aba 2
        else:
            vazio = ["Nenhum cliente encontrado"]
            combo_clientes.configure(values=vazio)
            combo_clientes.set(vazio[0])
            combo_clientes_adv.configure(values=vazio)
            combo_clientes_adv.set(vazio[0])
    except Exception as e:
        print("Erro ao carregar clientes", e)

# Atualiza a caixinha de etapas da Aba 2 com base no cliente selecionado
def atualizar_combo_etapas_aba2(event=None):
    nome_selecionado = combo_clientes.get()
    if nome_selecionado and nome_selecionado in dict_clientes:
        uid = dict_clientes[nome_selecionado]
        doc = db.collection("clientes").document(uid).get().to_dict()
        etapas = [e["nome"] for e in doc.get("etapas", [])]
        combo_etapa.configure(values=etapas if etapas else ["Sem etapas"])
        if etapas: combo_etapa.set(etapas[0])

def atualizar_etapa():
    nome_selecionado = combo_clientes.get()
    etapa_nome = combo_etapa.get()
    status_legivel = combo_status_etapa.get()
    
    if not nome_selecionado or nome_selecionado == "Nenhum cliente encontrado": return
        
    map_status = {"Concluído (Verde)": "concluido", "Em andamento (Laranja)": "atual", "Pendente (Cinza)": "pendente"}
    status_db = map_status[status_legivel]
    
    uid = dict_clientes[nome_selecionado]
    try:
        doc_ref = db.collection("clientes").document(uid)
        doc = doc_ref.get()
        if doc.exists:
            etapas_atuais = doc.to_dict().get("etapas", [])
            for etapa in etapas_atuais:
                if etapa["nome"] == etapa_nome:
                    etapa["status"] = status_db
            doc_ref.update({"etapas": etapas_atuais})
            messagebox.showinfo("Sucesso", f"Cor da etapa '{etapa_nome}' atualizada no site!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro: {e}")

def atualizar_campo_texto(campo, widget_entry):
    nome_selecionado = combo_clientes.get()
    novo_valor = widget_entry.get()
    if nome_selecionado and novo_valor:
        uid = dict_clientes[nome_selecionado]
        try:
            db.collection("clientes").document(uid).update({campo: novo_valor})
            messagebox.showinfo("Sucesso", f"Campo atualizado com sucesso!")
            widget_entry.delete(0, 'end')
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")

def adicionar_lista(campo, entry_widget):
    nome_selecionado = combo_clientes.get()
    item = entry_widget.get()
    if nome_selecionado and item:
        uid = dict_clientes[nome_selecionado]
        try:
            db.collection("clientes").document(uid).update({campo: firestore.ArrayUnion([item])})
            messagebox.showinfo("Sucesso", f"Adicionado com sucesso!")
            entry_widget.delete(0, 'end')
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")

def excluir_cliente():
    nome_selecionado = combo_clientes.get()
    if not nome_selecionado or nome_selecionado == "Nenhum cliente encontrado": return
    uid = dict_clientes.get(nome_selecionado)
    confirmar = messagebox.askyesno("Confirmação", f"Apagar DEFINITIVAMENTE o cliente '{nome_selecionado}'?")
    if confirmar:
        try:
            db.collection("clientes").document(uid).delete()
            auth.delete_user(uid)
            messagebox.showinfo("Sucesso", "Cliente excluído!")
            carregar_clientes() 
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")

# ==========================================
# 3. FUNÇÕES DE EDIÇÃO AVANÇADA (ABA 3)
# ==========================================
def carregar_listas_avancadas():
    nome = combo_clientes_adv.get()
    if not nome or nome == "Nenhum cliente encontrado": return
    uid = dict_clientes[nome]
    try:
        dados = db.collection("clientes").document(uid).get().to_dict()
        
        feitos = dados.get("feito", [])
        combo_feito_adv.configure(values=feitos if feitos else ["Vazio"])
        combo_feito_adv.set(feitos[0] if feitos else "Vazio")
        
        faltas = dados.get("falta", [])
        combo_falta_adv.configure(values=faltas if faltas else ["Vazio"])
        combo_falta_adv.set(faltas[0] if faltas else "Vazio")
        
        etapas = [e["nome"] for e in dados.get("etapas", [])]
        combo_etapas_adv.configure(values=etapas if etapas else ["Vazio"])
        combo_etapas_adv.set(etapas[0] if etapas else "Vazio")
        
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível carregar os dados: {e}")

def acao_avancada_array(campo, widget_combo, acao):
    nome = combo_clientes_adv.get()
    item_selecionado = widget_combo.get()
    if not nome or item_selecionado == "Vazio": return
    uid = dict_clientes[nome]
    doc_ref = db.collection("clientes").document(uid)
    
    if acao == "apagar":
        if messagebox.askyesno("Confirmar", f"Apagar o item:\n'{item_selecionado}'?"):
            doc_ref.update({campo: firestore.ArrayRemove([item_selecionado])})
            messagebox.showinfo("Sucesso", "Item apagado!")
            carregar_listas_avancadas()
            
    elif acao == "editar":
        dialog = ctk.CTkInputDialog(text="Edite o texto abaixo:", title="Editar Item")
        novo_texto = dialog.get_input()
        if novo_texto and novo_texto != item_selecionado:
            # Remove o antigo e adiciona o novo editado
            doc_ref.update({campo: firestore.ArrayRemove([item_selecionado])})
            doc_ref.update({campo: firestore.ArrayUnion([novo_texto])})
            messagebox.showinfo("Sucesso", "Item editado!")
            carregar_listas_avancadas()

def acao_avancada_etapa(acao):
    nome = combo_clientes_adv.get()
    nome_etapa = combo_etapas_adv.get()
    if not nome or nome_etapa == "Vazio": return
    uid = dict_clientes[nome]
    doc_ref = db.collection("clientes").document(uid)
    etapas_atuais = doc_ref.get().to_dict().get("etapas", [])
    
    if acao == "apagar":
        if messagebox.askyesno("Confirmar", f"Apagar a bolinha '{nome_etapa}' da linha do tempo?"):
            novas_etapas = [e for e in etapas_atuais if e["nome"] != nome_etapa]
            doc_ref.update({"etapas": novas_etapas})
            messagebox.showinfo("Sucesso", "Etapa apagada!")
            carregar_listas_avancadas()
            atualizar_combo_etapas_aba2()
            
    elif acao == "editar":
        dialog = ctk.CTkInputDialog(text="Novo nome para a etapa:", title="Editar Etapa")
        novo_nome = dialog.get_input()
        if novo_nome:
            for e in etapas_atuais:
                if e["nome"] == nome_etapa: e["nome"] = novo_nome
            doc_ref.update({"etapas": etapas_atuais})
            messagebox.showinfo("Sucesso", "Nome da etapa alterado!")
            carregar_listas_avancadas()
            atualizar_combo_etapas_aba2()

def adicionar_nova_etapa():
    nome = combo_clientes_adv.get()
    nova_etapa = entry_nova_etapa.get()
    if not nome or not nova_etapa: return
    uid = dict_clientes[nome]
    
    doc_ref = db.collection("clientes").document(uid)
    etapas_atuais = doc_ref.get().to_dict().get("etapas", [])
    etapas_atuais.append({"nome": nova_etapa, "status": "pendente"})
    
    doc_ref.update({"etapas": etapas_atuais})
    messagebox.showinfo("Sucesso", f"Bolinha '{nova_etapa}' adicionada no final da linha do tempo!")
    entry_nova_etapa.delete(0, 'end')
    carregar_listas_avancadas()
    atualizar_combo_etapas_aba2()

# ==========================================
# 4. INTERFACE GRÁFICA (TELA)
# ==========================================
app = ctk.CTk()
app.title("Sistema Nexus - Gestão de Processos")
app.geometry("700x750") 

label_titulo = ctk.CTkLabel(app, text="Gestão Imobiliária", font=ctk.CTkFont(size=24, weight="bold"))
label_titulo.pack(pady=(15, 5))

tabview = ctk.CTkTabview(app, width=650, height=650)
tabview.pack(padx=20, pady=5, fill="both", expand=True)

aba1 = tabview.add("1. Novo Cliente")
aba2 = tabview.add("2. Atualizar Rápido")
aba3 = tabview.add("3. Edição Avançada") # NOVA ABA!

scroll_aba1 = ctk.CTkScrollableFrame(aba1, fg_color="transparent")
scroll_aba1.pack(fill="both", expand=True)
scroll_aba2 = ctk.CTkScrollableFrame(aba2, fg_color="transparent")
scroll_aba2.pack(fill="both", expand=True)
scroll_aba3 = ctk.CTkScrollableFrame(aba3, fg_color="transparent")
scroll_aba3.pack(fill="both", expand=True)

# --- ABA 1: CADASTRAR CLIENTE ---
ctk.CTkLabel(scroll_aba1, text="Nome do Cliente:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10,0))
entry_nome = ctk.CTkEntry(scroll_aba1, width=450)
entry_nome.pack(anchor="w", padx=20, pady=5)

ctk.CTkLabel(scroll_aba1, text="E-mail (Login):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10,0))
entry_email = ctk.CTkEntry(scroll_aba1, width=450)
entry_email.pack(anchor="w", padx=20, pady=5)

ctk.CTkLabel(scroll_aba1, text="Senha:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10,0))
entry_senha = ctk.CTkEntry(scroll_aba1, width=450, show="*")
entry_senha.pack(anchor="w", padx=20, pady=5)

ctk.CTkLabel(scroll_aba1, text="Imóvel:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10,0))
entry_imovel_cadastro = ctk.CTkEntry(scroll_aba1, width=450)
entry_imovel_cadastro.pack(anchor="w", padx=20, pady=5)

ctk.CTkLabel(scroll_aba1, text="Protocolo:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10,0))
entry_protocolo = ctk.CTkEntry(scroll_aba1, width=450)
entry_protocolo.pack(anchor="w", padx=20, pady=5)

btn_cadastrar = ctk.CTkButton(scroll_aba1, text="CADASTRAR CLIENTE", fg_color="#27ae60", hover_color="#2ecc71", font=ctk.CTkFont(weight="bold"), command=cadastrar_cliente)
btn_cadastrar.pack(pady=30)

# --- ABA 2: ATUALIZAÇÃO RÁPIDA ---
frame_select = ctk.CTkFrame(scroll_aba2, fg_color="transparent")
frame_select.pack(fill="x", padx=10, pady=(10,5))
ctk.CTkLabel(frame_select, text="Selecione o Cliente:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
combo_clientes = ctk.CTkComboBox(frame_select, width=250, values=["Carregando..."], command=atualizar_combo_etapas_aba2)
combo_clientes.pack(side="left", padx=5)
ctk.CTkButton(frame_select, text="🔄 Recarregar", width=100, command=carregar_clientes).pack(side="left", padx=5)

frame_etapas = ctk.CTkFrame(scroll_aba2)
frame_etapas.pack(fill="x", padx=10, pady=10)
ctk.CTkLabel(frame_etapas, text="Mudar Cor da Etapa (Timeline):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
combo_etapa = ctk.CTkComboBox(frame_etapas, width=180, values=["Carregando..."])
combo_etapa.pack(side="left", padx=10, pady=10)
combo_status_etapa = ctk.CTkComboBox(frame_etapas, width=180, values=["Concluído (Verde)", "Em andamento (Laranja)", "Pendente (Cinza)"])
combo_status_etapa.pack(side="left", padx=5, pady=10)
ctk.CTkButton(frame_etapas, text="Salvar Cor", width=90, fg_color="#d35400", hover_color="#e67e22", command=atualizar_etapa).pack(side="left", padx=10, pady=10)

frame_textos = ctk.CTkFrame(scroll_aba2)
frame_textos.pack(fill="x", padx=10, pady=5)
ctk.CTkLabel(frame_textos, text="Status Geral (Texto):").grid(row=0, column=0, sticky="w", padx=10, pady=(10,0))
entry_novo_status = ctk.CTkEntry(frame_textos, width=300)
entry_novo_status.grid(row=1, column=0, padx=10, pady=5)
ctk.CTkButton(frame_textos, text="Atualizar", width=80, command=lambda: atualizar_campo_texto("statusGeral", entry_novo_status)).grid(row=1, column=1, padx=5, pady=5)
ctk.CTkLabel(frame_textos, text="Imóvel:").grid(row=2, column=0, sticky="w", padx=10, pady=(5,0))
entry_novo_imovel = ctk.CTkEntry(frame_textos, width=300)
entry_novo_imovel.grid(row=3, column=0, padx=10, pady=(5, 15))
ctk.CTkButton(frame_textos, text="Atualizar", width=80, command=lambda: atualizar_campo_texto("imovel", entry_novo_imovel)).grid(row=3, column=1, padx=5, pady=(5, 15))

frame_listas = ctk.CTkFrame(scroll_aba2, fg_color="transparent")
frame_listas.pack(fill="x", padx=10, pady=5)
ctk.CTkLabel(frame_listas, text="Adicionar ao que JÁ FOI FEITO:").pack(anchor="w")
entry_feito = ctk.CTkEntry(frame_listas, width=300)
entry_feito.pack(side="left", pady=5)
ctk.CTkButton(frame_listas, text="Adicionar", width=80, fg_color="#27ae60", hover_color="#2ecc71", command=lambda: adicionar_lista("feito", entry_feito)).pack(side="left", padx=10)

frame_listas2 = ctk.CTkFrame(scroll_aba2, fg_color="transparent")
frame_listas2.pack(fill="x", padx=10, pady=5)
ctk.CTkLabel(frame_listas2, text="Adicionar ao que FALTA:").pack(anchor="w")
entry_falta = ctk.CTkEntry(frame_listas2, width=300)
entry_falta.pack(side="left", pady=5)
ctk.CTkButton(frame_listas2, text="Adicionar", width=80, fg_color="#d35400", hover_color="#e67e22", command=lambda: adicionar_lista("falta", entry_falta)).pack(side="left", padx=10)

frame_excluir = ctk.CTkFrame(scroll_aba2, fg_color="transparent")
frame_excluir.pack(fill="x", padx=10, pady=(20, 10))
ctk.CTkButton(frame_excluir, text="EXCLUIR CLIENTE INTEIRO", width=300, fg_color="#c0392b", hover_color="#922b21", command=excluir_cliente).pack(anchor="w")

# --- ABA 3: EDIÇÃO AVANÇADA (INDIVIDUAL) ---
frame_adv_select = ctk.CTkFrame(scroll_aba3, fg_color="transparent")
frame_adv_select.pack(fill="x", padx=10, pady=(10,15))
ctk.CTkLabel(frame_adv_select, text="Cliente:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
combo_clientes_adv = ctk.CTkComboBox(frame_adv_select, width=250)
combo_clientes_adv.pack(side="left", padx=5)
ctk.CTkButton(frame_adv_select, text="⬇️ Puxar Dados Deste Cliente", width=180, fg_color="#2980b9", hover_color="#3498db", command=carregar_listas_avancadas).pack(side="left", padx=10)

# Editar Já Feito
frame_adv_feito = ctk.CTkFrame(scroll_aba3)
frame_adv_feito.pack(fill="x", padx=10, pady=5)
ctk.CTkLabel(frame_adv_feito, text="✏️ Editar / Apagar de 'JÁ FOI FEITO'", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
combo_feito_adv = ctk.CTkComboBox(frame_adv_feito, width=350, values=["Carregue o cliente primeiro"])
combo_feito_adv.pack(side="left", padx=10, pady=10)
ctk.CTkButton(frame_adv_feito, text="Editar", width=60, command=lambda: acao_avancada_array("feito", combo_feito_adv, "editar")).pack(side="left", padx=5)
ctk.CTkButton(frame_adv_feito, text="Apagar", width=60, fg_color="#c0392b", hover_color="#922b21", command=lambda: acao_avancada_array("feito", combo_feito_adv, "apagar")).pack(side="left", padx=5)

# Editar Falta
frame_adv_falta = ctk.CTkFrame(scroll_aba3)
frame_adv_falta.pack(fill="x", padx=10, pady=10)
ctk.CTkLabel(frame_adv_falta, text="✏️ Editar / Apagar de 'O QUE FALTA'", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
combo_falta_adv = ctk.CTkComboBox(frame_adv_falta, width=350, values=["Carregue o cliente primeiro"])
combo_falta_adv.pack(side="left", padx=10, pady=10)
ctk.CTkButton(frame_adv_falta, text="Editar", width=60, command=lambda: acao_avancada_array("falta", combo_falta_adv, "editar")).pack(side="left", padx=5)
ctk.CTkButton(frame_adv_falta, text="Apagar", width=60, fg_color="#c0392b", hover_color="#922b21", command=lambda: acao_avancada_array("falta", combo_falta_adv, "apagar")).pack(side="left", padx=5)

# Editar Linha do Tempo (Etapas)
frame_adv_etapas = ctk.CTkFrame(scroll_aba3)
frame_adv_etapas.pack(fill="x", padx=10, pady=10)
ctk.CTkLabel(frame_adv_etapas, text="⚙️ Gerenciar LINHA DO TEMPO (Bolinhas)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
combo_etapas_adv = ctk.CTkComboBox(frame_adv_etapas, width=350, values=["Carregue o cliente primeiro"])
combo_etapas_adv.pack(side="left", padx=10, pady=10)
ctk.CTkButton(frame_adv_etapas, text="Renomear", width=60, command=lambda: acao_avancada_etapa("editar")).pack(side="left", padx=5)
ctk.CTkButton(frame_adv_etapas, text="Apagar", width=60, fg_color="#c0392b", hover_color="#922b21", command=lambda: acao_avancada_etapa("apagar")).pack(side="left", padx=5)

# Adicionar Nova Etapa
frame_nova_etapa = ctk.CTkFrame(scroll_aba3, fg_color="transparent")
frame_nova_etapa.pack(fill="x", padx=10, pady=5)
ctk.CTkLabel(frame_nova_etapa, text="➕ Adicionar nova bolinha na linha do tempo:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=5)
entry_nova_etapa = ctk.CTkEntry(frame_nova_etapa, width=350, placeholder_text="Ex: Vistoria da Caixa")
entry_nova_etapa.pack(side="left")
ctk.CTkButton(frame_nova_etapa, text="Criar Etapa", width=100, fg_color="#8e44ad", hover_color="#9b59b6", command=adicionar_nova_etapa).pack(side="left", padx=10)

# Inicializa Listas
carregar_clientes()
app.mainloop()