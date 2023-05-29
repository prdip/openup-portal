# Render to string 
from django.template.loader import render_to_string

#import message 
from django.contrib import messages

#import mail library
from django.core.mail import EmailMessage
import environ 
env = environ.Env()
environ.Env.read_env()







class SendEmail:
    
    def send_email(data_dict): 

        domain              =   env('MAIL_URL')
        Subject             =   data_dict['Subject']
        text_template       =   data_dict['text_template'] #"email/verify_user.txt"
        # EMAIL FORMAT
        email_data = {
                "token"     :   data_dict['token'],
                'domain'    :   domain,
    			'site_name' :   'Website',     #Data which will send with E-mail id
    			'protocol'  :   'http',

            } 
        myemail     =       render_to_string(text_template,email_data)  # Converts text file to string 
        email       =       EmailMessage(Subject, myemail, to=[ data_dict['to']])  #Formats Email message       
        email.send()
        return True
