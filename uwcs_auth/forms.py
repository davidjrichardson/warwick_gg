from django import forms


class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    uni_id = forms.CharField(max_length=11, help_text='If you are an associate member then use that ID number')
    nickname = forms.CharField(max_length=50, required=False)

    def signup(self, request, user):
        pass
