from rest_framework.exceptions import APIException


EMAIL_DELIVERY_FAILED = (
    "We couldn't send that email right now. Wait a minute and try again."
)


class EmailDeliveryFailed(APIException):
    status_code = 503
    default_detail = EMAIL_DELIVERY_FAILED
    default_code = "email_delivery_failed"
