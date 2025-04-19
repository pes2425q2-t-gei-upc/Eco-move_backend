from modeltranslation.translator import register, TranslationOptions
from .models import TextItem

@register(TextItem)
class TextItemTranslationOptions(TranslationOptions):
    fields = ('text',)