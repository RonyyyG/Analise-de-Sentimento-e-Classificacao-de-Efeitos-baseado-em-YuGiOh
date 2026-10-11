import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import pandas as pd
import torch

import estudoIA

# Configurações globais de aparência
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Paleta de cores temática Yu-Gi-Oh! (Obsidian / Pharaoh Gold / Millennium Violet / Cyber Blue)
COLORS = {
    "bg_main": "#0D1117",
    "bg_sidebar": "#131722",
    "bg_card": "#181D2A",
    "bg_card_secondary": "#222838",
    "bg_card_hover": "#2B3347",
    "border": "#2D3548",
    "gold": "#E5B842",
    "gold_hover": "#F5C756",
    "violet": "#8B5CF6",
    "violet_hover": "#A78BFA",
    "blue": "#38BDF8",
    "blue_hover": "#60A5FA",
    "text_primary": "#F8FAFC",
    "text_muted": "#94A3B8",
    "text_dark": "#0B0E14",
    "success": "#10B981",
    "danger": "#EF4444",
}


class YuGiOhAIApp(ctk.CTk):
    def __init__(self, headless_test=False):
        super().__init__()

        self.headless_test = headless_test

        # Configurações da Janela
        self.title("Yu-Gi-Oh! AI Card Analyzer")
        self.geometry("1280x820")
        self.minsize(1050, 700)
        self.configure(fg_color=COLORS["bg_main"])

        # Estado da Aplicação
        self.csv_path = estudoIA.caminho_arquivo
        self.df = None
        self.candidate_labels = list(estudoIA.candidate_labels)
        self.current_device = estudoIA.get_default_device()
        self.classifier = None
        self.is_loading_model = False
        self.is_analyzing = False
        self.selected_card_data = None
        self.current_page = None

        # Dados da Tabela / Paginação
        self.filtered_df = None
        self.current_page_idx = 1
        self.page_size = 50

        # Configurar Estilos TTK para Treeview Dark
        self._setup_ttk_styles()

        # Layout Principal (Sidebar à esquerda, Container de páginas à direita)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content_area()

        # Carregar Base de Dados inicial
        self._load_initial_data()

        # Navegar para Dashboard
        self.show_page("dashboard")

    def _setup_ttk_styles(self):
        """Configura os estilos do Treeview do TTK para combinar perfeitamente com o tema escuro."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Treeview principal
        self.style.configure(
            "Dark.Treeview",
            background=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_card"],
            borderwidth=0,
            rowheight=32,
            font=("Segoe UI", 10),
        )
        self.style.map(
            "Dark.Treeview",
            background=[("selected", COLORS["violet"])],
            foreground=[("selected", "#FFFFFF")],
        )

        # Cabeçalhos da Treeview
        self.style.configure(
            "Dark.Treeview.Heading",
            background=COLORS["bg_card_secondary"],
            foreground=COLORS["gold"],
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padding=6,
        )
        self.style.map(
            "Dark.Treeview.Heading",
            background=[("active", COLORS["bg_card_hover"])],
            foreground=[("active", COLORS["gold_hover"])],
        )

        # Scrollbars
        self.style.configure(
            "Dark.Vertical.TScrollbar",
            gripcount=0,
            background=COLORS["bg_card_secondary"],
            troughcolor=COLORS["bg_main"],
            bordercolor=COLORS["border"],
            arrowcolor=COLORS["gold"],
            relief="flat",
        )
        self.style.configure(
            "Dark.Horizontal.TScrollbar",
            gripcount=0,
            background=COLORS["bg_card_secondary"],
            troughcolor=COLORS["bg_main"],
            bordercolor=COLORS["border"],
            arrowcolor=COLORS["gold"],
            relief="flat",
        )

    def _build_sidebar(self):
        """Constrói a barra lateral fixa com navegação moderna e indicador de status."""
        self.sidebar = ctk.CTkFrame(
            self,
            width=250,
            corner_radius=0,
            fg_color=COLORS["bg_sidebar"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        # Logo / Cabeçalho
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(25, 20), sticky="ew")

        ctk.CTkLabel(
            logo_frame,
            text="⚔️ YU-GI-OH!",
            font=ctk.CTkFont(size=21, weight="bold"),
            text_color=COLORS["gold"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="AI Card Analyzer & DB",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w")

        # Divisor
        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color=COLORS["border"],
        ).grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))

        # Botões de Navegação
        self.nav_buttons = {}
        pages = [
            ("dashboard", "📊  Dashboard"),
            ("analyzer", "🔮  Analisar Carta"),
            ("database", "🗃️  Banco de Cartas"),
            ("settings", "⚙️  Configurações"),
        ]

        for idx, (page_key, title) in enumerate(pages, start=2):
            btn = ctk.CTkButton(
                self.sidebar,
                text=title,
                height=44,
                corner_radius=8,
                fg_color="transparent",
                text_color=COLORS["text_muted"],
                hover_color=COLORS["bg_card_secondary"],
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda k=page_key: self.show_page(k),
            )
            btn.grid(row=idx, column=0, padx=14, pady=5, sticky="ew")
            self.nav_buttons[page_key] = btn

        # Rodapé da Barra Lateral: Status da IA e Dispositivo
        status_frame = ctk.CTkFrame(
            self.sidebar,
            corner_radius=10,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        status_frame.grid(row=7, column=0, padx=14, pady=20, sticky="ew")

        self.lbl_ai_status_badge = ctk.CTkLabel(
            status_frame,
            text="○ IA: Não Carregada",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#F59E0B",
        )
        self.lbl_ai_status_badge.pack(anchor="w", padx=12, pady=(10, 2))

        dev_name = "GPU (CUDA)" if (isinstance(self.current_device, int) and self.current_device >= 0) else "CPU"
        self.lbl_device_badge = ctk.CTkLabel(
            status_frame,
            text=f"🖥️ Disp: {dev_name}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        )
        self.lbl_device_badge.pack(anchor="w", padx=12, pady=(0, 10))

    def _build_content_area(self):
        """Área central onde as páginas são alternadas."""
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # Dicionário de frames das páginas
        self.page_frames = {}
        self.page_frames["dashboard"] = self._create_dashboard_page()
        self.page_frames["analyzer"] = self._create_analyzer_page()
        self.page_frames["database"] = self._create_database_page()
        self.page_frames["settings"] = self._create_settings_page()

    def show_page(self, page_name):
        """Exibe a página selecionada e atualiza os botões de navegação."""
        if self.current_page == page_name:
            return

        for key, frame in self.page_frames.items():
            if key == page_name:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

        # Atualiza o destaque nos botões
        for key, btn in self.nav_buttons.items():
            if key == page_name:
                btn.configure(
                    fg_color=COLORS["bg_card_secondary"],
                    text_color=COLORS["gold"],
                    border_width=1,
                    border_color=COLORS["gold"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_muted"],
                    border_width=0,
                )

        self.current_page = page_name

    def _load_initial_data(self):
        """Carrega o CSV em memória."""
        try:
            self.df = estudoIA.carregar_dados(self.csv_path)
            self.filtered_df = self.df.copy()
            self._update_dashboard_stats()
            self._refresh_database_filters()
            self._display_database_page(1)
        except Exception as e:
            messagebox.showerror("Erro ao carregar dados", f"Não foi possível ler o CSV:\n{str(e)}")

    # -------------------------------------------------------------
    # PÁGINA 1: DASHBOARD
    # -------------------------------------------------------------
    def _create_dashboard_page(self):
        page = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        page.grid_columnconfigure((0, 1), weight=1)

        # Banner de Boas-Vindas
        banner = ctk.CTkFrame(
            page,
            corner_radius=14,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        banner.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        ctk.CTkLabel(
            banner,
            text="Yu-Gi-Oh! AI Card Analyzer",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["gold"],
        ).pack(anchor="w", padx=25, pady=(20, 4))

        ctk.CTkLabel(
            banner,
            text="Classificação de estratégias e efeitos de cartas com Hugging Face (facebook/bart-large-mnli) e base completa oficial.",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=25, pady=(0, 20))

        # Métricas Rápidas (4 Cards)
        cards_frame = ctk.CTkFrame(page, fg_color="transparent")
        cards_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.kpi_cards = {}
        kpi_configs = [
            ("total_cards", "Total de Cartas", "Carregando...", COLORS["gold"]),
            ("ai_status", "Status da IA", "Não Carregada", "#F59E0B"),
            ("device", "Dispositivo", "CPU", COLORS["blue"]),
            ("model", "Modelo", "bart-large-mnli", COLORS["violet"]),
        ]

        for col, (kpi_id, title, val, color) in enumerate(kpi_configs):
            card = ctk.CTkFrame(
                cards_frame,
                corner_radius=12,
                fg_color=COLORS["bg_card"],
                border_width=1,
                border_color=COLORS["border"],
            )
            card.grid(row=0, column=col, padx=6, sticky="ew")

            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLORS["text_muted"],
            ).pack(anchor="w", padx=16, pady=(14, 2))

            lbl_val = ctk.CTkLabel(
                card,
                text=val,
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=color,
            )
            lbl_val.pack(anchor="w", padx=16, pady=(0, 14))
            self.kpi_cards[kpi_id] = lbl_val

        # Seção Central: Distribuição do Banco de Cartas + Ações Rápidas
        left_col = ctk.CTkFrame(
            page,
            corner_radius=12,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        left_col.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=0)

        ctk.CTkLabel(
            left_col,
            text="Distribuição da Base de Dados",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w", padx=20, pady=(16, 12))

        self.lbl_stats_monsters = ctk.CTkLabel(left_col, text="Monstros: --", font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"])
        self.lbl_stats_monsters.pack(anchor="w", padx=25, pady=4)

        self.lbl_stats_spells = ctk.CTkLabel(left_col, text="Magias (Spells): --", font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"])
        self.lbl_stats_spells.pack(anchor="w", padx=25, pady=4)

        self.lbl_stats_traps = ctk.CTkLabel(left_col, text="Armadilhas (Traps): --", font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"])
        self.lbl_stats_traps.pack(anchor="w", padx=25, pady=4)

        self.lbl_stats_sets = ctk.CTkLabel(left_col, text="Coleções Distintas: --", font=ctk.CTkFont(size=13), text_color=COLORS["text_muted"])
        self.lbl_stats_sets.pack(anchor="w", padx=25, pady=(4, 16))

        # Ações Rápidas
        right_col = ctk.CTkFrame(
            page,
            corner_radius=12,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        right_col.grid(row=2, column=1, sticky="nsew", padx=(10, 0), pady=0)

        ctk.CTkLabel(
            right_col,
            text="Ações e Atalhos",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w", padx=20, pady=(16, 12))

        ctk.CTkButton(
            right_col,
            text="🔮 Analisar Carta Agora",
            height=40,
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_hover"],
            text_color=COLORS["text_dark"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.show_page("analyzer"),
        ).pack(fill="x", padx=20, pady=6)

        ctk.CTkButton(
            right_col,
            text="🗃️ Explorar Banco de Cartas",
            height=40,
            fg_color=COLORS["violet"],
            hover_color=COLORS["violet_hover"],
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.show_page("database"),
        ).pack(fill="x", padx=20, pady=6)

        self.btn_preload_model = ctk.CTkButton(
            right_col,
            text="⚡ Pré-carregar Modelo na Memória",
            height=40,
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=13),
            command=self._async_preload_model,
        )
        self.btn_preload_model.pack(fill="x", padx=20, pady=(6, 16))

        return page

    def _update_dashboard_stats(self):
        """Atualiza os números do dashboard a partir dos dados do CSV."""
        if self.df is None:
            return

        total = len(self.df)
        self.kpi_cards["total_cards"].configure(text=f"{total:,}".replace(",", "."))

        # Monstros, Magias, Armadilhas
        if "type" in self.df.columns:
            m_cnt = len(self.df[self.df["type"].str.upper() == "MONSTER"])
            s_cnt = len(self.df[self.df["type"].str.upper() == "SPELL"])
            t_cnt = len(self.df[self.df["type"].str.upper() == "TRAP"])
            self.lbl_stats_monsters.configure(text=f"🐉 Monstros: {m_cnt:,} cartas ({m_cnt/total*100:.1f}%)".replace(",", "."))
            self.lbl_stats_spells.configure(text=f"📖 Magias (Spells): {s_cnt:,} cartas ({s_cnt/total*100:.1f}%)".replace(",", "."))
            self.lbl_stats_traps.configure(text=f"🛡️ Armadilhas (Traps): {t_cnt:,} cartas ({t_cnt/total*100:.1f}%)".replace(",", "."))

        if "set_name" in self.df.columns:
            sets_cnt = self.df["set_name"].dropna().nunique()
            self.lbl_stats_sets.configure(text=f"📦 Coleções Registradas: {sets_cnt:,}".replace(",", "."))

        dev_name = "GPU (CUDA)" if (isinstance(self.current_device, int) and self.current_device >= 0) else "CPU"
        self.kpi_cards["device"].configure(text=dev_name)

    # -------------------------------------------------------------
    # PÁGINA 2: ANALISAR CARTA (IA ZERO-SHOT)
    # -------------------------------------------------------------
    def _create_analyzer_page(self):
        page = ctk.CTkFrame(self.content_container, fg_color="transparent")
        page.grid_rowconfigure(0, weight=1)
        page.grid_columnconfigure(0, weight=5)  # Formulário de entrada
        page.grid_columnconfigure(1, weight=5)  # Resultados

        # Coluna da Esquerda: Formulário de Entrada
        form_frame = ctk.CTkFrame(
            page,
            corner_radius=12,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        form_frame.grid_rowconfigure(4, weight=1)
        form_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            form_frame,
            text="Entrada da Carta",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["gold"],
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 5))

        self.lbl_analyzer_origin = ctk.CTkLabel(
            form_frame,
            text="Digite o nome e efeito ou selecione uma carta no Banco de Cartas.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        )
        self.lbl_analyzer_origin.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))

        # Barra de Pesquisa Rápida na tela de Análise
        quick_search_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        quick_search_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 12))

        self.entry_analyzer_quick_search = ctk.CTkEntry(
            quick_search_frame,
            height=34,
            placeholder_text="Buscar carta no banco para preencher (ex: Dark Magician)...",
            fg_color=COLORS["bg_card_secondary"],
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=12),
        )
        self.entry_analyzer_quick_search.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_analyzer_quick_search.bind("<Return>", lambda e: self._on_analyzer_quick_search())

        ctk.CTkButton(
            quick_search_frame,
            text="🔍 Carregar",
            width=85,
            height=34,
            fg_color=COLORS["violet"],
            hover_color=COLORS["violet_hover"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_analyzer_quick_search,
        ).pack(side="left")

        # Campo Nome da Carta
        ctk.CTkLabel(
            form_frame,
            text="Nome da Carta:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_primary"],
        ).grid(row=3, column=0, sticky="w", padx=20, pady=(0, 4))

        self.entry_card_name = ctk.CTkEntry(
            form_frame,
            height=38,
            placeholder_text="Ex: Dark Magician, Ash Blossom, Pot of Greed...",
            fg_color=COLORS["bg_card_secondary"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
        )
        self.entry_card_name.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 14))

        # Campo Descrição do Efeito
        ctk.CTkLabel(
            form_frame,
            text="Descrição / Texto do Efeito:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_primary"],
        ).grid(row=5, column=0, sticky="nw", padx=20, pady=(0, 4))

        self.txt_card_effect = ctk.CTkTextbox(
            form_frame,
            fg_color=COLORS["bg_card_secondary"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=13),
            wrap="word",
        )
        self.txt_card_effect.grid(row=6, column=0, sticky="nsew", padx=20, pady=(0, 14))
        form_frame.grid_rowconfigure(6, weight=1)

        # Botões de Ação
        btn_bar = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_bar.grid(row=7, column=0, sticky="ew", padx=20, pady=(0, 20))
        btn_bar.grid_columnconfigure(0, weight=2)
        btn_bar.grid_columnconfigure((1, 2), weight=1)

        self.btn_analyze = ctk.CTkButton(
            btn_bar,
            text="⚡ ANALISAR EFEITO",
            height=42,
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_hover"],
            text_color=COLORS["text_dark"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._async_analyze_effect,
        )
        self.btn_analyze.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.btn_clear_analysis = ctk.CTkButton(
            btn_bar,
            text="🧹 Limpar",
            height=42,
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=12),
            command=self._clear_analyzer_fields,
        )
        self.btn_clear_analysis.grid(row=0, column=1, sticky="ew", padx=4)

        self.btn_copy_results = ctk.CTkButton(
            btn_bar,
            text="📋 Copiar",
            height=42,
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=12),
            command=self._copy_analysis_results,
        )
        self.btn_copy_results.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        # Coluna da Direita: Painel de Resultados
        results_container = ctk.CTkFrame(
            page,
            corner_radius=12,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        results_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)
        results_container.grid_rowconfigure(2, weight=1)
        results_container.grid_columnconfigure(0, weight=1)

        # Cabeçalho dos Resultados
        res_header = ctk.CTkFrame(results_container, fg_color="transparent")
        res_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 5))

        ctk.CTkLabel(
            res_header,
            text="Resultados da Classificação",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["gold"],
        ).pack(side="left")

        self.lbl_analysis_status = ctk.CTkLabel(
            res_header,
            text="Aguardando efeito...",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        )
        self.lbl_analysis_status.pack(side="right")

        ctk.CTkLabel(
            results_container,
            text="Probabilidades relativas calculadas pelo modelo zero-shot (facebook/bart-large-mnli):",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))

        # Lista com rolagem para as barras de progresso
        self.results_scroll = ctk.CTkScrollableFrame(
            results_container,
            fg_color="transparent",
        )
        self.results_scroll.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 10))
        self.results_scroll.grid_columnconfigure(0, weight=1)

        # Nota de rodapé explicativa
        self.lbl_disclaimer = ctk.CTkLabel(
            results_container,
            text="ℹ️ As porcentagens indicam afinidade textual relativa de classificação zero-shot e não garantias de regras.",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
            wraplength=450,
            justify="left",
        )
        self.lbl_disclaimer.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))

        self.last_analysis_data = None
        return page

    def _on_analyzer_quick_search(self):
        """Busca uma carta pelo nome no DataFrame e preenche os campos automaticamente."""
        if self.df is None:
            messagebox.showinfo("Aviso", "A base de cartas ainda não está carregada.")
            return

        query = self.entry_analyzer_quick_search.get().strip()
        if not query:
            return

        # Busca por nome na base
        q_lower = query.lower()
        matches = self.df[self.df["name"].astype(str).str.lower().str.contains(q_lower, na=False)]
        if len(matches) == 0:
            # Tentar também pelo nome oficial
            if "name_official" in self.df.columns:
                matches = self.df[self.df["name_official"].astype(str).str.lower().str.contains(q_lower, na=False)]

        if len(matches) == 0:
            messagebox.showinfo("Não encontrada", f"Nenhuma carta encontrada contendo '{query}'.")
            return

        card = matches.iloc[0]
        self.set_card_for_analysis(card.get("name", ""), card.get("description", ""))
        self.lbl_analyzer_origin.configure(
            text=f"✓ '{card.get('name', '')}' carregada ({len(matches)} resultado(s) encontrado(s))",
            text_color=COLORS["gold"],
        )

    def _clear_analyzer_fields(self):
        """Limpa as entradas e a lista de resultados."""
        self.entry_analyzer_quick_search.delete(0, tk.END)
        self.entry_card_name.delete(0, tk.END)
        self.txt_card_effect.delete("1.0", tk.END)
        self.lbl_analyzer_origin.configure(text="Digite o nome e efeito ou selecione uma carta no Banco de Cartas.")
        self.lbl_analysis_status.configure(text="Campos limpos.")
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
        self.last_analysis_data = None

    def _copy_analysis_results(self):
        """Copia os resultados formatados da análise para o clipboard."""
        if not self.last_analysis_data:
            messagebox.showinfo("Copiar", "Nenhum resultado de análise disponível para copiar.")
            return

        nome = self.entry_card_name.get().strip() or "Carta sem nome"
        texto = [f"=== Yu-Gi-Oh! AI Analysis: {nome} ==="]
        texto.append("Classificação Zero-Shot BART-Large-MNLI:")
        for label, score in zip(self.last_analysis_data["labels"], self.last_analysis_data["scores"]):
            texto.append(f"• {label}: {score*100:.2f}%")

        self.clipboard_clear()
        self.clipboard_append("\n".join(texto))
        messagebox.showinfo("Copiado", "Resultados da análise copiados para a área de transferência!")

    def set_card_for_analysis(self, name, description):
        """Preenche automaticamente os dados de uma carta e vai para a tela de análise."""
        self.show_page("analyzer")
        self.entry_card_name.delete(0, tk.END)
        self.entry_card_name.insert(0, str(name) if pd.notna(name) else "")

        self.txt_card_effect.delete("1.0", tk.END)
        self.txt_card_effect.insert("1.0", str(description) if pd.notna(description) else "")

        self.lbl_analyzer_origin.configure(
            text=f"✓ Carta importada do Banco de Cartas: '{name}'",
            text_color=COLORS["gold"],
        )
        self.lbl_analysis_status.configure(text="Pronto para analisar.")

    def _async_preload_model(self):
        """Carrega o modelo do Hugging Face em segundo plano."""
        if self.is_loading_model:
            return
        if self.classifier is not None:
            messagebox.showinfo("Modelo", "O modelo já está carregado na memória!")
            return

        self.is_loading_model = True
        self.btn_preload_model.configure(text="⏳ Carregando Modelo...", state="disabled")
        self.lbl_ai_status_badge.configure(text="⟳ Carregando Modelo...", text_color="#F59E0B")
        self.kpi_cards["ai_status"].configure(text="Carregando...", text_color="#F59E0B")

        def worker():
            try:
                self.classifier = estudoIA.carregar_classificador(device=self.current_device)
                self.after(0, self._on_model_loaded_success)
            except Exception as e:
                self.after(0, lambda err=e: self._on_model_loaded_error(err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_model_loaded_success(self):
        self.is_loading_model = False
        self.btn_preload_model.configure(text="✓ Modelo Carregado", state="disabled")
        self.lbl_ai_status_badge.configure(text="● IA: Pronta", text_color=COLORS["success"])
        self.kpi_cards["ai_status"].configure(text="Pronto na Memória", text_color=COLORS["success"])

    def _on_model_loaded_error(self, error):
        self.is_loading_model = False
        self.btn_preload_model.configure(text="⚡ Carregar Modelo", state="normal")
        self.lbl_ai_status_badge.configure(text="✕ Erro ao Carregar", text_color=COLORS["danger"])
        self.kpi_cards["ai_status"].configure(text="Erro", text_color=COLORS["danger"])
        messagebox.showerror("Erro de Carregamento", f"Falha ao carregar o modelo Hugging Face:\n{str(error)}")

    def _async_analyze_effect(self):
        """Inicia a classificação do efeito em thread de background."""
        effect_text = self.txt_card_effect.get("1.0", tk.END).strip()
        if not effect_text:
            messagebox.showwarning("Texto Vazio", "Por favor, insira a descrição ou efeito da carta para analisar.")
            return

        if self.is_analyzing:
            return

        self.is_analyzing = True
        self.btn_analyze.configure(text="⏳ ANALISANDO...", state="disabled")
        self.lbl_analysis_status.configure(text="Processando na IA (BART-Large)...", text_color=COLORS["gold"])

        # Limpar widgets anteriores da lista de resultados
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        def worker():
            try:
                # Classificar usando a lógica reutilizável do estudoIA
                resultado = estudoIA.classificar_efeito(
                    texto_efeito=effect_text,
                    labels=self.candidate_labels,
                    device=self.current_device,
                    classificador=self.classifier,
                )
                # Salva o classificador se foi inicializado nesta chamada
                if self.classifier is None:
                    self.classifier = estudoIA._classifier_instance

                self.after(0, lambda r=resultado: self._on_analysis_success(r))
            except Exception as e:
                self.after(0, lambda err=e: self._on_analysis_error(err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_analysis_success(self, resultado):
        self.is_analyzing = False
        self.btn_analyze.configure(text="⚡ ANALISAR EFEITO", state="normal")
        self.lbl_analysis_status.configure(text="✓ Análise concluída!", text_color=COLORS["success"])
        self._on_model_loaded_success()

        self.last_analysis_data = resultado
        labels = resultado.get("labels", [])
        scores = resultado.get("scores", [])

        # Limpar widgets de resultados anteriores
        for widget in self.results_scroll.winfo_children():
            widget.destroy()

        if not labels:
            ctk.CTkLabel(self.results_scroll, text="Nenhum resultado retornado.", text_color=COLORS["text_muted"]).pack(pady=20)
            return

        # Renderizar cada categoria ordenada
        for idx, (label, score) in enumerate(zip(labels, scores)):
            is_winner = (idx == 0)
            pct = score * 100

            item_card = ctk.CTkFrame(
                self.results_scroll,
                corner_radius=10,
                fg_color=COLORS["bg_card_secondary"] if not is_winner else "#20283C",
                border_width=1,
                border_color=COLORS["gold"] if is_winner else COLORS["border"],
            )
            item_card.pack(fill="x", pady=5, padx=2)

            top_row = ctk.CTkFrame(item_card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(10, 4))

            title_text = f"★ {label}" if is_winner else f"• {label}"
            lbl_title = ctk.CTkLabel(
                top_row,
                text=title_text,
                font=ctk.CTkFont(size=13, weight="bold" if is_winner else "normal"),
                text_color=COLORS["gold"] if is_winner else COLORS["text_primary"],
            )
            lbl_title.pack(side="left")

            if is_winner:
                badge = ctk.CTkLabel(
                    top_row,
                    text="EFEITO PRINCIPAL",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=COLORS["text_dark"],
                    fg_color=COLORS["gold"],
                    corner_radius=4,
                    padx=6,
                    pady=2,
                )
                badge.pack(side="left", padx=8)

            lbl_score = ctk.CTkLabel(
                top_row,
                text=f"{pct:.2f}%",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLORS["gold"] if is_winner else COLORS["blue"],
            )
            lbl_score.pack(side="right")

            # Barra de Progresso Horizontal
            progress = ctk.CTkProgressBar(
                item_card,
                height=10,
                corner_radius=5,
                progress_color=COLORS["gold"] if is_winner else COLORS["violet"],
                fg_color=COLORS["bg_card"],
            )
            progress.pack(fill="x", padx=12, pady=(0, 10))
            progress.set(max(0.01, min(1.0, score)))

    def _on_analysis_error(self, error):
        self.is_analyzing = False
        self.btn_analyze.configure(text="⚡ ANALISAR EFEITO", state="normal")
        self.lbl_analysis_status.configure(text="✕ Falha na análise", text_color=COLORS["danger"])
        messagebox.showerror("Erro de Análise", f"Ocorreu um erro durante a inferência do modelo:\n{str(error)}")

    # -------------------------------------------------------------
    # PÁGINA 3: BANCO DE CARTAS (CONSULTA AO CSV REAL)
    # -------------------------------------------------------------
    def _create_database_page(self):
        page = ctk.CTkFrame(self.content_container, fg_color="transparent")
        page.grid_rowconfigure(2, weight=3)  # Tabela
        page.grid_rowconfigure(4, weight=2)  # Painel de Detalhes
        page.grid_columnconfigure(0, weight=1)

        # Barra Superior: Pesquisa Ampla
        search_card = ctk.CTkFrame(
            page,
            corner_radius=10,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        search_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_card.grid_columnconfigure(0, weight=1)

        search_row = ctk.CTkFrame(search_card, fg_color="transparent")
        search_row.pack(fill="x", padx=15, pady=10)

        self.entry_search = ctk.CTkEntry(
            search_row,
            height=38,
            placeholder_text="Buscar por Nome, Nome Oficial, Efeito, Index, Join ID ou Set ID...",
            fg_color=COLORS["bg_card_secondary"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=12),
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_search.bind("<Return>", lambda e: self._on_search_triggered())

        btn_search = ctk.CTkButton(
            search_row,
            text="🔍 Buscar",
            width=90,
            height=38,
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_hover"],
            text_color=COLORS["text_dark"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_search_triggered,
        )
        btn_search.pack(side="left", padx=4)

        btn_reset = ctk.CTkButton(
            search_row,
            text="↺ Limpar",
            width=80,
            height=38,
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=12),
            command=self._on_search_reset,
        )
        btn_reset.pack(side="left", padx=4)

        # Barra de Filtros Específicos
        filters_bar = ctk.CTkFrame(page, fg_color="transparent")
        filters_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ctk.CTkLabel(filters_bar, text="Filtros:", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["text_muted"]).pack(side="left", padx=(5, 10))

        # Filtro de Tipo
        self.combo_type = ctk.CTkComboBox(
            filters_bar,
            values=["Todos os Tipos", "MONSTER", "SPELL", "TRAP"],
            width=140,
            height=32,
            command=lambda v: self._on_filter_changed(),
        )
        self.combo_type.pack(side="left", padx=4)

        # Filtro de Atributo
        self.combo_attribute = ctk.CTkComboBox(
            filters_bar,
            values=["Todos os Atributos"],
            width=150,
            height=32,
            command=lambda v: self._on_filter_changed(),
        )
        self.combo_attribute.pack(side="left", padx=4)

        # Filtro de Subtipo
        self.combo_subtype = ctk.CTkComboBox(
            filters_bar,
            values=["Todos os Subtipos"],
            width=160,
            height=32,
            command=lambda v: self._on_filter_changed(),
        )
        self.combo_subtype.pack(side="left", padx=4)

        # Filtro de Raridade
        self.combo_rarity = ctk.CTkComboBox(
            filters_bar,
            values=["Todas as Raridades"],
            width=150,
            height=32,
            command=lambda v: self._on_filter_changed(),
        )
        self.combo_rarity.pack(side="left", padx=4)

        # Filtro de Coleção
        self.combo_set = ctk.CTkComboBox(
            filters_bar,
            values=["Todas as Coleções"],
            width=160,
            height=32,
            command=lambda v: self._on_filter_changed(),
        )
        self.combo_set.pack(side="left", padx=4)

        # Rótulo de Contagem / Paginação
        self.lbl_table_counts = ctk.CTkLabel(
            filters_bar,
            text="Exibindo 0 cartas",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["gold"],
        )
        self.lbl_table_counts.pack(side="right", padx=5)

        # Tabela com Treeview (Dark TTK)
        table_container = ctk.CTkFrame(
            page,
            corner_radius=10,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        table_container.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Colunas Requeridas
        self.table_columns = [
            ("name", "Nome", 220),
            ("type", "Tipo", 80),
            ("sub_type", "Subtipo", 110),
            ("attribute", "Atributo", 80),
            ("attack", "ATK", 65),
            ("defense", "DEF", 65),
            ("index", "Index (ID)", 80),
            ("index_market", "Index Mkt", 85),
            ("join_id", "Join ID", 110),
            ("set_id", "Set ID", 95),
            ("rarity", "Raridade", 120),
            ("price", "Preço", 75),
        ]

        col_ids = [c[0] for c in self.table_columns]
        self.tree = ttk.Treeview(
            table_container,
            columns=col_ids,
            show="headings",
            style="Dark.Treeview",
            selectmode="browse",
        )

        for col_id, col_text, col_width in self.table_columns:
            self.tree.heading(col_id, text=col_text, anchor="w")
            self.tree.column(col_id, width=col_width, minwidth=50, anchor="w")

        # Scrollbars para Treeview
        tree_scroll_y = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview, style="Dark.Vertical.TScrollbar")
        tree_scroll_x = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview, style="Dark.Horizontal.TScrollbar")
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self._on_card_row_selected)

        # Barra de Navegação de Paginação
        pagination_bar = ctk.CTkFrame(page, fg_color="transparent")
        pagination_bar.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        self.btn_prev_page = ctk.CTkButton(
            pagination_bar,
            text="◀ Anterior",
            width=90,
            height=28,
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["bg_card_hover"],
            command=self._on_prev_page,
        )
        self.btn_prev_page.pack(side="left")

        self.lbl_pagination_info = ctk.CTkLabel(
            pagination_bar,
            text="Página 1 de 1",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        self.lbl_pagination_info.pack(side="left", padx=15)

        self.btn_next_page = ctk.CTkButton(
            pagination_bar,
            text="Próxima ▶",
            width=90,
            height=28,
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["bg_card_hover"],
            command=self._on_next_page,
        )
        self.btn_next_page.pack(side="left")

        # Painel de Detalhes da Carta Selecionada (Abaixo da Tabela)
        details_card = ctk.CTkFrame(
            page,
            corner_radius=10,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        details_card.grid(row=4, column=0, sticky="nsew")
        details_card.grid_rowconfigure(1, weight=1)
        details_card.grid_columnconfigure(0, weight=4)  # Metadados e ações
        details_card.grid_columnconfigure(1, weight=6)  # Efeito completo com scroll

        # Cabeçalho dos Detalhes
        det_header = ctk.CTkFrame(details_card, fg_color="transparent")
        det_header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=(10, 5))

        self.lbl_detail_name = ctk.CTkLabel(
            det_header,
            text="Selecione uma carta na tabela para visualizar todos os detalhes",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["gold"],
        )
        self.lbl_detail_name.pack(side="left")

        # Metadados e IDs à esquerda
        left_meta = ctk.CTkFrame(details_card, fg_color="transparent")
        left_meta.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)

        self.lbl_meta_types = ctk.CTkLabel(left_meta, text="Tipo: -- | Atributo: -- | ATK/DEF: --", font=ctk.CTkFont(size=12), text_color=COLORS["text_primary"], anchor="w")
        self.lbl_meta_types.pack(fill="x", pady=2)

        self.lbl_meta_set = ctk.CTkLabel(left_meta, text="Coleção: -- | Lançamento: -- | Preço: --", font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"], anchor="w")
        self.lbl_meta_set.pack(fill="x", pady=2)

        self.lbl_meta_ids = ctk.CTkLabel(left_meta, text="IDs: Index: -- | Market: -- | Join: -- | Set: --", font=ctk.CTkFont(size=11), text_color=COLORS["blue"], anchor="w")
        self.lbl_meta_ids.pack(fill="x", pady=(2, 10))

        # Botões de ação do detalhe
        det_btns = ctk.CTkFrame(left_meta, fg_color="transparent")
        det_btns.pack(fill="x", pady=5)

        self.btn_send_to_ai = ctk.CTkButton(
            det_btns,
            text="⚡ ANALISAR ESTA CARTA",
            height=34,
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_hover"],
            text_color=COLORS["text_dark"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._send_selected_to_analysis,
        )
        self.btn_send_to_ai.pack(side="left", padx=(0, 8))

        self.btn_copy_ids = ctk.CTkButton(
            det_btns,
            text="📋 Copiar Identificadores",
            height=34,
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=11),
            command=self._copy_selected_ids,
        )
        self.btn_copy_ids.pack(side="left")

        # Texto do Efeito com Scroll à direita
        right_effect = ctk.CTkFrame(details_card, fg_color="transparent")
        right_effect.grid(row=1, column=1, sticky="nsew", padx=15, pady=(0, 10))
        right_effect.grid_rowconfigure(1, weight=1)
        right_effect.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right_effect, text="Texto do Efeito / Descrição:", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["text_muted"]).grid(row=0, column=0, sticky="w", pady=(0, 2))

        self.txt_detail_effect = ctk.CTkTextbox(
            right_effect,
            fg_color=COLORS["bg_card_secondary"],
            border_color=COLORS["border"],
            border_width=1,
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=12),
            wrap="word",
        )
        self.txt_detail_effect.grid(row=1, column=0, sticky="nsew")

        return page

    def _refresh_database_filters(self):
        """Preenche as opções dos filtros combobox a partir das colunas únicas do CSV."""
        if self.df is None:
            return

        if "attribute" in self.df.columns:
            attrs = ["Todos os Atributos"] + sorted([str(x) for x in self.df["attribute"].dropna().unique()])
            self.combo_attribute.configure(values=attrs)
            self.combo_attribute.set("Todos os Atributos")

        if "sub_type" in self.df.columns:
            subtypes = ["Todos os Subtipos"] + sorted([str(x) for x in self.df["sub_type"].dropna().unique() if len(str(x)) < 30])
            self.combo_subtype.configure(values=subtypes[:40])
            self.combo_subtype.set("Todos os Subtipos")

        if "rarity" in self.df.columns:
            rarities = ["Todas as Raridades"] + sorted([str(x) for x in self.df["rarity"].dropna().unique()])
            self.combo_rarity.configure(values=rarities[:35])
            self.combo_rarity.set("Todas as Raridades")

        if "set_name" in self.df.columns:
            sets = ["Todas as Coleções"] + sorted([str(x) for x in self.df["set_name"].dropna().unique()])
            self.combo_set.configure(values=sets[:60])
            self.combo_set.set("Todas as Coleções")

    def _on_search_triggered(self):
        """Aplica a busca rápida textual no DataFrame já carregado em memória."""
        if self.df is None:
            return

        query = self.entry_search.get().strip()
        data = self.df

        # Aplicar Filtro de Busca Textual
        if query:
            q_lower = query.lower()
            mask = (
                data["name"].astype(str).str.lower().str.contains(q_lower, na=False) |
                data.get("name_official", pd.Series([""] * len(data))).astype(str).str.lower().str.contains(q_lower, na=False) |
                data["description"].astype(str).str.lower().str.contains(q_lower, na=False) |
                data["index"].astype(str).str.lower().str.contains(q_lower, na=False) |
                data.get("index_market", pd.Series([""] * len(data))).astype(str).str.lower().str.contains(q_lower, na=False) |
                data.get("join_id", pd.Series([""] * len(data))).astype(str).str.lower().str.contains(q_lower, na=False) |
                data.get("set_id", pd.Series([""] * len(data))).astype(str).str.lower().str.contains(q_lower, na=False)
            )
            data = data[mask]

        # Aplicar Filtros de Combobox
        t_val = self.combo_type.get()
        if t_val != "Todos os Tipos" and "type" in data.columns:
            data = data[data["type"].astype(str).str.upper() == t_val.upper()]

        attr_val = self.combo_attribute.get()
        if attr_val != "Todos os Atributos" and "attribute" in data.columns:
            data = data[data["attribute"].astype(str) == attr_val]

        sub_val = self.combo_subtype.get()
        if sub_val != "Todos os Subtipos" and "sub_type" in data.columns:
            data = data[data["sub_type"].astype(str) == sub_val]

        rar_val = self.combo_rarity.get()
        if rar_val != "Todas as Raridades" and "rarity" in data.columns:
            data = data[data["rarity"].astype(str) == rar_val]

        set_val = self.combo_set.get()
        if set_val != "Todas as Coleções" and "set_name" in data.columns:
            data = data[data["set_name"].astype(str) == set_val]

        self.filtered_df = data
        self.current_page_idx = 1
        self._display_database_page(1)

    def _on_filter_changed(self):
        """Dispara a busca quando qualquer filtro combobox é alterado."""
        self._on_search_triggered()

    def _on_search_reset(self):
        """Reseta todos os filtros e campo de busca para o estado original."""
        self.entry_search.delete(0, tk.END)
        self.combo_type.set("Todos os Tipos")
        self.combo_attribute.set("Todos os Atributos")
        self.combo_subtype.set("Todos os Subtipos")
        self.combo_rarity.set("Todas as Raridades")
        self.combo_set.set("Todas as Coleções")
        self.filtered_df = self.df.copy() if self.df is not None else None
        self.current_page_idx = 1
        self._display_database_page(1)

    def _display_database_page(self, page_num):
        """Renderiza a página atual de resultados na Treeview."""
        if self.filtered_df is None:
            return

        total_records = len(self.filtered_df)
        total_pages = max(1, (total_records + self.page_size - 1) // self.page_size)
        self.current_page_idx = max(1, min(page_num, total_pages))

        start_idx = (self.current_page_idx - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total_records)

        # Atualizar Contadores e Botões
        self.lbl_table_counts.configure(text=f"Total: {total_records:,} cartas".replace(",", "."))
        self.lbl_pagination_info.configure(text=f"Página {self.current_page_idx} de {total_pages} (Exibindo {start_idx + 1 if total_records > 0 else 0}-{end_idx})")
        self.btn_prev_page.configure(state="normal" if self.current_page_idx > 1 else "disabled")
        self.btn_next_page.configure(state="normal" if self.current_page_idx < total_pages else "disabled")

        # Limpar linhas existentes da Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        if total_records == 0:
            return

        page_slice = self.filtered_df.iloc[start_idx:end_idx]

        for df_row_idx, row in page_slice.iterrows():
            vals = []
            for col_id, _, _ in self.table_columns:
                v = row.get(col_id, "")
                if pd.isna(v):
                    v = "-"
                elif isinstance(v, float) and v.is_integer():
                    v = str(int(v))
                else:
                    v = str(v)
                vals.append(v)

            # Armazena o índice original do DataFrame no iid da linha
            self.tree.insert("", "end", iid=str(df_row_idx), values=vals)

    def _on_prev_page(self):
        if self.current_page_idx > 1:
            self._display_database_page(self.current_page_idx - 1)

    def _on_next_page(self):
        self._display_database_page(self.current_page_idx + 1)

    def _on_card_row_selected(self, event):
        """Quando o usuário clica em uma carta na tabela, preenche o painel de detalhes."""
        selected_items = self.tree.selection()
        if not selected_items or self.df is None:
            return

        row_id = selected_items[0]
        try:
            row_idx = int(row_id)
            card = self.df.loc[row_idx]
            if isinstance(card, pd.DataFrame):
                card = card.iloc[0]
            self.selected_card_data = card

            name = str(card.get("name", "Sem Nome"))
            c_type = str(card.get("type", "-"))
            sub_type = str(card.get("sub_type", "-"))
            attr = str(card.get("attribute", "-"))
            atk = str(card.get("attack", "-"))
            defe = str(card.get("defense", "-"))
            if atk != "-" and isinstance(card.get("attack"), float):
                atk = str(int(card["attack"]))
            if defe != "-" and isinstance(card.get("defense"), float):
                defe = str(int(card["defense"]))

            set_name = str(card.get("set_name", "-"))
            set_rel = str(card.get("set_release", "-"))
            price = str(card.get("price", "-"))

            idx = str(card.get("index", "-"))
            mkt = str(card.get("index_market", "-"))
            join_id = str(card.get("join_id", "-"))
            set_id = str(card.get("set_id", "-"))

            self.lbl_detail_name.configure(text=f"✦ {name}")
            self.lbl_meta_types.configure(text=f"Tipo: {c_type} | Subtipo: {sub_type} | Atributo: {attr} | ATK: {atk} / DEF: {defe}")
            self.lbl_meta_set.configure(text=f"Coleção: {set_name} | Lançamento: {set_rel} | Preço: {price}")
            self.lbl_meta_ids.configure(text=f"Identificadores Oficiais:  Index: {idx}  |  Market: {mkt}  |  Join ID: {join_id}  |  Set ID: {set_id}")

            self.txt_detail_effect.delete("1.0", tk.END)
            self.txt_detail_effect.insert("1.0", str(card.get("description", "Sem descrição disponível.")))
        except Exception as e:
            print(f"Erro ao selecionar carta: {e}")

    def _send_selected_to_analysis(self):
        """Envia a carta selecionada para a tela de análise."""
        if self.selected_card_data is None:
            messagebox.showinfo("Aviso", "Selecione uma carta na tabela primeiro.")
            return

        name = self.selected_card_data.get("name", "")
        effect = self.selected_card_data.get("description", "")
        self.set_card_for_analysis(name, effect)

    def _copy_selected_ids(self):
        """Copia os identificadores oficiais da carta selecionada."""
        if self.selected_card_data is None:
            messagebox.showinfo("Aviso", "Selecione uma carta na tabela primeiro.")
            return

        c = self.selected_card_data
        ids_text = (
            f"Carta: {c.get('name', '')}\n"
            f"Index: {c.get('index', '')}\n"
            f"Index Market: {c.get('index_market', '')}\n"
            f"Join ID: {c.get('join_id', '')}\n"
            f"Set ID: {c.get('set_id', '')}"
        )
        self.clipboard_clear()
        self.clipboard_append(ids_text)
        messagebox.showinfo("Copiado", "Identificadores oficiais copiados para a área de transferência!")

    # -------------------------------------------------------------
    # PÁGINA 4: CONFIGURAÇÕES
    # -------------------------------------------------------------
    def _create_settings_page(self):
        page = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)

        # Seção 1: Arquivo de Base de Dados (CSV)
        csv_sec = ctk.CTkFrame(
            page,
            corner_radius=12,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        csv_sec.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            csv_sec,
            text="📁 Base de Dados de Cartas (CSV)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["gold"],
        ).pack(anchor="w", padx=20, pady=(16, 6))

        self.lbl_csv_path_display = ctk.CTkLabel(
            csv_sec,
            text=f"Caminho atual: {os.path.abspath(self.csv_path)}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
            wraplength=800,
            justify="left",
        )
        self.lbl_csv_path_display.pack(anchor="w", padx=20, pady=(0, 10))

        btn_pick_csv = ctk.CTkButton(
            csv_sec,
            text="Selecionar Outro Arquivo CSV...",
            height=36,
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text_primary"],
            border_width=1,
            border_color=COLORS["border"],
            command=self._on_change_csv_file,
        )
        btn_pick_csv.pack(anchor="w", padx=20, pady=(0, 16))

        # Seção 2: Dispositivo de Execução (CPU / GPU)
        dev_sec = ctk.CTkFrame(
            page,
            corner_radius=12,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        dev_sec.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            dev_sec,
            text="⚡ Dispositivo de Execução da IA",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["gold"],
        ).pack(anchor="w", padx=20, pady=(16, 6))

        has_cuda = torch.cuda.is_available()
        cuda_info = f"GPU Detectada: {torch.cuda.get_device_name(0)}" if has_cuda else "Nenhuma GPU com suporte CUDA detectada (execução segura em CPU)."

        ctk.CTkLabel(
            dev_sec,
            text=cuda_info,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=20, pady=(0, 10))

        dev_row = ctk.CTkFrame(dev_sec, fg_color="transparent")
        dev_row.pack(anchor="w", padx=20, pady=(0, 16))

        ctk.CTkLabel(dev_row, text="Dispositivo:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 10))

        dev_options = ["CPU (Recomendado se sem CUDA)", "GPU (CUDA 0)"] if has_cuda else ["CPU (Padrão)"]
        self.combo_device_sel = ctk.CTkComboBox(
            dev_row,
            values=dev_options,
            width=260,
            command=self._on_device_selection_changed,
        )
        self.combo_device_sel.pack(side="left")
        if not has_cuda:
            self.combo_device_sel.set("CPU (Padrão)")
        else:
            self.combo_device_sel.set("GPU (CUDA 0)" if self.current_device >= 0 else "CPU (Recomendado se sem CUDA)")

        # Seção 3: Categorias de Classificação da IA (Candidate Labels)
        cat_sec = ctk.CTkFrame(
            page,
            corner_radius=12,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        cat_sec.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            cat_sec,
            text="🏷️ Categorias de Classificação Zero-Shot",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["gold"],
        ).pack(anchor="w", padx=20, pady=(16, 6))

        ctk.CTkLabel(
            cat_sec,
            text="Categorias atuais utilizadas pelo modelo para avaliar o efeito das cartas:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=20, pady=(0, 10))

        # Lista de categorias
        self.listbox_labels = tk.Listbox(
            cat_sec,
            height=7,
            bg=COLORS["bg_card_secondary"],
            fg=COLORS["text_primary"],
            selectbackground=COLORS["violet"],
            selectforeground="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 11),
            highlightthickness=1,
            highlightcolor=COLORS["border"],
        )
        self.listbox_labels.pack(fill="x", padx=20, pady=(0, 10))
        self._populate_categories_list()

        # Botões de gerenciamento de categorias
        cat_input_row = ctk.CTkFrame(cat_sec, fg_color="transparent")
        cat_input_row.pack(fill="x", padx=20, pady=(0, 16))

        self.entry_new_cat = ctk.CTkEntry(
            cat_input_row,
            placeholder_text="Nova categoria (ex: banish cards from graveyard)...",
            fg_color=COLORS["bg_card_secondary"],
            border_color=COLORS["border"],
            height=34,
        )
        self.entry_new_cat.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            cat_input_row,
            text="+ Adicionar",
            width=90,
            height=34,
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_hover"],
            text_color=COLORS["text_dark"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_add_category,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            cat_input_row,
            text="- Remover",
            width=90,
            height=34,
            fg_color=COLORS["danger"],
            hover_color="#DC2626",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_remove_category,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            cat_input_row,
            text="↺ Restaurar Padrão",
            width=130,
            height=34,
            fg_color=COLORS["bg_card_secondary"],
            hover_color=COLORS["bg_card_hover"],
            border_width=1,
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=12),
            command=self._on_reset_categories,
        ).pack(side="left", padx=4)

        # Seção 4: Informações do Modelo Hugging Face
        model_sec = ctk.CTkFrame(
            page,
            corner_radius=12,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        model_sec.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            model_sec,
            text="🧠 Informações do Modelo de IA",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["gold"],
        ).pack(anchor="w", padx=20, pady=(16, 6))

        model_desc = (
            "• Identificador do Modelo: facebook/bart-large-mnli\n"
            "• Tipo de Tarefa: Zero-Shot Sequence Classification\n"
            "• Parâmetros: ~407M parâmetros (~1.6 GB)\n"
            "• Repositório Hugging Face: https://huggingface.co/facebook/bart-large-mnli"
        )
        ctk.CTkLabel(
            model_sec,
            text=model_desc,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 16))

        return page

    def _populate_categories_list(self):
        self.listbox_labels.delete(0, tk.END)
        for cat in self.candidate_labels:
            self.listbox_labels.insert(tk.END, f"  • {cat}")

    def _on_add_category(self):
        new_val = self.entry_new_cat.get().strip()
        if not new_val:
            return
        if new_val in self.candidate_labels:
            messagebox.showinfo("Aviso", "Esta categoria já existe.")
            return
        self.candidate_labels.append(new_val)
        self.entry_new_cat.delete(0, tk.END)
        self._populate_categories_list()

    def _on_remove_category(self):
        sel = self.listbox_labels.curselection()
        if not sel:
            messagebox.showinfo("Aviso", "Selecione uma categoria na lista para remover.")
            return
        idx = sel[0]
        if len(self.candidate_labels) <= 2:
            messagebox.showwarning("Aviso", "Mantenha ao menos 2 categorias para classificação.")
            return
        removed = self.candidate_labels.pop(idx)
        self._populate_categories_list()

    def _on_reset_categories(self):
        self.candidate_labels = list(estudoIA.candidate_labels)
        self._populate_categories_list()
        messagebox.showinfo("Restaurado", "Categorias restauradas para o padrão do projeto.")

    def _on_device_selection_changed(self, choice):
        if "GPU" in choice:
            self.current_device = 0
            self.lbl_device_badge.configure(text="🖥️ Disp: GPU (CUDA)")
            self.kpi_cards["device"].configure(text="GPU (CUDA)")
        else:
            self.current_device = -1
            self.lbl_device_badge.configure(text="🖥️ Disp: CPU")
            self.kpi_cards["device"].configure(text="CPU")

    def _on_change_csv_file(self):
        new_path = filedialog.askopenfilename(
            title="Selecione o arquivo CSV de Cartas",
            filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")],
        )
        if not new_path:
            return

        try:
            # Validação prévia das colunas mínimas
            sample_df = pd.read_csv(new_path, nrows=5)
            required_cols = ["name", "description"]
            missing = [c for c in required_cols if c not in sample_df.columns]
            if missing:
                messagebox.showerror(
                    "CSV Inválido",
                    f"O arquivo selecionado não contém as colunas obrigatórias: {missing}\nA base anterior foi mantida.",
                )
                return

            # Carregar base completa
            self.df = pd.read_csv(new_path)
            self.csv_path = new_path
            self.lbl_csv_path_display.configure(text=f"Caminho atual: {os.path.abspath(new_path)}")
            self.filtered_df = self.df.copy()
            self._update_dashboard_stats()
            self._refresh_database_filters()
            self._display_database_page(1)
            messagebox.showinfo("Sucesso", f"Base carregada com sucesso!\nTotal de {len(self.df):,} registros.")
        except Exception as e:
            messagebox.showerror("Erro ao carregar CSV", f"Falha ao processar o arquivo:\n{str(e)}\nOs dados anteriores foram preservados.")


def main():
    # Suporte a teste automatizado ou execução interativa
    is_test = "--test-mode" in sys.argv
    app = YuGiOhAIApp(headless_test=is_test)

    if is_test:
        print("[TEST] App inicializado com sucesso!")
        print(f"[TEST] Total de cartas no DataFrame: {len(app.df) if app.df is not None else 0}")
        print(f"[TEST] Categorias ativas: {len(app.candidate_labels)}")
        # Testa busca por nome
        app.entry_search.insert(0, "Dark Magician")
        app._on_search_triggered()
        print(f"[TEST] Cartas encontradas para 'Dark Magician': {len(app.filtered_df)}")
        # Testa busca por ID
        app.entry_search.delete(0, tk.END)
        app.entry_search.insert(0, "JUSH-EN040")
        app._on_search_triggered()
        print(f"[TEST] Cartas encontradas para 'JUSH-EN040': {len(app.filtered_df)}")
        # Testa envio para página de análise
        if len(app.filtered_df) > 0:
            card = app.filtered_df.iloc[0]
            app.set_card_for_analysis(card["name"], card["description"])
            print(f"[TEST] Nome na página de análise: {app.entry_card_name.get()}")
            print(f"[TEST] Efeito preenchido: {len(app.txt_card_effect.get('1.0', tk.END).strip())} caracteres")
        app.destroy()
        print("[TEST] Teste concluído com êxito.")
        return

    app.mainloop()


if __name__ == "__main__":
    main()
