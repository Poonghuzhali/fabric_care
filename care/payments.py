import logging
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings

logger = logging.getLogger(__name__)


def payments_enabled():
    return bool(getattr(settings, "RAZORPAY_KEY_ID", "") and getattr(settings, "RAZORPAY_KEY_SECRET", ""))


def price_to_paise(amount) -> int:
    value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(value * 100)


def get_razorpay_client():
    if not payments_enabled():
        return None
    try:
        import razorpay
    except ImportError as exc:
        raise RuntimeError("Install the razorpay package to accept online payments.") from exc
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def create_service_order(*, user, service):
    client = get_razorpay_client()
    amount_paise = price_to_paise(service.price)
    if amount_paise < 100:
        raise ValueError("Service price must be at least ₹1.")
    receipt = f"svc-{service.id}-u{user.id}"[:40]
    order = client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": {
                "service_id": str(service.id),
                "service_name": service.name,
                "user_id": str(user.id),
            },
        }
    )
    return order, amount_paise


def verify_payment_signature(*, order_id, payment_id, signature):
    if getattr(settings, "PAYMENT_SKIP_VERIFY", False):
        if order_id and payment_id and signature:
            return True
        return False
    client = get_razorpay_client()
    if not client:
        return False
    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )
        return True
    except Exception:
        logger.exception("Razorpay signature verification failed")
        return False
