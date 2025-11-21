from django import forms
from .models import MindLog

class MindLogForm(forms.ModelForm):
    
    class Meta:
        model = MindLog
        fields = ['content', 'snap_shot']
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': "What are you working on today?",
                'id': "mind-log-input",
                'class': "flex-1 h-12 sm:h-14 bg-transparent focus:outline-none text-white placeholder-gray-500 font-mono text-sm",
                'autocomplete': "off",
                'autocorrect': "off",
                'spellcheck': "false",
                'maxlength': '280',
            }),
            'snap_shot': forms.ClearableFileInput(attrs={
                'id': 'snapshotInput',
                'accept': 'image/*',
                'onchange': 'handle_log_ImageUpload(event)',
                'class': 'hidden',
            }),
        }
