# English

[English](README_EN.md) | [中文](README_ZH.md) | [한국어](README.md)

A powerful GUI application for translating Paradox game mods. It leverages the Google Gemini API to efficiently translate YAML localization files.

![UI Setting](asset/image%201%20-%20ui%20setting.png)

## Key Features

### 🌍 Multilingual Support
- Real-time UI language switching
- Automatic detection of system language
- Supports Korean, English, and Chinese

### 🔧 Advanced Translation Features
- **Google Gemini API Integration**: High-quality AI translation
- **Batch Processing**: Splits large files into chunks for processing
- **Recovery System**: Checkpoint-based recovery for interrupted translations
- **Quality Assurance**: YAML syntax checking and translation quality verification

### 🎮 Game-specific Optimization
- Specialized translation prompts for each Paradox game
- Support for game-specific glossaries
- Supports Europa Universalis IV, Crusader Kings III, Hearts of Iron IV, etc.

### 📊 Analysis & Monitoring
- **Live Preview**: Real-time monitoring of translation progress
- **Statistics Dashboard**: Translation analysis and progress tracking
- **Consistency Checker**: Verifies consistency of translated terms

## Screenshots

### API Settings
![API Settings](asset/image%202%20-%20API%20setting.png)

- Currently, you can choose from 5 APIs
- 2.5 Flash: Default
- 2.0 Flash: An option to avoid censorship
- 1.5 Series: When cost is a concern
- 2.5 Pro: For those who want high quality (very expensive and has strict limits!!)

### Folder Selection
![Folder Selection](asset/image%203%20-%20Floder%20Selection.png)

### Language Settings
![Language Settings](asset/image%204%20-%20Language%20Setting.png)

- Currently supports English, Korean, Chinese (Simplified), French, German, Spanish, Portuguese, Japanese, Russian, and Turkish

### Translation Settings
![Translation Settings](asset/image%205%20-%20Translation%20Setting.png)

- **Batch Size**: How many lines to translate at once.
- **Concurrent Files**: How many files to translate simultaneously.
- **Max Output Tokens**: Controls the maximum number of tokens (set to 65536 for 2.5, 8192 for others).
- **Delay Between Batches**: Sets the time delay between API responses.
- **File Split Threshold**: A feature to split long files for translation (e.g., a 30,000-line file set to 1000 will be split into 30 parts).
- **Temperature**: How creative you want the responses to be (closer to 0 is more deterministic, closer to 2.0 is more imaginative).
- **Max Retries**: How many times to retry a batch if an error occurs during translation.

- **Keep Original l_english identifier**: Check this if your language is not supported by the game.
- **Prioritize UI setting...**: Check this if the source language of the file you want to translate is also not supported by the game (e.g., translating Chinese -> Korean in Europa Universalis).
- **Skip Already Translated Lines**: Use this when translating a partially translated mod.

### Prompt Editing
![Prompt Editing](asset/image%206%20-%20Edit%20Prompt.png)

### Glossary Management
![Glossary Management](asset/image%207%20-%20glossary%20management.png)

### Control Panel
![Start/Stop Buttons](asset/image%208%20-%20start%20and%20stop%20button.png)

### Log Panel
![Log Panel](asset/image%209%20-%20File%20Comparison%20Review%20Tool.png)

### Live Preview Panel
![Live Preview Panel](asset/image%2010%20-%20File%20Comparison%20Review%20Tool%20Window.png)

## Installation and Execution

### Prerequisites
```bash
pip install customtkinter google-generativeai
```

### How to Run
```bash
python "pdx translation tool/run_translator.py"
```

-Or, download and run the .EXE file from the Release section.

## How to Use

### 1. API Settings
- Enter your Google Gemini API key.
- Select the model to use (e.g., gemini-1.5-pro, gemini-1.5-flash).

### 2. Folder Settings
- **Input Folder**: Select the folder containing the YAML files to be translated.
- **Output Folder**: Select the folder where the translated files will be saved.

### 3. Language Settings
- **Source Language**: The language of the original files.
- **Target Language**: The language to translate to.

### 4. Advanced Settings
- **Batch Size**: The amount of text to process in one go.
- **Concurrent Workers**: The number of parallel processing threads.
- **Retry Count**: The number of retries upon API errors.

### 5. Start Translation
- Click the "Start Translation" button.
- Monitor the real-time progress.
- Review the results upon completion.

## Architecture

### Core Components

#### TranslatorEngine (`translator_app/core/translator_engine.py`)
- Handles API calls and file processing.
- Implements batch translation and recovery mechanisms.

#### TranslationGUI (`translator_app/gui/main_window.py`)
- The main application window.
- Coordinates all UI panels and manages application state.

#### SettingsManager (`translator_app/core/settings_manager.py`)
- Handles settings persistence and loading.

### GUI Panel Structure

#### Settings Panels (`translator_app/gui/panels/`)
- `api_model_panel.py`: API key and model selection.
- `folder_panel.py`: Input/output folder selection.
- `translation_lang_panel.py`: Source/target language settings.
- `detailed_settings_panel.py`: Advanced translation parameters.
- `prompt_glossary_panel.py`: Custom prompt and glossary management.
- `control_panel.py`: Start/stop translation control.
- `log_panel.py`: Logs translation progress.
- `live_preview_panel.py`: Real-time translation preview.

#### Tool Windows (`translator_app/gui/windows/`)
- `translation_dashboard.py`: Translation statistics and analysis.
- `term_consistency_checker.py`: Translation consistency verification.

## Translation Workflow

1.  **File Discovery**: Scans for YAML files (.yml/.yaml) in the input folder.
2.  **Batch Processing**: Splits large files based on a configurable threshold.
3.  **API Translation**: Uses the Google Gemini API with custom prompts and glossaries.
4.  **Recovery System**: Checkpoint-based recovery for interrupted translations.
5.  **Quality Assurance**: Built-in YAML syntax validation and translation quality checks.

## Key Features

### 🔄 Multithreaded Processing
- Concurrent file processing with a configurable worker limit.

### 🎯 Game-Specific Prompts
- Enhanced prompts for various Paradox games.

### 📚 Glossary Support
- External glossary files for consistent terminology.

### 👀 Live Preview
- Real-time preview of translations as they are being processed.

### 📈 Statistics Dashboard
- Comprehensive translation analytics.

### 💾 Backup System
- Optional file backup before translation.

## Configuration Files

- **Main Settings**: `translation_gui_config.json`
- **Checkpoint Directory**: `checkpoints/` (for recovery)
- Settings are automatically saved upon application exit.

## Development Information

### Tech Stack
- **GUI**: CustomTkinter (for modern UI styling)
- **API**: Google Generative AI
- **Language**: Python 3.7+
- **Encoding**: UTF-8-BOM (for compatibility)

### Language Files
- Location: `translator_app/utils/localization.py`
- Supports automatic system language detection.

### Contributing
1.  Fork this repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## License

This project is distributed under the MIT License. See the `LICENSE` file for more information.

## Support

If you encounter any issues or have feature requests, please let us know via GitHub Issues.

---

**Happy translating! 🎮🌍**

***