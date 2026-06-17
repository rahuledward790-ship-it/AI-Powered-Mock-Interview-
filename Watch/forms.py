from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password


class RegisterForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Enter Password'
            }
        )
    )

    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter Full Name'
            }
        )
    )

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Enter Email Address'
            }
        )
    )

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter Username'
            }
        )
    )

    class Meta:
        model = User

        fields = [
            'first_name',
            'email',
            'username',
            'password'
        ]

    def save(self, commit=True):

        user = super().save(commit=False)

        user.password = make_password(
            self.cleaned_data['password']
        )

        if commit:
            user.save()

        return user