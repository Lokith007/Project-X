from django import forms
from tinymce.widgets import TinyMCE
from myapp.models import event

class EventForm(forms.ModelForm):          
    description = forms.CharField(widget=TinyMCE(attrs={
                'class': 'w-full px-4 py-2 mx-auto text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 h-96 resize-none',
                'placeholder': 'Give a Brief Overview of the Event, details, rewards...',
                'id': 'eventDescription',
                'data-mce-theme': 'dark'
            }, mce_attrs={
                'skin': 'oxide-dark',
                'content_css': 'dark',
                'toolbar_mode': 'sliding',
                'menubar': False,
                'plugins': 'advlist autolink lists link image charmap print preview anchor searchreplace visualblocks code fullscreen insertdatetime media table paste code help wordcount',
                'toolbar': 'undo redo | formatselect | bold italic backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | help',
                'content_style': 'body { font-family:Helvetica,Arial,sans-serif; font-size:14px; background-color: #0e1217; color: #ffffff; } .tox-tinymce { background-color: #0e1217 !important; border: 1px solid #0e1217 !important; border-radius: 6px !important; } .tox-toolbar { background-color: #0e1217 !important; } .tox-edit-area { background-color: #0e1217 !important; }'
            }))
    
    class Meta:
        model = event
        exclude = ['organization', 'created_at', 'updated_at']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
                'placeholder': 'Event Title',
                'id': 'eventName'
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 h-20 resize-none transition-all duration-200',
                'placeholder': 'Event Description',
                'id': 'eventShortDescription'
            }),
            'event_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
                'id': 'eventType'
            }),
            'mode': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
                'id': 'eventMode'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
                'placeholder': 'Location',
                'id': 'eventLocation',
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
                'id': 'eventStartdate'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-5/6 px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
                'id': 'eventStartTime',
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
                'id': 'eventEnddate'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-5/6 px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
                'id': 'eventEndTime',
            }),
            'registration_link': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
                'placeholder': 'https://register-link.com',
                'id': 'regLink'
            }),
            'contact_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
                'placeholder': 'Organizer Name',
                'id': 'eventOrganizerName'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
                'placeholder': 'Organizer Email',
                'id': 'eventOrganizerEmail'
            }),
            'contact_phone': forms.TextInput(attrs={
                'type': 'tel',
                'class': 'w-full px-4 py-2 border border-[#2d323b] bg-[#161b22] text-white rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
                'placeholder': 'Organizer Phone',
                'id': 'eventOrganizerPhone'
            }),
            'banner': forms.FileInput(attrs={
                'class': 'w-full border border-[#2d323b] bg-[#161b22] text-white p-3 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 file:bg-gradient-to-br file:from-green-600 file:to-green-800 file:text-white file:border-none file:px-4 file:py-2 file:rounded-md file:cursor-pointer hover:file:from-green-500 hover:file:to-green-700 transition-all duration-200'
            }),
        }
        labels = {
            'title': 'Event Name',
            'start_time':'Event Time'
        }