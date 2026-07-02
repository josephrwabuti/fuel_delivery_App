from core.models import Notification
from django.utils.timesince import timesince
import json


def customer_unread_notif_count(request):
    ctx = {"unread_notif_count": 0, "notifs_json": "[]"}
    if not request.user.is_authenticated:
        return ctx

    notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")[:5]

    notifs_list = []
    unread = 0
    for n in notifications:
        if not n.is_read:
            unread += 1
        notifs_list.append({
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "time": timesince(n.created_at) + " ago",
        })

    ctx["unread_notif_count"] = unread
    ctx["notifs_json"] = json.dumps(notifs_list)
    return ctx
