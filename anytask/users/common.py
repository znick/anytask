# coding: utf-8


def get_user_fullname(user):
    return u"%s %s" % (user.last_name, user.first_name)


def get_user_link(user):
    return u'<a class="user" href="{0}">{1}</a>'.format(user.get_absolute_url(), get_user_fullname(user))
