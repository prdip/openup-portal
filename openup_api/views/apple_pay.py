from rest_framework.decorators import api_view
from django.http.response import JsonResponse
from django.utils import timezone
from openup_api.views.auth_views import token_verification
from openup_app.models import SuccessPayments
import stripe
import environ
import logging

env = environ.Env()
environ.Env.read_env()

logger = logging.getLogger(__name__)

stripe.api_key = env('STRIPE_SECRET')


@api_view(['POST'])
def apple_pay(request):
    token = request.headers.get('Authorization')
    if not token:
        return JsonResponse({"success": 2, "message": "Authorization header missing"})

    user_token = token.replace("Bearer", '')
    check_user = token_verification(user_token)

    if check_user is None:
        return JsonResponse({"success": 2, "message": "Unauthorized User"})

    user_id = check_user['session_user']

    amount = request.data.get('amount')
    currency = request.data.get('currency', 'usd')
    payment_token = request.data.get('payment_token')

    if not amount:
        return JsonResponse({"success": 0, "message": "Amount is required"})

    if not payment_token:
        return JsonResponse({"success": 0, "message": "Payment token is required"})

    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount),
            currency=currency,
            payment_method_data={
                'type': 'card',
                'card': {
                    'token': payment_token['id'],
                },
            },
            confirm=True,
            automatic_payment_methods={
                'enabled': True,
                'allow_redirects': 'never',
            },
        )

        if payment_intent.status == 'succeeded':
            '''
            APPLE PAY TOKENS ARE SINGLE USE, SO NOTHING CAN BE SAVED ON THE CUSTOMER
            FOR A LATER CHARGE. INSTEAD THE SUCCESSFUL PAYMENT IS PARKED HERE WITH AN
            EMPTY pay_job AND add_job CLAIMS IT FOR THE JOB IT CREATES.
            '''
            SuccessPayments.objects.create(
                pay_user=str(user_id),
                pay_job="",
                pay_type="apple_pay",
                pay_response=str(payment_intent),
                create_at=timezone.now(),
            )

            return JsonResponse({
                "success": 1,
                "message": "Payment completed successfully",
                "data": {
                    "payment_intent_id": payment_intent.id,
                    "status": payment_intent.status,
                    "amount": payment_intent.amount,
                    "currency": payment_intent.currency,
                }
            })
        else:
            return JsonResponse({
                "success": 0,
                "message": f"Payment not completed: {payment_intent.status}",
            })

    except stripe.error.CardError as e:
        logger.error(f"Apple Pay card error: {e}")
        return JsonResponse({"success": 0, "message": e.error.message})

    except stripe.error.InvalidRequestError as e:
        logger.error(f"Apple Pay invalid request: {e}")
        return JsonResponse({"success": 0, "message": "Invalid payment request"})

    except stripe.error.AuthenticationError as e:
        logger.error(f"Apple Pay auth error: {e}")
        return JsonResponse({"success": 0, "message": "Payment authentication failed"})

    except Exception as e:
        logger.error(f"Apple Pay error: {e}")
        return JsonResponse({"success": 0, "message": "Something went wrong with the payment"})
