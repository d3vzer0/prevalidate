import clr  # noqa: F401
import os
from System import Reflection

# Load KustoLanguage DLL to analyse queries
dll_path = f'{os.getcwd()}/prevalidate/libs//Kusto.Language.dll'
Reflection.Assembly.LoadFile(dll_path)
