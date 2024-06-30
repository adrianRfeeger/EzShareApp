# -*- mode: python ; coding: utf-8 -*-

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

pyz = PYZ(a.pure)

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
    bundle_identifier=None,
info_plist={
        'CFBundleName': 'EzShareCPAP',
        'CFBundleDisplayName': 'EzShareCPAP',
        'CFBundleGetInfoString': 'EzShareCPAP',
        'CFBundleIdentifier': 'com.ezsharecpap',  # Replace with your bundle identifier
        'CFBundleVersion': '1.0.1',
        'CFBundleShortVersionString': '1.0.1',
        'NSAppTransportSecurity': {
            'NSAllowsArbitraryLoads': True,
        },
        'NSDocumentsFolderUsageDescription': 'Reason for accessing the Documents folder',
        'NSLocalNetworkUsageDescription': 'Reason for accessing the local network',
        'NSLocationWhenInUseUsageDescription': 'Reason for accessing location information',
    }
)
