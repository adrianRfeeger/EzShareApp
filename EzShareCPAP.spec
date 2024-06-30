# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('icon.icns', '.'), ('config.ini', '.')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EzShareCPAP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
    icon='icon.icns'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=True,
    name='EzShareCPAP'
)

app = BUNDLE(
    coll,
    name='EzShareCPAP.app',
    icon='icon.icns',
    bundle_identifier='com.ezsharecpap',
    info_plist={
        'CFBundleName': 'EzShareCPAP',
        'CFBundleDisplayName': 'EzShareCPAP',
        'CFBundleGetInfoString': 'EzShareCPAP',
        'CFBundleIdentifier': 'com.ezsharecpap',
        'CFBundleVersion': '1.0.1',
        'CFBundleShortVersionString': '1.0.1',
        'NSAppTransportSecurity': {
            'NSAllowsArbitraryLoads': True,
        },
        'NSDocumentsFolderUsageDescription': 'This application requires access to the Documents folder.',
        'NSLocalNetworkUsageDescription': 'This application requires access to the local network to find and communicate with devices.',
        'NSLocationWhenInUseUsageDescription': 'This application requires access to location information for better user experience.',
    }
)
