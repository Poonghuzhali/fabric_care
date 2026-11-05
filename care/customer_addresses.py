from decimal import Decimal

from django.db import transaction

from .models import CustomerAddress


def _normalize_address(text):
    return " ".join((text or "").split()).lower()


def addresses_for_user(user):
    return CustomerAddress.objects.filter(customer=user).order_by("-is_default", "-updated_at", "-id")


def address_payload(address):
    return {
        "id": address.id,
        "label": address.display_label(),
        "address": address.address,
        "lat": float(address.latitude),
        "lng": float(address.longitude),
        "maps_url": address.maps_url or "",
        "is_default": address.is_default,
    }


def remember_customer_address(
    user,
    *,
    address,
    latitude,
    longitude,
    maps_url="",
    label="",
):
    if not user or not user.is_authenticated:
        return None
    normalized = _normalize_address(address)
    if len(normalized) < 10:
        return None
    lat = Decimal(str(latitude))
    lng = Decimal(str(longitude))

    with transaction.atomic():
        qs = CustomerAddress.objects.select_for_update().filter(customer=user)
        for existing in qs:
            if _normalize_address(existing.address) == normalized:
                existing.latitude = lat
                existing.longitude = lng
                existing.maps_url = maps_url or existing.maps_url
                if label.strip():
                    existing.label = label.strip()[:40]
                existing.save(
                    update_fields=["latitude", "longitude", "maps_url", "label", "updated_at"]
                )
                return existing

        count = qs.count()
        auto_label = label.strip()[:40] if label.strip() else ("Home" if count == 0 else f"Address {count + 1}")
        is_default = count == 0
        return CustomerAddress.objects.create(
            customer=user,
            label=auto_label,
            address=" ".join(address.split()),
            latitude=lat,
            longitude=lng,
            maps_url=maps_url or "",
            is_default=is_default,
        )


def set_default_address(user, address_id):
    with transaction.atomic():
        qs = CustomerAddress.objects.filter(customer=user)
        target = qs.filter(pk=address_id).first()
        if not target:
            return False
        qs.update(is_default=False)
        target.is_default = True
        target.save(update_fields=["is_default", "updated_at"])
        return True
