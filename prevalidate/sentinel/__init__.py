import clr  # noqa: F401
import os
from System import Reflection

current_dir = os.path.dirname(__file__)
dll_path = 'libs/Kusto.Language.dll'
# Load KustoLanguage DLL to analyse queries
Reflection.Assembly.LoadFile(os.path.join(current_dir, dll_path))
