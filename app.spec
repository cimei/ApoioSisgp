# -*- mode: python -*-

block_cipher = None


a = Analysis(['app.py'],
             pathex=['C:\\Users\\cimeibt\\Documents\\PythonScripts\\ApoioSisgp'],
             binaries=[],
             datas=[('instance','var\\project-instance'),
                    ('project\\atividades', 'project\\atividades'),
                    ('project\\consultas', 'project\\consultas'),
                    ('project\\core', 'project\\core'),
                    ('project\\error_pages', 'project\\error_pages'),
                    ('project\\padroes', 'project\\padroes'),
                    ('project\\pessoas', 'project\\pessoas'),
                    ('project\\static','project\\static')],
                    ('project\\templates', 'project\\templates'),
                    ('project\\unidades', 'project\\unidades'),
                    ('project\\usuarios', 'project\\usuarios'),
             hiddenimports=['sqlalchemy.sql.default_comparator','pyodbc'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='app',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
