import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont
import locale
import re
import os
from datetime import datetime

# Configuração de localidade para moeda
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

class DateEntry(ttk.Entry):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind('<KeyRelease>', self.format_date)
        self.last_value = ""

    def format_date(self, event):
        # Ignorar teclas de navegação, backspace, delete
        if event.keysym in ['Left', 'Right', 'BackSpace', 'Delete', 'Shift_L', 'Shift_R']:
            return

        # Obter texto atual
        texto = self.get()
        
        # Remover caracteres não numéricos
        texto = re.sub(r'\D', '', texto)
        
        # Validações de formatação
        formatted_texto = texto

        # Lógica de formatação mais robusta
        if len(texto) == 2:
            # Se dois primeiros dígitos, adicionar barra
            if int(texto) > 31:
                formatted_texto = texto[0]
            else:
                formatted_texto = f"{texto}/"
        elif len(texto) == 4:
            # Após dois dígitos do mês
            if int(texto[2:4]) > 12:
                formatted_texto = f"{texto[:2]}/{texto[2]}"
            else:
                formatted_texto = f"{texto[:2]}/{texto[2:4]}/"
        elif len(texto) > 4:
            # Ano
            formatted_texto = f"{texto[:2]}/{texto[2:4]}/{texto[4:]}"

        # Definir texto formatado
        if formatted_texto != texto:
            self.delete(0, tk.END)
            self.insert(0, formatted_texto)

        # Posicionar cursor no final
        self.icursor(tk.END)

        # Atualizar último valor
        self.last_value = formatted_texto


