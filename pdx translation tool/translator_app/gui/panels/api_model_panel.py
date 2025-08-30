# translator_project/translator_app/gui/panels/api_model_panel.py
import customtkinter as ctk
from ..tooltip import Tooltip
from ...core.api_providers import APIProviderFactory

class APIModelPanel(ctk.CTkFrame):
    def __init__(self, master, main_app, **kwargs):
        # 프리미엄 스타일링
        super().__init__(
            master, 
            corner_radius=16, 
            border_width=1,
            border_color=("#E5E7EB", "#4B5563"),
            fg_color=("#FFFFFF", "#1F2937"),
            **kwargs
        )
        self.main_app = main_app

        self.grid_columnconfigure(1, weight=1)

        # 더 고급스러운 제목 스타일링
        self.api_model_title_label = ctk.CTkLabel(
            self, 
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("#1F2937", "#F3F4F6")
        )
        self.api_model_title_label.grid(row=0, column=0, columnspan=3, padx=15, pady=(12,15), sticky="w")

        # API Provider selection
        self.provider_label_widget = ctk.CTkLabel(self)
        self.provider_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        # Get available providers
        available_providers = APIProviderFactory.get_available_providers()
        if not available_providers:
            available_providers = ["gemini"]  # Fallback
            
        self.provider_combo_widget = ctk.CTkComboBox(
            self, 
            variable=self.main_app.api_provider_var, 
            values=available_providers, 
            state='readonly',
            command=self.on_provider_changed
        )
        self.provider_combo_widget.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        self.provider_combo_tooltip = Tooltip(self.provider_combo_widget, "")

        self.api_key_label_widget = ctk.CTkLabel(self)
        self.api_key_label_widget.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.api_entry_widget = ctk.CTkEntry(self, textvariable=self.main_app.api_key_var, show="*", placeholder_text="Enter API Key")
        self.api_entry_widget.grid(row=2, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        self.api_entry_tooltip = Tooltip(self.api_entry_widget, "")

        self.model_label_widget = ctk.CTkLabel(self)
        self.model_label_widget.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.model_combo_widget = ctk.CTkComboBox(self, values=self.main_app.available_models, state='readonly', command=self.on_model_changed)
        self.model_combo_widget.grid(row=3, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        self.model_combo_tooltip = Tooltip(self.model_combo_widget, "")

        # 프리미엄 테스트 연결 버튼
        self.test_button = ctk.CTkButton(
            self, 
            text="🔗 Test Connection", 
            command=self.test_connection,
            width=140,
            height=36,
            corner_radius=12,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#3B82F6", "#2563EB"),
            hover_color=("#2563EB", "#1D4ED8"),
            border_width=0
        )
        self.test_button.grid(row=4, column=1, columnspan=2, padx=15, pady=15, sticky="ew")

        self.update_language()
    
    def on_provider_changed(self, provider_name):
        """Update available models when provider changes"""
        try:
            model_keys = APIProviderFactory.get_models_for_provider(provider_name)
            # Create display names for UI
            display_names = [APIProviderFactory.get_model_display_name(key) for key in model_keys]
            
            self.model_combo_widget.configure(values=display_names)
            if model_keys:
                # Set first model as default (using the actual key, not display name)
                self.main_app.model_name_var.set(model_keys[0])
                # But show the display name in the combo box
                self.model_combo_widget.set(display_names[0])
            
            # Store both for mapping
            self.model_keys = model_keys
            self.display_names = display_names
            
            # Update main app's available models (use actual keys)
            self.main_app.available_models = model_keys
            
            # Update placeholder text based on provider
            provider_placeholders = {
                'gemini': 'Enter Google Gemini API Key',
                'claude': 'Enter Anthropic Claude API Key', 
                'openai': 'Enter OpenAI API Key'
            }
            placeholder = provider_placeholders.get(provider_name, 'Enter API Key')
            self.api_entry_widget.configure(placeholder_text=placeholder)
            
        except Exception as e:
            print(f"Error updating provider: {e}")
    
    def on_model_changed(self, display_name):
        """Update model variable when model selection changes"""
        try:
            if hasattr(self, 'display_names') and hasattr(self, 'model_keys'):
                # Find the corresponding model key for the selected display name
                if display_name in self.display_names:
                    index = self.display_names.index(display_name)
                    model_key = self.model_keys[index]
                    # Set the actual model key in the variable
                    self.main_app.model_name_var.set(model_key)
        except Exception as e:
            print(f"Error setting model: {e}")
    
    def test_connection(self):
        """Test API connection with user-friendly messages"""
        try:
            provider_type = self.main_app.api_provider_var.get()
            api_key = self.main_app.api_key_var.get()
            
            # Use the new validation method for better error messages
            is_valid, message = APIProviderFactory.validate_provider_setup(provider_type, api_key)
            
            if is_valid:
                self.show_connection_result(message, True)
            else:
                self.show_connection_result(message, False)
                
        except Exception as e:
            self.show_connection_result(f"연결 테스트 중 오류 발생: {str(e)}", False)
    
    def show_connection_result(self, message, success):
        """Show connection test result"""
        # Create a temporary label to show the result
        if hasattr(self, 'result_label'):
            self.result_label.destroy()
        
        color = "green" if success else "red"
        self.result_label = ctk.CTkLabel(
            self, 
            text=message, 
            text_color=color,
            font=ctk.CTkFont(size=11)
        )
        self.result_label.grid(row=5, column=0, columnspan=3, padx=10, pady=5)
        
        # Remove the label after 3 seconds
        self.after(3000, lambda: self.result_label.destroy() if hasattr(self, 'result_label') else None)

    def update_language(self):
        texts = self.main_app.texts
        self.api_model_title_label.configure(text=texts.get("api_settings_frame"))
        self.provider_label_widget.configure(text=texts.get("api_provider_label", "API Provider"))
        self.provider_combo_tooltip.update_text(texts.get("api_provider_tooltip", "Select API provider (Gemini, Claude, or OpenAI)"))
        self.api_key_label_widget.configure(text=texts.get("api_key_label"))
        self.api_entry_tooltip.update_text(texts.get("api_key_tooltip"))
        self.model_label_widget.configure(text=texts.get("model_label"))
        self.model_combo_tooltip.update_text(texts.get("model_tooltip"))
        self.test_button.configure(text=texts.get("test_connection_button", "Test Connection"))