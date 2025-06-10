import customtkinter as ctk
import os
import yaml
import threading
import codecs
from collections import defaultdict
from tkinter import filedialog, messagebox
from ...utils.localization import get_text


class TermConsistencyChecker(ctk.CTkToplevel):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        self.analysis_running = False
        self.inconsistencies = {}
        
        self.setup_window()
        self.create_widgets()
        
    def setup_window(self):
        self.title(get_text("consistency_checker_title"))
        self.geometry("1200x800")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.lift()
        self.focus()
        
    def create_widgets(self):
        # Control frame
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        control_frame.grid_columnconfigure(4, weight=1)
        
        # Analysis button
        self.analyze_btn = ctk.CTkButton(
            control_frame,
            text=get_text("analyze_consistency"),
            command=self.start_analysis,
            width=150
        )
        self.analyze_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # Minimum occurrences setting
        ctk.CTkLabel(
            control_frame,
            text=get_text("min_occurrences")
        ).grid(row=0, column=1, padx=(15, 5), pady=5)
        
        self.min_occur_entry = ctk.CTkEntry(control_frame, width=60)
        self.min_occur_entry.insert(0, "2")
        self.min_occur_entry.grid(row=0, column=2, padx=5, pady=5)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(control_frame)
        self.progress_bar.grid(row=0, column=3, padx=15, pady=5, sticky="ew")
        self.progress_bar.set(0)
        
        # Export button
        self.export_btn = ctk.CTkButton(
            control_frame,
            text=get_text("export_glossary"),
            command=self.export_glossary,
            state="disabled",
            width=120
        )
        self.export_btn.grid(row=0, column=5, padx=5, pady=5)
        
        # Main content frame with tabs
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Tab view
        self.tab_view = ctk.CTkTabview(main_frame)
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Overview tab
        self.overview_tab = self.tab_view.add("Overview")
        self.overview_tab.grid_columnconfigure(0, weight=1)
        self.overview_tab.grid_rowconfigure(0, weight=1)
        
        # Side-by-side comparison tab
        self.comparison_tab = self.tab_view.add("Detailed Comparison")
        self.comparison_tab.grid_columnconfigure(0, weight=1)
        self.comparison_tab.grid_columnconfigure(1, weight=1)
        self.comparison_tab.grid_rowconfigure(1, weight=1)
        
        self.create_overview_tab()
        self.create_comparison_tab()
        
    def create_overview_tab(self):
        # Overview results table (existing functionality)
        self.results_table = ctk.CTkScrollableFrame(
            self.overview_tab,
            label_text=get_text("tab_inconsistencies")
        )
        self.results_table.grid(row=0, column=0, sticky="nsew")
        self.results_table.grid_columnconfigure(0, weight=1)
        self.results_table.grid_columnconfigure(1, weight=2)
        self.results_table.grid_columnconfigure(2, weight=1)
        
    def create_comparison_tab(self):
        # Search and filter frame
        filter_frame = ctk.CTkFrame(self.comparison_tab)
        filter_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        filter_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(filter_frame, text="Search:").grid(row=0, column=0, padx=5, pady=5)
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Filter terms...")
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.filter_comparison_results)
        
        # Term list frame (left side)
        terms_frame = ctk.CTkFrame(self.comparison_tab)
        terms_frame.grid(row=1, column=0, sticky="nsew", padx=(5, 2), pady=5)
        terms_frame.grid_columnconfigure(0, weight=1)
        terms_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(terms_frame, text="Inconsistent Terms", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=5)
        
        self.terms_listbox = ctk.CTkScrollableFrame(terms_frame)
        self.terms_listbox.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.terms_listbox.grid_columnconfigure(0, weight=1)
        
        # Details frame (right side)
        details_frame = ctk.CTkFrame(self.comparison_tab)
        details_frame.grid(row=1, column=1, sticky="nsew", padx=(2, 5), pady=5)
        details_frame.grid_columnconfigure(0, weight=1)
        details_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(details_frame, text="Translation Variants", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=5)
        
        self.details_frame_content = ctk.CTkScrollableFrame(details_frame)
        self.details_frame_content.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.details_frame_content.grid_columnconfigure(0, weight=1)
        self.details_frame_content.grid_columnconfigure(1, weight=1)
        
        self.selected_term = None
        
    def on_close(self):
        if self.analysis_running:
            messagebox.showwarning(
                get_text("warn_title"),
                get_text("analyzing"),
                parent=self
            )
            return
        self.destroy()
        
    def start_analysis(self):
        if self.analysis_running:
            return
            
        input_folder = self.main_app.input_folder_var.get()
        output_folder = self.main_app.output_folder_var.get()
        
        if not input_folder or not output_folder:
            messagebox.showerror(
                get_text("error_title"),
                get_text("comparison_review_select_folders_first"),
                parent=self
            )
            return
            
        if not os.path.exists(input_folder) or not os.path.exists(output_folder):
            messagebox.showerror(
                get_text("error_title"),
                "Selected folders do not exist",
                parent=self
            )
            return
            
        try:
            min_occurrences = int(self.min_occur_entry.get())
            if min_occurrences < 1:
                raise ValueError()
        except ValueError:
            messagebox.showerror(
                get_text("error_title"),
                get_text("error_numeric_setting_invalid"),
                parent=self
            )
            return
            
        self.clear_results()
        self.set_analysis_state(True)
        
        thread = threading.Thread(
            target=self.run_analysis,
            args=(input_folder, output_folder, min_occurrences),
            daemon=True
        )
        thread.start()
        
    def set_analysis_state(self, running):
        self.analysis_running = running
        if running:
            self.analyze_btn.configure(text=get_text("analyzing"), state="disabled")
            self.progress_bar.set(0)
        else:
            self.analyze_btn.configure(text=get_text("analyze_consistency"), state="normal")
            self.progress_bar.set(1)
            
    def clear_results(self):
        self.clear_all_results()
        self.inconsistencies = {}
        self.export_btn.configure(state="disabled")
        
    def run_analysis(self, input_folder, output_folder, min_occurrences):
        try:
            # Get language codes
            source_lang = self.main_app.source_lang_for_api_var.get()
            target_lang = self.main_app.target_lang_for_api_var.get()
            
            source_code = self.main_app.translator_engine.get_language_code(source_lang)
            target_code = self.main_app.translator_engine.get_language_code(target_lang)
            
            self.after(0, lambda: self.progress_bar.set(0.1))
            
            # Find file pairs
            file_pairs = self.find_file_pairs(input_folder, output_folder, source_code, target_code)
            
            if not file_pairs:
                self.after(0, self.show_no_files_error)
                return
                
            self.after(0, lambda: self.progress_bar.set(0.2))
            
            # Analyze files
            term_translations = self.analyze_file_pairs(file_pairs)
            
            self.after(0, lambda: self.progress_bar.set(0.8))
            
            # Filter inconsistencies
            inconsistencies = self.filter_inconsistencies(term_translations, min_occurrences)
            
            self.after(0, lambda: self.progress_bar.set(0.9))
            
            # Update UI
            self.inconsistencies = inconsistencies
            self.after(0, self.display_results)
            
        except Exception as e:
            self.after(0, lambda: self.show_analysis_error(str(e)))
        finally:
            self.after(0, lambda: self.set_analysis_state(False))
            
    def find_file_pairs(self, input_folder, output_folder, source_code, target_code):
        file_pairs = []
        source_pattern = f"l_{source_code}"
        target_pattern = f"l_{target_code}"
        
        # Debug logging
        print(f"Looking for source files with pattern: {source_pattern}")
        print(f"Looking for target files with pattern: {target_pattern}")
        print(f"Input folder: {input_folder}")
        print(f"Output folder: {output_folder}")
        
        # Find source files
        source_files = {}
        for root, _, files in os.walk(input_folder):
            for file in files:
                if file.lower().endswith(('.yml', '.yaml')):
                    print(f"Found YAML file in input: {file}")
                    if source_pattern in file.lower():
                        # More flexible base name extraction
                        base_name = file.lower()
                        for ext in ['.yml', '.yaml']:
                            base_name = base_name.replace(ext, '')
                        base_name = base_name.replace(source_pattern, '')
                        # Clean up underscores at start/end
                        base_name = base_name.strip('_')
                        source_files[base_name] = os.path.join(root, file)
                        print(f"Source file mapped: {base_name} -> {file}")
                    
        # Find corresponding target files
        for root, _, files in os.walk(output_folder):
            for file in files:
                if file.lower().endswith(('.yml', '.yaml')):
                    print(f"Found YAML file in output: {file}")
                    if target_pattern in file.lower():
                        # More flexible base name extraction
                        base_name = file.lower()
                        for ext in ['.yml', '.yaml']:
                            base_name = base_name.replace(ext, '')
                        base_name = base_name.replace(target_pattern, '')
                        # Clean up underscores at start/end
                        base_name = base_name.strip('_')
                        if base_name in source_files:
                            file_pairs.append((source_files[base_name], os.path.join(root, file)))
                            print(f"Matched pair: {source_files[base_name]} <-> {os.path.join(root, file)}")
                        else:
                            print(f"No matching source file for target: {file} (base: {base_name})")
        
        print(f"Total file pairs found: {len(file_pairs)}")
        return file_pairs
        
    def analyze_file_pairs(self, file_pairs):
        term_translations = defaultdict(lambda: defaultdict(int))
        total_pairs = len(file_pairs)
        
        for i, (source_file, target_file) in enumerate(file_pairs):
            progress = 0.2 + (0.6 * i / total_pairs)
            self.after(0, lambda p=progress: self.progress_bar.set(p))
            
            source_data = self.load_yaml_file(source_file)
            target_data = self.load_yaml_file(target_file)
            
            self.compare_translations(source_data, target_data, term_translations)
            
        return term_translations
        
    def load_yaml_file(self, filepath):
        try:
            print(f"Loading YAML file: {filepath}")
            if not os.path.exists(filepath):
                print(f"File does not exist: {filepath}")
                return {}
                
            with codecs.open(filepath, 'r', 'utf-8-sig') as f:
                content = f.read()
            
            if not content.strip():
                print(f"File is empty: {filepath}")
                return {}
                
            # Handle YAML files that might not be properly formatted
            data = {}
            line_count = 0
            for line_num, line in enumerate(content.split('\n'), 1):
                line = line.strip()
                if ':' in line and not line.startswith('#') and line:
                    try:
                        # Handle cases where there might be multiple colons
                        colon_index = line.find(':')
                        key = line[:colon_index].strip()
                        value = line[colon_index + 1:].strip()
                        
                        # Extract quoted strings
                        if value.startswith('"') and value.endswith('"') and len(value) > 1:
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'") and len(value) > 1:
                            value = value[1:-1]
                        
                        # Skip empty values or keys with special characters that aren't translations
                        if key and value and not key.startswith(' ') and len(value) > 1:
                            # Skip lines that look like comments or structural YAML
                            if not any(char in key for char in ['[', ']', '{', '}', '@', '$']):
                                data[key] = value
                                line_count += 1
                    except Exception as e:
                        print(f"Error parsing line {line_num} in {filepath}: {e}")
                        continue
            
            print(f"Loaded {line_count} entries from {filepath}")
            return data
            
        except Exception as e:
            print(f"Error loading YAML file {filepath}: {e}")
            return {}
            
    def compare_translations(self, source_data, target_data, term_translations):
        for key, source_term in source_data.items():
            if key in target_data:
                target_term = target_data[key]
                if source_term and target_term:
                    # Clean up terms
                    source_term = source_term.strip()
                    target_term = target_term.strip()
                    
                    if len(source_term) > 2 and len(target_term) > 2:
                        term_translations[source_term][target_term] += 1
                        
    def filter_inconsistencies(self, term_translations, min_occurrences):
        inconsistencies = {}
        
        for source_term, translations in term_translations.items():
            if len(translations) > 1:
                total_count = sum(translations.values())
                if total_count >= min_occurrences:
                    inconsistencies[source_term] = dict(translations)
                    
        return inconsistencies
        
    def display_results(self):
        self.clear_all_results()
        
        if not self.inconsistencies:
            self.show_no_inconsistencies()
            return
            
        # Populate overview tab
        self.create_table_headers()
        self.populate_table()
        
        # Populate comparison tab
        self.populate_comparison_tab()
        
        self.export_btn.configure(state="normal")
        
        messagebox.showinfo(
            get_text("analysis_complete"),
            f"Found {len(self.inconsistencies)} inconsistent terms",
            parent=self
        )
        
    def clear_all_results(self):
        # Clear overview tab
        for widget in self.results_table.winfo_children():
            widget.destroy()
        # Clear comparison tab
        for widget in self.terms_listbox.winfo_children():
            widget.destroy()
        for widget in self.details_frame_content.winfo_children():
            widget.destroy()
        self.selected_term = None
            
    def clear_table(self):
        for widget in self.results_table.winfo_children():
            widget.destroy()
            
    def populate_comparison_tab(self):
        # Populate terms list
        sorted_items = sorted(
            self.inconsistencies.items(),
            key=lambda x: sum(x[1].values()),
            reverse=True
        )
        
        for i, (source_term, translations) in enumerate(sorted_items):
            term_button = ctk.CTkButton(
                self.terms_listbox,
                text=f"{source_term} ({sum(translations.values())})",
                command=lambda term=source_term: self.select_term(term),
                anchor="w",
                height=30
            )
            term_button.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            
    def select_term(self, term):
        self.selected_term = term
        self.display_term_details(term)
        
    def display_term_details(self, term):
        # Clear previous details
        for widget in self.details_frame_content.winfo_children():
            widget.destroy()
            
        if term not in self.inconsistencies:
            return
            
        translations = self.inconsistencies[term]
        
        # Original term section
        original_frame = ctk.CTkFrame(self.details_frame_content)
        original_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        original_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            original_frame,
            text="Original Term:",
            font=ctk.CTkFont(weight="bold", size=14)
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        original_textbox = ctk.CTkTextbox(original_frame, height=60)
        original_textbox.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        original_textbox.insert("1.0", term)
        original_textbox.configure(state="disabled")
        
        # Translations header
        ctk.CTkLabel(
            self.details_frame_content,
            text="Translation Variants:",
            font=ctk.CTkFont(weight="bold", size=14)
        ).grid(row=1, column=0, columnspan=2, padx=5, pady=(15, 5), sticky="w")
        
        # Sort translations by frequency
        sorted_translations = sorted(translations.items(), key=lambda x: x[1], reverse=True)
        
        for i, (translation, count) in enumerate(sorted_translations):
            # Translation variant frame
            variant_frame = ctk.CTkFrame(self.details_frame_content)
            variant_frame.grid(row=i+2, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
            variant_frame.grid_columnconfigure(1, weight=1)
            
            # Count badge
            count_label = ctk.CTkLabel(
                variant_frame,
                text=f"{count}x",
                font=ctk.CTkFont(weight="bold"),
                width=50
            )
            count_label.grid(row=0, column=0, padx=5, pady=5)
            
            # Translation text
            translation_textbox = ctk.CTkTextbox(variant_frame, height=40)
            translation_textbox.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
            translation_textbox.insert("1.0", translation)
            translation_textbox.configure(state="disabled")
            
            # Color coding for most/least common
            if i == 0:  # Most common
                count_label.configure(fg_color="green")
            elif i == len(sorted_translations) - 1 and len(sorted_translations) > 1:  # Least common
                count_label.configure(fg_color="red")
                
    def filter_comparison_results(self, event=None):
        search_term = self.search_entry.get().lower()
        
        # Clear and repopulate terms list with filtered results
        for widget in self.terms_listbox.winfo_children():
            widget.destroy()
            
        if not self.inconsistencies:
            return
            
        sorted_items = sorted(
            self.inconsistencies.items(),
            key=lambda x: sum(x[1].values()),
            reverse=True
        )
        
        filtered_items = []
        if search_term:
            for source_term, translations in sorted_items:
                if (search_term in source_term.lower() or 
                    any(search_term in trans.lower() for trans in translations.keys())):
                    filtered_items.append((source_term, translations))
        else:
            filtered_items = sorted_items
            
        for i, (source_term, translations) in enumerate(filtered_items):
            term_button = ctk.CTkButton(
                self.terms_listbox,
                text=f"{source_term} ({sum(translations.values())})",
                command=lambda term=source_term: self.select_term(term),
                anchor="w",
                height=30
            )
            term_button.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            
    def show_no_inconsistencies(self):
        label = ctk.CTkLabel(
            self.results_table,
            text="No term inconsistencies found",
            font=ctk.CTkFont(size=14)
        )
        label.grid(row=0, column=0, pady=20)
        
    def create_table_headers(self):
        header_font = ctk.CTkFont(weight="bold", size=12)
        
        ctk.CTkLabel(
            self.results_table,
            text="Original Term",
            font=header_font
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(
            self.results_table,
            text="Translation Variants",
            font=header_font
        ).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(
            self.results_table,
            text="Count",
            font=header_font
        ).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
    def populate_table(self):
        sorted_items = sorted(
            self.inconsistencies.items(),
            key=lambda x: sum(x[1].values()),
            reverse=True
        )
        
        for row, (source_term, translations) in enumerate(sorted_items, 1):
            # Source term
            ctk.CTkLabel(
                self.results_table,
                text=source_term,
                anchor="w"
            ).grid(row=row, column=0, padx=5, pady=2, sticky="ew")
            
            # Translation variants
            variants_text = "\n".join([
                f'"{trans}" ({count})'
                for trans, count in sorted(translations.items(), key=lambda x: x[1], reverse=True)
            ])
            
            ctk.CTkLabel(
                self.results_table,
                text=variants_text,
                anchor="w",
                justify="left"
            ).grid(row=row, column=1, padx=5, pady=2, sticky="ew")
            
            # Total count
            total_count = sum(translations.values())
            ctk.CTkLabel(
                self.results_table,
                text=str(total_count),
                anchor="w"
            ).grid(row=row, column=2, padx=5, pady=2, sticky="ew")
            
    def export_glossary(self):
        if not self.inconsistencies:
            return
            
        filepath = filedialog.asksaveasfilename(
            title=get_text("export_glossary_title"),
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            parent=self
        )
        
        if not filepath:
            return
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# Term Consistency Glossary\n")
                f.write("# Format: original_term:preferred_translation\n\n")
                
                for source_term, translations in self.inconsistencies.items():
                    # Use most common translation
                    preferred = max(translations, key=translations.get)
                    f.write(f"{source_term}:{preferred}\n")
                    
            messagebox.showinfo(
                get_text("info_title"),
                f"Glossary exported to {filepath}",
                parent=self
            )
            
        except Exception as e:
            messagebox.showerror(
                get_text("error_title"),
                f"Export failed: {str(e)}",
                parent=self
            )
            
    def show_no_files_error(self):
        messagebox.showerror(
            get_text("error_title"),
            "No matching translation files found",
            parent=self
        )
        
    def show_analysis_error(self, error):
        messagebox.showerror(
            get_text("error_title"),
            f"Analysis failed: {error}",
            parent=self
        )
        
    def update_language(self):
        self.title(get_text("consistency_checker_title"))
        self.analyze_btn.configure(text=get_text("analyze_consistency"))
        self.export_btn.configure(text=get_text("export_glossary"))
        self.results_table.configure(label_text=get_text("tab_inconsistencies"))