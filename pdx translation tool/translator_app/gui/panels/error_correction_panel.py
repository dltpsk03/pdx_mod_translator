# translator_project/translator_app/gui/panels/error_correction_panel.py
import customtkinter as ctk
from ..tooltip import Tooltip

class ErrorCorrectionPanel(ctk.CTkFrame):
    def __init__(self, master, main_app, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.main_app = main_app

        self.grid_columnconfigure(1, weight=1)

        # Title
        self.error_correction_title_label = ctk.CTkLabel(self, font=ctk.CTkFont(size=13, weight="bold"))
        self.error_correction_title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(7,10), sticky="w")

        # Validation Level Selection (replaces simple enable/disable)
        self.validation_level_label = ctk.CTkLabel(self)
        self.validation_level_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.validation_level_var = ctk.StringVar(value="standard")
        self.validation_level_combo = ctk.CTkComboBox(
            self, 
            variable=self.validation_level_var,
            values=["off", "basic", "standard", "strict"],
            state='readonly',
            command=self.on_validation_level_changed
        )
        self.validation_level_combo.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.validation_level_tooltip = Tooltip(self.validation_level_combo, "")

        # Auto-activation threshold
        self.auto_threshold_label = ctk.CTkLabel(self)
        self.auto_threshold_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        
        self.auto_threshold_var = ctk.DoubleVar(value=0.2)  # 20% error rate
        self.auto_threshold_slider = ctk.CTkSlider(
            self, 
            variable=self.auto_threshold_var,
            from_=0.05,
            to=0.5,
            number_of_steps=18
        )
        self.auto_threshold_slider.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        
        self.auto_threshold_value_label = ctk.CTkLabel(self)
        self.auto_threshold_value_label.grid(row=2, column=2, padx=5, pady=5)
        
        # Bind threshold slider update
        self.auto_threshold_var.trace('w', self.update_threshold_label)

        # Auto-fix options frame
        self.auto_fix_frame = ctk.CTkFrame(self)
        self.auto_fix_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.auto_fix_frame.grid_columnconfigure(0, weight=1)

        self.auto_fix_title = ctk.CTkLabel(self.auto_fix_frame, font=ctk.CTkFont(size=11, weight="bold"))
        self.auto_fix_title.grid(row=0, column=0, sticky="w", padx=10, pady=(10,5))

        # YAML syntax correction
        self.fix_yaml_var = ctk.BooleanVar(value=True)
        self.fix_yaml_checkbox = ctk.CTkCheckBox(self.auto_fix_frame, variable=self.fix_yaml_var)
        self.fix_yaml_checkbox.grid(row=1, column=0, sticky="w", padx=20, pady=2)
        
        # Paradox format preservation
        self.preserve_format_var = ctk.BooleanVar(value=True)
        self.preserve_format_checkbox = ctk.CTkCheckBox(self.auto_fix_frame, variable=self.preserve_format_var)
        self.preserve_format_checkbox.grid(row=2, column=0, sticky="w", padx=20, pady=2)
        
        # Remove duplicates
        self.remove_duplicates_var = ctk.BooleanVar(value=True)
        self.remove_duplicates_checkbox = ctk.CTkCheckBox(self.auto_fix_frame, variable=self.remove_duplicates_var)
        self.remove_duplicates_checkbox.grid(row=3, column=0, sticky="w", padx=20, pady=2)
        
        # Fix incomplete translations
        self.fix_incomplete_var = ctk.BooleanVar(value=False)
        self.fix_incomplete_checkbox = ctk.CTkCheckBox(self.auto_fix_frame, variable=self.fix_incomplete_var)
        self.fix_incomplete_checkbox.grid(row=4, column=0, sticky="w", padx=20, pady=2)

        # Duplicate handling strategy
        self.duplicate_strategy_label = ctk.CTkLabel(self)
        self.duplicate_strategy_label.grid(row=4, column=0, sticky="w", padx=10, pady=(15,5))
        
        self.duplicate_strategy_var = ctk.StringVar(value="keep_first")
        self.duplicate_strategy_combo = ctk.CTkComboBox(
            self, 
            variable=self.duplicate_strategy_var,
            values=["keep_first", "keep_last", "keep_longest", "keep_shortest"],
            state='readonly'
        )
        self.duplicate_strategy_combo.grid(row=4, column=1, sticky="ew", padx=10, pady=(15,5))
        self.duplicate_strategy_tooltip = Tooltip(self.duplicate_strategy_combo, "")

        # Quality threshold settings
        self.quality_frame = ctk.CTkFrame(self)
        self.quality_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.quality_frame.grid_columnconfigure(1, weight=1)

        self.quality_title = ctk.CTkLabel(self.quality_frame, font=ctk.CTkFont(size=11, weight="bold"))
        self.quality_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10,5))

        # Minimum translation length ratio
        self.min_length_label = ctk.CTkLabel(self.quality_frame)
        self.min_length_label.grid(row=1, column=0, sticky="w", padx=10, pady=2)
        
        self.min_length_var = ctk.DoubleVar(value=0.3)
        self.min_length_slider = ctk.CTkSlider(
            self.quality_frame, 
            variable=self.min_length_var,
            from_=0.1,
            to=0.8,
            number_of_steps=14
        )
        self.min_length_slider.grid(row=1, column=1, sticky="ew", padx=10, pady=2)
        
        self.min_length_value_label = ctk.CTkLabel(self.quality_frame)
        self.min_length_value_label.grid(row=1, column=2, padx=5, pady=2)

        # Maximum translation length ratio
        self.max_length_label = ctk.CTkLabel(self.quality_frame)
        self.max_length_label.grid(row=2, column=0, sticky="w", padx=10, pady=2)
        
        self.max_length_var = ctk.DoubleVar(value=3.0)
        self.max_length_slider = ctk.CTkSlider(
            self.quality_frame, 
            variable=self.max_length_var,
            from_=2.0,
            to=5.0,
            number_of_steps=15
        )
        self.max_length_slider.grid(row=2, column=1, sticky="ew", padx=10, pady=2)
        
        self.max_length_value_label = ctk.CTkLabel(self.quality_frame)
        self.max_length_value_label.grid(row=2, column=2, padx=5, pady=2)

        # Bind slider updates
        self.min_length_var.trace('w', self.update_length_labels)
        self.max_length_var.trace('w', self.update_length_labels)

        # Statistics display
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.stats_frame.grid_columnconfigure(1, weight=1)

        self.stats_title = ctk.CTkLabel(self.stats_frame, font=ctk.CTkFont(size=11, weight="bold"))
        self.stats_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10,5))

        self.stats_text = ctk.CTkTextbox(self.stats_frame, height=80)
        self.stats_text.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0,10))

        self.update_language()
        self.update_length_labels()
    
    def on_validation_level_changed(self, level):
        """Handle validation level change"""
        # Enable/disable options based on validation level
        if level == "off":
            state = "disabled"
            self.auto_threshold_slider.configure(state="disabled")
        else:
            state = "normal"
            self.auto_threshold_slider.configure(state="normal")
        
        # Update all correction options
        self.fix_yaml_checkbox.configure(state=state)
        self.preserve_format_checkbox.configure(state=state)
        self.remove_duplicates_checkbox.configure(state=state)
        self.fix_incomplete_checkbox.configure(state=state)
        self.duplicate_strategy_combo.configure(state=state)
        self.min_length_slider.configure(state=state)
        self.max_length_slider.configure(state=state)
        
        # Update description text based on level
        self.update_level_description(level)
    
    def update_level_description(self, level):
        """Update description text based on validation level"""
        descriptions = {
            "off": "No validation - fastest translation speed",
            "basic": "Key translation + YAML quotes only - good speed/quality balance", 
            "standard": "Full validation with retry logic - recommended for most users",
            "strict": "Maximum validation - slowest but highest quality"
        }
        
        # Update tooltip with description
        description = descriptions.get(level, "")
        self.validation_level_tooltip.update_text(description)
    
    def update_threshold_label(self, *args):
        """Update the auto-activation threshold label"""
        threshold = self.auto_threshold_var.get()
        self.auto_threshold_value_label.configure(text=f"{threshold:.0%}")
    
    def get_session_error_rate(self):
        """Get current session error rate from main app if available"""
        if hasattr(self.main_app, 'translator_engine'):
            engine = self.main_app.translator_engine
            if hasattr(engine, 'error_detector') and hasattr(engine.error_detector, 'get_current_error_rate'):
                return engine.error_detector.get_current_error_rate()
        return 0.0
    
    def update_length_labels(self, *args):
        """Update the length ratio value labels"""
        min_val = self.min_length_var.get()
        max_val = self.max_length_var.get()
        self.min_length_value_label.configure(text=f"{min_val:.1f}")
        self.max_length_value_label.configure(text=f"{max_val:.1f}")
    
    def get_error_correction_settings(self):
        """Get current error correction settings as a dictionary"""
        return {
            'validation_level': self.validation_level_var.get(),
            'auto_activation_threshold': self.auto_threshold_var.get(),
            'auto_fix': {
                'yaml_syntax': self.fix_yaml_var.get(),
                'preserve_format': self.preserve_format_var.get(),
                'remove_duplicates': self.remove_duplicates_var.get(),
                'fix_incomplete': self.fix_incomplete_var.get()
            },
            'duplicate_strategy': self.duplicate_strategy_var.get(),
            'quality_thresholds': {
                'min_length_ratio': self.min_length_var.get(),
                'max_length_ratio': self.max_length_var.get()
            },
            # Add performance optimization settings
            'performance_optimization': {
                'enable_fast_mode': self.validation_level_var.get() in ['off', 'basic'],
                'dynamic_batch_sizing': True,
                'adaptive_concurrency': True
            }
        }
    
    def set_error_correction_settings(self, settings):
        """Set error correction settings from dictionary"""
        if not isinstance(settings, dict):
            return
        
        # Handle both old and new settings format
        if 'validation_level' in settings:
            self.validation_level_var.set(settings.get('validation_level', 'standard'))
        else:
            # Convert old format to new
            enabled = settings.get('enabled', True)
            strictness = settings.get('strictness', 'normal')
            if not enabled:
                self.validation_level_var.set('off')
            elif strictness == 'strict':
                self.validation_level_var.set('strict')
            else:
                self.validation_level_var.set('standard')
        
        self.auto_threshold_var.set(settings.get('auto_activation_threshold', 0.2))
        
        auto_fix = settings.get('auto_fix', {})
        self.fix_yaml_var.set(auto_fix.get('yaml_syntax', True))
        self.preserve_format_var.set(auto_fix.get('preserve_format', True))
        self.remove_duplicates_var.set(auto_fix.get('remove_duplicates', True))
        self.fix_incomplete_var.set(auto_fix.get('fix_incomplete', False))
        
        self.duplicate_strategy_var.set(settings.get('duplicate_strategy', 'keep_first'))
        
        thresholds = settings.get('quality_thresholds', {})
        self.min_length_var.set(thresholds.get('min_length_ratio', 0.3))
        self.max_length_var.set(thresholds.get('max_length_ratio', 3.0))
        
        # Update UI state based on validation level
        self.on_validation_level_changed(self.validation_level_var.get())
        self.update_threshold_label()
    
    def update_stats(self, stats_text):
        """Update the statistics display"""
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", stats_text)
    
    def update_language(self):
        """Update UI text based on current language"""
        texts = self.main_app.texts
        
        self.error_correction_title_label.configure(text=texts.get("error_correction_title", "Smart Error Correction & Quality Control"))
        
        self.validation_level_label.configure(text=texts.get("validation_level", "Validation Level:"))
        self.validation_level_tooltip.update_text(texts.get("validation_level_tooltip", 
            "Control validation strictness vs speed:\n• Off: Fastest (no validation)\n• Basic: Key + YAML only\n• Standard: Full validation (recommended)\n• Strict: Maximum quality"))
        
        self.auto_threshold_label.configure(text=texts.get("auto_threshold", "Auto-Strict Threshold:"))
        
        self.auto_fix_title.configure(text=texts.get("auto_fix_options", "Auto-Fix Options"))
        self.fix_yaml_checkbox.configure(text=texts.get("fix_yaml_syntax", "Fix YAML syntax errors"))
        self.preserve_format_checkbox.configure(text=texts.get("preserve_paradox_format", "Preserve Paradox game format (keys, variables, tags)"))
        self.remove_duplicates_checkbox.configure(text=texts.get("remove_duplicates", "Remove duplicate entries"))
        self.fix_incomplete_checkbox.configure(text=texts.get("fix_incomplete_translations", "Fix incomplete translations"))
        
        self.duplicate_strategy_label.configure(text=texts.get("duplicate_strategy", "Duplicate Strategy:"))
        self.duplicate_strategy_tooltip.update_text(texts.get("duplicate_strategy_tooltip", "How to handle duplicate entries"))
        
        self.quality_title.configure(text=texts.get("quality_thresholds", "Quality Thresholds"))
        self.min_length_label.configure(text=texts.get("min_length_ratio", "Min Length Ratio:"))
        self.max_length_label.configure(text=texts.get("max_length_ratio", "Max Length Ratio:"))
        
        self.stats_title.configure(text=texts.get("correction_stats", "Real-time Statistics"))
        
        # Initialize threshold label
        self.update_threshold_label()