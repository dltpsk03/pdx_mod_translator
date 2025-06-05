# translator_project/run_translator.py
import sys
import os

current_script_dir = os.path.dirname(os.path.abspath(__file__))
if current_script_dir not in sys.path:
    sys.path.insert(0, current_script_dir)

from translator_app.gui.main_window import TranslationGUI

def main():
    app = TranslationGUI()
    app.mainloop()

if __name__ == "__main__":
    if sys.platform == "win32":
        import ctypes
        myappid = u'mycompany.myproduct.paradoxmodtranslator.1' # 앱 ID 변경
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except AttributeError:
            pass
    main()
