# Render to string 
from django.template.loader import render_to_string

#import message 
from django.contrib import messages

#import mail library
from django.core.mail import EmailMessage


class SendEmail:
    
    def send_email(data_dict): 
        Subject             =   data_dict['Subject']
        text_template       =   data_dict['text_template'] #"email/verify_user.txt"
        # EMAIL FORMAT
        email_data = {
                "email"     :   data_dict['email'],
                'domain'    :   '192.168.1.4:8000',
    			'site_name' :   'Website',     #Data which will send with E-mail id
    			'protocol'  :   'http',
            }
        myemail     =       render_to_string(text_template,email_data)  # Converts text file to string 
        email       =       EmailMessage(Subject, myemail, to=[ data_dict['to']])  #Formats Email message       
        email.send()
        return True