class ParcelasMistasFrame(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        
        # Frame para conter as parcelas
        self.parcelas_container = ttk.Frame(self)
        self.parcelas_container.pack(fill=tk.X, expand=True)
        
        # Lista para armazenar as linhas de parcelas
        self.parcelas_rows = []
        
        # Botão para adicionar nova parcela
        self.btn_add_parcela = ttk.Button(
            self, 
            text="+ Adicionar Parcela", 
            command=self.adicionar_parcela
        )
        self.btn_add_parcela.pack(pady=10)
        
        # Adicionar primeira parcela inicial
        self.adicionar_parcela()
    

    def get_parcelas_height(self):
        """Calcula a altura total ocupada pelas parcelas mistas."""
        height = len(self.parcelas_rows) * 50  # Assume 50 pixels por linha de parcela
        return height
    
    def adicionar_parcela(self):
        # Criar frame para esta linha de parcela
        row_frame = ttk.Frame(self.parcelas_container)
        row_frame.pack(fill=tk.X, pady=5)
        
        # Label "de"
        lbl_de = ttk.Label(row_frame, text="De")
        lbl_de.pack(side=tk.LEFT, padx=5)
        
        # Parcela inicial
        self.entry_inicio = ttk.Entry(row_frame, width=10)
        
        # Se houver parcelas anteriores, preencher o início com o fim da última parcela + 1
        if self.parcelas_rows:
            last_parcela = self.parcelas_rows[-1]
            self.entry_inicio.insert(0, str(int(last_parcela['fim'].get()) + 1))
        
        self.entry_inicio.pack(side=tk.LEFT, padx=5)
        
        # Label "a"
        lbl_a = ttk.Label(row_frame, text="a")
        lbl_a.pack(side=tk.LEFT, padx=5)
        
        # Parcela final
        self.entry_fim = ttk.Entry(row_frame, width=10)
        self.entry_fim.pack(side=tk.LEFT, padx=5)
        
        # Label ":"
        lbl_doispontos = ttk.Label(row_frame, text=":")
        lbl_doispontos.pack(side=tk.LEFT, padx=5)
        
        # Label "R$"
        lbl_rs = ttk.Label(row_frame, text="R$")
        lbl_rs.pack(side=tk.LEFT, padx=5)
        
        # Valor da parcela
        self.entry_valor = ttk.Entry(row_frame, width=15)
        self.entry_valor.pack(side=tk.LEFT, padx=5)
        
        # Botão para remover esta linha
        btn_remover = ttk.Button(
            row_frame, 
            text="X", 
            width=2,
            command=lambda f=row_frame: self.remover_parcela(f)
        )
        btn_remover.pack(side=tk.LEFT, padx=5)
        
        # Armazenar referências
        self.parcelas_rows.append({
            'frame': row_frame,
            'inicio': self.entry_inicio,
            'fim': self.entry_fim,
            'valor': self.entry_valor
        })
    
    

    def remover_parcela(self, frame):
        # Impedir que a última parcela seja removida
        if len(self.parcelas_rows) > 1:
            frame.destroy()
            # Remover da lista de parcelas
            self.parcelas_rows = [
                p for p in self.parcelas_rows if p['frame'] != frame
            ] 

    
    
    def validar_e_formatar_parcelas(self):
        """Valida e formata as parcelas para impressão na carta."""
        parcelas_texto = []

        for parcela in self.parcelas_rows:
            inicio = parcela['inicio'].get()
            fim = parcela['fim'].get()
            valor = parcela['valor'].get()
            
            # Validações básicas
            if not all([inicio, fim, valor]):
                messagebox.showerror("Erro", "Todos os campos de parcelas devem ser preenchidos.")
                return None
            
            try:
                # Formatar o texto da parcela
                valor_float = locale.atof(valor)
                texto_parcela = f"{inicio} à {fim} parcelas: {locale.currency(valor_float, grouping=True)}"
                parcelas_texto.append(texto_parcela)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao processar parcelas: {e}")
                return None

        return "\n".join(parcelas_texto)




class ImageGeneratorApp:
    def __init__(self, master):
        self.master = master
        self.var_tipo_parcelas = tk.StringVar(value="Simples")
        master.title("Gerador de Cartas")
        master.geometry("500x700")
        master.configure(bg='#f0f0f0')

        # Estilo
        self.style = ttk.Style()
        self.style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 10))
        self.style.configure('TButton', font=('Helvetica', 10, 'bold'))
        self.style.configure('TFrame', background='#f0f0f0')

        # Criar frame principal
        self.main_frame = ttk.Frame(master, padding="20 10 20 10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)

        # Criar variáveis
        self.var_opcao = tk.StringVar(value="Imóvel")
        self.var_vencimento = tk.BooleanVar()
        self.var_taxa_transferencia = tk.BooleanVar()

        # Criar elementos da interface
        self.create_widgets()



    def create_widgets(self):
        
        # Título
        ttk.Label(self.main_frame, text="Gerador de Cartas", font=('Helvetica', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Crédito
        ttk.Label(self.main_frame, text="Valor do Crédito:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_credito = ttk.Entry(self.main_frame, width=30)
        self.entry_credito.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        # Entrada
        ttk.Label(self.main_frame, text="Valor de Entrada:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.entry_entrada = ttk.Entry(self.main_frame, width=30)
        self.entry_entrada.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)

        # Tipo de parcelas
        ttk.Label(self.main_frame, text="Tipo de Parcelas:").grid(row=3, column=0, sticky=tk.W, pady=5)
        tipo_parcelas_frame = ttk.Frame(self.main_frame)
        tipo_parcelas_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)

        ttk.Radiobutton(tipo_parcelas_frame, text="Simples", variable=self.var_tipo_parcelas, value="Simples", 
                        command=self.toggle_parcelas_mistas).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(tipo_parcelas_frame, text="Mistas", variable=self.var_tipo_parcelas, value="Mistas", 
                        command=self.toggle_parcelas_mistas).pack(side=tk.LEFT, padx=5)

        # Parcelas Simples
        self.parcelas_simples_frame = ttk.Frame(self.main_frame)
        self.parcelas_simples_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.parcelas_simples_frame, text="Parcelas:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.entry_qtd_parcelas_simples = ttk.Entry(self.parcelas_simples_frame, width=10)
        self.entry_qtd_parcelas_simples.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.parcelas_simples_frame, text="de").grid(row=0, column=2, padx=5)
        
        self.entry_valor_parcela_simples = ttk.Entry(self.parcelas_simples_frame, width=20)
        self.entry_valor_parcela_simples.grid(row=0, column=3, padx=5)

        # Parcelas mistas
        self.frame_parcelas_mistas = ParcelasMistasFrame(self.main_frame)
        self.frame_parcelas_mistas.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Tipo de Carta
        ttk.Label(self.main_frame, text="Tipo de Carta:").grid(row=6, column=0, sticky=tk.W, pady=5)
        tipo_carta_frame = ttk.Frame(self.main_frame)
        tipo_carta_frame.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Radiobutton(tipo_carta_frame, text="Imóvel", variable=self.var_opcao, value="Imóvel", 
                        command=self.atualizar_subgrupos).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(tipo_carta_frame, text="Automóvel", variable=self.var_opcao, value="Automóvel", 
                        command=self.atualizar_subgrupos).pack(side=tk.LEFT, padx=5)

        # Subgrupo
        ttk.Label(self.main_frame, text="Subgrupo:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.combo_subgrupo = ttk.Combobox(self.main_frame, state="readonly", width=27)
        self.combo_subgrupo.grid(row=7, column=1, sticky=(tk.W, tk.E), pady=5)

        # Observações
        ttk.Label(self.main_frame, text="Observações (opcional):").grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))

        # Próximo vencimento
        self.vencimento_frame = ttk.Frame(self.main_frame)
        self.vencimento_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.check_vencimento = ttk.Checkbutton(self.vencimento_frame, text="Próximo vencimento:", 
                                                variable=self.var_vencimento)
        self.check_vencimento.pack(side=tk.LEFT, padx=(0, 5))
        
        self.entry_vencimento = DateEntry(self.vencimento_frame, width=20)
        self.entry_vencimento.pack(side=tk.LEFT)

        # Taxa de transferência
        self.taxa_frame = ttk.Frame(self.main_frame)
        self.taxa_frame.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.check_taxa = ttk.Checkbutton(self.taxa_frame, text="Taxa de transferência:", 
                                          variable=self.var_taxa_transferencia)
        self.check_taxa.pack(side=tk.LEFT, padx=(0, 5))
        
        self.entry_taxa = ttk.Entry(self.taxa_frame, width=20)
        self.entry_taxa.pack(side=tk.LEFT)

        # Botão Gerar
        self.botao_gerar = ttk.Button(self.main_frame, text="Gerar Imagem", command=self.gerar_imagem)
        self.botao_gerar.grid(row=15, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))
        
        # Configurar peso das colunas
        self.main_frame.columnconfigure(1, weight=1)

        # Inicializar subgrupos
        self.toggle_parcelas_mistas()
        self.atualizar_subgrupos()

    def toggle_parcelas_mistas(self):
        if self.var_tipo_parcelas.get() == "Mistas":
            self.parcelas_simples_frame.grid_remove()
            self.frame_parcelas_mistas.grid()
                      
        else:
            self.parcelas_simples_frame.grid()
            self.frame_parcelas_mistas.grid_remove()              
            

    def atualizar_subgrupos(self):
        """Atualiza as opções de subgrupos com base na opção principal escolhida."""
        opcao = self.var_opcao.get()
        if opcao == "Imóvel":
            subopcoes = ["porto_seguro", "itau", "santander", "uniao_catarinense", "servopa", "caixa", "hs", "bradesco", "magalu", "mycon", "caixa_cnp", "randon", "sinosserra", "maggi", "embracon", "canopus", "caoa"]
        elif opcao == "Automóvel":
            subopcoes = ["porto_seguro", "itau", "santander", "uniao_catarinense", "servopa", "caixa", "hs", "bradesco", "magalu", "mycon", "caixa_cnp", "randon", "sinosserra", "maggi", "embracon", "canopus", "caoa"]
        else:
            subopcoes = []
        
        self.combo_subgrupo['values'] = subopcoes
        self.combo_subgrupo.set("")

    def converter_para_float(self, valor):
        """Converte um valor numérico em string para float, substituindo vírgulas por pontos."""
        try:
            return float(valor.replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", f"Formato inválido para valor: {valor}")
            raise

    def formatar_moeda(self, valor):
        """Formata um número em reais."""
        return locale.currency(float(valor), grouping=True)

    def gerar_imagem(self):
        """Função para gerar a imagem com validações e tratamentos de erro."""
        try:
            # Validar campos obrigatórios
            campos = [
                (self.entry_credito, "Crédito"),
                (self.entry_entrada, "Entrada"),
                (self.combo_subgrupo, "Subgrupo")
            ]

            for campo, nome in campos:
                if not campo.get().strip():
                    messagebox.showerror("Erro", f"O campo '{nome}' não pode estar vazio!")
                    return

            # Process parcels based on type
            if self.var_tipo_parcelas.get() == "Simples":
                qtd_parcelas = int(self.entry_qtd_parcelas_simples.get())
                valor_parcela = self.converter_para_float(self.entry_valor_parcela_simples.get())
                parcelas_formatadas = f"{qtd_parcelas} parcelas de {self.formatar_moeda(valor_parcela)}"
            else:  # Parcelas Mistas
                parcelas_formatadas = self.frame_parcelas_mistas.validar_e_formatar_parcelas()
                if parcelas_formatadas is None:
                    return  # Stop if there's an error in validation

            # Conversões e processamento
            credito = self.converter_para_float(self.entry_credito.get())
            entrada = self.converter_para_float(self.entry_entrada.get())

            # Coletar observações
            observacoes = []
            if self.var_vencimento.get():
                vencimento = self.entry_vencimento.get()
                if vencimento:
                    observacoes.append(f"Próximo vencimento: {vencimento}")
            
            if self.var_taxa_transferencia.get():
                taxa = self.entry_taxa.get()
                if taxa:
                    taxa_float = self.converter_para_float(taxa)
                    observacoes.append(f"Taxa de transferência: {self.formatar_moeda(taxa_float)}")

            # Chamar função original de editar imagem
            self.editar_imagem(
                self.var_opcao.get(), 
                self.combo_subgrupo.get(), 
                credito, 
                entrada, 
                parcelas_formatadas, 
                observacoes
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")


    def editar_imagem(self, opcao, subgrupo, credito, entrada, parcelas, observacoes):
        try:
            data_hora_atual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            # Escolhe a imagem com base na subopção
            if opcao == "Imóvel":
                imagem_path = f'./data/imovel/Imovel_{subgrupo}.png'
                base_filename = f'Carta_Imovel_{subgrupo}_{data_hora_atual}'
            elif opcao == "Automóvel":
                imagem_path = f'./data/automovel/Auto_{subgrupo}.png'
                base_filename = f'Carta_Automovel_{subgrupo}_{data_hora_atual}'
            else:
                base_filename = 'Carta_{data_hora_atual}'  # Fallback case

            data_hora_atual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # Gerar nome de arquivo único
            counter = 1
            while True:
                output_path = os.path.join('Imagens', f'{base_filename}_{counter}.png')
                if not os.path.exists(output_path):
                    break
                counter += 1
            
            # Abrir a imagem
            image = Image.open(imagem_path)
            draw = ImageDraw.Draw(image)

            # Configurações de texto
            font_path = "./data/fonte/Poppins-ExtraBold.ttf"
            font1 = ImageFont.truetype(font_path, 75)
            font2 = ImageFont.truetype(font_path, 40)
            font3 = ImageFont.truetype(font_path, 35)

            # Adicionando os textos na imagem
            draw.text((180, 570), f"{self.formatar_moeda(credito)}", fill="white", font=font1)
            draw.text((180, 720), f"{self.formatar_moeda(entrada)}", fill="white", font=font1)
            draw.text((180, 810), f"{parcelas}", fill="white", font=font2)

            # Calcular a posição vertical inicial para as observações
            y_offset = 1375
            if self.var_tipo_parcelas.get() == "Mistas":
                parcelas_height = self.frame_parcelas_mistas.get_parcelas_height()
                y_offset += parcelas_height

            # Adicionar observações
            for obs in observacoes:
                draw.text((150, y_offset), obs, fill="white", font=font3)
                y_offset += 50

            # Salvar imagem
            image.save(output_path)
            messagebox.showinfo("Sucesso", f"Imagem salva em: {output_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao editar a imagem: {e}")

def main():
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()