# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['jcatch/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # CLI
        'click',

        # Data models
        'pydantic',
        'pydantic_core',

        # HTTP requests
        'requests',
        'requests.adapters',

        # HTML parsing
        'bs4',
        'bs4.builder',
        'lxml',
        'lxml._elementpath',

        # Selenium
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.webdriver',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'webdriver_manager',
        'webdriver_manager.chrome',

        # Other
        'dotenv',
        'PIL',
    ],
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
    a.binaries,
    a.datas,
    [],
    name='jcatch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
