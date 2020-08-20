# picture_handler na pasta users

import os
from PIL import Image
from flask import url_for, current_app

def add_profile_pic(pic_upload):
    """+--------------------------------------------------------------------------------------+
       |Trata e salva a imagem de perfil do usuário quando este a atualiza.                   |
       |A imagem fica guardada em pasta específica do sistema. No banco de dados fica         |
       |somente o nome do arquivo de imagem.                                                  |
       +--------------------------------------------------------------------------------------+
    """

    filename = pic_upload.filename

    filepath = os.path.join(current_app.root_path,'static\profile_pics',filename)

    output_size = (200,200)

    pic = Image.open(pic_upload)
    pic.thumbnail(output_size)
    pic.save(filepath)
    pic.close()

    return filename
