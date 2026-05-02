from .models import Service, Hero, About, EmergencyInfo, Emergency, Contact
from django import forms #type:ignore

class HeroForm(forms.ModelForm):
    class Meta:
        model = Hero
        fields = ('title', 'subtitle', 'description','image')
        widgets = {
            'title': forms.TextInput(attrs={'type':'text', 'class':'form-control', 'placeholder':'titre'}),
            'subtitle': forms.TextInput(attrs={
                'type':'text', 
                'class':'form-control', 
                'placeholder':'sous titre'
                }),
            'description': forms.Textarea(attrs={'placeholder': 'description', 'rows':4}),
            'image':forms.ClearableFileInput(attrs={'class':'form-control'})
        }
        
class AboutForm(forms.ModelForm):
    class Meta:
        model = About
        fields = ('title', 'subtitle', 'year', 'goal', 'location', 'description', 'image')
        widgets = {
            'title': forms.TextInput(attrs={
                'type':'text', 
                'class':'form-control', 
                'placeholder':'titre'}),
            
            'subtitle': forms.TextInput(attrs={
                'type':'text', 
                'class':'form-control', 
                'placeholder':'sous titre'}),
            
            'year': forms.DateInput(attrs={'class':'form-control'}),
            'goal': forms.Textarea(attrs={
                'class':'form-control', 
                'placeholder' : 'Le but de votre orgatisation'
                ,'rows':4}),
            'location': forms.TextInput(attrs={
                'type':'text', 
                'class':'form-control', 
                'placeholder':'Votre adresse'
            }),
            
            'description': forms.Textarea(attrs={
                'placeholder': 'description', 
                'rows':4,
                'class':'form-control'}),
            'image':forms.ClearableFileInput(attrs={'class':'form-control'})
        }
        
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ('title', 'departement', 'description', 'icon', 'short_description')
        widgets = {
            'title': forms.TextInput(attrs={
                'type':'text', 
                'class':'form-control', 
                'placeholder':'titre'}),
            
            'departement': forms.Select(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={
                'placeholder': 'description', 
                'rows':4,
                'class':'form-control'}),            
            'icon':forms.TextInput(attrs={'class':'form-control'}),
            'short_description': forms.Textarea(attrs={
                'placeholder': 'description courte', 
                'rows':4,
                'class':'form-control'
            })
            }
        
        help_texts = {
            'title': 'Titre',
            'departement': 'Departement',
            'description': 'Description',
            'icon': 'Icone',
            'short_description': 'ex. 24/7 disponible, service efficace, ...',
        }

class EmergencyInfoForm(forms.ModelForm):
    class Meta:
        model = EmergencyInfo
        fields = ('title', 'phone', 'address', 'operation_time')
        widgets = {
            'title': forms.TextInput(attrs={
                'type':'text', 
                'class':'form-control', 
            }),
            
            'phone': forms.TextInput(attrs={
                'type':'tel', 
                'class':'form-control',
            }),
            'address': forms.Textarea(attrs={
                'class':'form-control',
                'rows':4
            }),
            'operation_time': forms.Textarea(attrs={
                'class':'form-control',
                'rows':4
            })
        }
        
class EmergencyForm(forms.ModelForm):
    class Meta:
        model = Emergency
        fields = ('title', 'description', 'phone')
        widgets = {
            'title': forms.TextInput(attrs={
                'type':'text', 
                'class':'form-control', 
            }),
            
            'description': forms.Textarea(attrs={
                'class':'form-control',
                'rows':4
            }),
            'phone': forms.TextInput(attrs={
                'type':'tel', 
                'class':'form-control',
            })
        }
        
class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ('name', 'operation_days_time','phone', 'email', 'address', 'facebook', 'twitter', 'instagram', 'linkedin')
        widgets = {
            'name': forms.TextInput(attrs={
                'class':'form-control', 
                'placeholder':'Nom de l\'entreprise'
                }),
            'operation_days_time':forms.TextInput(attrs={
                'class':'form-control', 
                'placeholder':'jours et heures de service'
            })
            ,
            'phone': forms.TextInput(attrs={
                'type':'tel', 
                'class':'form-control', 
            }),
            'email': forms.EmailInput(attrs={
                'type':'email', 
                'class':'form-control', 
            }),
            'address': forms.Textarea(attrs={
                'class':'form-control',
                'rows':4
            }), 
            'facebook': forms.TextInput(attrs={'class':'form-control', 
                                               'placeholder':'Lien facebook'}),
            'twitter': forms.TextInput(attrs={'class':'form-control', 
                                               'placeholder':'Lien X(twitter)'}),
            'instagram': forms.TextInput(attrs={'class':'form-control', 
                                               'placeholder':'Lien instagram'}), 
            'linkedin': forms.TextInput(attrs={'class':'form-control', 
                                               'placeholder':'Lien linkedin'})
        }