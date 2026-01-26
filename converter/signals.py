import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from converter.models.file_model import ConverterFile


@receiver(post_delete, sender=ConverterFile)
def delete_file_on_model_delete(sender, instance, **kwargs):
    """
    Remove o ficheiro físico do disco (e pasta UUID vazia)
    quando o ConverterFile é deletado.
    """
    if not instance.file:
        return

    try:
        # Captura a pasta ANTES de deletar o arquivo
        try:
            folder = os.path.dirname(instance.file.path)
        except Exception:
            folder = None

        # Remove o arquivo via storage (correto para S3, FS, etc)
        instance.file.delete(save=False)

        # Remove a pasta UUID se estiver vazia
        if folder and os.path.isdir(folder) and not os.listdir(folder):
            try:
                os.rmdir(folder)
            except OSError:
                pass

    except Exception:
        # Em produção, usar logging
        pass
