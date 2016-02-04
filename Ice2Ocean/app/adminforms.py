from django import forms

class NameForm(forms.Form):
    your_name = forms.CharField(label='Your name', max_length=100)


class PopulateTableForm(forms.Form):
    year        = forms.DecimalField(label="Year")
    julian_hour = forms.DecimalField(label='Julian Hour')
