# -*- mode: python ; coding: utf-8 -*-

# Define your data files
added_files = [    
    ('./src/resources/*', 'src/resources'),
    ('./src/resources/HelpImages/*', 'src/resources/HelpImages'),              
    ('./src/lib/*.ini', 'src/lib'),     
    ('./src/lib/data/*', 'src/lib/data'),   
    ('./predictand files/*', 'predictand files'), 
    ('./predictor files/*', 'predictorfiles'), 
    # Add any other data files your app needs
]

# Make sure all modules in src/modules are included
import os
module_files = []
modules_dir = './src/modules'
if os.path.exists(modules_dir):
    # Get all Python files in the modules directory
    module_files = []
    for f in os.listdir(modules_dir):
        if f.endswith('.py') and f != '__init__.py':
            # Just use the filename without extension
            module_name = os.path.splitext(f)[0]
            module_files.append(module_name)

hidden_modules = [
    'numpy.random',
    'numpy.random.common',
    'numpy.random.bounded_integers',
    'numpy.random.entropy',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_tkagg',
    'PyQt5.QtPrintSupport',      # Required for some Matplotlib features
]

# Add all modules from src/modules to hiddenimports
for module_name in module_files:
    # Convert to proper module format
    hidden_modules.append(f"src.modules.{module_name}")

# These module paths look good - no change needed
hidden_modules.append("src.core.data_settings")
hidden_modules.append("src.core.home")
hidden_modules.append("src.core.system_settings")
hidden_modules.append("src.lib.FrequencyAnalysis.FA")
hidden_modules.append("src.lib.FrequencyAnalysis.FATabluar")
hidden_modules.append("src.lib.FrequencyAnalysis.frequency_analysis_function")
hidden_modules.append("src.lib.FrequencyAnalysis.IDF")
hidden_modules.append("src.lib.FrequencyAnalysis.IDFTabular")
hidden_modules.append("src.lib.FrequencyAnalysis.Line")
hidden_modules.append("src.lib.FrequencyAnalysis.PDF")
hidden_modules.append("src.lib.FrequencyAnalysis.QQ")

a = Analysis(
    ['main.py'],
    pathex=['.'],  # Include current directory in path
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_modules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Changed from False to True to show console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SDSM',
)