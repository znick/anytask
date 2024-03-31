from django.http import HttpResponseBadRequest, Http404, HttpResponse
from django.utils import translation
from django.views.decorators.http import require_POST
from django.utils.deprecation import MiddlewareMixin

COOKIE_NAME = "anytask_lang"

# Recipe from https://stackoverflow.com/questions/36859854/use-cookie-only-for-user-language-instead-of-opening-session


class LanguageCookieMiddleware(MiddlewareMixin):
    def process_request(self, request):
        lang = request.COOKIES.get(COOKIE_NAME)
        if not lang:
            return

        if not translation.check_for_language(lang):
            return

        translation.activate(lang)
        request.LANGUAGE_CODE = translation.get_language()


@require_POST
def set_lang_view(request):
    lang = request.POST.get('lang')
    if not lang:
        return HttpResponseBadRequest()

    if not translation.check_for_language(lang):
        raise Http404

    response = HttpResponse('ok')
    response.set_cookie(COOKIE_NAME, lang)
    return response


def get_lang_view(request):
    response = HttpResponse(translation.get_language())
    return response
