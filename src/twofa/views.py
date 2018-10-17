from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from twofa import models


@login_required
def index(request):

    if request.POST:
        _type = request.POST.get('register')
        models.UserRegistration.objects.get_or_create(
            account=request.user,
            type=_type
        )

        messages.add_message(request, messages.SUCCESS, 'Registration complete')
        return redirect(reverse('twofa_index'))

    user_registrations = [reg.type for reg in models.UserRegistration.objects.filter(account=request.user)]

    template = 'twofa/index.html'
    context = {
        'types': models.two_factor_types,
        'user_registrations': user_registrations,
    }

    return render(request, template, context)


def handler(request):
    print('hi')
    user_registrations = [reg.type for reg in models.UserRegistration.objects.filter(account=request.user)]

    # TODO: Decide which 2FA method to use
    if 'u2f' in user_registrations:
        # TODO: redirect to u2f handler
        pass
    elif 'authenticator' in user_registrations:
        # TODO: redirect to authenticator handler
        pass
    elif 'email' in user_registrations:
        # TODO: redirect to email handler
        pass
    else:
        messages.add_message(request, messages.WARNING, 'No Two Factor Auth registrations found.')
        return redirect(reverse('core_login'))

