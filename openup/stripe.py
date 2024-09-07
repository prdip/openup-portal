# import datetime
import requests,json,time 
import stripe
import environ 
env = environ.Env()
environ.Env.read_env()


Skey         =   env('STRIPE_KEY')
Ssecret      =   env('STRIPE_SECRET')

stripe.api_key = Skey

class InStripe: 
    def create_invoice():
    # def create_invoi  ce(stripe_customer_id,amount):
        stripe_customer_id  = 'cus_NbmGZ2EEbO9yOt'
        amount              = 500
        currency            = 'inr'
 
        # return_data = stripe.Invoice.create(
        #     customer=stripe_customer_id,  
        # )
        
        # # ADD ITEM
        # invoice_item = stripe.InvoiceItem.create(
        #     customer    =   stripe_customer_id,
        #     amount      =   int(amount*100),
        #     currency    =   currency,
        #     description =   'DONE DONA DONE',
        #     invoice     =   return_data.id
        # )


        try:
           aa=  stripe.PaymentIntent.create(
                amount          =   1099,
                currency        =   'inr',
                customer        =   stripe_customer_id,
                payment_method  =   'pm_1MqZlWSFAwJIbH9ep3gVCW4Y',
                off_session     =   True,
                confirm         =   True,
            )
          
        except stripe.error.CardError as e:
            err = e.error
            # Error code will be authentication_required if authentication is needed
            
            payment_intent_id = err.payment_intent['id']
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)



        # charge_data = stripe.Invoice.pay(return_data.id)
        # print(charge_data)

        # RETRIVE
        # invoice = stripe.Invoice.retrieve(
        #   "in_1MqZ7VSFAwJIbH9eceCijVtY",
        # )


        # card = InStripe.create_payment_method("4242424242424242",8,2023,"314")
        # print(card)

        # link = InStripe.link_method("pm_1MqZlWSFAwJIbH9ep3gVCW4Y",'cus_NbmGZ2EEbO9yOt')
        # print(link)

        # link = InStripe.get_payment_method("pm_1MqZlWSFAwJIbH9ep3gVCW4Y")
        # print(link)

        # CHARGE
        # charge_data = stripe.Invoice.pay("in_1MqZ7VSFAwJIbH9eceCijVtY")
        
        # print(charge_data)  
        return True
         

         
    def create_payment_method(card_no,exp_month,exp_year,cvc):
        card = stripe.PaymentMethod.create(
            type  =   "card",
            card  =   {
                "number"        :   card_no,
                "exp_month"     :   exp_month,
                "exp_year"      :   exp_year,
                "cvc"           :   cvc,
            },
        ) 
        return card

    def get_payment_method(method_id):
        card = stripe.PaymentMethod.retrieve(
            method_id,
        )
        return card


    def link_method(method_id,customer_id):
        stripe.PaymentMethod.attach(
            method_id,
            customer=customer_id,
        )

    def setupIntent(customer_id):
        instance = stripe.SetupIntent.create(
            customer=customer_id,
            payment_method_types=["bancontact", "card", "ideal"],
        )
        return instance
