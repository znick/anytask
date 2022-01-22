from django.utils.translation import ugettext as _


class BaseRenderer:
    def __init__(self):
        pass

    def render_notification(self, user_profile, unread_messages):
        raise NotImplementedError

    def render_fulltext(self, message, recipients):
        raise NotImplementedError

    @classmethod
    def _get_string(cls, num):
        if 11 <= num <= 14:
            return _(u"novyh_soobshenij")
        elif str(num)[-1] == "1":
            return _(u"novoe_soobshenie")
        elif str(num)[-1] in ["2", "3", "4"]:
            return _(u"novyh_soobshenija")
        else:
            return _(u"novyh_soobshenij")


class BaseSender:
    def __init__(self):
        pass

    def mass_send(self, prepared_messages):
        """
        Returns: number of sent messages (1 or 0)
        """
        raise NotImplementedError
