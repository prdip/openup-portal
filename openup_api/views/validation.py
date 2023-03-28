
import re
# Validation for checkboxes
def check_text(text):   

    flag = True
    if any (char.isdigit() for char in text):
        flag = False
        return False
    
    else:
        regex = re.compile(r'<[^>]+>')
        text =  regex.sub('', text)

        specialsymbols = ['!','@','#','&']
        if not any(char in specialsymbols for char in text):
            return text
        else:
            return False




# Email Validation

def email_address(email):
    reg = r'\b[a-z0-9.%+-]+@[a-z0-9.-]+[a-z]\b'

    if (re.fullmatch(reg,email)):
        return True
    else:
        return False




# Check Mobile Number 
def mobile_number(mob_no):
    check = (re.findall("[0123456789]",mob_no))
    if check == []:
        return False
    else:
        if len(mob_no) >= 10 and len(mob_no)<12:
            return True
        else:
            return False
        



# validate only number 

def check_number(check_no): 
    if not all (char.isdigit() for char in check_no):
        return False
    else:
        return True
    





'''

convert queryset to dict
list_result = [entry for entry in verify]   Queryset to dict
        verify  =verify.__dict__
        session= list_result[0]
       
'''


'''
        # s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        # s.bind(('', 0))
        # owners_port = int(s.getsockname()[1])
        '''



def verify_card(card_no):
    sum=0
    even_no_sum = 0
    not_greater_sum = 0
    card = len(card_no)
    
    card_no= card_no.replace(" ", "")
    for i in range (card-1,-1,-1):

        if i % 2 == 0:
            d = ord(card_no[i]) - ord('0')
            double = 2*d

            if double > 9:
                for num in str(double):
                    sum = int(num)+sum
            else:
                not_greater_sum = not_greater_sum+double
        else:
             
            
            even_no_sum = even_no_sum+int(card_no[i])
 
            
        Total_sum = even_no_sum+not_greater_sum+sum

      

    if Total_sum % 10==0:
        return True
    else:
        return False



# card_no = "4111111111111111"

# flag = verify_card(card_no)

# print(flag)


